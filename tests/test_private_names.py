"""familiar-core is what publishes. It never names the private modules it sits beside.

The public repo is built from this folder. A private module's name in a prompt,
a doc or a changelog would ship to strangers, and would tell a public writer to
reach for a tool they do not have.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRIVATE = re.compile(r"\b(portent|magpie|find-familiar)\b", re.I)
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv"}


def published_text_files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or SKIP_DIRS & set(path.relative_to(ROOT).parts):
            continue
        if path == Path(__file__).resolve():
            continue
        try:
            yield path, path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue  # binary: an image, a font


class PrivateNames(unittest.TestCase):
    def test_no_file_names_a_private_module(self):
        hits = [f"{p.relative_to(ROOT)}:{text[:m.start()].count(chr(10)) + 1} {m.group(0)}"
                for p, text in published_text_files() for m in PRIVATE.finditer(text)]
        self.assertEqual([], hits, "private module named in what publishes")

    def test_the_pattern_catches_the_names_and_spares_ordinary_words(self):
        for caught in ("Portent's steps", "run magpie track", "the find-familiar repo", "PORTENT"):
            self.assertRegex(caught, PRIVATE, caught)
        for spared in ("portentous", "portents of doom", "magpies at dawn", "familiar find"):
            self.assertNotRegex(spared, PRIVATE, spared)


if __name__ == "__main__":
    unittest.main()
