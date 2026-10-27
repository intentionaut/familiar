"""familiar-core is what publishes. It never names the private modules it sits beside.

The public repo is built from this folder. A private module's name in a prompt,
a doc or a changelog would ship to strangers, and would tell a public writer to
reach for a tool they do not have.

The names themselves live outside this folder, in the workshop's
contracts/private-names.txt, so this test never prints them either. In the
workshop the list is required: a missing or empty list fails, it does not skip.
Released on its own, where there is no workshop, the check has nothing to read
and is skipped; it already ran before the release.
"""
import re
import unittest
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKSHOP = ROOT.parent.parent if ROOT.parent.name == "modules" else None
TERMS_FILE = WORKSHOP / "contracts" / "private-names.txt" if WORKSHOP else None
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv"}


def load_terms(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    return [t.strip() for t in lines if t.strip() and not t.strip().startswith("#")]


def pattern_for(terms):
    return re.compile(r"\b(" + "|".join(re.escape(t) for t in terms) + r")\b", re.I)


def published_text_files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or SKIP_DIRS & set(path.relative_to(ROOT).parts):
            continue
        try:
            yield path, path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue  # binary: an image, a font

if WORKSHOP is None:
    # A skip is easy to read as a pass. Say, in the run's own output, that nothing was checked here.
    warnings.warn("private-names check NOT RUN: no workshop list beside this copy; it runs in the workshop "
                  "and on the extract before release", stacklevel=1)


@unittest.skipIf(WORKSHOP is None, "released copy: no workshop list to read; the check ran before release")
class PrivateNames(unittest.TestCase):
    def test_the_list_is_there_and_not_empty(self):
        self.assertTrue(TERMS_FILE.is_file(), f"missing {TERMS_FILE.relative_to(WORKSHOP)}")
        self.assertTrue(load_terms(TERMS_FILE), f"{TERMS_FILE.relative_to(WORKSHOP)} lists no names")

    def test_no_file_names_a_private_module(self):
        private = pattern_for(load_terms(TERMS_FILE))
        hits = [f"{p.relative_to(ROOT)}:{text[:m.start()].count(chr(10)) + 1} {m.group(0)}"
                for p, text in published_text_files() for m in private.finditer(text)]
        self.assertEqual([], hits, "private module named in what publishes")


class Pattern(unittest.TestCase):
    def test_the_pattern_catches_the_names_and_spares_ordinary_words(self):
        pattern = pattern_for(["examplemod", "side-tool"])
        for caught in ("Examplemod's steps", "run side-tool track", "the side-tool repo", "EXAMPLEMOD"):
            self.assertRegex(caught, pattern, caught)
        for spared in ("examplemods", "side tool", "example mod", "tool side"):
            self.assertNotRegex(spared, pattern, spared)


if __name__ == "__main__":
    unittest.main()
