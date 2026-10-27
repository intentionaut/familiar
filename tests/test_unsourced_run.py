"""Uniform confidence. A flag nobody trusts is noise, so it is tested both ways: each synthetic run it must flag,
each it must leave alone (hedged, sourced, quoted, hers, too short), and the one way it can fail to run.
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

spec = importlib.util.spec_from_file_location("unsourced_run", ROOT / "scripts" / "unsourced-run.py")
ur = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ur)

CASES = json.loads((ROOT / "tests" / "fixtures" / "unsourced-cases.json").read_text())["cases"]


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = ur.main(argv)
    return code, out.getvalue(), err.getvalue()


def draft(d, text):
    p = Path(d) / "draft.md"
    p.write_text(text)
    return str(p)


class Cases(unittest.TestCase):
    def test_every_case_both_ways(self):
        self.assertTrue(any(c["want"] == "flag" for c in CASES) and any(c["want"] == "spare" for c in CASES))
        wrong = []
        for c in CASES:
            runs = ur.check(c["text"])["runs"]
            if (len(runs) == 1) != (c["want"] == "flag") or (c["want"] == "spare" and runs):
                wrong.append(f"{c['id']}: want {c['want']}, got {len(runs)} runs")
        self.assertEqual(wrong, [])

    def test_a_run_names_its_lines_and_signals(self):
        text = "The kettle broke on Monday.\nShared rotas always fail. Owned rotas never do. Everyone knows this.\n"
        r = ur.check(text)["runs"][0]
        self.assertEqual((r["from_line"], r["to_line"], len(r["sentences"])), (2, 2, 3))
        self.assertEqual(r["sentences"][0]["signals"], ["sweeping"])

    def test_the_run_length_can_change(self):
        text = "Shared rotas always fail. Owned rotas never do.\n"
        self.assertEqual(ur.check(text)["runs"], [])
        self.assertEqual(len(ur.check(text, run=2)["runs"]), 1)

    def test_claims_outside_a_run_are_counted_not_flagged(self):
        res = ur.check("The most useful meeting is the short one.\n")
        self.assertEqual((res["runs"], res["claim_shaped_not_flagged"]), ([], 1))

    def test_frontmatter_is_not_read(self):
        text = '---\ntitle: "Rotas always fail. Owners never do. Everyone knows this."\n---\nA plain line.\n'
        self.assertEqual(ur.check(text)["runs"], [])


class Runs(unittest.TestCase):
    def test_a_flag_exits_zero_and_asks_the_question(self):
        with tempfile.TemporaryDirectory() as d:
            code, out, _ = run([draft(d, CASES[0]["text"])])
        self.assertEqual(code, 0)
        self.assertIn("1 run of 3 or more", out)
        self.assertIn("which of these can she back?", out)

    def test_json(self):
        with tempfile.TemporaryDirectory() as d:
            f = draft(d, CASES[0]["text"])
            code, out, _ = run([f, "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(len(json.loads(out)[f]["runs"]), 1)

    def test_a_missing_file_stops(self):
        code, _, err = run(["/nonexistent/draft.md"])
        self.assertEqual(code, 2)
        self.assertIn("not found", err)

    def test_nothing_given_stops(self):
        code, _, err = run([])
        self.assertEqual(code, 2)
        self.assertIn("no draft given", err)


class Wiring(unittest.TestCase):
    def test_draft_names_the_script(self):
        self.assertIn("scripts/unsourced-run.py", (ROOT / "prompts" / "draft.md").read_text())


if __name__ == "__main__":
    unittest.main()
