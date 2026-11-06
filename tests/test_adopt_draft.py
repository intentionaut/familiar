"""adopt-draft.py is the only way a revised draft replaces draft.md: a verified backup first, or nothing changes."""
import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("adopt_draft", ROOT / "scripts" / "adopt-draft.py")
ad = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ad)

OLD = "# Piece\n\nThe writer's words, as they were.\n".encode()
NEW = b"# Piece\n\nThe revised words.\n"


def run(*argv):
    err = io.StringIO()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
        return ad.main(list(argv)), err.getvalue()


class AdoptDraft(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.piece = Path(self.tmp.name)
        (self.piece / "draft.md").write_bytes(OLD)
        (self.piece / ".versions").mkdir(parents=True)
        self.revised = self.piece / ".versions" / "dev-edit-draft.md"
        self.revised.write_bytes(NEW)

    def tearDown(self):
        self.tmp.cleanup()

    def test_backup_is_byte_identical_and_draft_is_replaced(self):
        code, _ = run(str(self.piece), str(self.revised))
        self.assertEqual(code, 0)
        self.assertEqual((self.piece / ".versions" / "draft-before-r1.md").read_bytes(), OLD)
        self.assertEqual((self.piece / "draft.md").read_bytes(), NEW)

    def test_an_existing_backup_is_never_clobbered(self):
        kept = self.piece / ".versions" / "draft-before-r1.md"
        kept.write_bytes(b"round one, kept")
        code, _ = run(str(self.piece), str(self.revised))
        self.assertEqual(code, 0)
        self.assertEqual(kept.read_bytes(), b"round one, kept")
        self.assertEqual((self.piece / ".versions" / "draft-before-r2.md").read_bytes(), OLD)

    def test_a_backup_taken_meanwhile_stops_it_and_draft_is_untouched(self):
        with mock.patch.object(ad, "write_new", side_effect=FileExistsError):
            code, err = run(str(self.piece), str(self.revised))
        self.assertEqual(code, 1)
        self.assertIn("already exists", err)
        self.assertEqual((self.piece / "draft.md").read_bytes(), OLD)

    def test_a_failed_backup_leaves_draft_untouched(self):
        def bad(path, data):
            path.write_bytes(data[:-1])          # a short write: the backup no longer matches
        with mock.patch.object(ad, "write_new", side_effect=bad):
            code, err = run(str(self.piece), str(self.revised))
        self.assertEqual(code, 1)
        self.assertIn("does not match", err)
        self.assertEqual((self.piece / "draft.md").read_bytes(), OLD)

    def test_an_unwritable_backup_leaves_draft_untouched(self):
        with mock.patch.object(ad, "write_new", side_effect=PermissionError("denied")):
            code, _ = run(str(self.piece), str(self.revised))
        self.assertEqual(code, 1)
        self.assertEqual((self.piece / "draft.md").read_bytes(), OLD)

    def test_missing_files_change_nothing(self):
        code, _ = run(str(self.piece), str(self.piece / "edits" / "nope.md"))
        self.assertEqual(code, 1)
        self.assertEqual((self.piece / "draft.md").read_bytes(), OLD)
        self.assertFalse((self.piece / ".versions" / "draft-before-r1.md").exists())


class VersionsAreNotReports(unittest.TestCase):
    """Full drafts kept in .versions/ must not be read as edit reports by the board or her-share."""

    def test_board_listing_and_her_share_scan_ignore_the_versions_store(self):
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        import board_edit
        hs_spec = importlib.util.spec_from_file_location("her_share", ROOT / "scripts" / "her-share.py")
        hs = importlib.util.module_from_spec(hs_spec)
        hs_spec.loader.exec_module(hs)
        with tempfile.TemporaryDirectory() as d:
            piece = Path(d)
            (piece / "draft.md").write_text("# Piece\n")
            (piece / ".versions").mkdir(); (piece / "edits").mkdir()
            (piece / "edits" / "line-edit-report.md").write_text(
                "Fix: The report sentence that counts as a suggested rewrite here.\n")
            for name in ("draft-before-r1.md", "dev-edit-draft.md", "line-edit-draft.md"):
                (piece / ".versions" / name).write_text(
                    "Fix: A full draft sentence that must never count as a suggested rewrite.\n")
            listed = board_edit.option_files(piece)
            self.assertIn("edits/line-edit-report.md", listed)
            self.assertFalse([f for f in listed if "versions/" in f], listed)
            rewrites = hs.suggested_rewrites(piece)
            self.assertTrue(any("report sentence" in s for s in rewrites), rewrites)
            self.assertFalse(any("full draft sentence" in s for s in rewrites), rewrites)

    def test_revival_check_does_not_reparse_the_versions_store(self):
        rc_spec = importlib.util.spec_from_file_location("revival_check", ROOT / "scripts" / "revival-check.py")
        rc = importlib.util.module_from_spec(rc_spec)
        rc_spec.loader.exec_module(rc)
        bad = "## Option set: x\n\n### A. One\nSome words here.\nChosen: none of them\n"
        with tempfile.TemporaryDirectory() as d:
            piece = Path(d)
            (piece / ".versions").mkdir()
            (piece / ".versions" / "draft-before-r1.md").write_text(bad)
            self.assertEqual(rc.kills_from_piece(piece)[1], [])
            (piece / "options.md").write_text(bad)     # the same text in the piece itself is still read
            self.assertEqual(len(rc.kills_from_piece(piece)[1]), 1)


if __name__ == "__main__":
    unittest.main()
