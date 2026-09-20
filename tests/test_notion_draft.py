"""A draft copied to a Notion page and back, against a fake Notion.

Every piece and page is synthetic. Nothing here reaches Notion or reads a real
house. A green run says the engine is consistent with Notion's documented block
calls. It does not say a real workspace accepts them; that needs the writer's
token and one run of their own.

The rules under test:
  - a push or a pull goes ahead only when exactly one side changed since the
    last time they agreed; when both did, nothing changes and nothing is merged
  - before draft.md is replaced its text is kept, and before a page is replaced
    its text is kept
  - a block that did not change is not touched, so its comments stay
  - front matter stays in draft.md, and a sent piece's draft is never written
  - content with no form on the other side is refused and named
  - an interrupted push is not mistaken for edits, and cannot be pulled
"""
import copy
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import board_edit as be  # noqa: E402
import board_provider as bp  # noqa: E402
import notion_blocks as blocks  # noqa: E402
import notion_board as nb  # noqa: E402
import notion_draft as nd  # noqa: E402
import test_notion_board as tn  # noqa: E402

DRAFT = """---
title: Gamma
subtitle: A subtitle
---

Opening paragraph.

## A heading

- one
- two

Closing line.
"""


class FakePages(tn.FakeNotion):
    """FakeNotion, plus the block calls under a page."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.kids, self.blocks, self.trash, self.n = {}, {}, [], 0
        self.mutations, self.fail_after, self.page_size = [], None, 2

    # -- building read-shaped blocks from create-shaped ones --------------------

    @staticmethod
    def _read_rich(els):
        out = []
        for e in els or []:
            c = e["text"]["content"]
            out.append({"type": "text", "plain_text": c, "text": {"content": c, "link": e["text"].get("link")},
                        "annotations": {"bold": False, "italic": False, "strikethrough": False, "underline": False,
                                        "code": False, "color": "default", **e.get("annotations", {})},
                        "href": (e["text"].get("link") or {}).get("url")})
        return out

    def _make(self, spec, parent, depth=0):
        assert depth <= 2, "Notion takes two levels of nesting in one request"
        t = spec["type"]
        body = copy.deepcopy(spec[t])
        kids = body.pop("children", [])
        for k in ("rich_text", "caption"):
            if k in body:
                assert all(len(e["text"]["content"]) <= 2000 for e in body[k]), "rich text over 2,000 characters"
                body[k] = self._read_rich(body[k])
        if t == "table_row":
            body["cells"] = [self._read_rich(c) for c in body["cells"]]
        self.n += 1
        bid = f"blk-{self.n}"
        self.blocks[bid] = {"object": "block", "id": bid, "type": t, "has_children": bool(kids), t: body}
        self.kids[bid] = []
        self.kids.setdefault(parent, []).append(bid)
        for k in kids:
            self._make(k, bid, depth + 1)
        return bid

    def seed(self, page_id, md):
        for spec in blocks.md_to_blocks(md):
            self._make(spec, page_id)

    def body(self, page_id="page-1"):
        def one(bid):
            b = copy.deepcopy(self.blocks[bid])
            if b["has_children"]:
                b["children"] = [one(k) for k in self.kids[bid]]
            return b
        return [one(b) for b in self.kids.get(page_id, [])]

    def md(self, page_id="page-1"):
        return blocks.blocks_to_md(self.body(page_id))

    # -- edits a person makes in Notion ------------------------------------------

    def edit_text(self, bid, text):
        t = self.blocks[bid]["type"]
        self.blocks[bid][t]["rich_text"] = self._read_rich([{"text": {"content": text}}])

    def add_after(self, page_id, after, spec):
        bid = self._make(spec, page_id)
        lst = self.kids[page_id]
        lst.remove(bid)
        lst.insert(0 if after is None else lst.index(after) + 1, bid)
        return bid

    def ids(self, page_id="page-1"):
        return list(self.kids.get(page_id, []))

    # -- the calls ----------------------------------------------------------------

    def mutating(self, method):
        return method in ("PATCH", "DELETE")

    def __call__(self, method, url, headers, body):
        path = url[len(nb.API):]
        if not path.startswith("/blocks/"):
            return super().__call__(method, url, headers, body)
        self.calls.append((method, path))
        data = json.loads(body) if body else None
        if self.mutating(method):
            if self.fail_after is not None:
                if self.fail_after <= 0:
                    return 503, {}, {"code": "service_unavailable"}
                self.fail_after -= 1
            self.mutations.append((method, path, data))
        rest = path[len("/blocks/"):]
        if method == "GET":
            bid, _, q = rest.partition("/children")
            start = 0
            if "start_cursor=" in q:
                start = int(q.split("start_cursor=")[1].split("&")[0])
            ids = self.kids.get(bid, [])
            chunk = ids[start:start + self.page_size]
            more = start + self.page_size < len(ids)
            out = []
            for i in chunk:
                b = copy.deepcopy(self.blocks[i])
                out.append(b)
            return 200, {}, {"results": out, "has_more": more,
                             "next_cursor": str(start + self.page_size) if more else None}
        if method == "PATCH" and rest.endswith("/children"):
            parent = rest[:-len("/children")]
            assert len(data["children"]) <= 100, "more than 100 children in one request"
            made = [self._make(c, parent) for c in data["children"]]
            lst = self.kids[parent]
            for m in made:
                lst.remove(m)
            pos = data["position"]
            at = 0 if pos["type"] == "start" else lst.index(pos["after_block"]["id"]) + 1
            lst[at:at] = made
            return 200, {}, {"results": [self.blocks[m] for m in made], "has_more": False}
        if method == "PATCH":
            t, payload = next(iter(data.items()))
            assert self.blocks[rest]["type"] == t, "a block's type cannot be changed"
            body = self.blocks[rest][t]
            for k, v in payload.items():
                body[k] = self._read_rich(v) if k in ("rich_text", "caption") else v
            return 200, {}, self.blocks[rest]
        if method == "DELETE":
            for lst in self.kids.values():
                if rest in lst:
                    lst.remove(rest)
            self.trash.append(rest)
            return 200, {}, {"id": rest, "in_trash": True}
        raise AssertionError(f"unexpected call {method} {path}")


class Base(unittest.TestCase):
    house_text = "- Draft copy: on\n"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "pieces"
        self.folder = self.root / "2026-02-01-gamma"
        self.folder.mkdir(parents=True)
        self.draft = self.folder / "draft.md"
        self.draft.write_text(DRAFT, encoding="utf-8")
        self.house = Path(self.tmp.name) / "house"
        self.house.mkdir()
        (self.house / bp.SETTINGS_FILE).write_text(self.house_text, encoding="utf-8")
        self.fake = FakePages()
        self.prov, self.clock = tn.provider(self.fake)

    def push(self, **kw):
        return nd.push([self.root], "gamma", knowledge=self.house, provider=self.prov, **kw)

    def pull(self, **kw):
        return nd.pull([self.root], "gamma", knowledge=self.house, provider=self.prov, **kw)

    def synced(self):
        status, msg = self.push()
        self.assertEqual("pushed", status, msg)
        self.fake.mutations.clear()
        return self.fake.ids()

    def files(self):
        return {str(p.relative_to(self.folder)) for p in self.folder.rglob("*") if p.is_file()}


class Push(Base):
    def test_a_first_push_adds_the_row_and_copies_the_body_and_not_the_front_matter(self):
        status, msg = self.push()
        self.assertEqual("pushed", status, msg)
        self.assertEqual(blocks.canon(nd.split_draft(DRAFT)[1]), self.fake.md())
        sent = json.dumps(self.fake.bodies)
        for leak in ("subtitle", "A subtitle", "title: Gamma"):
            self.assertNotIn(leak, sent)
        self.assertEqual({"draft.md", ".piece-id", ".notion-sync.json"}, self.files())
        self.assertEqual(DRAFT, self.draft.read_text(), "a push never writes draft.md")

    def test_pushing_again_with_nothing_changed_touches_nothing(self):
        self.synced()
        status, msg = self.push()
        self.assertEqual("unchanged", status)
        self.assertEqual([], self.fake.mutations)

    def test_a_small_edit_updates_that_block_in_place_and_leaves_the_rest(self):
        ids = self.synced()
        self.draft.write_text(DRAFT.replace("Opening paragraph.", "A better opening."), encoding="utf-8")
        status, msg = self.push()
        self.assertEqual("pushed", status, msg)
        self.assertEqual(ids, self.fake.ids(), "no block was replaced, so its comments stay")
        self.assertEqual([("PATCH", f"/blocks/{ids[0]}")], [(m, p) for m, p, _ in self.fake.mutations])
        self.assertIn("1 updated", msg)
        self.assertEqual(self.fake.md(), blocks.canon(nd.split_draft(self.draft.read_text())[1]))

    def test_an_added_paragraph_goes_in_after_the_one_before_it(self):
        ids = self.synced()
        self.draft.write_text(DRAFT.replace("Closing line.", "Middle line.\n\nClosing line."), encoding="utf-8")
        self.assertEqual("pushed", self.push()[0])
        self.assertEqual(ids[:3], self.fake.ids()[:3])
        self.assertEqual("Middle line.\n\nClosing line.", self.fake.md().split("\n\n")[-2] + "\n\n" + self.fake.md().split("\n\n")[-1])
        pos = [d["position"] for m, p, d in self.fake.mutations if p.endswith("/children")]
        self.assertEqual("after_block", pos[0]["type"])

    def test_a_removed_paragraph_goes_to_the_trash_and_the_rest_stays(self):
        ids = self.synced()
        self.draft.write_text(DRAFT.replace("Opening paragraph.\n\n", ""), encoding="utf-8")
        self.assertEqual("pushed", self.push()[0])
        self.assertEqual([ids[0]], self.fake.trash)
        self.assertEqual(ids[1:], self.fake.ids())

    def test_edits_in_notion_that_were_never_pulled_stop_a_push_and_change_nothing(self):
        ids = self.synced()
        self.fake.edit_text(ids[0], "Edited in Notion.")
        self.draft.write_text(DRAFT.replace("Closing line.", "Changed here."), encoding="utf-8")
        status, msg = self.push()
        self.assertEqual("failed", status)
        self.assertIn("never pulled", msg)
        self.assertIn("familiar pull", msg)
        self.assertEqual([], self.fake.mutations)
        self.assertIn("Edited in Notion.", self.fake.md())

    def test_force_replaces_the_page_and_keeps_its_text_first(self):
        ids = self.synced()
        self.fake.edit_text(ids[0], "Edited in Notion.")
        self.draft.write_text(DRAFT.replace("Closing line.", "Changed here."), encoding="utf-8")
        status, msg = self.push(force=True)
        self.assertEqual("pushed", status, msg)
        kept = list((self.folder / ".versions").glob("notion-*.md"))
        self.assertEqual(1, len(kept))
        self.assertIn("Edited in Notion.", kept[0].read_text())
        self.assertIn("Changed here.", self.fake.md())
        self.assertNotIn("Edited in Notion.", self.fake.md())

    def test_a_page_with_content_familiar_did_not_put_there_is_left_alone(self):
        status, msg = tn_first_row_then(self)
        self.assertEqual("failed", status)
        self.assertIn("did not put there", msg)
        self.assertEqual([], self.fake.mutations)

    def test_check_says_what_it_would_do_and_changes_nothing(self):
        self.synced()
        self.draft.write_text(DRAFT.replace("Opening paragraph.", "A better opening."), encoding="utf-8")
        before = self.files()
        status, msg = self.push(check=True)
        self.assertEqual("check", status)
        self.assertIn("1 updated", msg)
        self.assertEqual([], self.fake.mutations)
        self.assertEqual(before, self.files())

    def test_a_first_check_writes_no_file_and_makes_no_row(self):
        status, msg = self.push(check=True)
        self.assertEqual("check", status)
        self.assertEqual({"draft.md"}, self.files())
        self.assertEqual([], self.fake.pages)

    def test_a_construct_with_no_notion_form_is_refused_and_nothing_is_sent(self):
        self.draft.write_text(DRAFT + "\n#### Too deep\n", encoding="utf-8")
        status, msg = self.push()
        self.assertEqual("failed", status)
        self.assertIn("level 4 heading", msg)
        self.assertEqual([], self.fake.pages)

    def test_a_block_on_the_page_that_the_draft_has_no_form_for_stops_a_push(self):
        ids = self.synced()
        self.fake.add_after("page-1", ids[-1], {"type": "callout", "callout": {"rich_text": []}})
        status, msg = self.push()
        self.assertEqual("failed", status)
        self.assertIn("callout", msg)
        self.assertEqual([], self.fake.mutations)

    def test_a_draft_over_100_blocks_goes_in_chunks_and_a_long_paragraph_is_split(self):
        big = "\n\n".join(f"Paragraph {i}." for i in range(230)) + "\n\n" + ("x" * 4500)
        self.draft.write_text(big, encoding="utf-8")
        status, msg = self.push()
        self.assertEqual("pushed", status, msg)
        chunks = [len(d["children"]) for m, p, d in self.fake.bodies_children()]
        self.assertTrue(all(c <= 100 for c in chunks), chunks)
        self.assertEqual(blocks.canon(big), self.fake.md())

    def test_the_copy_is_off_unless_the_house_says_on(self):
        (self.house / bp.SETTINGS_FILE).write_text("- Draft copy: off\n", encoding="utf-8")
        status, msg = self.push()
        self.assertEqual("skipped", status)
        self.assertIn("Draft copy is off", msg)
        self.assertEqual([], self.fake.pages)

    def test_a_house_with_no_notion_provider_is_told_so(self):
        status, msg = nd.push([self.root], "gamma", knowledge=self.house)
        self.assertEqual("skipped", status)
        self.assertIn("needs a Notion board provider", msg)

    def test_no_piece_and_many_pieces_are_lines(self):
        status, msg = nd.push([self.root], "zzz", knowledge=self.house, provider=self.prov)
        self.assertEqual("failed", status)
        self.assertIn("No piece matches", msg)

    def test_a_sent_piece_can_still_be_copied_as_a_record(self):
        (self.folder / "final.md").write_text("Sent.\n", encoding="utf-8")
        status, msg = self.push()
        self.assertEqual("pushed", status, msg)


def tn_first_row_then(t):
    """A page that already has a body, and no sync state."""
    t.prov.create(bp.BoardItem(id="preset", title="x", state="writing"))
    # Make the piece's row the one that already has content.
    ident = bp.ensure_piece_id(t.folder)
    t.fake.pages[0]["properties"]["Piece ID"] = {"rich_text": [{"plain_text": ident}]}
    t.fake.seed("page-1", "Someone else's text.")
    return t.push()


def bodies_children(self):
    return [(m, p, d) for m, p, d in self.mutations if p.endswith("/children")]


FakePages.bodies_children = bodies_children


class Pull(Base):
    def test_a_pull_needs_a_push_first(self):
        status, msg = self.pull()
        self.assertEqual("failed", status)
        self.assertIn("Nothing has been pushed", msg)

    def test_an_edit_in_notion_replaces_the_body_and_keeps_the_front_matter_and_the_old_draft(self):
        ids = self.synced()
        self.fake.edit_text(ids[0], "Rewritten in Notion.")
        status, msg = self.pull()
        self.assertEqual("pulled", status, msg)
        text = self.draft.read_text()
        self.assertTrue(text.startswith("---\ntitle: Gamma\nsubtitle: A subtitle\n---\n\nRewritten in Notion."))
        self.assertTrue(text.endswith("Closing line.\n"))
        kept = list((self.folder / ".versions").glob("draft-*.md"))
        self.assertEqual(1, len(kept))
        self.assertEqual(DRAFT, kept[0].read_text())
        self.assertEqual("unchanged", self.pull()[0], "the next pull has nothing to bring")

    def test_after_a_pull_the_next_push_has_nothing_to_send(self):
        ids = self.synced()
        self.fake.edit_text(ids[0], "Rewritten in Notion.")
        self.pull()
        self.assertEqual("unchanged", self.push()[0])
        self.assertEqual([], self.fake.mutations)

    def test_only_local_edits_means_nothing_to_pull(self):
        self.synced()
        self.draft.write_text(DRAFT.replace("Closing line.", "Changed here."), encoding="utf-8")
        status, msg = self.pull()
        self.assertEqual("unchanged", status)
        self.assertIn("only draft.md changed", msg)

    def test_edits_on_both_sides_stop_and_change_nothing(self):
        ids = self.synced()
        self.fake.edit_text(ids[0], "Edited in Notion.")
        edited = DRAFT.replace("Closing line.", "Changed here.")
        self.draft.write_text(edited, encoding="utf-8")
        status, msg = self.pull()
        self.assertEqual("failed", status)
        self.assertIn("Both draft.md and the Notion page changed", msg)
        self.assertIn("--force", msg)
        self.assertEqual(edited, self.draft.read_text())
        self.assertFalse((self.folder / ".versions").exists())

    def test_force_takes_the_page_and_keeps_the_draft_first(self):
        ids = self.synced()
        self.fake.edit_text(ids[0], "Edited in Notion.")
        edited = DRAFT.replace("Closing line.", "Changed here.")
        self.draft.write_text(edited, encoding="utf-8")
        status, msg = self.pull(force=True)
        self.assertEqual("pulled", status, msg)
        self.assertIn("Edited in Notion.", self.draft.read_text())
        self.assertNotIn("Changed here.", self.draft.read_text())
        (kept,) = list((self.folder / ".versions").glob("draft-*.md"))
        self.assertEqual(edited, kept.read_text())

    def test_an_empty_page_never_replaces_a_draft(self):
        ids = self.synced()
        for i in ids:
            self.fake.kids["page-1"].remove(i)
        status, msg = self.pull()
        self.assertEqual("failed", status)
        self.assertIn("empty page does not replace a draft", msg)
        self.assertEqual(DRAFT, self.draft.read_text())

    def test_a_sent_piece_is_never_written(self):
        ids = self.synced()
        (self.folder / "final.md").write_text("Sent.\n", encoding="utf-8")
        self.fake.edit_text(ids[0], "Edited in Notion.")
        status, msg = self.pull()
        self.assertEqual("failed", status)
        self.assertIn("has been sent", msg)
        self.assertEqual(DRAFT, self.draft.read_text())

    def test_underline_and_colour_are_dropped_reported_and_the_text_kept(self):
        ids = self.synced()
        self.fake.blocks[ids[0]]["paragraph"]["rich_text"][0]["annotations"]["underline"] = True
        self.fake.edit_text(ids[-1], "Closing, edited.")
        self.fake.blocks[ids[-1]]["paragraph"]["rich_text"][0]["annotations"]["color"] = "red"
        status, msg = self.pull()
        self.assertEqual("pulled", status, msg)
        self.assertIn("colour x1", msg)
        self.assertIn("Closing, edited.", self.draft.read_text())

    def test_a_block_with_no_draft_form_stops_a_pull_and_is_named(self):
        ids = self.synced()
        self.fake.add_after("page-1", ids[0], {"type": "toggle", "toggle": {"rich_text": []}})
        status, msg = self.pull()
        self.assertEqual("failed", status)
        self.assertIn("toggle", msg)
        self.assertEqual(DRAFT, self.draft.read_text())

    def test_spacer_paragraphs_left_by_editing_are_not_an_edit(self):
        ids = self.synced()
        self.fake.add_after("page-1", ids[0], {"type": "paragraph", "paragraph": {"rich_text": []}})
        self.assertEqual("unchanged", self.pull()[0])

    def test_check_reports_and_writes_nothing(self):
        ids = self.synced()
        self.fake.edit_text(ids[0], "Rewritten in Notion.")
        before = self.files()
        status, msg = self.pull(check=True)
        self.assertEqual("check", status)
        self.assertIn("words", msg)
        self.assertEqual(DRAFT, self.draft.read_text())
        self.assertEqual(before, self.files())

    def test_a_note_above_the_front_matter_survives_a_pull(self):
        noted = "A note to self.\n\n" + DRAFT
        self.draft.write_text(noted, encoding="utf-8")
        ids = self.synced()
        self.fake.edit_text(ids[0], "Rewritten in Notion.")
        self.assertEqual("pulled", self.pull()[0])
        self.assertTrue(self.draft.read_text().startswith("A note to self.\n\n---\ntitle: Gamma"))

    def test_a_draft_with_no_front_matter_and_no_final_newline_round_trips(self):
        self.draft.write_text("Just a body.\n\nTwo paragraphs.", encoding="utf-8")
        ids = self.synced()
        self.fake.edit_text(ids[0], "Edited body.")
        self.assertEqual("pulled", self.pull()[0])
        self.assertEqual("Edited body.\n\nTwo paragraphs.", self.draft.read_text())

    def test_tables_code_quotes_and_nested_lists_survive_both_ways(self):
        rich = ("Intro.\n\n| A | B |\n| --- | --- |\n| 1 | 2 |\n\n```python\nx = 1\n```\n\n> quoted\n\n"
                "- a\n  - b\n\n1. one\n2. two\n\n---\n\nEnd.")
        self.draft.write_text("---\ntitle: T\n---\n\n" + rich + "\n", encoding="utf-8")
        ids = self.synced()
        self.fake.edit_text(ids[0], "Intro, edited.")
        self.assertEqual("pulled", self.pull()[0])
        self.assertEqual("---\ntitle: T\n---\n\n" + rich.replace("Intro.", "Intro, edited.") + "\n",
                         self.draft.read_text())

    def test_only_the_expected_files_appear(self):
        ids = self.synced()
        self.fake.edit_text(ids[0], "Rewritten in Notion.")
        self.pull()
        names = self.files()
        self.assertEqual({"draft.md", ".piece-id", ".notion-sync.json"},
                         {n for n in names if not n.startswith(".versions")})
        self.assertEqual(1, len([n for n in names if n.startswith(".versions")]))


class Interrupted(Base):
    def test_a_push_that_fails_partway_is_a_line_and_cannot_be_pulled(self):
        self.synced()
        self.draft.write_text(DRAFT.replace("Opening paragraph.", "Opening, changed.")
                              .replace("Closing line.", "Closing, changed."), encoding="utf-8")
        self.fake.fail_after = 1                      # one step goes through, then the connection fails
        status, msg = self.push()
        self.assertEqual("failed", status)
        self.assertTrue(msg)
        self.assertTrue(nd.read_state(self.folder).get("interrupted"))
        self.fake.fail_after = None
        status, msg = self.pull()
        self.assertEqual("failed", status)
        self.assertIn("did not finish", msg)

    def test_pushing_again_finishes_the_job_and_keeps_the_partial_page(self):
        self.synced()
        self.draft.write_text(DRAFT.replace("Opening paragraph.", "Opening, changed.")
                              .replace("Closing line.", "Closing, changed."), encoding="utf-8")
        self.fake.fail_after = 1
        self.push()
        self.fake.fail_after = None
        status, msg = self.push()
        self.assertEqual("pushed", status, msg)
        self.assertEqual(self.fake.md(), blocks.canon(nd.split_draft(self.draft.read_text())[1]))
        self.assertFalse(nd.read_state(self.folder).get("interrupted"))
        self.assertEqual(1, len(list((self.folder / ".versions").glob("notion-*.md"))))
        self.assertEqual("unchanged", self.push()[0])


class Wiring(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "pieces"
        (self.root / "2026-02-01-gamma").mkdir(parents=True)
        (self.root / "2026-02-01-gamma" / "draft.md").write_text(DRAFT, encoding="utf-8")
        self.house = Path(self.tmp.name) / "house"
        self.house.mkdir()
        (self.house / "positioning.md").write_text("# Positioning\n", encoding="utf-8")
        self.home = Path(self.tmp.name) / "home"
        self.home.mkdir()

    def run_cli(self, *args, house_text=None):
        import subprocess
        if house_text is not None:
            (self.house / bp.SETTINGS_FILE).write_text(house_text, encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if not k.startswith(("FAMILIAR", "NOTION"))}
        env.update(HOME=str(self.home), FAMILIAR_KNOWLEDGE=str(self.house), FAMILIAR_PIECES=str(self.root))
        return subprocess.run([sys.executable, str(ROOT / "scripts" / "familiar"), *args],
                              capture_output=True, text=True, env=env, cwd=self.tmp.name)

    def test_with_no_provider_push_and_pull_say_so_and_succeed(self):
        for cmd in ("push", "pull"):
            r = self.run_cli(cmd, "gamma")
            self.assertEqual(0, r.returncode, r.stderr)
            self.assertIn("needs a Notion board provider", r.stdout)

    def test_a_notion_house_with_no_token_says_where_it_goes(self):
        r = self.run_cli("push", "gamma", house_text=f"- Provider: notion\n- Notion database: {tn.DB}\n- Draft copy: on\n")
        self.assertEqual(1, r.returncode)
        self.assertIn(nb.TOKEN_ENV, r.stdout)

    def test_the_flags_are_offered(self):
        r = self.run_cli("push", "--help")
        self.assertIn("--check", r.stdout)
        self.assertIn("--force", r.stdout)


if __name__ == "__main__":
    unittest.main()
