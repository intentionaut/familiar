"""The engagement rule, and the memory file it is installed into.

That file is the writer's, it is read at the start of every session, and it
usually holds a great deal Familiar knows nothing about. Everything here is
about not damaging it: no second copy, no explanation installed as an
instruction, no bracket installed as a task, and nothing outside the block
touched on the way in or out.
"""
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import engagement  # noqa: E402

SCRIPT = ROOT / "scripts" / "engagement.py"
TEMPLATE = ROOT / "knowledge" / "engagement.md"

RULE = """Engage me like a trusted chief of staff, not a tool.

- **Keep messages short and plain.** No filler openers, no hype words.
- **Frame offers as systems, not one-offs.**"""


class Rule(unittest.TestCase):
    """What counts as a rule worth installing."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = Path(self.tmp.name) / "knowledge"
        self.cfg.mkdir()
        # knowledge_dir tests positioning.md to decide a folder is a house.
        (self.cfg / "positioning.md").write_text("# mine\n")
        self.memory = Path(self.tmp.name) / "CLAUDE.md"

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, setting="on", rule=RULE):
        text = TEMPLATE.read_text()
        text = text.replace("- Engagement rule: [on / off]",
                            f"- Engagement rule: {setting}")
        text = re.sub(r"^\[Your rule goes here.*\]$", rule, text, flags=re.M)
        (self.cfg / "engagement.md").write_text(text)

    def run_script(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--config", str(self.cfg), *args],
            capture_output=True, text=True)

    # --- what is off ---

    def test_the_shipped_template_is_off(self):
        """A bracket installed into a memory file is read every session as a
        thing to do. The template has to be inert."""
        state, _, _, _ = engagement.read_rule(str(ROOT / "knowledge"))
        self.assertEqual("template", state)

    def test_a_bracket_left_in_the_rule_keeps_it_off(self):
        self.write(setting="on", rule="[still deciding what I want here]")
        out = self.run_script("--install", str(self.memory))
        self.assertEqual(2, out.returncode)
        self.assertFalse(self.memory.exists())

    def test_a_written_rule_switched_off_stays_out(self):
        self.write(setting="off")
        out = self.run_script("--install", str(self.memory))
        self.assertEqual(2, out.returncode)
        self.assertIn("switched off", out.stdout)
        self.assertFalse(self.memory.exists())

    def test_a_missing_file_is_not_a_failure(self):
        out = self.run_script("--install", str(self.memory))
        self.assertEqual(2, out.returncode)

    # --- what is installed ---

    def test_only_the_rule_is_installed(self):
        """The rest of engagement.md explains what the file is for. An
        explanation in a memory file is read as an instruction."""
        self.write()
        self.assertEqual(0, self.run_script("--install", str(self.memory)).returncode)
        got = self.memory.read_text()
        self.assertIn("chief of staff", got)
        self.assertNotIn("## Writing it", got)
        self.assertNotIn("Everything under", got)

    def test_it_keeps_what_was_already_in_the_file(self):
        self.memory.write_text("# Mine\n\nBritish spelling everywhere.\n")
        self.write()
        self.run_script("--install", str(self.memory))
        self.assertIn("British spelling everywhere.", self.memory.read_text())

    def test_running_twice_leaves_one_block(self):
        self.write()
        self.run_script("--install", str(self.memory))
        self.run_script("--install", str(self.memory))
        self.assertEqual(1, self.memory.read_text().count(engagement.START))

    def test_an_edited_rule_replaces_the_block_rather_than_joining_it(self):
        self.write()
        self.run_script("--install", str(self.memory))
        self.write(rule="Say less.")
        self.run_script("--install", str(self.memory))
        got = self.memory.read_text()
        self.assertEqual(1, got.count(engagement.START))
        self.assertIn("Say less.", got)
        self.assertNotIn("chief of staff", got)

    def test_the_block_says_where_to_edit_it(self):
        """Without the pointer, the next person edits the copy, the next setup
        run overwrites the edit, and the rule they changed is the rule they
        had before."""
        self.write()
        self.run_script("--install", str(self.memory))
        self.assertIn("engagement.md", self.memory.read_text())

    def test_a_copy_already_there_by_hand_is_named(self):
        """Pasting it in yourself is the sensible first move and this is the
        second, so the two meeting is the normal case."""
        self.memory.write_text(
            "# Mine\n\nEngage me like a trusted chief of staff, not a tool.\n")
        self.write()
        out = self.run_script("--install", str(self.memory))
        self.assertEqual(0, out.returncode)
        self.assertIn("by hand", out.stdout)

    # --- the surface with no file ---

    def test_copy_prints_the_rule_and_nothing_around_it(self):
        """It is going into a settings box, so the explanation and the heading
        that suit a memory file are both wrong there."""
        self.write()
        out = self.run_script("--copy")
        self.assertEqual(0, out.returncode)
        self.assertIn("chief of staff", out.stdout)
        self.assertNotIn("## Writing it", out.stdout)
        self.assertNotIn(engagement.START, out.stdout)

    def test_copy_says_what_to_do_with_it(self):
        self.write()
        out = self.run_script("--copy")
        self.assertIn("preferences", out.stdout)

    def test_copy_has_nothing_to_copy_from_a_template(self):
        out = subprocess.run(
            [sys.executable, str(SCRIPT), "--config", str(ROOT / "knowledge"), "--copy"],
            capture_output=True, text=True)
        self.assertEqual(2, out.returncode)

    def test_check_names_the_surface_it_cannot_see(self):
        """A surface nobody mentions is a surface somebody assumes is covered."""
        self.write()
        out = self.run_script("--check")
        self.assertIn("no file to read", out.stdout)

    # --- coming back out ---

    def test_remove_takes_the_block_and_nothing_else(self):
        self.memory.write_text("# Mine\n\nBritish spelling everywhere.\n")
        self.write()
        self.run_script("--install", str(self.memory))
        out = subprocess.run([sys.executable, str(SCRIPT), "--remove", str(self.memory)],
                             capture_output=True, text=True)
        self.assertEqual(0, out.returncode)
        got = self.memory.read_text()
        self.assertNotIn(engagement.START, got)
        self.assertIn("British spelling everywhere.", got)

    def test_remove_on_a_file_without_a_block_says_absent(self):
        self.memory.write_text("# Mine\n")
        out = subprocess.run([sys.executable, str(SCRIPT), "--remove", str(self.memory)],
                             capture_output=True, text=True)
        self.assertIn("absent", out.stdout)
        self.assertEqual("# Mine\n", self.memory.read_text())


class SetupAgrees(unittest.TestCase):
    """setup.sh and engagement.py each name the memory files. Two lists kept in
    agreement by memory is how one of them goes stale in silence."""

    def test_every_agent_setup_installs_for_has_the_same_memory_file(self):
        sh = (ROOT / "scripts" / "setup.sh").read_text()
        block = re.search(r"memory_for\(\)\s*\{(.*?)\n\}", sh, re.S)
        self.assertIsNotNone(block, "setup.sh has no memory_for()")
        found = dict(re.findall(r"(\w+)\)\s*echo \"\$HOME/([^\"]+)\"", block.group(1)))
        self.assertEqual(
            {a: f.replace("~/", "") for a, f in engagement.MEMORY_FILES.items()},
            found)

    def test_setup_installs_the_rule_for_each_agent_it_installs_commands_for(self):
        sh = (ROOT / "scripts" / "setup.sh").read_text()
        for agent in engagement.MEMORY_FILES:
            self.assertIn(f"install_engagement {agent}", sh)


if __name__ == "__main__":
    unittest.main()
