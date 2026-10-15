"""The mechanical tell check. A flag nobody reads is noise and a list that silently
loads nothing passes every draft, so it is tested both ways: each synthetic case
it must flag, and each it must leave alone, and every way it can fail to run.
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

spec = importlib.util.spec_from_file_location("tell_check", ROOT / "scripts" / "tell-check.py")
tc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tc)

RULES = ROOT / "knowledge" / "style-rules.md"
CASES = json.loads((ROOT / "tests" / "fixtures" / "tell-cases.json").read_text())["cases"]


def kill_file(d, body):
    p = Path(d) / "killed.md"
    p.write_text(body if "## " in body else "## Killed\n\n" + body + "\n")
    return p


def run(argv, env=None):
    out, err = io.StringIO(), io.StringIO()
    clean = {k: v for k, v in os.environ.items() if not k.startswith("FAMILIAR_")}
    clean.update(env or {})
    with mock.patch.dict(os.environ, clean, clear=True), \
            mock.patch.object(tc.paths, "read_config", return_value={}), \
            contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = tc.main(argv)
    return code, out.getvalue(), err.getvalue()


class Cases(unittest.TestCase):
    def setUp(self):
        self.rules = tc.read_rules(RULES)

    def flags_for(self, case):
        kills = None
        if "kills" in case:
            with tempfile.TemporaryDirectory() as d:
                kills = tc.read_kills(kill_file(d, case["kills"]))
        return tc.check(case["text"], self.rules, kills)

    def test_every_case_both_ways(self):
        cases = [c for c in CASES if c["check"] == "tell-check"]
        self.assertTrue(any(c["want"] == "flag" for c in cases) and any(c["want"] == "spare" for c in cases))
        wrong = []
        for c in cases:
            rules = [f["rule"] for f in self.flags_for(c)]
            hit = c["rule"] in rules if c["rule"] != "kill" else any(r.startswith("kill") for r in rules)
            if (c["want"] == "flag") != hit:
                wrong.append(f"{c['id']}: wanted {c['want']} on {c['rule']}, got {rules}")
        self.assertEqual([], wrong)

    def test_a_flag_names_its_line_and_asks(self):
        flags = tc.check("Fine.\n\nWe delve in.", self.rules, None)
        self.assertEqual([3], [f["line"] for f in flags])
        self.assertIn("earn its place", flags[0]["why"])

    def test_a_span_named_twice_is_one_flag_under_the_kill(self):
        with tempfile.TemporaryDirectory() as d:
            kills = tc.read_kills(kill_file(d, "- phrase `tell the story` : test."))
        flags = tc.check("This will tell the story.", self.rules, kills)
        self.assertEqual(["kill"], [f["rule"] for f in flags])


class ReadsTheHouse(unittest.TestCase):
    def test_a_phrase_added_to_the_rules_is_checked_with_no_code_change(self):
        text = RULES.read_text().replace('"Let\'s dive in",', '"Let\'s dive in", "zorbly wibble",', 1)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "style-rules.md"
            p.write_text(text)
            rules = tc.read_rules(p)
        self.assertIn("rule 4", [f["rule"] for f in tc.check("A zorbly wibble start.", rules, None)])

    def test_rules_that_lost_a_pattern_stop_the_run(self):
        for broken in (RULES.read_text().replace("## AI-tell patterns to flag", "## Patterns"),
                       RULES.read_text().replace("12. **Overused AI words.**", "**Overused AI words.**"),
                       RULES.read_text().replace("### Familiar's own tells", "### Other tells")):
            with tempfile.TemporaryDirectory() as d:
                p = Path(d) / "style-rules.md"
                p.write_text(broken)
                with self.assertRaises(tc.CannotRun):
                    tc.read_rules(p)


class Runs(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        (self.d / "knowledge").mkdir()
        (self.d / "knowledge" / "positioning.md").write_text("# Positioning\n")
        self.draft = self.d / "draft.md"
        self.draft.write_text("We delve in.\n")
        self.env = {"FAMILIAR_KNOWLEDGE": str(self.d / "knowledge")}

    def tearDown(self):
        self.tmp.cleanup()

    def test_flags_are_advice_so_the_exit_is_zero(self):
        code, out, _ = run(["--rules", str(RULES), str(self.draft)], self.env)
        self.assertEqual(0, code)
        self.assertIn("delve", out)

    def test_no_kill_list_set_says_not_checked(self):
        code, out, _ = run(["--rules", str(RULES), str(self.draft)], self.env)
        self.assertEqual(0, code)
        self.assertIn("kills: not checked", out)

    def test_a_kill_list_in_the_knowledge_folder_is_read(self):
        kill_file(self.d / "knowledge", "- phrase `we delve` : test.")
        code, out, _ = run(["--rules", str(RULES), str(self.draft)], self.env)
        self.assertEqual(0, code)
        self.assertIn("(1 read)", out)

    def test_a_named_kill_list_that_is_missing_is_unknown(self):
        for argv, env in ((["--kills", str(self.d / "nope.md")], {}),
                          ([], {"FAMILIAR_KILLS": str(self.d / "nope.md")})):
            code, out, err = run(["--rules", str(RULES), *argv, str(self.draft)], {**self.env, **env})
            self.assertEqual(2, code)
            self.assertIn("unknown, not clean", err)
            self.assertEqual("", out)

    def test_a_kill_line_that_will_not_load_stops_the_run(self):
        for body in ("- phrase delve without backticks", "- pattern bad `(` : test."):
            p = kill_file(self.d, body)
            code, _, err = run(["--rules", str(RULES), "--kills", str(p), str(self.draft)], self.env)
            self.assertEqual(2, code, body)
            self.assertIn("killed.md:3", err)

    def test_a_missing_draft_or_rules_file_stops_the_run(self):
        self.assertEqual(2, run(["--rules", str(RULES), str(self.d / "nope.md")], self.env)[0])
        self.assertEqual(2, run(["--rules", str(self.d / "nope.md"), str(self.draft)], self.env)[0])

    def test_json_carries_what_was_read(self):
        code, out, _ = run(["--rules", str(RULES), "--json", str(self.draft)], self.env)
        report = json.loads(out)
        self.assertEqual(0, code)
        self.assertFalse(report["kills"]["read"])
        self.assertGreater(report["rules"]["phrases"], 50)
        self.assertEqual(["rule 12"], [f["rule"] for f in report["files"][str(self.draft)]])


class Wired(unittest.TestCase):
    def test_the_stages_that_sweep_for_tells_run_it(self):
        """A check nothing calls is a check that never runs."""
        for stage in ("draft.md", "line-edit.md"):
            self.assertIn("scripts/tell-check.py", (ROOT / "prompts" / stage).read_text(), stage)


if __name__ == "__main__":
    unittest.main()
