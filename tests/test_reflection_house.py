"""Reflection settings come from the writer's house, the way every other knowledge file does.

`log.py` and `reflection-nudge.sh` used to look in one person's vault path, written into public code. Now both ask
`paths.py`, so the settings are found wherever FAMILIAR_KNOWLEDGE (or `.familiar`) puts the house, and with no house
the shipped copy answers. HOME is a temp folder in every test.
"""
import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("flog_reflect", ROOT / "scripts" / "log.py")
flog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flog)

SETTINGS = "# Reflection\n\n- Reflection: {on}\n- Cadence: weekly\n- Reflections live in: {folder}\n"


class ReflectionSettingsComeFromTheHouse(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.home = base / "home"
        self.house = base / "house"
        self.house.mkdir()
        (self.house / "positioning.md").write_text("# Positioning\n", encoding="utf-8")
        self.mine = base / "my-reflections"
        self.mine.mkdir()
        self.home.mkdir()
        self.env = {k: v for k, v in os.environ.items()
                    if k not in ("FAMILIAR_KNOWLEDGE", "FAMILIAR_CONFIG", "FAMILIAR_PIECES", "FAMILIAR_VAULT")}
        self.env["HOME"] = str(self.home)
        self.saved = dict(os.environ)
        os.environ.clear()
        os.environ.update(self.env)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.saved)
        self.tmp.cleanup()

    def test_the_scan_skips_the_folder_the_house_names(self):
        (self.house / "reflection.md").write_text(SETTINGS.format(on="on", folder=self.mine), encoding="utf-8")
        os.environ["FAMILIAR_KNOWLEDGE"] = str(self.house)
        self.assertEqual(flog.reflections_folder(), self.mine.resolve())

    def test_with_no_house_the_shipped_settings_answer(self):
        self.assertEqual(flog.reflections_folder(), (self.home / "Projects" / "reflections").resolve())

    def nudge(self, **extra):
        return subprocess.run(["bash", str(ROOT / "scripts" / "reflection-nudge.sh"), "--dry-run"],
                              capture_output=True, text=True, env={**self.env, **extra}, cwd=self.tmp.name)

    def test_the_nudge_reads_the_house(self):
        (self.house / "reflection.md").write_text(SETTINGS.format(on="off", folder=self.mine), encoding="utf-8")
        out = self.nudge(FAMILIAR_KNOWLEDGE=str(self.house))
        self.assertIn("reflection is off", out.stdout, out.stderr)

    def test_with_no_house_the_nudge_reads_the_shipped_template(self):
        out = self.nudge()
        self.assertIn("settings still the template", out.stdout, out.stderr)


if __name__ == "__main__":
    unittest.main()
