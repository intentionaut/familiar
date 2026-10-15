"""The one check that refuses. It has to be right in both directions: a miss
lets a client's name into a newsletter, and a false alarm gets it switched off.
"""
import contextlib
import importlib.util
import io
import os
import sys
import tempfile
import datetime
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

spec = importlib.util.spec_from_file_location("never_publish",
                                              ROOT / "scripts" / "never-publish.py")
np = importlib.util.module_from_spec(spec)
spec.loader.exec_module(np)

LIST = """# Never publish

## Settings

- Never publish: on

## Block

```
Acme Holdings  # a note about where this came from
CAT
£50,000
```

## Warn

```
42%
```
"""


class Matching(unittest.TestCase):
    def test_a_name_matches_whole_words_only(self):
        self.assertTrue(np.present("CAT", "a role at CAT next year"))
        self.assertFalse(np.present("CAT", "the catalogue was updated"))
        self.assertFalse(np.present("CAT", "vacation dates"))

    def test_case_does_not_matter(self):
        self.assertTrue(np.present("Acme Holdings", "we met ACME HOLDINGS today"))

    def test_money_matches_anywhere(self):
        self.assertTrue(np.present("£50,000", "(£50,000-£60,000)"))

    def test_a_name_with_punctuation_still_matches(self):
        self.assertTrue(np.present("Beacon Talent Partners", "via Beacon Talent Partners."))

    def test_a_name_that_ends_in_a_full_stop_matches(self):
        """Ltd. and Inc. are how half a client list is written."""
        self.assertTrue(np.present("Acme Inc.", "we rebranded Acme Inc. last spring"))
        self.assertTrue(np.present("Acme Inc.", "ACME INC. paid on time"))
        self.assertFalse(np.present("Acme Inc.", "acme incorporated the feedback"))


class Loading(unittest.TestCase):
    def setUp(self):
        self._env = os.environ.pop("FAMILIAR_KNOWLEDGE", None)
        self.dir = tempfile.TemporaryDirectory()
        house = Path(self.dir.name)
        (house / "positioning.md").write_text("# marks this as a house\n")
        self.house = house
        os.environ["FAMILIAR_KNOWLEDGE"] = str(house)

    def tearDown(self):
        os.environ.pop("FAMILIAR_KNOWLEDGE", None)
        if self._env:
            os.environ["FAMILIAR_KNOWLEDGE"] = self._env
        self.dir.cleanup()

    def test_missing_file_is_off(self):
        state, block, warn = np.load()
        self.assertEqual(state, "off")
        self.assertEqual(block, [])

    def test_untouched_template_is_off(self):
        (self.house / "never-publish.md").write_text(
            (ROOT / "knowledge" / "never-publish.md").read_text())
        state, block, warn = np.load()
        self.assertEqual(state, "off", "placeholders must not become real entries")

    def test_a_filled_list_loads(self):
        (self.house / "never-publish.md").write_text(LIST)
        state, block, warn = np.load()
        self.assertEqual(state, "on")
        self.assertEqual(block, ["Acme Holdings", "CAT", "£50,000"])
        self.assertEqual(warn, ["42%"])

    def test_trailing_notes_are_not_part_of_the_string(self):
        (self.house / "never-publish.md").write_text(LIST)
        _, block, _ = np.load()
        self.assertIn("Acme Holdings", block)
        self.assertNotIn("#", " ".join(block))

    def test_off_means_off(self):
        (self.house / "never-publish.md").write_text(LIST.replace("on", "off", 1))
        state, _, _ = np.load()
        self.assertEqual(state, "off")

    def test_a_stale_list_is_not_off_it_is_unknown(self):
        """Off is a choice. Stale is a check that quietly stopped running.

        Collapsing the two is how a gate reports clean while covering nothing.
        """
        old = (datetime.date.today() - datetime.timedelta(days=60)).isoformat()
        (self.house / "never-publish.md").write_text(
            LIST.replace("## Block", f"- Generated: {old}\n\n## Block", 1))
        state, block, _ = np.load()
        self.assertEqual(state, "stale")
        self.assertEqual(block, [], "a stale list must not be used as if current")

    def test_a_fresh_generated_list_still_loads(self):
        today = datetime.date.today().isoformat()
        (self.house / "never-publish.md").write_text(
            LIST.replace("## Block", f"- Generated: {today}\n\n## Block", 1))
        state, block, _ = np.load()
        self.assertEqual(state, "on")
        self.assertIn("Acme Holdings", block)


