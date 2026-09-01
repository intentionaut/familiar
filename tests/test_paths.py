"""The knowledge address. Getting this wrong looks like a bad edit, not a
missing file, which is why it is worth a test."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import paths  # noqa: E402


class KnowledgeAddress(unittest.TestCase):
    def setUp(self):
        self._env = {k: os.environ.pop(k, None)
                     for k in ("FAMILIAR_KNOWLEDGE", "FAMILIAR_CONFIG", "FAMILIAR_PIECES")}
        self._cwd = os.getcwd()
        # The real install may have its own .familiar next to the repo, and it
        # would otherwise answer questions these tests are asking about a clean
        # machine. Look only at the working directory here.
        self._config_file = paths._config_file
        paths._config_file = lambda: (
            Path.cwd() / ".familiar" if (Path.cwd() / ".familiar").is_file() else None)

    def tearDown(self):
        paths._config_file = self._config_file
        os.chdir(self._cwd)
        for k, v in self._env.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v

    def _filled(self, tmp):
        d = Path(tmp) / "mine"
        d.mkdir()
        (d / "positioning.md").write_text("# theirs\n")
        return d

    def test_falls_back_to_the_shipped_templates_and_says_so(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            found, whose = paths.knowledge_dir()
            self.assertEqual(paths.SHIPPED, found)
            self.assertEqual("the shipped templates", whose)

    def test_env_var_wins_and_is_reported_as_the_writers(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            d = self._filled(tmp)
            os.environ["FAMILIAR_KNOWLEDGE"] = str(d)
            found, whose = paths.knowledge_dir()
            self.assertEqual(d.resolve(), found)
            self.assertEqual("yours", whose)

    def test_the_older_config_name_still_works(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            d = self._filled(tmp)
            os.environ["FAMILIAR_CONFIG"] = str(d)
            self.assertEqual(d.resolve(), paths.knowledge_dir()[0])

    def test_a_config_file_is_read_when_no_env_var_is_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            d = self._filled(tmp)
            Path(tmp, ".familiar").write_text(
                "# a comment\n\nknowledge = %s\n" % d)
            self.assertEqual(d.resolve(), paths.knowledge_dir()[0])

    def test_a_folder_without_positioning_is_not_a_knowledge_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            empty = Path(tmp) / "empty"
            empty.mkdir()
            os.environ["FAMILIAR_KNOWLEDGE"] = str(empty)
            self.assertEqual(paths.SHIPPED, paths.knowledge_dir()[0])

    def test_pieces_takes_several_and_keeps_their_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            a, b = Path(tmp, "a"), Path(tmp, "b")
            a.mkdir(); b.mkdir()
            Path(tmp, ".familiar").write_text(f"pieces = {a}\npieces = {b}\n")
            self.assertEqual([a.resolve(), b.resolve()], paths.pieces_dirs())

    def test_pieces_does_not_repeat_a_folder_named_twice(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            a = Path(tmp, "a"); a.mkdir()
            os.environ["FAMILIAR_PIECES"] = os.pathsep.join([str(a), str(a)])
            self.assertEqual([a.resolve()], paths.pieces_dirs())


if __name__ == "__main__":
    unittest.main()
