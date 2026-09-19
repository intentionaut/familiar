"""The board's provider boundary.

Every fixture is built in a temporary folder and is synthetic. Nothing here
reads a real house or a real piece.

The rules under test:
  - the built-in board reads the same state the board page shows, through the
    same call
  - draft text never reaches a board field, including the text inside a bracket
  - with no setting, or the template's, the built-in board is the provider
  - a provider that is not there, or not a provider, stops with what to do
  - any provider must: keep unknown properties on update, refuse a stale write
    rather than pick a value, refuse a field that is not a board field, and say
    so when the board cannot be reached
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import board  # noqa: E402
import board_provider as bp  # noqa: E402


def make_pieces(base):
    pieces = Path(base) / "pieces"
    for name, files in {
        "2026-01-01-alpha": {"notes.md": "# Alpha\n\n## Working thesis\n\nSomething to say.\n"},
        "2026-01-02-beta": {"outline.md": "# Beta\n\n## A\n"},
        "2026-01-03-gamma": {
            "draft.md": "---\ntitle: Gamma\n---\nAn opening line.\n\nThe private detail is 4471. "
                        "[NEEDS SOURCE: the private detail]\n"},
        "2026-01-04-delta": {"draft.md": "---\ntitle: Delta\n---\nDone.\n", "final.md": "Sent.\n"},
    }.items():
        d = pieces / name
        d.mkdir(parents=True)
        for f, text in files.items():
            (d / f).write_text(text, encoding="utf-8")
    return pieces


class MemoryProvider(bp.BoardProvider):
    """A writable provider held in memory. The contract any real one must meet."""

    name = "memory"

    def __init__(self, unreachable=False):
        self.rows, self.unreachable, self._n = {}, unreachable, 0

    def _guard(self):
        if self.unreachable:
            raise bp.BoardUnavailable("The board could not be reached.", "Check the connection and run it again.")

    def read_all(self):
        self._guard()
        return list(self.rows.values())

    def create(self, item):
        self._guard()
        self._n += 1
        row = bp.BoardItem(**{**item.__dict__, "version": str(self._n)})
        self.rows[row.id] = row
        return row

    def update(self, item_id, changes, version):
        self._guard()
        self.check_fields(changes)
        row = self.rows[item_id]
        if row.version != version:
            raise bp.BoardConflict("That row changed after it was read.", "Choose which value stands.")
        self._n += 1
        row = bp.BoardItem(**{**row.__dict__, **changes, "version": str(self._n)})
        self.rows[item_id] = row
        return row


class Local(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pieces = make_pieces(self.tmp.name)
        self.items = {i.id: i for i in bp.LocalProvider([self.pieces]).read_all()}

    def test_it_reads_the_state_the_board_page_shows(self):
        import datetime
        now = datetime.datetime.now().timestamp()
        for folder in self.pieces.iterdir():
            p = board.gather(folder, now, 7, "")
            item = self.items[folder.name]
            self.assertEqual((p["stage"], p["title"], p["action"]),
                             (item.state, item.title, item.next_decision))

    def test_every_piece_is_counted_by_state(self):
        self.assertEqual({"thinking": 1, "writing": 1, "editing": 1, "sent": 1},
                         bp.counts(self.items.values()))

    def test_draft_text_never_reaches_a_board_field(self):
        for item in self.items.values():
            blob = repr(item)
            self.assertNotIn("4471", blob)
            self.assertNotIn("private detail", blob)
        self.assertEqual(("1 unresolved bracket",), tuple(self.items["2026-01-03-gamma"].blockers))

    def test_it_has_nothing_to_write_to(self):
        p = bp.LocalProvider([self.pieces])
        with self.assertRaises(bp.ReadOnly):
            p.create(self.items["2026-01-01-alpha"])
        with self.assertRaises(bp.ReadOnly):
            p.update("2026-01-01-alpha", {"title": "x"}, "")

    def test_reading_writes_no_file(self):
        before = sorted(str(p) for p in self.pieces.rglob("*"))
        bp.LocalProvider([self.pieces]).read_all()
        self.assertEqual(before, sorted(str(p) for p in self.pieces.rglob("*")))

    def test_one_piece_can_be_read_and_a_missing_one_is_none(self):
        p = bp.LocalProvider([self.pieces])
        self.assertEqual("Gamma", p.read("2026-01-03-gamma").title)
        self.assertIsNone(p.read("2099-01-01-nothing"))


class Setting(unittest.TestCase):
    def house(self, text=None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        if text is not None:
            (Path(tmp.name) / bp.SETTINGS_FILE).write_text(text, encoding="utf-8")
        return tmp.name

    def test_the_shipped_template_leaves_it_unset(self):
        self.assertIsNone(bp.read_setting(ROOT / "knowledge"))

    def test_unset_or_local_is_the_built_in_board(self):
        for text in (None, "- Provider: [local / notion]\n", "- Provider: local\n", "- Provider:\n"):
            p = bp.resolve_provider([], self.house(text))
            self.assertIsInstance(p, bp.LocalProvider, text)

    def test_notion_says_it_is_not_in_this_version(self):
        with self.assertRaises(bp.BoardError) as cm:
            bp.resolve_provider([], self.house("- Provider: notion\n"))
        self.assertIn("not in this version", str(cm.exception))
        self.assertIn(bp.SETTINGS_FILE, cm.exception.next_step)

    def test_a_value_that_is_no_provider_names_the_ones_that_are(self):
        with self.assertRaises(bp.BoardError) as cm:
            bp.resolve_provider([], self.house("- Provider: airtable\n"))
        self.assertIn("airtable", str(cm.exception))
        self.assertIn("local or notion", str(cm.exception))

    def test_the_value_is_case_insensitive(self):
        self.assertIsInstance(bp.resolve_provider([], self.house("- Provider: Local\n")), bp.LocalProvider)


class Contract(unittest.TestCase):
    """What every writable provider must do. A Notion provider is held to this."""

    def make(self):
        return MemoryProvider()

    def item(self, **kw):
        return bp.BoardItem(**{"id": "p1", "title": "T", "state": "writing", **kw})

    def test_a_row_is_created_and_read_back(self):
        p = self.make()
        made = p.create(self.item())
        self.assertEqual("T", p.read("p1").title)
        self.assertTrue(made.version)

    def test_an_update_changes_named_fields_and_keeps_unknown_properties(self):
        p = self.make()
        made = p.create(self.item(extra={"Owner": "kept"}))
        after = p.update("p1", {"state": "editing"}, made.version)
        self.assertEqual("editing", after.state)
        self.assertEqual({"Owner": "kept"}, dict(after.extra))
        self.assertEqual("T", after.title)

    def test_a_stale_write_is_refused_not_resolved(self):
        p = self.make()
        made = p.create(self.item())
        p.update("p1", {"state": "editing"}, made.version)
        with self.assertRaises(bp.BoardConflict):
            p.update("p1", {"state": "ready"}, made.version)
        self.assertEqual("editing", p.read("p1").state)

    def test_a_field_that_is_not_a_board_field_is_refused(self):
        p = self.make()
        made = p.create(self.item())
        with self.assertRaises(bp.UndeclaredField):
            p.update("p1", {"draft_text": "x"}, made.version)

    def test_an_unreachable_board_says_so_and_is_never_empty(self):
        p = MemoryProvider(unreachable=True)
        with self.assertRaises(bp.BoardUnavailable) as cm:
            p.read_all()
        self.assertTrue(cm.exception.next_step)

    def test_no_provider_can_delete(self):
        for name in ("delete", "archive", "remove"):
            self.assertFalse(hasattr(bp.BoardProvider, name), name)


class Errors(unittest.TestCase):
    def test_each_says_what_happened_then_what_to_do(self):
        e = bp.BoardConflict("A row changed.", "Pick a value.")
        self.assertEqual("A row changed. Pick a value.", str(e))
        for cls in (bp.BoardUnavailable, bp.SchemaDrift, bp.RateLimited, bp.ReadOnly, bp.UndeclaredField):
            self.assertTrue(issubclass(cls, bp.BoardError))


class Command(unittest.TestCase):
    def test_it_prints_the_provider_and_the_count_by_state(self):
        import io
        import contextlib
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        pieces = make_pieces(tmp.name)
        # A house with positioning.md, so nothing falls through to a real one.
        house = Path(tmp.name) / "knowledge"
        house.mkdir()
        (house / "positioning.md").write_text("# Positioning\n", encoding="utf-8")
        keys = ("FAMILIAR_PIECES", "FAMILIAR_KNOWLEDGE", "FAMILIAR_CONFIG")
        saved = {k: os.environ.get(k) for k in keys}
        os.environ.pop("FAMILIAR_CONFIG", None)
        os.environ.update(FAMILIAR_PIECES=str(pieces), FAMILIAR_KNOWLEDGE=str(house))
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                code = bp.main()
        finally:
            for k, v in saved.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        out = buf.getvalue()
        self.assertEqual(0, code)
        self.assertIn("board: built-in, 4 pieces", out)
        self.assertNotIn("Gamma", out)   # counts, never titles


if __name__ == "__main__":
    unittest.main()
