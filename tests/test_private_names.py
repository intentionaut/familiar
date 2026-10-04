"""familiar-core is what publishes. It never names the private modules it sits beside.

The public repo is built from this folder. A private module's name in a prompt,
a doc or a changelog would ship to strangers, and would tell a public writer to
reach for a tool they do not have.
"""
import os
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TERMS_FILE = ROOT / "tests" / "private-terms.txt"  # gitignored; one term per line
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv"}


def load_terms():
    """The real list lives outside the public repo: FAMILIAR_PRIVATE_TERMS
    (comma separated) or the gitignored tests/private-terms.txt."""
    raw = os.environ.get("FAMILIAR_PRIVATE_TERMS", "")
    terms = [t.strip() for t in raw.split(",")]
    if TERMS_FILE.exists():
        terms += [l.strip() for l in TERMS_FILE.read_text(encoding="utf-8").splitlines()]
    return [t for t in terms if t and not t.startswith("#")]


def pattern_for(terms):
    return re.compile(r"\b(" + "|".join(re.escape(t) for t in terms) + r")\b", re.I)


def published_text_files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or SKIP_DIRS & set(path.relative_to(ROOT).parts):
            continue
        if path in (Path(__file__).resolve(), TERMS_FILE):
            continue
        try:
            yield path, path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue  # binary: an image, a font


class PrivateNames(unittest.TestCase):
    @unittest.skipUnless(load_terms(), "no private term list; set FAMILIAR_PRIVATE_TERMS or tests/private-terms.txt")
    def test_no_file_names_a_private_module(self):
        PRIVATE = pattern_for(load_terms())
        hits = [f"{p.relative_to(ROOT)}:{text[:m.start()].count(chr(10)) + 1} {m.group(0)}"
                for p, text in published_text_files() for m in PRIVATE.finditer(text)]
        self.assertEqual([], hits, "private module named in what publishes")

    def test_the_pattern_catches_the_names_and_spares_ordinary_words(self):
        pattern = pattern_for(["examplemod", "side-tool"])
        for caught in ("Examplemod's steps", "run side-tool track", "the side-tool repo", "EXAMPLEMOD"):
            self.assertRegex(caught, pattern, caught)
        for spared in ("examplemods", "side tool", "example mod", "tool side"):
            self.assertNotRegex(spared, pattern, spared)


if __name__ == "__main__":
    unittest.main()
