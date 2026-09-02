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
COMMANDS_WITHOUT_A_PROMPT = {"board", "doctor"}


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

    def test_the_dex_installer_seeds_every_knowledge_file(self):
        """It must glob knowledge/, never enumerate it.

        Same shape of mistake as the hardcoded adapter list, with a quieter
        failure: a knowledge file missing from the vault means the stage that
        needs it reads the shipped template instead of the writer's house, and
        nothing errors. The output looks like a bad edit rather than a missing
        file, so it gets argued with instead of investigated.
        """
        install = (ROOT / "dex" / "install.sh").read_text()
        self.assertNotIn("for f in positioning.md", install,
                         "dex/install.sh enumerates the knowledge files again, "
                         "so anything added later will not reach a vault.")
        self.assertIn('find . -name "*.md"', install,
                      "dex/install.sh no longer globs knowledge/.")

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

    def test_the_site_lists_every_stage(self):
        """familiar.intentionaut.com is the product page, and its stage list is
        hand-written. A hardcoded list that nobody updates is how `repurpose`
        once shipped without a command; this is the same shape of mistake with
        a slower feedback loop, so it gets the same kind of check."""
        site = ROOT / "site" / "index.html"
        if not site.is_file():
            self.skipTest("no site/ in this checkout")
        listed = set(re.findall(r'class="stage-cmd">familiar ([a-z-]+)',
                                site.read_text()))
        missing = sorted((stems(PROMPTS) - PROMPTS_WITHOUT_A_COMMAND) - listed)
        self.assertEqual([], missing, f"stages missing from the site: {missing}")

    def test_no_prompt_fixes_anything_silently(self):
        """Every edit surfaces a decision; the writer accepts or rejects it.

        The social stage once told an agent to fix mechanical violations
        silently, which made a self-graded one-word field the only quality
        check a post ever got. This is that regression, written broadly enough
        to catch the next prompt that reaches for the same shortcut.
        """
        pattern = re.compile(r"(fix|correct|appl|chang|rewrit)\w*[^.]{0,60}?"
                             r"(silently|quietly|without (?:asking|telling))",
                             re.IGNORECASE)
        offenders = []
        for path in PROMPTS.glob("*.md"):
            # Whole file, whitespace collapsed: the wording this guards against
            # was wrapped across two lines, so a line-by-line search misses it.
            text = " ".join(path.read_text().split())
            found = pattern.search(text)
            if found:
                offenders.append(f"{path.name}: {found.group(0)!r}")
        self.assertEqual([], offenders, f"prompts fixing things silently: {offenders}")

    def test_the_social_gate_runs_the_edit_stage(self):
        """Gate 2 of `social` is where a picked post gets its edit pass.

        Posts shipped for a while with no edit stage at all: `dev-edit` and
        `line-edit` cover a piece, and nothing covered a post. If this gate
        stops naming social-edit, that hole is back.
        """
        social = (PROMPTS / "social.md").read_text()
        self.assertIn("prompts/social-edit.md", social,
                      "the social stage no longer hands gate 2 to social-edit, "
                      "so a picked post reaches the schedule unedited.")
        for name in ("social-rules.md", "style-rules.md"):
            self.assertIn(f"knowledge/{name}",
                          (PROMPTS / "social-edit.md").read_text(),
                          f"social-edit no longer reads {name}")

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
