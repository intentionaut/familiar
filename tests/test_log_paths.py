"""A build log that lives outside the project it describes.

A public repository cannot hold a candid build log: it carries defect notes,
hours budgets and plan of record. Gitignoring it leaves one copy on one disk.
So the registry records where the log went, and every reader resolves it the
same way.
"""
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("flog", ROOT / "scripts" / "log.py")
flog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flog)


class ResolveLog(unittest.TestCase):
    def test_a_bare_name_is_inside_the_project(self):
        got = flog.resolve_log(Path("/tmp/proj"), "PROJ-LOG.md")
        self.assertEqual(Path("/tmp/proj/PROJ-LOG.md"), got)

    def test_a_path_is_used_as_it_stands(self):
        got = flog.resolve_log(Path("/tmp/proj"), "/vault/logs/PROJ-LOG.md")
        self.assertEqual(Path("/vault/logs/PROJ-LOG.md"), got)

    def test_a_tilde_path_expands(self):
        got = flog.resolve_log(Path("/tmp/proj"), "~/vault/PROJ-LOG.md")
        self.assertEqual(Path.home() / "vault/PROJ-LOG.md", got)
        self.assertNotIn("~", str(got))

    def test_nothing_recorded_resolves_to_nothing(self):
        self.assertIsNone(flog.resolve_log(Path("/tmp/proj"), None))


class MoveAndFind(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.project = base / "proj"
        self.project.mkdir()
        self.log = self.project / "PROJ-LOG.md"
        self.log.write_text("# proj build log\n\n## 2026-09-04\n\nkept\n")
        self.vault = base / "vault"
        self.vault.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_find_log_accepts_a_recorded_external_path(self):
        moved = self.vault / "PROJ-LOG.md"
        self.log.replace(moved)
        watched = {str(self.project.resolve()): str(moved)}
        self.assertEqual(str(moved), flog.find_log(self.project, watched))

    def test_find_log_ignores_a_recorded_path_that_is_not_there(self):
        watched = {str(self.project.resolve()): "/nowhere/PROJ-LOG.md"}
        # Falls back to what is actually in the folder rather than insisting.
        self.assertEqual("PROJ-LOG.md", flog.find_log(self.project, watched))
