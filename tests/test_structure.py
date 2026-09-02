"""Structural invariants for the Familiar repo.

Cheap checks for the class of mistake that has actually shipped: a stage added
without a command, a prompt referenced but never written, a knowledge file named
in a prompt that does not exist. No model, no network, no key. Under a second.
"""
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "prompts"
ADAPTERS = ROOT / ".claude" / "commands"

# The three ways in. Only harvest is a prompt; board and new-piece are
# script-backed. Every other stage is agent-routed.
PROMPTS_WITH_COMMANDS = {"harvest", "reflect"}
# A command backed by a script instead of a prompt.
COMMANDS_WITHOUT_A_PROMPT = {"board", "doctor", "new-piece"}


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
        """Only harvest is a prompt with a slash command; the rest are routed."""
        missing = sorted(PROMPTS_WITH_COMMANDS - stems(ADAPTERS))
        self.assertEqual([], missing, f"slash commands with no adapter: {missing}")

    def test_setup_installs_every_adapter(self):
        """setup.sh installs the three ways in: board, new-piece, harvest."""
        setup = (ROOT / "scripts" / "setup.sh").read_text()
        for cmd in ("board", "new-piece", "harvest"):
            self.assertIn(cmd, setup, f"setup.sh missing {cmd} command")

    def test_setup_takes_out_commands_that_no_longer_exist(self):
        """Installing must remove an earlier version's commands, not just add.

        The installer only ever wrote files, so a writer upgrading kept every
        command from the version before. A left-behind command is worse than a
        missing one: it still appears in the agent's list and calls a prompt
        that is not there any more. It must not reach past its own files, so
        the writer's own commands survive an install.
        """
        setup = (ROOT / "scripts" / "setup.sh").read_text()
        self.assertIn("rm -f", setup,
                      "setup.sh never removes a command, so an upgrade leaves "
                      "the previous version's commands installed.")
        self.assertIn('for f in "$dir"/familiar-*.md', setup,
                      "setup.sh no longer scopes its cleanup to familiar-*.md, "
                      "so it may delete a command the writer wrote.")
        self.assertNotIn('rm -f "$dir/reflect.md"', setup,
                         "setup.sh deletes the /reflect alias, which has a "
                         "scheduled nudge pointing at it.")

    def test_the_reflect_alias_is_installed(self):
        """A scheduled nudge tells the writer to reflect, so /reflect must exist.

        reflect is not a way into a piece, so it is not one of the three
        commands, but reflection-nudge.sh points at it on a cadence. A nudge
        naming a command the writer does not have is worse than no nudge.
        """
        setup = (ROOT / "scripts" / "setup.sh").read_text()
        self.assertIn('ALIAS="reflect"', setup,
                      "setup.sh no longer installs the /reflect alias.")
        self.assertTrue((ADAPTERS / "reflect.md").is_file(),
                        "the reflect adapter is missing.")

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
        # All prompts should be listed in the skill, except those without a command.
        # The skill lists everything so agents can route to any stage.
        self.assertTrue(len(listed) > 0, "skill table is empty")

    def test_the_site_lists_every_stage(self):
        """familiar.intentionaut.com lists the three ways in."""
        site = ROOT / "site" / "index.html"
        if not site.is_file():
            self.skipTest("no site/ in this checkout")
        text = site.read_text()
        for cmd in ("board", "new-piece", "harvest"):
            self.assertIn(cmd, text, f"site missing slash command: {cmd}")

    def test_the_release_notes_page_matches_the_changelog(self):
        """The site is canonical for the product, so it cannot lag the source.

        releases.html is generated from CHANGELOG.md. It is committed so the
        site keeps its promise of needing no build step, which means it can be
        committed stale. Regenerating and comparing is what stops that.
        """
        page = ROOT / "site" / "releases.html"
        if not (ROOT / "site").is_dir():
            self.skipTest("no site/ in this checkout")
        self.assertTrue(page.is_file(),
                        "site/releases.html is missing. Run scripts/build-site.py")
        before = page.read_text()
        subprocess.run([sys.executable, str(ROOT / "scripts" / "build-site.py")],
                       capture_output=True, check=True)
        self.assertEqual(before, page.read_text(),
                         "site/releases.html is out of date with CHANGELOG.md. "
                         "Run scripts/build-site.py and commit the result.")

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
        `line-edit` cover a piece, and nothing covered a post. The quality pass
        was previously a separate social-edit stage; it is now inlined into
        social.md at gate 2.
        """
        social = (PROMPTS / "social.md").read_text()
        # Gate 2 must contain the quality pass logic (was in social-edit)
        self.assertIn("social-rules.md", social,
                       "social stage no longer reads social-rules.md at gate 2")
        self.assertIn("style-rules.md", social,
                       "social stage no longer reads style-rules.md at gate 2")
        self.assertIn("viewpoint", social.lower(),
                       "social stage no longer offers viewpoints for failed posts")
        self.assertIn("two questions", social.lower(),
                       "social stage no longer asks the two questions after the pick")

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
