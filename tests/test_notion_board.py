"""The Notion board provider, against a fake Notion.

Nothing here reaches Notion or reads a real house. A fake speaks the request
and response shapes in Notion's documentation (version 2025-09-03), so each
rule can be tested without a workspace. A green run says the adapter is
consistent with those documented shapes. It does not say a real workspace
accepts it; that needs the writer's token and one run of their own.

The rules under test:
  - only board fields are sent, and never draft text
  - properties the adapter does not map are left as they are
  - a row that changed since it was read is refused, not overwritten
  - nothing is deleted or archived
  - a board that cannot be reached, refused, drifted or paused says what
    happened and what to do, and is never reported as empty
  - requests are paced, and a 429 waits as long as Notion asks
  - the token never appears in an error
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import board_provider as bp  # noqa: E402
import notion_board as nb  # noqa: E402

DB = "a" * 32
DS = "b" * 32
TOKEN = "secret_token_value_123"


class FakeNotion:
    """The parts of Notion's API this adapter calls."""

    def __init__(self, sources=None, schema=None, per_page=2):
        self.sources = sources if sources is not None else [{"id": DS, "name": "Board"}]
        self.schema = schema if schema is not None else {
            "Name": {"type": "title"}, "State": {"type": "select"},
            "Next decision": {"type": "rich_text"}, "Last activity": {"type": "date"},
            "Blockers": {"type": "rich_text"}, "Links": {"type": "rich_text"},
            "Piece ID": {"type": "rich_text"}, "Owner": {"type": "people"}}
        self.pages, self.calls, self.bodies, self.script, self.per_page = [], [], [], [], per_page
        self.tick = 0

    def stamp(self):
        self.tick += 1
        return f"2026-09-20T10:00:{self.tick:02d}.000Z"

    def add(self, pid="", title="T", state="writing", extra=None):
        props = {"Name": {"title": [{"plain_text": title}]},
                 "State": {"select": {"name": state}},
                 "Next decision": {"rich_text": []}, "Last activity": {"date": None},
                 "Blockers": {"rich_text": []}, "Links": {"rich_text": []},
                 "Piece ID": {"rich_text": [{"plain_text": pid}] if pid else []},
                 "Owner": {"people": [{"id": "u1"}]}}
        props.update(extra or {})
        page = {"id": f"page-{len(self.pages) + 1}", "url": "https://notion.so/x",
                "properties": props, "last_edited_time": self.stamp()}
        self.pages.append(page)
        return page

    def edit_elsewhere(self, page):
        page["last_edited_time"] = self.stamp()

    @staticmethod
    def _read(value):
        out = dict(value)
        for k in ("title", "rich_text"):
            if k in out:
                out[k] = [{"plain_text": r["text"]["content"]} for r in out[k]]
        return out

    def __call__(self, method, url, headers, body):
        assert headers["Notion-Version"] == nb.VERSION
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
                want = flt["rich_text"]["equals"]
                rows = [p for p in rows
                        if "".join(r["plain_text"] for r in p["properties"]["Piece ID"]["rich_text"]) == want]
            start = int(data.get("start_cursor") or 0)
            chunk = rows[start:start + self.per_page]
            more = start + self.per_page < len(rows)
            return 200, {}, {"results": chunk, "has_more": more,
                             "next_cursor": str(start + self.per_page) if more else None}
        if method == "POST" and path == "/pages":
            assert data["parent"] == {"type": "data_source_id", "data_source_id": DS}
            page = self.add(title="", state="")
            for name, value in data["properties"].items():
                page["properties"][name] = self._read(value)
            return 200, {}, page
        if method == "PATCH" and path.startswith("/pages/"):
            page = next(p for p in self.pages if p["id"] == path.split("/")[-1])
            for name, value in data["properties"].items():
                page["properties"][name] = self._read(value)
            page["last_edited_time"] = self.stamp()
            return 200, {}, page
        raise AssertionError(f"unexpected call {method} {path}")


