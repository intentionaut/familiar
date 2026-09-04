"""The one check that refuses. It has to be right in both directions: a miss
lets a client's name into a newsletter, and a false alarm gets it switched off.
"""
import importlib.util
import os
import sys
import tempfile
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
        on, block, warn = np.load()
        self.assertFalse(on)
        self.assertEqual(block, [])

    def test_untouched_template_is_off(self):
        (self.house / "never-publish.md").write_text(
            (ROOT / "knowledge" / "never-publish.md").read_text())
        on, block, warn = np.load()
        self.assertFalse(on, "placeholders must not become real entries")

    def test_a_filled_list_loads(self):
        (self.house / "never-publish.md").write_text(LIST)
        on, block, warn = np.load()
        self.assertTrue(on)
        self.assertEqual(block, ["Acme Holdings", "CAT", "£50,000"])
        self.assertEqual(warn, ["42%"])

    def test_trailing_notes_are_not_part_of_the_string(self):
        (self.house / "never-publish.md").write_text(LIST)
        _, block, _ = np.load()
        self.assertIn("Acme Holdings", block)
        self.assertNotIn("#", " ".join(block))

    def test_off_means_off(self):
        (self.house / "never-publish.md").write_text(LIST.replace("on", "off", 1))
        on, _, _ = np.load()
        self.assertFalse(on)


if __name__ == "__main__":
    unittest.main()
