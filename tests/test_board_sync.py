"""`familiar board` and `familiar next`, and the sync after a stage exit.

Fixtures are synthetic and built in temporary folders, and Notion is a fake.
Nothing here reads a real house or writes a real piece.

The rules under test:
  - a sync never raises and never blocks: a failure is one line saying what
    happened and what to do
  - a piece gets its ID file at its first sync, once, and no other file changes
  - a copied folder is found before anything is sent
  - `next` names where a piece is and starts nothing
  - with no provider set, the built-in board is unchanged and sync does nothing
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import board_provider as bp  # noqa: E402
import board_sync as bs  # noqa: E402
import notion_board as nb  # noqa: E402
import test_notion_board as tn  # noqa: E402

FAMILIAR = ROOT / "scripts" / "familiar"


def pieces(base, spec=None):
    root = Path(base) / "pieces"
    spec = spec or {"2026-01-01-alpha": {"notes.md": "# Alpha\n\n## Working thesis\n\nA thesis.\n"},
                    "2026-01-02-beta": {"outline.md": "# Beta\n\n## A\n"}}
    for name, files in spec.items():
        d = root / name
        d.mkdir(parents=True, exist_ok=True)
        for f, text in files.items():
            (d / f).write_text(text, encoding="utf-8")
    return root


def tree(root):
    return sorted((str(p.relative_to(root)), p.read_text() if p.is_file() else "")
                  for p in Path(root).rglob("*"))


class Sync(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pieces(self.tmp.name)
        self.fake = tn.FakeNotion()
        self.prov, _ = tn.provider(self.fake)

    def sync(self, query, provider=None):
        return bs.sync_piece([self.root], query, provider=provider or self.prov)

    def test_with_no_provider_there_is_nothing_to_do_and_no_file_is_made(self):
        house = Path(self.tmp.name) / "house"
        house.mkdir()
        before = tree(self.root)
        status, msg = bs.sync_piece([self.root], "alpha", knowledge=house)
        self.assertEqual("skipped", status)
        self.assertEqual(before, tree(self.root))

    def test_a_new_piece_is_created_and_gets_its_id_file_and_nothing_else_changes(self):
        before = dict(tree(self.root))
        status, msg = self.sync("alpha")
        self.assertEqual("created", status)
        self.assertIn("created on the notion board", msg)
        after = dict(tree(self.root))
        added = set(after) - set(before)
        self.assertEqual({str(Path("2026-01-01-alpha") / bp.ID_FILE)}, added)
        for k, v in before.items():
            self.assertEqual(v, after[k], k)

    def test_syncing_again_changes_nothing_and_a_new_stage_updates_the_row(self):
        self.assertEqual("created", self.sync("alpha")[0])
        self.assertEqual("unchanged", self.sync("alpha")[0])
        (self.root / "2026-01-01-alpha" / "outline.md").write_text("# Alpha\n\n## A\n", encoding="utf-8")
        self.assertEqual("updated", self.sync("alpha")[0])
        (row,) = self.prov.read_all()
        self.assertEqual("writing", row.state)

    def test_the_row_keeps_matching_after_the_folder_is_renamed(self):
        self.sync("alpha")
        old = self.root / "2026-01-01-alpha"
        old.rename(self.root / "2026-01-01-alpha-renamed")
        self.assertEqual("unchanged", self.sync("alpha-renamed")[0])
        self.assertEqual(1, len(self.prov.read_all()))

    def test_no_piece_and_more_than_one_piece_are_lines_not_crashes(self):
        status, msg = self.sync("nothing-like-this")
        self.assertEqual("failed", status)
        self.assertIn("No piece matches", msg)
        status, msg = self.sync("2026-01")
        self.assertEqual("failed", status)
        self.assertIn("matches 2 pieces", msg)
        self.assertEqual([], self.fake.pages)

    def test_a_copied_folder_is_found_before_anything_is_sent(self):
        import shutil
        self.sync("alpha")
        shutil.copytree(self.root / "2026-01-01-alpha", self.root / "2026-01-05-alpha-copy")
        sent = len(self.fake.bodies)
        status, msg = self.sync("alpha-copy")
        self.assertEqual("failed", status)
        self.assertIn("carry the ID", msg)
        self.assertIn(".piece-id", msg)
        self.assertEqual(sent, len(self.fake.bodies))

    def test_a_refused_token_is_a_line_with_what_to_do(self):
        f = tn.FakeNotion()
        f.script = [(401, {}, {"code": "unauthorized"})]
        prov, _ = tn.provider(f)
        status, msg = self.sync("alpha", provider=prov)
        self.assertEqual("failed", status)
        self.assertIn("token", msg)
        self.assertNotIn(tn.TOKEN, msg)

    def test_a_setting_that_cannot_resolve_is_a_line_too(self):
        house = Path(self.tmp.name) / "house"
        house.mkdir()
        (house / bp.SETTINGS_FILE).write_text("- Provider: notion\n", encoding="utf-8")
        status, msg = bs.sync_piece([self.root], "alpha", knowledge=house, env={})
        self.assertEqual("failed", status)
        self.assertIn("Notion database", msg)

    def test_no_draft_text_is_sent(self):
        root = pieces(self.tmp.name, {"2026-02-01-gamma": {
            "draft.md": "---\ntitle: Gamma\n---\nAn opening line.\n\nDetail 4471. [NEEDS SOURCE: detail]\n"}})
        status, _ = bs.sync_piece([root], "gamma", provider=self.prov)
        self.assertEqual("created", status)
        blob = json.dumps(self.fake.bodies)
        for leak in ("4471", "opening line", "NEEDS SOURCE"):
            self.assertNotIn(leak, blob)


class Board(unittest.TestCase):
    def test_the_board_is_the_providers_count_grouped_by_state(self):
        f = tn.FakeNotion()
        f.add(pid="a", title="One", state="writing")
        f.add(pid="b", title="Two", state="sent")
        f.add(pid="c", title="Three", state="writing")
        text = bs.show_board(tn.provider(f)[0])
        self.assertIn("board: notion, 3 pieces", text)
        self.assertLess(text.index("writing (2)"), text.index("sent (1)"))
        for t in ("One", "Two", "Three"):
            self.assertIn(t, text)

    def test_an_empty_board_says_so_and_an_unreachable_one_is_never_empty(self):
        self.assertIn("0 pieces", bs.show_board(tn.provider(tn.FakeNotion())[0]))
        f = tn.FakeNotion()
        f.script = [(401, {}, {})]
        with self.assertRaises(bp.BoardUnavailable):
            bs.show_board(tn.provider(f)[0])


class Next(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pieces(self.tmp.name)
        self.prov = bp.LocalProvider([self.root])

    def test_it_names_where_the_piece_is_and_what_it_needs(self):
        code, text = bs.next_text(self.prov, "beta")
        self.assertEqual(0, code)
        self.assertIn("(writing)", text)
        self.assertIn("Next:", text)

    def test_more_than_one_open_piece_and_no_name_asks_which(self):
        code, text = bs.next_text(self.prov)
        self.assertEqual(1, code)
        self.assertIn("Name one", text)
        self.assertIn("2026-01-02-beta", text)

    def test_the_only_open_piece_is_the_default(self):
        (self.root / "2026-01-01-alpha").rename(self.root / ".gone")
        code, text = bs.next_text(bp.LocalProvider([self.root]))
        self.assertEqual(0, code)
        self.assertIn("Beta", text)

    def test_inside_a_piece_that_piece_is_the_default(self):
        here = bs.piece_here([self.root], self.root / "2026-01-01-alpha" / "edits")
        self.assertEqual("2026-01-01-alpha", here.name)
        code, text = bs.next_text(self.prov, None, here)
        self.assertEqual(0, code)
        self.assertIn("Alpha", text)
        self.assertIsNone(bs.piece_here([self.root], self.tmp.name))

    def test_an_unknown_or_ambiguous_name_is_said_plainly(self):
        self.assertEqual(1, bs.next_text(self.prov, "zzz")[0])
        code, text = bs.next_text(self.prov, "2026-01")
        self.assertEqual(1, code)
        self.assertIn("matches 2 pieces", text)

    def test_when_every_piece_is_sent_it_says_so(self):
        for d in self.root.iterdir():
            (d / "draft.md").write_text("Body.\n", encoding="utf-8")
            (d / "final.md").write_text("Sent.\n", encoding="utf-8")
        self.assertIn("Every piece is sent", bs.next_text(self.prov)[1])

    def test_it_starts_nothing_and_writes_no_file(self):
        before = tree(self.root)
        bs.next_text(self.prov, "beta")
        bs.next_text(self.prov)
        self.assertEqual(before, tree(self.root))

    def test_it_reads_through_the_notion_board_too(self):
        f = tn.FakeNotion()
        f.add(pid="a", title="Only piece", state="editing")
        f.pages[0]["properties"]["Next decision"] = {"rich_text": [{"plain_text": "Work through the line edit"}]}
        code, text = bs.next_text(tn.provider(f)[0])
        self.assertEqual(0, code)
        self.assertIn("Only piece (editing)", text)
        self.assertIn("Next: Work through the line edit", text)


class Wiring(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pieces(self.tmp.name)
        self.house = Path(self.tmp.name) / "house"
        self.house.mkdir()
        (self.house / "positioning.md").write_text("# Positioning\n", encoding="utf-8")
        self.home = Path(self.tmp.name) / "home"
        self.home.mkdir()

    def run_cli(self, *args, provider=None):
        if provider:
            (self.house / bp.SETTINGS_FILE).write_text(f"- Provider: {provider}\n", encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if not k.startswith(("FAMILIAR", "NOTION"))}
        env.update(HOME=str(self.home), FAMILIAR_KNOWLEDGE=str(self.house),
                   FAMILIAR_PIECES=str(self.root))
        return subprocess.run([sys.executable, str(FAMILIAR), *args], capture_output=True,
                              text=True, env=env, cwd=self.tmp.name)

    def test_next_names_the_only_open_piece_or_asks(self):
        r = self.run_cli("next", "beta")
        self.assertEqual(0, r.returncode, r.stderr)
        self.assertIn("Next:", r.stdout)
        r = self.run_cli("next")
        self.assertEqual(1, r.returncode)
        self.assertIn("Name one", r.stdout)

    def test_sync_with_no_provider_says_so_and_succeeds(self):
        r = self.run_cli("board", "sync", "alpha")
        self.assertEqual(0, r.returncode, r.stderr)
        self.assertIn("nothing to sync", r.stdout)

    def test_sync_needs_a_piece(self):
        self.assertEqual(1, self.run_cli("board", "sync").returncode)

    def test_a_notion_house_with_no_token_stops_with_where_it_goes(self):
        (self.house / bp.SETTINGS_FILE).write_text(
            f"- Provider: notion\n- Notion database: {tn.DB}\n", encoding="utf-8")
        r = self.run_cli("board")
        self.assertEqual(2, r.returncode)
        self.assertIn(nb.TOKEN_ENV, r.stderr)

    def test_a_failed_sync_exits_one_and_prints_one_line(self):
        (self.house / bp.SETTINGS_FILE).write_text(
            f"- Provider: notion\n- Notion database: {tn.DB}\n", encoding="utf-8")
        r = self.run_cli("board", "sync", "alpha")
        self.assertEqual(1, r.returncode)
        self.assertEqual(1, len([l for l in r.stdout.splitlines() if l.strip()]))


if __name__ == "__main__":
    unittest.main()
