"""The wider Notion schema map, against a fake Notion.

Same rules as test_notion_board.py, extended to the seventeen logical fields
in notion_schema.py: only mapped, changed fields are ever sent; properties
this map does not own survive untouched; a missing or wrong-typed property
stops before any write; a stale row is refused; lifecycle values pass through
an explicit table with no fuzzy matching; an identical write is a no-op.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import board_provider as bp  # noqa: E402
import notion_board as nb  # noqa: E402
import notion_schema as ns  # noqa: E402

DB = "a" * 32
DS = "b" * 32
TOKEN = "secret_token_value_123"

LIFECYCLE_TABLE = {
    "thinking": "01 Idea", "writing": "02 Drafting", "editing": "03 Review",
    "ready": "04 Ready", "sent": "05 Live",
}

def full_schema(extra=None):
    schema = {name: {"type": kind} for f, (name, kind) in ns.FIELDS.items()}
    schema.update(extra or {})
    return schema


class FakeNotion:
    """The parts of Notion's API notion_schema.py calls."""

    def __init__(self, sources=None, schema=None, extra_props=None):
        self.sources = sources if sources is not None else [{"id": DS, "name": "Board"}]
        self.schema = schema if schema is not None else full_schema()
        self.extra_props = extra_props or {}
        self.pages, self.calls, self.bodies, self.script = [], [], [], []
        self.tick = 0

    def stamp(self):
        self.tick += 1
        return f"2026-09-20T10:00:{self.tick:02d}.000Z"

    def add(self, piece_id="", **values):
        props = {}
        for f, (name, kind) in ns.FIELDS.items():
            if f == "piece_id":
                props[name] = {"rich_text": [{"plain_text": piece_id}] if piece_id else []}
                continue
            v = values.get(f, "")
            if kind == "rich_text":
                props[name] = {"rich_text": [{"plain_text": v}] if v else []}
            elif kind == "select":
                props[name] = {"select": {"name": v} if v else None}
            elif kind == "url":
                props[name] = {"url": v or None}
            elif kind == "date":
                props[name] = {"date": {"start": v} if v else None}
        props.update(self.extra_props)
        page = {"id": f"page-{len(self.pages) + 1}", "url": "https://notion.so/x",
                "properties": props, "last_edited_time": self.stamp()}
        self.pages.append(page)
        return page

    def edit_elsewhere(self, page):
        page["last_edited_time"] = self.stamp()

    @staticmethod
    def _read(value):
        out = dict(value)
        if "rich_text" in out:
            out["rich_text"] = [{"plain_text": r["text"]["content"]} for r in out["rich_text"]]
        return out

    def __call__(self, method, url, headers, body):
        path = url[len(nb.API):]
        data = json.loads(body) if body else None
        self.calls.append((method, path))
        if data is not None:
            self.bodies.append(data)
        if self.script:
            step = self.script.pop(0)
            if isinstance(step, Exception):
                raise step
            return step
        if method == "GET" and path == f"/databases/{DB}":
            return 200, {}, {"data_sources": self.sources}
        if method == "GET" and path.startswith("/data_sources/"):
            return 200, {}, {"object": "data_source", "properties": self.schema}
        if method == "POST" and path.endswith("/query"):
            rows = self.pages
            flt = (data or {}).get("filter")
            if flt:
                pid_name = ns.FIELDS["piece_id"][0]
                want = flt["rich_text"]["equals"]
                rows = [p for p in rows
                        if "".join(r["plain_text"] for r in p["properties"][pid_name]["rich_text"]) == want]
            return 200, {}, {"results": rows, "has_more": False, "next_cursor": None}
        if method == "PATCH" and path.startswith("/pages/"):
            page = next(p for p in self.pages if p["id"] == path.split("/")[-1])
            for name, value in data["properties"].items():
                page["properties"][name] = self._read(value)
            page["last_edited_time"] = self.stamp()
            return 200, {}, page
        raise AssertionError(f"unexpected call {method} {path}")


def provider(fake, names=None, lifecycle_table=None, data_source=None):
    client = nb.NotionClient(TOKEN, transport=fake, sleep=lambda s: None, clock=lambda: 0.0, rng=lambda: 0.5)
    lifecycle = ns.LifecycleMap(lifecycle_table if lifecycle_table is not None else LIFECYCLE_TABLE)
    return ns.SchemaProvider(client, DB, data_source, names, lifecycle)


