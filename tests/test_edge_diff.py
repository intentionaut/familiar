"""The edge diff. A flag nobody trusts is noise, so it is tested both ways: each
synthetic pair it must flag, each it must leave alone, and every way it can
fail to run (a report it cannot read is unknown, never clean).
"""
import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

spec = importlib.util.spec_from_file_location("edge_diff", ROOT / "scripts" / "edge-diff.py")
ed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ed)

CASES = [c for c in json.loads((ROOT / "tests" / "fixtures" / "tell-cases.json").read_text())["cases"]
         if c["check"] == "edge-diff"]

REPORT = '''# Line-edit report

### 1. Contractions

[line 4] "It's late and we don't know."
Issue: formal register
Fix: It is late and we do not know.

### 2. Unsourced

[line 9] "Recent studies show"
Issue: announcing evidence
Fix: name it

### 3. Tighten

**[line 12]** "We kind of ran out of road."
Issue: filler
**Fix:** "We ran out of road."
'''


def run(argv, env=None):
    out, err = io.StringIO(), io.StringIO()
    clean = {k: v for k, v in os.environ.items() if not k.startswith("FAMILIAR_")}
    clean.update(env or {})
    with mock.patch.dict(os.environ, clean, clear=True), \
            mock.patch.object(ed.paths, "read_config", return_value={}), \
            contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = ed.main(argv)
    return code, out.getvalue(), err.getvalue()


def write(d, name, body):
    p = Path(d) / name
    p.write_text(body)
    return str(p)


class Cases(unittest.TestCase):
    def test_every_case_both_ways(self):
        self.assertTrue(any(c["want"] == "flag" for c in CASES) and any(c["want"] == "spare" for c in CASES))
        wrong = []
        for c in CASES:
            rules = [r for r, _ in ed.compare(c["her"], c["proposed"], list(ed.IDIOMS))]
            if (c["rule"] in rules) != (c["want"] == "flag"):
                wrong.append(f"{c['id']}: want {c['want']} {c['rule']}, got {rules}")
        self.assertEqual(wrong, [])

    def test_a_bigger_band_spares_a_length_change(self):
        her, prop = "The meeting ran long.", "The meeting ran long and covered the budget, the rota and the roof."
        self.assertIn("length", [r for r, _ in ed.compare(her, prop, [], 0.3)])
        self.assertNotIn("length", [r for r, _ in ed.compare(her, prop, [], 5.0)])

    def test_curly_apostrophes_count_as_contractions(self):
        self.assertIn("contractions", [r for r, _ in ed.compare("It’s late.", "It is late.", [])])


class Reports(unittest.TestCase):
    def test_pairs_come_from_quote_and_fix(self):
        with tempfile.TemporaryDirectory() as d:
            pairs, instructions, markers = ed.read_report(write(d, "r.md", REPORT))
        self.assertEqual([p["line"] for p in pairs], [4, 12])
        self.assertEqual(pairs[1]["proposed"], "We ran out of road.")
        self.assertEqual((instructions, markers), (1, 3))

    def test_an_instruction_is_counted_not_compared(self):
        with tempfile.TemporaryDirectory() as d:
            code, out, _ = run([write(d, "r.md", REPORT)])
        self.assertEqual(code, 0)
        self.assertIn("pairs read: 2 (1 suggestions had no rewritten line to compare)", out)
        self.assertIn("contractions", out)
        self.assertIn("idiom", out)
        self.assertIn("does she want this cost?", out)

    def test_a_fix_with_no_quoted_line_is_said_not_hidden(self):
        with tempfile.TemporaryDirectory() as d:
            code, out, _ = run([write(d, "r.md", "# Report\n\nFix: It is late.\n")])
        self.assertEqual(code, 0)
        self.assertIn("pairs read: 0 (1 suggestions had no rewritten line to compare)", out)

    def test_a_report_with_markers_and_no_readable_shape_stops(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.object(ed, "read_report", return_value=([], 0, 2)):
                code, _, err = run([write(d, "r.md", "x")])
        self.assertEqual(code, 2)
        self.assertIn("Unknown, not clean", err)

    def test_missing_report_stops(self):
        code, _, err = run(["/nonexistent/report.md"])
        self.assertEqual(code, 2)
        self.assertIn("not found", err)

    def test_nothing_given_stops(self):
        code, _, err = run([])
        self.assertEqual(code, 2)
        self.assertIn("nothing to compare", err)


class Sources(unittest.TestCase):
    def test_pair_flag(self):
        code, out, _ = run(["--pair", "It's late.", "It is late."])
        self.assertEqual(code, 0)
        self.assertIn("contractions", out)

    def test_pairs_file_and_json_output(self):
        with tempfile.TemporaryDirectory() as d:
            f = write(d, "p.json", json.dumps([{"her": "Rain. Again.", "proposed": "It rained again.", "label": "c1"}]))
            code, out, _ = run(["--pairs", f, "--json"])
        self.assertEqual(code, 0)
        flags = json.loads(out)["results"][0]["flags"]
        self.assertEqual([x["rule"] for x in flags], ["fragments"])

    def test_bad_pairs_file_stops(self):
        with tempfile.TemporaryDirectory() as d:
            code, _, err = run(["--pairs", write(d, "p.json", '{"her": 1}')])
        self.assertEqual(code, 2)
        self.assertIn("not a list", err)

    def test_her_idioms_add_to_the_generic_list(self):
        with tempfile.TemporaryDirectory() as d:
            lst = write(d, "idioms.txt", "# mine\n- by the by\n")
            args = ["--pair", "By the by, it ran.", "It ran."]
            self.assertNotIn("idiom", run(args)[1].replace("idioms:", ""))
            code, out, _ = run(args + ["--idioms", lst])
        self.assertIn('idiom  her "by the by" not kept', out)

    def test_a_named_idiom_list_that_is_missing_is_unknown(self):
        code, _, err = run(["--pair", "a", "b"], env={"FAMILIAR_IDIOMS": "/nonexistent/idioms.txt"})
        self.assertEqual(code, 2)
        self.assertIn("unknown, not clean", err)


class Wiring(unittest.TestCase):
    def test_the_edit_stages_name_the_script(self):
        for stage in ("line-edit.md", "dev-edit.md"):
            self.assertIn("scripts/edge-diff.py", (ROOT / "prompts" / stage).read_text(), stage)


if __name__ == "__main__":
    unittest.main()