SYNTHETIC = ("# Never publish\n## Settings\n- Never publish: on\n"
             "## Block\n```\nSynthetic Client\n```\n")


class AHouseNamedOnlyInTheEnvironment(unittest.TestCase):
    """FAMILIAR_KNOWLEDGE and FAMILIAR_CONFIG configure the house as surely as
    `.familiar` does, so one that names a folder that is not a house leaves the
    text unexamined, not clean. HOME and the working directory are throwaway
    folders, and `.familiar` is looked for only there, so a real install can
    neither rescue nor spoil a case."""

    def setUp(self):
        self._env = {k: os.environ.get(k) for k in
                     ("HOME", "FAMILIAR_KNOWLEDGE", "FAMILIAR_CONFIG")}
        self._cwd = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        for sub in ("home", "work", "house"):
            (d / sub).mkdir()
        os.environ["HOME"] = str(d / "home")
        os.chdir(d / "work")
        self._config_file = np.paths._config_file
        np.paths._config_file = lambda: (
            Path.cwd() / ".familiar" if (Path.cwd() / ".familiar").is_file() else None)
        self.house = d / "house"
        (self.house / "positioning.md").write_text("# marks this as a house\n")
        (self.house / "never-publish.md").write_text(SYNTHETIC)
        self.absent = str(d / "no-such-house")
        os.environ.pop("FAMILIAR_CONFIG", None)
        os.environ["FAMILIAR_KNOWLEDGE"] = str(self.house)

    def tearDown(self):
        np.paths._config_file = self._config_file
        os.chdir(self._cwd)
        for k, v in self._env.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v
        self.tmp.cleanup()

    def cli(self, *args, text=""):
        """The command line, run in this process so the sandbox holds."""
        out, argv, stdin = io.StringIO(), sys.argv, sys.stdin
        sys.argv, sys.stdin = ["never-publish.py", *args], io.StringIO(text)
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
                return np.main()
        finally:
            sys.argv, sys.stdin = argv, stdin

    def assert_unexamined(self):
        self.assertNotEqual(np.paths.knowledge_dir()[1], "yours")
        self.assertEqual(np.load()[0], "unresolved")
        self.assertEqual(self.cli("-", text="Synthetic Client"), 2)
        self.assertEqual(self.cli("-", text="Nothing sensitive here."), 2)
        self.assertEqual(self.cli("--list"), 2)

    def test_a_valid_house_from_the_environment_allows_clean_and_blocks_a_name(self):
        self.assertEqual(np.load()[0], "on")
        self.assertEqual(self.cli("-", text="Nothing sensitive here."), 0)
        self.assertEqual(self.cli("-", text="We worked with Synthetic Client."), 1)

    def test_familiar_knowledge_naming_a_missing_folder_is_unexamined(self):
        os.environ["FAMILIAR_KNOWLEDGE"] = self.absent
        self.assert_unexamined()

    def test_familiar_knowledge_naming_a_folder_that_is_not_a_house_is_unexamined(self):
        (self.house / "positioning.md").unlink()
        self.assert_unexamined()

    def test_the_older_familiar_config_naming_a_missing_folder_is_unexamined(self):
        os.environ.pop("FAMILIAR_KNOWLEDGE")
        os.environ["FAMILIAR_CONFIG"] = self.absent
        self.assert_unexamined()

    def test_a_familiar_file_naming_a_missing_folder_is_still_unexamined(self):
        os.environ.pop("FAMILIAR_KNOWLEDGE")
        Path(".familiar").write_text(f"knowledge = {self.absent}\n")
        self.assert_unexamined()

    def test_nothing_configured_and_no_house_is_a_new_install_and_off(self):
        os.environ.pop("FAMILIAR_KNOWLEDGE")
        self.assertFalse(np.paths.familiar_configured())
        self.assertEqual(np.load()[0], "off")
        self.assertEqual(self.cli("-", text="Synthetic Client"), 0)

    def test_an_empty_variable_configures_nothing(self):
        os.environ["FAMILIAR_KNOWLEDGE"] = ""
        self.assertEqual(np.load()[0], "off")

    def test_off_in_a_resolved_environment_house_stays_off(self):
        (self.house / "never-publish.md").write_text(
            SYNTHETIC.replace("Never publish: on", "Never publish: off"))
        self.assertEqual(np.load()[0], "off")
        self.assertEqual(self.cli("-", text="Synthetic Client"), 0)


if __name__ == "__main__":
    unittest.main()
