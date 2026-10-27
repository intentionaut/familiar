"""The critique lint. A flag nobody trusts is noise, so it is tested both ways: each synthetic report it must flag,
each it must leave alone (specific praise, a section heading, a report with no findings), and every way it can
fail to run (a report it cannot read is unknown, never clean).
"""
import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

spec = importlib.util.spec_from_file_location("critique_lint", ROOT / "scripts" / "critique-lint.py")
cl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cl)

CASES = json.loads((ROOT / "tests" / "fixtures" / "critique-cases.json").read_text())["cases"]


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cl.main(argv)
    return code, out.getvalue(), err.getvalue()


def report(d, text):
    p = Path(d) / "dev-edit-report.md"
    p.write_text(text)
    return str(p)


class Cases(unittest.TestCase):
    def test_every_case_both_ways(self):
        self.assertTrue(any(c["want"] == "flag" for c in CASES) and any(c["want"] == "spare" for c in CASES))
        wrong = []
        for c in CASES:
            rules = [f["rule"] for f in cl.check(c["report"])[1]]
            if c["want"] == "flag" and c["rule"] not in rules:
                wrong.append(f"{c['id']}: want {c['rule']}, got {rules}")
            if c["want"] == "spare" and rules:
                wrong.append(f"{c['id']}: want nothing, got {rules}")
        self.assertEqual(wrong, [])

    def test_a_flag_names_its_line_and_where_it_sits(self):
        case = next(c for c in CASES if c["id"] == "praise-opens-a-finding")
        flag = cl.check(case["report"])[1][0]
        self.assertEqual((flag["line"], flag["rule"], flag["where"]), (5, "praise", "finding"))

    def test_findings_are_counted(self):
        case = next(c for c in CASES if c["id"] == "section-heading-is-not-a-finding")
        self.assertEqual(cl.check(case["report"])[0], 1)

    def test_one_line_of_praise_is_one_flag(self):
        flags = cl.check("### 2. Great ending\n\n[line 4] \"Which rota would you keep?\"\nIssue: x\nFix: y\n")[1]
        self.assertEqual([f["rule"] for f in flags], ["praise"])


class Runs(unittest.TestCase):
    def test_flags_exit_zero(self):
        case = next(c for c in CASES if c["id"] == "issue-with-no-quote")
        with tempfile.TemporaryDirectory() as d:
            code, out, _ = run([report(d, case["report"])])
        self.assertEqual(code, 0)
        self.assertIn("unquoted", out)
        self.assertIn("Quote it.", out)

    def test_json(self):
        case = next(c for c in CASES if c["id"] == "issue-with-no-quote")
        with tempfile.TemporaryDirectory() as d:
            f = report(d, case["report"])
            code, out, _ = run([f, "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)[f]["flags"][0]["rule"], "unquoted")

    def test_a_report_with_edit_lines_and_no_finding_heading_is_unknown_not_clean(self):
        with tempfile.TemporaryDirectory() as d:
            code, out, err = run([report(d, "Issue: the middle sags.\nFix: move the example up.\n")])
        self.assertEqual((code, out), (2, ""))
        self.assertIn("unknown, not clean", err)

    def test_a_missing_file_stops(self):
        code, _, err = run(["/nonexistent/report.md"])
        self.assertEqual(code, 2)
        self.assertIn("not found", err)

    def test_nothing_given_stops(self):
        code, _, err = run([])
        self.assertEqual(code, 2)
        self.assertIn("no report given", err)


class Wiring(unittest.TestCase):
    def test_the_edit_stages_name_the_script(self):
        for stage in ("line-edit.md", "dev-edit.md"):
            self.assertIn("scripts/critique-lint.py", (ROOT / "prompts" / stage).read_text(), stage)


if __name__ == "__main__":
    unittest.main()