class Clock:
    def __init__(self):
        self.t, self.slept = 1000.0, []

    def now(self):
        return self.t

    def sleep(self, s):
        self.slept.append(s)
        self.t += s


def provider(fake, clock=None, names=None, data_source=None, **kw):
    clock = clock or Clock()
    client = nb.NotionClient(TOKEN, transport=fake, sleep=clock.sleep, clock=clock.now, rng=lambda: 0.5, **kw)
    return nb.NotionProvider(client, DB, data_source, names), clock


def item(**kw):
    return bp.BoardItem(**{"id": "abc123", "title": "A piece", "state": "writing",
                           "next_decision": "Pick a structure", "last_activity": 1_790_000_000.0, **kw})


class Reading(unittest.TestCase):
    def test_every_page_of_a_long_board_is_read(self):
        f = FakeNotion(per_page=2)
        for i in range(5):
            f.add(pid=f"id{i}", title=f"T{i}")
        rows = provider(f)[0].read_all()
        self.assertEqual(5, len(rows))
        self.assertEqual(["id0", "id1", "id2", "id3", "id4"], [r.id for r in rows])

    def test_a_row_with_no_piece_id_is_kept_and_named_by_its_page(self):
        f = FakeNotion()
        f.add(pid="", title="Made by hand")
        row = provider(f)[0].read_all()[0]
        self.assertEqual("page:page-1", row.id)
        self.assertEqual("Made by hand", row.title)

    def test_a_row_reads_back_as_board_fields(self):
        f = FakeNotion()
        p, _ = provider(f)
        p.create(item(blockers=("1 unresolved bracket", "2 comments open"), links=("a.md", "b.md")))
        row = p.read("abc123")
        self.assertEqual(("A piece", "writing", "Pick a structure"), (row.title, row.state, row.next_decision))
        self.assertEqual(("1 unresolved bracket", "2 comments open"), tuple(row.blockers))
        self.assertEqual(("a.md", "b.md"), tuple(row.links))
        self.assertAlmostEqual(1_790_000_000.0, row.last_activity, places=0)

    def test_the_count_by_state_comes_from_the_board(self):
        f = FakeNotion()
        for s in ("writing", "writing", "sent"):
            f.add(pid=s + str(len(f.pages)), state=s)
        self.assertEqual({"writing": 2, "sent": 1}, bp.counts(provider(f)[0].read_all()))


