"""Structural invariants for the Familiar repo.

Cheap checks for the class of mistake that has actually shipped: a stage added
without a command, a prompt referenced but never written, a knowledge file named
in a prompt that does not exist. No model, no network, no key. Under a second.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "prompts"
ADAPTERS = ROOT / ".claude" / "commands"

# A prompt run through the skill rather than a slash command.
PROMPTS_WITHOUT_A_COMMAND = {"log"}
# A command backed by a script instead of a prompt.
COMMANDS_WITHOUT_A_PROMPT = {"board"}


def stems(directory):
    return {p.stem for p in directory.glob("*.md")}


def shipped_prose():
    """Prose that ships as the product.

    docs/ is excluded on purpose: those are working design notes, not the
    tool's own voice.
    """
    files = [ROOT / n for n in ("README.md", "CONTRIBUTING.md", "AGENTS.md")]
    for d in ("prompts", "knowledge", "skills", "dex"):
        files += sorted((ROOT / d).rglob("*.md"))
    return [f for f in files if f.exists()]


class Structure(unittest.TestCase):
    def test_every_command_has_a_prompt(self):
        missing = sorted(stems(ADAPTERS) - stems(PROMPTS) - COMMANDS_WITHOUT_A_PROMPT)
        self.assertEqual([], missing, f"commands with no prompt: {missing}")

    def test_every_prompt_has_a_command(self):
        """`repurpose` once shipped with no command. This is that regression."""
        missing = sorted(stems(PROMPTS) - stems(ADAPTERS) - PROMPTS_WITHOUT_A_COMMAND)
        self.assertEqual([], missing, f"prompts with no command: {missing}")

    def test_setup_installs_every_adapter(self):
        """setup.sh must glob the adapters, never enumerate them.

        A hardcoded stage list is exactly how `repurpose` shipped without a
        command: the installer silently skipped a stage added later.
        """
        setup = (ROOT / "scripts" / "setup.sh").read_text()
        self.assertTrue(
            ".claude/commands/*.md" in setup,
            "setup.sh no longer globs the adapters, so a stage added later "
            "will be silently skipped by the installer.")

    def test_adapters_carry_the_home_placeholder(self):
        bad = [p.name for p in ADAPTERS.glob("*.md")
               if "{{FAMILIAR_HOME}}" not in p.read_text()]
        self.assertEqual([], bad, f"adapters missing the home placeholder: {bad}")

    def test_referenced_prompts_exist(self):
        missing = set()
        for f in ROOT.rglob("*.md"):
            if ".git" in f.parts or "pieces" in f.parts:
                continue
            for ref in re.findall(r"prompts/([a-z0-9-]+)\.md", f.read_text()):
                if not (PROMPTS / f"{ref}.md").exists():
                    missing.add(f"{ref}.md in {f.relative_to(ROOT)}")
        self.assertEqual(set(), missing, f"dangling prompt references: {sorted(missing)}")

    def test_referenced_knowledge_files_exist(self):
        missing = set()
        searched = list(PROMPTS.glob("*.md"))
        searched += list((ROOT / "skills").rglob("*.md"))
        searched += list((ROOT / "dex").rglob("*.md"))
        searched += [ROOT / "AGENTS.md"]
        for f in searched:
            for ref in re.findall(r"knowledge/([a-z0-9_/-]+\.md)", f.read_text()):
                if not (ROOT / "knowledge" / ref).exists():
                    missing.add(f"{ref} in {f.relative_to(ROOT)}")
        self.assertEqual(set(), missing, f"dangling knowledge references: {sorted(missing)}")

    def test_referenced_scripts_exist(self):
        missing = set()
        for f in list(PROMPTS.glob("*.md")) + list((ROOT / "skills").rglob("*.md")):
            for ref in re.findall(r"scripts/([a-z0-9_.-]+)", f.read_text()):
                if not (ROOT / "scripts" / ref).exists():
                    missing.add(f"{ref} in {f.relative_to(ROOT)}")
        self.assertEqual(set(), missing, f"dangling script references: {sorted(missing)}")

    def test_the_skill_lists_every_stage(self):
        """The skill's table is how a stage is discovered. A stage missing from
        it exists but is invisible."""
        skill = (ROOT / "skills" / "familiar" / "SKILL.md").read_text()
        listed = set(re.findall(r"`prompts/([a-z0-9-]+)\.md`", skill))
        missing = sorted((stems(PROMPTS) - PROMPTS_WITHOUT_A_COMMAND) - listed)
        self.assertEqual([], missing, f"stages absent from the skill's table: {missing}")

    def test_no_em_dashes_in_shipped_prose(self):
        """Familiar's own first style rule bans them, so its prose must obey.

        style-rules.md is exempt on the one line that states the rule and has
        to name the character to do so.
        """
        offenders = []
        for path in shipped_prose():
            rel = str(path.relative_to(ROOT))
            for i, line in enumerate(path.read_text().splitlines(), 1):
                if "—" in line or "―" in line:
                    if rel == "knowledge/style-rules.md" and "No em dashes" in line:
                        continue
                    offenders.append(f"{rel}:{i}")
        self.assertEqual([], offenders, f"em dashes in shipped prose: {offenders}")


if __name__ == "__main__":
    unittest.main()
