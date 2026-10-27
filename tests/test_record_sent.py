"""record-sent.py: writes `sent`, `platform` and `web_url` into final.md, only on --confirm, and only when it reads back."""
import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("record_sent", ROOT / "scripts" / "record-sent.py")
rs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rs)

URL = "https://www.linkedin.com/feed/update/urn%3Ali%3Ashare%3A1"
ARGS = ["--platform", "linkedin", "--url", URL, "--sent", "2026-08-31"]


class RecordSent(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.dir = Path(t.name) / "2026-09-01-post"
        self.dir.mkdir()
        self.final = self.dir / "final.md"

    def run_rs(self, *extra, args=ARGS):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = rs.main([str(self.dir), *args, *extra])
            except SystemExit as e:
                code = e.code
        return code, out.getvalue()

    def test_without_confirm_nothing_is_written(self):
        self.final.write_text("The post.\n")
        code, out = self.run_rs()
        self.assertEqual(code, 0)
        self.assertIn("would add", out)
        self.assertEqual(self.final.read_text(), "The post.\n")

    def test_confirm_adds_frontmatter_and_leaves_the_body_alone(self):
        self.final.write_text("The post.\n\nSecond paragraph.\n")
        code, out = self.run_rs("--confirm")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.final.read_text(),
                         f"---\nsent: 2026-08-31\nplatform: linkedin\nweb_url: {URL}\n---\nThe post.\n\nSecond paragraph.\n")
        self.assertIn("resolved", out)

    def test_existing_frontmatter_keeps_its_fields_and_gains_the_missing_ones(self):
        self.final.write_text("---\ntitle: A post\n---\nBody.\n")
        self.assertEqual(self.run_rs("--confirm")[0], 0)
        text = self.final.read_text()
        self.assertTrue(text.startswith("---\ntitle: A post\nsent: 2026-08-31\n"))
        self.assertTrue(text.endswith("---\nBody.\n"))

    def test_a_field_already_recorded_is_never_overwritten(self):
        original = f"---\nsent: 2026-01-01\n---\nBody.\n"
        self.final.write_text(original)
        code, _ = self.run_rs("--confirm")
        self.assertNotEqual(code, 0)
        self.assertEqual(self.final.read_text(), original)

    def test_a_back_office_address_is_refused(self):
        self.final.write_text("Body.\n")
        code, _ = self.run_rs("--confirm", args=["--platform", "email", "--sent", "2026-08-31",
                                                 "--url", "https://app.beehiiv.com/posts/a/analytics"])
        self.assertNotEqual(code, 0)
        self.assertEqual(self.final.read_text(), "Body.\n")

    def test_a_bad_date_is_refused(self):
        self.final.write_text("Body.\n")
        code, _ = self.run_rs("--confirm", args=["--platform", "linkedin", "--url", URL, "--sent", "last week"])
        self.assertNotEqual(code, 0)

    def test_a_write_that_does_not_read_back_resolved_is_put_back(self):
        self.final.write_text("The post.\n")
        real = rs.read_piece
        rs.read_piece = lambda folder: {"state": "unresolved", "reason": "forced", "public_url": None}
        self.addCleanup(setattr, rs, "read_piece", real)
        code, _ = self.run_rs("--confirm")
        self.assertEqual(code, 1)
        self.assertEqual(self.final.read_text(), "The post.\n")

    def test_no_final_md_writes_nothing(self):
        code, _ = self.run_rs("--confirm")
        self.assertNotEqual(code, 0)
        self.assertFalse(self.final.exists())


if __name__ == "__main__":
    unittest.main()