class ExactSchema(unittest.TestCase):
    def test_reading_and_writing_each_mapped_field_round_trips(self):
        f = FakeNotion()
        p = provider(f)
        page = f.add(
            piece_id="abc123", lifecycle="01 Idea", body_state="thinking", content_type="Essay",
            audience="Newsletter", channel="Bluesky", theme="Craft", priority="High", owner="Elle",
            next_action="Draft the opening", decision_gate="Pick an angle", blocker="Waiting on a source",
            source_url="https://example.com/a", related_project="Familiar",
            last_worked="2026-09-18", target_date="2026-09-25", publication_url="https://example.com/b")
        row = p.read("abc123")
        expected = {
            "lifecycle": "thinking", "body_state": "thinking", "content_type": "Essay",
            "audience": "Newsletter", "channel": "Bluesky", "theme": "Craft", "priority": "High",
            "owner": "Elle", "next_action": "Draft the opening", "decision_gate": "Pick an angle",
            "blocker": "Waiting on a source", "source_url": "https://example.com/a",
            "related_project": "Familiar", "last_worked": "2026-09-18",
            "target_date": "2026-09-25", "publication_url": "https://example.com/b",
        }
        for field, value in expected.items():
            self.assertEqual(value, row[field], field)

        p.update("abc123", {"priority": "Low", "next_action": "Send the draft"}, row["version"])
        row2 = p.read("abc123")
        self.assertEqual("Low", row2["priority"])
        self.assertEqual("Send the draft", row2["next_action"])
        # Untouched fields keep their values.
        self.assertEqual("Essay", row2["content_type"])


class UnknownProperties(unittest.TestCase):
    def test_extra_unknown_properties_are_byte_for_byte_unchanged(self):
        extra = {"Owner (people)": {"people": [{"id": "u9"}]}, "Custom rank": {"number": 7}}
        f = FakeNotion(schema=full_schema({"Owner (people)": {"type": "people"},
                                            "Custom rank": {"type": "number"}}),
                       extra_props=extra)
        f.add(piece_id="abc123", priority="High")
        p = provider(f)
        before = json.loads(json.dumps(f.pages[0]["properties"]))
        row = p.read("abc123")
        p.update("abc123", {"priority": "Low"}, row["version"])
        after = f.pages[0]["properties"]
        for name in extra:
            self.assertEqual(before[name], after[name], name)
        # Only the one changed field was sent.
        self.assertEqual({ns.FIELDS["priority"][0]}, set(f.bodies[-1]["properties"]))


class MissingProperty(unittest.TestCase):
    def test_a_missing_mapped_property_stops_before_any_write(self):
        schema = full_schema()
        del schema[ns.FIELDS["owner"][0]]
        f = FakeNotion(schema=schema)
        f.add(piece_id="abc123")
        p = provider(f)
        with self.assertRaises(bp.SchemaDrift) as cm:
            p.update("abc123", {"priority": "Low"}, "any-version")
        self.assertIn('"Owner" is missing', str(cm.exception))
        self.assertIn("rich_text", str(cm.exception))
        self.assertEqual([], f.bodies)
        self.assertNotIn(("PATCH", f"/pages/{f.pages[0]['id']}"), f.calls)


class WrongType(unittest.TestCase):
    def test_a_wrong_property_type_stops_before_any_write(self):
        schema = full_schema()
        schema[ns.FIELDS["priority"][0]] = {"type": "number"}
        f = FakeNotion(schema=schema)
        f.add(piece_id="abc123")
        p = provider(f)
        with self.assertRaises(bp.SchemaDrift) as cm:
            p.update("abc123", {"priority": "Low"}, "any-version")
        text = str(cm.exception)
        self.assertIn('"Priority" is a number property', text)
        self.assertIn("a select one is needed", text)
        self.assertEqual([], f.bodies)


class Lifecycle(unittest.TestCase):
    def test_every_configured_value_round_trips(self):
        f = FakeNotion()
        p = provider(f)
        for state, option in LIFECYCLE_TABLE.items():
            f.add(piece_id=f"id-{state}", lifecycle=option)
        for state, option in LIFECYCLE_TABLE.items():
            row = p.read(f"id-{state}")
            self.assertEqual(state, row["lifecycle"])
            self.assertEqual(option, p.lifecycle.to_notion(state))

    def test_a_missing_lifecycle_entry_is_refused_at_build_not_write(self):
        incomplete = dict(LIFECYCLE_TABLE)
        del incomplete["sent"]
        with self.assertRaises(ns.LifecycleDrift) as cm:
            provider(FakeNotion(), lifecycle_table=incomplete)
        self.assertIn("sent", str(cm.exception))

    def test_two_body_states_sharing_one_option_is_refused(self):
        clashing = dict(LIFECYCLE_TABLE)
        clashing["sent"] = clashing["ready"]
        with self.assertRaises(ns.LifecycleDrift):
            provider(FakeNotion(), lifecycle_table=clashing)

    def test_writing_an_unconfigured_body_state_is_refused_not_guessed(self):
        f = FakeNotion()
        f.add(piece_id="abc123")
        p = provider(f)
        row = p.read("abc123")
        with self.assertRaises(ns.LifecycleDrift):
            p.update("abc123", {"lifecycle": "archived"}, row["version"])
        self.assertEqual([], [c for c in f.calls if c[0] == "PATCH"])


