"""The commit guard reads every byte of a file, including bytes that are not UTF-8.

A guard that pipes a diff through awk under a UTF-8 locale can skip a whole
file over one Latin-1 byte, letting a personal detail two lines below it
through. This guard greps whole files and does not, on macOS or Linux; these
tests keep it that way. The locale is forced to UTF-8 because that is where
the failure shows. Both directions are tested: a guard that blocks ordinary
files gets switched off.

Every file is synthetic, built in a throwaway repo.
"""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

GUARD = Path(__file__).resolve().parent.parent / "scripts" / "pre-commit-guard.sh"

# Assembled, not written out, so the guard does not block this file.
EMAIL = "real.person" + "@" + "gmail.com"


class GuardReadsEveryByte(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.d = Path(tmp.name)
        for args in (("init", "-q", "."),
                     ("remote", "add", "origin", "https://example.com/fake.git")):
            subprocess.run(("git",) + args, cwd=self.d, check=True)

    def guard(self, rel, body):
        p = self.d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(body)
        subprocess.run(("git", "add", "-A"), cwd=self.d, check=True)
        env = dict(os.environ, HOME=str(self.d), LC_ALL="C.UTF-8", LANG="C.UTF-8")
        return subprocess.run(("bash", str(GUARD)), cwd=self.d, env=env,
                              capture_output=True)

    def test_an_address_blocks(self):
        self.assertEqual(1, self.guard("src/notes.txt", EMAIL.encode() + b"\n").returncode)

    def test_an_address_below_a_latin1_byte_blocks(self):
        r = self.guard("src/notes.txt", b"caf\xe9 menu\n" + EMAIL.encode() + b"\n")
        self.assertEqual(1, r.returncode)

    def test_a_latin1_byte_alone_passes(self):
        r = self.guard("src/notes.txt", b"caf\xe9 menu\nordinary notes\n")
        self.assertEqual(0, r.returncode, r.stdout)

    def test_a_pdf_with_high_bytes_passes(self):
        r = self.guard("fixtures/a.pdf",
                       b"%PDF-1.3\n%\x93\x8c\x8b\x9e\nstream\nGaro:5u\nendstream\n")
        self.assertEqual(0, r.returncode, r.stdout)


if __name__ == "__main__":
    unittest.main()