class Writing(unittest.TestCase):
    def test_long_text_is_split_at_the_limit_and_rejoined(self):
        f = FakeNotion()
        p, _ = provider(f)
        p.create(item(next_decision="x" * 5000))
        sent = f.bodies[-1]["properties"]["Next decision"]["rich_text"]
        self.assertEqual([2000, 2000, 1000], [len(r["text"]["content"]) for r in sent])
        self.assertEqual("x" * 5000, p.read("abc123").next_decision)

    def test_an_update_sends_only_the_fields_it_names(self):
        f = FakeNotion()
        p, _ = provider(f)
        row = p.create(item())
        p.update("abc123", {"state": "editing"}, row.version)
        self.assertEqual({"State"}, set(f.bodies[-1]["properties"]))

    def test_properties_the_adapter_does_not_map_are_left_as_they_are(self):
        f = FakeNotion()
        f.add(pid="abc123", extra={"Owner": {"people": [{"id": "u9"}]}})
        p, _ = provider(f)
        row = p.read("abc123")
        p.update("abc123", {"title": "Renamed"}, row.version)
        self.assertEqual([{"id": "u9"}], f.pages[0]["properties"]["Owner"]["people"])
        self.assertEqual("Renamed", p.read("abc123").title)

    def test_a_field_that_is_not_a_board_field_is_refused_before_any_call(self):
        f = FakeNotion()
        p, _ = provider(f)
        with self.assertRaises(bp.UndeclaredField):
            p.update("abc123", {"draft_text": "x"}, "v")
        self.assertEqual([], f.calls)

    def test_a_row_that_changed_after_it_was_read_is_refused_and_left_alone(self):
        f = FakeNotion()
        f.add(pid="abc123", title="Original")
        p, _ = provider(f)
        row = p.read("abc123")
        f.edit_elsewhere(f.pages[0])
        with self.assertRaises(bp.BoardConflict) as cm:
            p.update("abc123", {"title": "Mine"}, row.version)
        self.assertTrue(cm.exception.next_step)
        self.assertEqual("Original", p.read("abc123").title)

    def test_two_rows_with_one_piece_id_stop_for_the_writer(self):
        f = FakeNotion()
        f.add(pid="abc123")
        f.add(pid="abc123")
        with self.assertRaises(bp.BoardConflict):
            provider(f)[0].read("abc123")

    def test_creating_a_row_that_exists_is_refused(self):
        f = FakeNotion()
        f.add(pid="abc123")
        with self.assertRaises(bp.BoardConflict):
            provider(f)[0].create(item())

    def test_nothing_is_ever_deleted_or_archived(self):
        f = FakeNotion()
        p, _ = provider(f)
        row = p.create(item())
        p.update("abc123", {"state": "sent", "blockers": ()}, row.version)
        self.assertEqual({"GET", "POST", "PATCH"}, {m for m, _ in f.calls})
        text = json.dumps(f.bodies)
        for word in ("archived", "in_trash", "trash", "delete"):
            self.assertNotIn(word, text)

    def test_renamed_properties_are_used(self):
        schema = {"Title": {"type": "title"}, "Stage": {"type": "select"},
                  "Next decision": {"type": "rich_text"}, "Last activity": {"type": "date"},
                  "Blockers": {"type": "rich_text"}, "Links": {"type": "rich_text"},
                  "Piece ID": {"type": "rich_text"}}
        f = FakeNotion(schema=schema)
        p, _ = provider(f, names={"title": "Title", "state": "Stage"})
        p.create(item())
        self.assertIn("Stage", f.bodies[-1]["properties"])
        self.assertNotIn("State", f.bodies[-1]["properties"])


class Push(unittest.TestCase):
    def test_a_new_piece_is_created_a_changed_one_updated_and_a_same_one_left(self):
        f = FakeNotion()
        p, _ = provider(f)
        self.assertEqual("created", bp.push(p, item()))
        self.assertEqual("unchanged", bp.push(p, item()))
        self.assertEqual("updated", bp.push(p, item(state="editing")))
        self.assertEqual("editing", p.read("abc123").state)

    def test_a_conflict_during_a_push_is_raised_and_the_row_kept(self):
        f = FakeNotion()
        p, _ = provider(f)
        bp.push(p, item())
        real = p.update

        def racing(item_id, changes, version):
            f.edit_elsewhere(f.pages[0])
            return real(item_id, changes, version)
        p.update = racing
        with self.assertRaises(bp.BoardConflict):
            bp.push(p, item(state="editing"))
        self.assertEqual("writing", p.read("abc123").state)