class StopConditions(unittest.TestCase):
    def test_a_stale_row_is_refused_and_left_alone(self):
        f = FakeNotion()
        f.add(piece_id="abc123", priority="High")
        p = provider(f)
        row = p.read("abc123")
        f.edit_elsewhere(f.pages[0])
        with self.assertRaises(bp.BoardConflict):
            p.update("abc123", {"priority": "Low"}, row["version"])
        self.assertEqual("High", p.read("abc123")["priority"])

    def test_a_missing_piece_id_is_refused(self):
        f = FakeNotion()
        p = provider(f)
        with self.assertRaises(bp.BoardError):
            p.update("", {"priority": "Low"}, "v")

    def test_a_duplicate_piece_id_is_refused(self):
        f = FakeNotion()
        f.add(piece_id="dupe")
        f.add(piece_id="dupe")
        p = provider(f)
        with self.assertRaises(ns.DuplicatePieceId):
            p.read("dupe")

    def test_an_undeclared_field_is_refused_before_any_call(self):
        f = FakeNotion()
        p = provider(f)
        with self.assertRaises(bp.UndeclaredField):
            p.update("abc123", {"draft_text": "x"}, "v")
        self.assertEqual([], f.calls)

    def test_no_property_is_ever_created_renamed_or_deleted(self):
        f = FakeNotion()
        f.add(piece_id="abc123")
        p = provider(f)
        row = p.read("abc123")
        p.update("abc123", {"priority": "Low"}, row["version"])
        blob = json.dumps(f.bodies)
        for word in ("archived", "in_trash", "trash", "delete"):
            self.assertNotIn(word, blob)


class NoOp(unittest.TestCase):
    def test_a_repeated_identical_update_makes_no_write(self):
        f = FakeNotion()
        f.add(piece_id="abc123")
        p = provider(f)
        self.assertEqual("updated", ns.push(p, "abc123", {"priority": "High"}))
        n_calls_after_first = len(f.calls)
        self.assertEqual("unchanged", ns.push(p, "abc123", {"priority": "High"}))
        # A read happens (to compare), but no PATCH.
        self.assertNotIn(("PATCH", f"/pages/{f.pages[0]['id']}"),
                         f.calls[n_calls_after_first:])


class Build(unittest.TestCase):
    def house(self, text):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        (Path(tmp.name) / bp.SETTINGS_FILE).write_text(text, encoding="utf-8")
        return tmp.name

    def test_a_complete_house_gives_the_schema_provider(self):
        lines = "\n".join(f"- Lifecycle {s}: {o}" for s, o in LIFECYCLE_TABLE.items())
        text = f"- Provider: notion\n- Notion database: {DB}\n{lines}\n"
        p = ns.build(self.house(text), env={nb.TOKEN_ENV: TOKEN}, transport=FakeNotion())
        self.assertIsInstance(p, ns.SchemaProvider)
        self.assertEqual("thinking", p.lifecycle.to_body_state(LIFECYCLE_TABLE["thinking"]))

    def test_missing_lifecycle_lines_are_refused_with_what_is_missing(self):
        text = f"- Provider: notion\n- Notion database: {DB}\n"
        with self.assertRaises(ns.LifecycleDrift):
            ns.build(self.house(text), env={nb.TOKEN_ENV: TOKEN}, transport=FakeNotion())

    def test_a_renamed_field_is_used(self):
        lines = "\n".join(f"- Lifecycle {s}: {o}" for s, o in LIFECYCLE_TABLE.items())
        text = f"- Provider: notion\n- Notion database: {DB}\n{lines}\n- Field owner: Assignee\n"
        p = ns.build(self.house(text), env={nb.TOKEN_ENV: TOKEN}, transport=FakeNotion())
        self.assertEqual("Assignee", p.names["owner"])


if __name__ == "__main__":
    unittest.main()
