"""Kills stay killed, in code. A flag nobody trusts is noise, so the keep cases come first and carry as much weight
as the catches: each synthetic revival it must flag, each near miss it must leave alone (same topic, another claim;
the chosen option; text both options share; a reusable cut; the record itself), and every way it can fail to run.
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

spec = importlib.util.spec_from_file_location("revival_check", ROOT / "scripts" / "revival-check.py")
rc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rc)

CASES = json.loads((ROOT / "tests" / "fixtures" / "revival-cases.json").read_text())["cases"]
RULES_HEAD = "| Date | Rule | Why not, in the writer's words |\n|------|------|------|\n"


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = rc.main(argv)
    return code, out.getvalue(), err.getvalue()


def piece(d, files):
    folder = Path(d) / "piece"
    folder.mkdir(exist_ok=True)
    for name, body in files.items():
        (folder / name).write_text(body)
    return folder


def house(d, rules):
    h = Path(d) / "house"
    h.mkdir(exist_ok=True)
    (h / "rejected-rules.md").write_text(rules)
    return h


def kills_for(d, case):
    kills = []
    if "piece" in case:
        kills, problems = rc.kills_from_piece(piece(d, case["piece"]))
        assert not problems, problems
    if "rules" in case:
        kills += rc.kills_from_rules(house(d, case["rules"]) / "rejected-rules.md")
    return kills


class Cases(unittest.TestCase):
    def test_every_case_both_ways(self):
        self.assertTrue(any(c["want"] == "flag" for c in CASES) and any(c["want"] == "spare" for c in CASES))
        wrong = []
        for c in CASES:
            with tempfile.TemporaryDirectory() as d:
                flags = rc.check(c["output"], kills_for(d, c))
            kinds = [f["kind"] for f in flags]
            if c["want"] == "flag" and c["kind"] not in kinds:
                wrong.append(f"{c['id']}: want {c['kind']}, got {kinds}")
            if c["want"] == "spare" and kinds:
                wrong.append(f"{c['id']}: want nothing, got {kinds}")
        self.assertEqual(wrong, [])

    def test_a_flag_carries_the_kill_and_its_reason(self):
        c = next(c for c in CASES if c["id"] == "dead-cut-reworded")
        with tempfile.TemporaryDirectory() as d:
            f = rc.check(c["output"], kills_for(d, c))[0]
        self.assertEqual((f["kill"], f["why_killed"], f["recorded_in"]),
                         ("The invoice backlog statistic", "the figure was wrong", "cuts.md"))
        self.assertEqual(f["question"], "did the evidence change?")

    def test_a_rejected_option_carries_the_writers_reason(self):
        c = next(c for c in CASES if c["id"] == "rejected-option-revived")
        with tempfile.TemporaryDirectory() as d:
            f = rc.check(c["output"], kills_for(d, c))[0]
        self.assertIn("option A", f["kill"])
        self.assertIn("the claim is the point", f["why_killed"])

    def test_the_line_of_the_revival_is_named(self):
        c = next(c for c in CASES if c["id"] == "dead-cut-reworded")
        with tempfile.TemporaryDirectory() as d:
            f = rc.check("An opening line.\n\n" + c["output"], kills_for(d, c))[0]
        self.assertEqual(f["line"], 3)


class Runs(unittest.TestCase):
    def test_a_revival_is_advice_so_the_exit_is_zero(self):
        c = next(c for c in CASES if c["id"] == "dead-cut-reworded")
        with tempfile.TemporaryDirectory() as d:
            p = piece(d, c["piece"])
            out_file = Path(d) / "dev-edit-report.md"
            out_file.write_text(c["output"])
            code, out, _ = run([str(out_file), "--piece", str(p), "--house", str(house(d, RULES_HEAD))])
        self.assertEqual(code, 0)
        self.assertIn("1 revival", out)
        self.assertIn("did the evidence change?", out)
        self.assertIn("rejected rules:", out)

    def test_json(self):
        c = next(c for c in CASES if c["id"] == "rejected-rule-revived")
        with tempfile.TemporaryDirectory() as d:
            out_file = Path(d) / "proposal.md"
            out_file.write_text(c["output"])
            code, out, _ = run([str(out_file), "--house", str(house(d, c["rules"])), "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["files"][str(out_file)][0]["kind"], "rule")

    def test_the_cuts_record_is_not_checked_as_output(self):
        c = next(c for c in CASES if c["id"] == "dead-cut-reworded")
        with tempfile.TemporaryDirectory() as d:
            p = piece(d, c["piece"])
            code, out, _ = run([str(p / "cuts.md"), "--piece", str(p), "--house", str(house(d, RULES_HEAD))])
        self.assertEqual(code, 0)
        self.assertIn("0 revivals", out)
        self.assertIn("the record of the cuts", out)

    def test_no_piece_says_cuts_were_not_read(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "out.md"
            f.write_text("Nothing here.\n")
            code, out, _ = run([str(f), "--house", str(house(d, RULES_HEAD))])
        self.assertEqual(code, 0)
        self.assertIn("cuts and rejected options not read", out)

    def test_the_shipped_template_is_never_read_as_her_rejections(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "out.md"
            f.write_text("Nothing here.\n")
            shipped = rc.paths.SHIPPED
            orig = rc.paths.knowledge_dir
            rc.paths.knowledge_dir = lambda explicit=None: (shipped, "the shipped templates")
            try:
                code, out, _ = run([str(f)])
            finally:
                rc.paths.knowledge_dir = orig
        self.assertEqual(code, 0)
        self.assertIn("rejected rules: not checked (no house resolved", out)

    def test_a_house_with_no_rejected_rules_file_says_so(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "out.md"
            f.write_text("Nothing here.\n")
            empty = Path(d) / "empty"
            empty.mkdir()
            code, out, _ = run([str(f), "--house", str(empty)])
        self.assertEqual(code, 0)
        self.assertIn("no rejected-rules.md", out)

    def test_a_chosen_line_naming_no_option_is_unknown_not_clean(self):
        bad = {"options.md": "## Option set: x\n\n### A. One\nSome words here.\nChosen: none of them\n"}
        with tempfile.TemporaryDirectory() as d:
            p = piece(d, bad)
            f = Path(d) / "out.md"
            f.write_text("Nothing here.\n")
            code, out, err = run([str(f), "--piece", str(p), "--house", str(house(d, RULES_HEAD))])
        self.assertEqual((code, out), (2, ""))
        self.assertIn("unknown, not clean", err)

    def test_a_missing_file_stops(self):
        code, _, err = run(["/nonexistent/out.md"])
        self.assertEqual(code, 2)
        self.assertIn("not found", err)

    def test_a_missing_piece_stops(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "out.md"
            f.write_text("x\n")
            code, _, err = run([str(f), "--piece", str(Path(d) / "nope")])
        self.assertEqual(code, 2)
        self.assertIn("not found", err)

    def test_nothing_given_stops(self):
        code, _, err = run([])
        self.assertEqual(code, 2)
        self.assertIn("no output given", err)


class Wiring(unittest.TestCase):
    def test_every_stage_that_proposes_names_the_script(self):
        for stage in ("draft.md", "dev-edit.md", "line-edit.md", "social.md", "learn.md"):
            self.assertIn("scripts/revival-check.py", (ROOT / "prompts" / stage).read_text(), stage)


if __name__ == "__main__":
    unittest.main()