class DraftText(unittest.TestCase):
    def test_no_draft_text_reaches_notion(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "pieces" / "2026-01-03-gamma"
            d.mkdir(parents=True)
            (d / "draft.md").write_text(
                "---\ntitle: Gamma\n---\nAn opening line.\n\nThe private detail is 4471. "
                "[NEEDS SOURCE: the private detail]\n", encoding="utf-8")
            bp.ensure_piece_id(d)
            f = FakeNotion()
            p, _ = provider(f)
            for it in bp.LocalProvider([d.parent]).read_all():
                bp.push(p, it)
        blob = json.dumps(f.bodies)
        self.assertIn("Gamma", blob)
        for leak in ("4471", "private detail", "opening line"):
            self.assertNotIn(leak, blob)


class Failing(unittest.TestCase):
    def raises(self, script, cls, fragment=""):
        f = FakeNotion()
        f.script = script
        with self.assertRaises(cls) as cm:
            provider(f)[0].read_all()
        self.assertTrue(cm.exception.next_step, "it must say what to do")
        self.assertNotIn(TOKEN, str(cm.exception))
        self.assertIn(fragment, str(cm.exception))
        return cm.exception

    def test_a_refused_token(self):
        self.raises([(401, {}, {"code": "unauthorized"})], bp.BoardUnavailable, "token")

    def test_no_permission(self):
        self.raises([(403, {}, {"code": "restricted_resource"})], bp.BoardUnavailable, "permission")

    def test_a_board_that_is_not_shared_with_the_integration(self):
        self.raises([(404, {}, {"code": "object_not_found"})], bp.BoardUnavailable, "cannot see")

    def test_an_unreachable_notion_is_not_an_empty_board(self):
        e = self.raises([bp.BoardUnavailable("Notion could not be reached.", "Check the connection.")],
                        bp.BoardUnavailable, "could not be reached")
        self.assertIsInstance(e, bp.BoardUnavailable)

    def test_an_unknown_refusal_names_the_code(self):
        self.raises([(400, {}, {"code": "validation_error"})], bp.BoardError, "validation_error")

    def test_a_missing_property_is_named_with_the_fix(self):
        schema = {"Name": {"type": "title"}, "State": {"type": "status"}}
        f = FakeNotion(schema=schema)
        with self.assertRaises(bp.SchemaDrift) as cm:
            provider(f)[0].read_all()
        text = str(cm.exception)
        self.assertIn('"State" is a status property', text)
        self.assertIn('"Piece ID" is missing', text)
        self.assertIn("board-provider.md", cm.exception.next_step)

    def test_nothing_is_written_when_the_schema_has_drifted(self):
        f = FakeNotion(schema={"Name": {"type": "title"}})
        with self.assertRaises(bp.SchemaDrift):
            provider(f)[0].create(item())
        self.assertNotIn(("POST", "/pages"), f.calls)


class DataSources(unittest.TestCase):
    def test_two_data_sources_and_no_choice_stops_and_names_them(self):
        f = FakeNotion(sources=[{"id": DS, "name": "Board"}, {"id": "c" * 32, "name": "Archive"}])
        with self.assertRaises(bp.BoardError) as cm:
            provider(f)[0].read_all()
        self.assertIn("2 data sources", str(cm.exception))
        self.assertIn("Archive", str(cm.exception))

    def test_a_named_data_source_is_used(self):
        f = FakeNotion(sources=[{"id": DS, "name": "Board"}, {"id": "c" * 32, "name": "Archive"}])
        f.add(pid="x1")
        self.assertEqual(1, len(provider(f, data_source=DS)[0].read_all()))

    def test_a_data_source_that_is_not_in_the_database_is_refused(self):
        f = FakeNotion()
        with self.assertRaises(bp.BoardError):
            provider(f, data_source="d" * 32)[0].read_all()


class Pacing(unittest.TestCase):
    def test_requests_are_spaced_to_three_a_second(self):
        f = FakeNotion()
        p, clock = provider(f)
        p.read_all()
        self.assertTrue(clock.slept)
        self.assertTrue(all(abs(s - 1 / 3) < 0.01 for s in clock.slept))

    def test_a_429_waits_as_long_as_notion_asks_then_succeeds(self):
        f = FakeNotion()
        f.script = [(429, {"Retry-After": "7"}, {"code": "rate_limited"})]
        p, clock = provider(f)
        p.read_all()
        self.assertIn(7.0, clock.slept)

    def test_a_429_that_never_stops_is_reported_as_a_pause_not_an_empty_board(self):
        f = FakeNotion()
        f.script = [(429, {"Retry-After": "1"}, {})] * 10
        p, _ = provider(f, max_attempts=3)
        with self.assertRaises(bp.RateLimited) as cm:
            p.read_all()
        self.assertTrue(cm.exception.next_step)

    def test_a_server_error_backs_off_and_recovers(self):
        f = FakeNotion()
        f.script = [(502, {}, {}), (503, {}, {})]
        p, clock = provider(f)
        p.read_all()
        self.assertGreaterEqual(len(clock.slept), 2)


class Settings(unittest.TestCase):
    def house(self, text):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        (Path(tmp.name) / bp.SETTINGS_FILE).write_text(text, encoding="utf-8")
        return tmp.name

    def test_a_database_url_or_id_gives_its_32_character_id(self):
        for value in (DB, "-".join([DB[:8], DB[8:12], DB[12:16], DB[16:20], DB[20:]]),
                      f"https://www.notion.so/workspace/Board-{DB}?v=abc"):
            self.assertEqual(DB, nb.database_id(value), value)
        self.assertIsNone(nb.database_id("[database ID or URL]"))

    def test_notion_with_no_database_says_what_to_add(self):
        with self.assertRaises(bp.BoardError) as cm:
            bp.resolve_provider([], self.house("- Provider: notion\n"), env={TOKEN and nb.TOKEN_ENV: TOKEN})
        self.assertIn("Notion database", cm.exception.next_step)

    def test_notion_with_no_token_says_where_it_goes(self):
        with self.assertRaises(bp.BoardError) as cm:
            bp.resolve_provider([], self.house(f"- Provider: notion\n- Notion database: {DB}\n"), env={})
        self.assertIn(nb.TOKEN_ENV, cm.exception.next_step)

    def test_a_complete_house_gives_the_notion_provider(self):
        text = (f"- Provider: notion\n- Notion database: {DB}\n- Notion data source: [only when more than one]\n"
                "- Property state: Stage\n")
        p = bp.resolve_provider([], self.house(text), env={nb.TOKEN_ENV: TOKEN}, transport=FakeNotion())
        self.assertIsInstance(p, nb.NotionProvider)
        self.assertEqual("Stage", p.names["state"])
        self.assertEqual("Name", p.names["title"])

    def test_the_shipped_template_selects_nothing_and_holds_no_token(self):
        template = (ROOT / "knowledge" / bp.SETTINGS_FILE).read_text()
        self.assertIsNone(bp.read_setting(ROOT / "knowledge"))
        self.assertNotIn("secret", template.lower().replace("no secret", ""))
        self.assertNotRegex(template, r"[0-9a-f]{32}")


class PieceId(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name) / "2026-01-01-alpha"
        self.folder.mkdir()
        (self.folder / "notes.md").write_text("# Alpha\n", encoding="utf-8")

    def test_an_id_is_made_once_and_never_rewritten(self):
        first = bp.ensure_piece_id(self.folder)
        self.assertEqual(12, len(first))
        self.assertEqual(first, bp.ensure_piece_id(self.folder))
        (self.folder / bp.ID_FILE).write_text("chosen\n", encoding="utf-8")
        self.assertEqual("chosen", bp.ensure_piece_id(self.folder))

    def test_it_adds_one_file_and_touches_nothing_else(self):
        before = (self.folder / "notes.md").read_text()
        bp.ensure_piece_id(self.folder)
        self.assertEqual(before, (self.folder / "notes.md").read_text())
        self.assertEqual({"notes.md", bp.ID_FILE}, {p.name for p in self.folder.iterdir()})

    def test_the_id_survives_a_renamed_folder(self):
        pid = bp.ensure_piece_id(self.folder)
        renamed = self.folder.parent / "2026-01-01-alpha-renamed"
        self.folder.rename(renamed)
        (item_,) = bp.LocalProvider([renamed.parent]).read_all()
        self.assertEqual(pid, item_.id)

    def test_a_copied_folder_is_found_as_a_duplicate(self):
        import shutil
        bp.ensure_piece_id(self.folder)
        shutil.copytree(self.folder, self.folder.parent / "2026-01-02-copy")
        dupes = bp.duplicate_ids(bp.LocalProvider([self.folder.parent]).read_all())
        self.assertEqual(1, len(dupes))
        self.assertEqual(2, len(next(iter(dupes.values()))))

    def test_a_piece_with_no_id_file_falls_back_to_its_folder_name(self):
        (item_,) = bp.LocalProvider([self.folder.parent]).read_all()
        self.assertEqual("2026-01-01-alpha", item_.id)


if __name__ == "__main__":
    unittest.main()
