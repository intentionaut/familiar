"""Capture: what reaches a build log, where it goes, and what survives the trip.

No model is called and no real transcript is read: every session here is built
in the test.
"""
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("ble", ROOT / "scripts" / "build_log_entry.py")
ble = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ble)
import log as flog  # noqa: E402


def line(role, content):
    return json.dumps({"type": role, "message": {"content": content}})


class Turns(unittest.TestCase):
    def test_a_subagent_report_is_kept_long_and_a_routine_result_is_not(self):
        report, dump = "R" * 3000, "D" * 3000
        lines = [
            line("assistant", [{"type": "tool_use", "id": "t1", "name": "Agent",
                                "input": {"description": "audit"}},
                               {"type": "tool_use", "id": "t2", "name": "Read",
                                "input": {"file_path": "/tmp/x.py"}}]),
            line("user", [{"type": "tool_result", "tool_use_id": "t1", "content": report},
                          {"type": "tool_result", "tool_use_id": "t2", "content": dump}]),
        ]
        text = "\n".join(ble.turns_from(lines))
        self.assertIn("R" * 2500, text)
        self.assertNotIn("D" * 300, text)

    def test_an_error_keeps_more_than_a_result(self):
        lines = [line("user", [{"type": "tool_result", "tool_use_id": "e", "is_error": True,
                                "content": "E" * 500}])]
        self.assertIn("E" * 350, "\n".join(ble.turns_from(lines)))

    def test_system_reminders_and_meta_are_left_out(self):
        lines = [line("user", "<system-reminder>ignore me</system-reminder>"),
                 json.dumps({"type": "user", "isMeta": True, "message": {"content": "meta"}}),
                 line("user", "real words")]
        self.assertEqual(["### USER\nreal words"], ble.turns_from(lines))


class LongSessions(unittest.TestCase):
    def test_a_short_session_is_one_call_with_no_notes(self):
        prompt = ble.build_prompt(["### USER\nhi"], "tail", "## H", False,
                                  call=lambda p: self.fail("should not summarise"))
        self.assertNotIn("NOTES FROM EARLIER", prompt)
        self.assertIn("### USER\nhi", prompt)

    def test_a_long_session_is_summarised_rather_than_truncated(self):
        turns = ["### USER\nwhy I did it"] + ["### ASSISTANT\n" + "y" * 130_000] * 2
        calls = []
        prompt = ble.build_prompt(turns, "tail", "## H", False,
                                  call=lambda p: calls.append(p) or "earlier notes")
        self.assertEqual(2, len(calls))
        self.assertIn("why I did it", calls[0])
        self.assertIn("earlier notes", prompt)

    def test_the_writers_words_survive_when_the_notes_call_fails(self):
        turns = ["### USER\nthe box thing was mine"] + ["### ASSISTANT\n" + "y" * 130_000]

        def boom(_):
            raise RuntimeError("no model")
        prompt = ble.build_prompt(turns, "tail", "## H", False, call=boom)
        self.assertIn("the box thing was mine", prompt)

    def test_a_cross_project_log_says_so_in_the_rules(self):
        self.assertIn("covers several projects",
                      ble.build_prompt(["### USER\nx"], "t", "## H", True))
        self.assertNotIn("covers several projects",
                         ble.build_prompt(["### USER\nx"], "t", "## H", False))

    def test_the_format_asks_for_quips_verbatim(self):
        self.assertIn("**Quips**", ble.build_prompt(["### USER\nx"], "t", "## H", False))


class Routing(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.root = self.base / "Projects"
        (self.root / "alpha").mkdir(parents=True)
        (self.root / "beta").mkdir()
        self.alpha_log = self.root / "alpha" / "ALPHA-LOG.md"
        self.alpha_log.write_text("# alpha\n")
        self.cross = self.base / "CROSS-LOG.md"
        self.cross.write_text("# cross\n")
        self.watched = {str(self.root / "alpha"): "ALPHA-LOG.md"}

    def route(self, cwd, touched=()):
        return flog.route(cwd, list(touched), self.root, self.watched, self.cross)

    def test_the_sessions_own_project_wins(self):
        log, why = self.route(self.root / "alpha")
        self.assertEqual(self.alpha_log, log)
        self.assertIn("alpha", why)

    def test_a_subfolder_still_finds_the_project(self):
        sub = self.root / "alpha" / "scripts" / "deep"
        sub.mkdir(parents=True)
        self.assertEqual(self.alpha_log, self.route(sub)[0])

    def test_a_session_elsewhere_goes_where_it_mostly_worked(self):
        touched = [str(self.root / "alpha" / f) for f in ("a", "b", "c")] + [str(self.root / "beta" / "z")]
        for f in touched:
            Path(f).write_text("x")
        log, why = self.route(self.base, touched)
        self.assertEqual(self.alpha_log, log)
        self.assertIn("mostly alpha", why)

    def test_a_session_spread_across_projects_goes_to_the_cross_project_log(self):
        touched = [str(self.root / "alpha" / "a"), str(self.root / "beta" / "b")]
        for f in touched:
            Path(f).write_text("x")
        log, why = self.route(self.base, touched)
        self.assertEqual(self.cross, log)
        self.assertIn("cross-project", why)

    def test_no_cross_project_log_means_nothing_is_written(self):
        log, why = flog.route(self.base, [], self.root, self.watched, None)
        self.assertIsNone(log)
        self.assertIn("no cross-project log", why)

    def test_the_registry_setting_is_read_and_a_placeholder_is_not(self):
        self.assertIsNone(flog.cross_project_log("- Cross-project log: [path, or \"none\"]"))
        self.assertIsNone(flog.cross_project_log("- Cross-project log: none"))
        self.assertEqual(Path.home() / "x/CROSS.md",
                         flog.cross_project_log("- Cross-project log: ~/x/CROSS.md"))


class Paths(unittest.TestCase):
    def test_paths_are_taken_from_tool_inputs(self):
        lines = [json.dumps({"x": 1, "file_path": "/Users/x/p/a.py"}),
                 '{"input": {"command": "grep -n foo /Users/x/p/b.py"}}']
        found = ble.paths_touched(lines)
        self.assertIn("/Users/x/p/a.py", found)
        self.assertIn("/Users/x/p/b.py", found)


if __name__ == "__main__":
    unittest.main()
