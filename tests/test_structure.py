"""Structural invariants for the Familiar repo.

Cheap checks for the class of mistake that has actually shipped: a stage added
without a command, a prompt referenced but never written, a knowledge file named
in a prompt that does not exist. No model, no network, no key. Under a second.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
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
    tool's own voice. knowledge/private/ and knowledge/proposals/ are excluded
    because neither ships: the first is the writer's own material, kept out of
    git, and the second is what learn proposes before anyone has accepted it.
    Holding either to the house style would mean a writer's private notes
    could fail this repo's tests.
    """
    files = [ROOT / n for n in ("README.md", "CONTRIBUTING.md", "AGENTS.md")]
    for d in ("prompts", "knowledge", "skills", "dex"):
        files += sorted((ROOT / d).rglob("*.md"))
    unshipped = (ROOT / "knowledge" / "private", ROOT / "knowledge" / "proposals")
    return [
        f for f in files
        if f.exists() and not any(f.is_relative_to(u) for u in unshipped)
    ]


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

    def test_the_share_card_says_what_the_page_says(self):
        """A pasted link is read in a feed, so it carries the hook, not the
        search title.

        The two are allowed to differ and do so on purpose. What they may not
        do is drift: og:title and twitter:title must match the h1, so someone
        arriving from a shared link lands on the line they clicked. <title>
        keeps the category words and is deliberately not checked against them.
        """
        site = ROOT / "site" / "index.html"
        if not site.is_file():
            self.skipTest("no site/ in this checkout")
        text = site.read_text()

        h1 = re.search(r"<h1>(.*?)</h1>", text, re.S)
        self.assertIsNotNone(h1, "the front page has no h1")
        heading = re.sub(r"<[^>]+>", "", h1.group(1)).strip()

        for prop in ('property="og:title"', 'name="twitter:title"'):
            m = re.search(prop + r' content="([^"]*)"', text)
            self.assertIsNotNone(m, f"{prop} is missing")
            self.assertEqual(heading, m.group(1),
                             f"{prop} no longer matches the h1. Either the "
                             f"heading changed without the share card, or the "
                             f"two were merged back together.")

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

    def test_plugin_commands_up_to_date(self):
        """commands/ is generated from .claude/commands/ by build-plugin.py.

        It is committed so the plugin needs no build step, which means it can
        be committed stale. Two sets of the same commands drifting apart is
        the failure this catches: the adapter gets a fix and the plugin keeps
        shipping the old wording.
        """
        out = ROOT / "commands"
        self.assertTrue(out.is_dir(),
                        "commands/ is missing. Run scripts/build-plugin.py")
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "build-plugin.py"), "--check"],
            capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_plugin_commands_carry_no_unresolved_placeholders(self):
        """A shipped command must not still say {{FAMILIAR_HOME}}.

        setup.sh substitutes those at install time. A plugin has no install
        step, so anything left behind reaches the writer as literal braces.
        """
        offenders = []
        for path in (ROOT / "commands").glob("*.md"):
            if "{{" in path.read_text():
                offenders.append(path.name)
        self.assertEqual([], offenders,
                         f"unsubstituted placeholders in commands/: {offenders}")

    def test_plugin_manifests_name_the_same_plugin(self):
        """The marketplace entry and the plugin manifest have to agree.

        They are two files a person edits by hand, and a mismatch fails at
        install time with a message about a plugin nobody has heard of.
        """
        manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
        market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
        names = [p["name"] for p in market["plugins"]]
        self.assertIn(manifest["name"], names,
                      f"plugin.json is '{manifest['name']}', marketplace lists {names}")
        for plugin in market["plugins"]:
            self.assertIn("source", plugin, f"{plugin['name']} has no source")

    WRITING_STAGES = ("draft", "dev-edit", "line-edit")
    SEARCH_MARKERS = ("themes.md", "target quer", "already ranks for", "## search")

    def test_writing_stages_never_read_themes_or_search(self):
        """No query reaches a sentence.

        themes.md carries a Search section for finalise. The stages that write
        or edit prose must not know it exists, or the writing starts bending
        toward what ranks. Cheap to hold, and the only thing keeping this from
        becoming an SEO tool.
        """
        offenders = []
        for stem in self.WRITING_STAGES:
            text = (PROMPTS / f"{stem}.md").read_text().lower()
            for marker in self.SEARCH_MARKERS:
                if marker in text:
                    offenders.append(f"{stem}.md mentions {marker!r}")
        self.assertEqual([], offenders, f"writing stages touching search: {offenders}")

    def test_themes_template_keeps_search_quarantined(self):
        """The theme block carries no query field; those live under ## Search."""
        text = (ROOT / "knowledge" / "themes.md").read_text()
        self.assertIn("\n## Search\n", text)
        body, _, search = text.partition("\n## Search\n")
        for field in ("Target queries", "Already ranks for"):
            self.assertNotIn(field, body, f"{field} sits in the theme block, not under ## Search")
            self.assertIn(field, search)
        self.assertIn("Written for:", body)
        self.assertNotIn("Serves:", body)

    def test_doctor_reads_the_template_as_unset(self):
        """The shipped reflection.md says "[on / off]"; that is neither."""
        out = subprocess.run([sys.executable, str(ROOT / "scripts" / "doctor.py"), "--config", str(ROOT / "knowledge")],
                             capture_output=True, text=True).stdout
        self.assertIn("Reflection: template", out)
        self.assertNotIn("Reflection: on", out)

    def _doctor(self, home, url):
        env = {**os.environ, "HOME": home, "FAMILIAR_UPDATE_URL": url, "FAMILIAR_KNOWLEDGE": str(ROOT / "knowledge")}
        return subprocess.run([sys.executable, str(ROOT / "scripts" / "doctor.py")],
                              capture_output=True, text=True, env=env).stdout

    def test_update_check_is_off_by_default(self):
        """The shipped updates.md is the template, and the template is off."""
        with tempfile.TemporaryDirectory() as home:
            out = self._doctor(home, "file:///nonexistent")
            self.assertNotIn("Update:", out)
            self.assertFalse((Path(home) / ".familiar" / "update-check").exists())

    def test_update_check_reads_a_page_says_unknown_and_caches_for_the_day(self):
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as kn:
            for name in ("positioning.md", "voice-guide.md"):
                shutil.copy(ROOT / "knowledge" / name, Path(kn) / name)
            (Path(kn) / "updates.md").write_text("- Update check: on\n")
            page = Path(home) / "releases.html"
            page.write_text('<h2 id="v9-9-9">9.9.9</h2>')
            env = {**os.environ, "HOME": home, "FAMILIAR_UPDATE_URL": page.as_uri(), "FAMILIAR_KNOWLEDGE": kn}
            run = lambda: subprocess.run([sys.executable, str(ROOT / "scripts" / "doctor.py")], capture_output=True, text=True, env=env).stdout
            self.assertIn("Update: 9.9.9 is out", run())
            stamp = Path(home) / ".familiar" / "update-check"
            self.assertTrue(stamp.is_file())
            # Same day: the cached answer is reprinted and the page is not read again.
            page.unlink()
            self.assertIn("Update: 9.9.9 is out", run())
            # A stale stamp with an unreachable page says unknown, never current,
            # and the failure is not written back as the day's answer.
            stamp.write_text("2000-01-01 9.9.9\n")
            self.assertIn("Update: unknown", run())
            self.assertEqual("2000-01-01 9.9.9", stamp.read_text().strip())

    def test_nothing_asks_the_writer_which_stage(self):
        """A writer should never be asked to name a stage or a mode.

        Familiar records where every piece is and can read it. The one
        question it may ask is about the writer's material or which piece.
        """
        offenders = []
        for path in list(PROMPTS.glob("*.md")) + list((ROOT / "skills").rglob("*.md")) + list((ROOT / "dex").rglob("*.md")):
            text = path.read_text().lower()
            for phrase in ("ask which stage", "ask which mode", "ask which one", "which stage are you", "what stage are you"):
                if phrase in text:
                    offenders.append(f"{path.relative_to(ROOT)}: {phrase!r}")
        self.assertEqual([], offenders, f"asks the writer to name a stage: {offenders}")

    def test_project_digest_reads_a_history(self):
        """Three commits in, three commits out, with the sections a brief needs."""
        with tempfile.TemporaryDirectory() as tmp:
            g = lambda *a: subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=tmp, capture_output=True, text=True, check=True)
            g("init", "-q")
            for i, (subj, body) in enumerate([("start", ""), ("add the thing", "Because the other way was wrong."), ("fix: it broke", "")]):
                Path(tmp, f"f{i}").write_text("x")
                g("add", ".")
                g("commit", "-q", "-m", subj, *(["-m", body] if body else []))
            out = subprocess.run([sys.executable, str(ROOT / "scripts" / "project-digest.py"), tmp], capture_output=True, text=True)
            self.assertEqual(0, out.returncode, out.stderr)
            self.assertIn("3 commits", out.stdout)
            for section in ("## The days that stand out", "## Where the work went", "## Commits that carried reasoning", "## Corrections the messages admit to", "## The history, by day"):
                self.assertIn(section, out.stdout)
            self.assertIn("Because the other way was wrong.", out.stdout)
            self.assertIn("fix: it broke", out.stdout.split("## Corrections the messages admit to")[1])

    def test_project_digest_all_writes_one_file_per_repo(self):
        with tempfile.TemporaryDirectory() as root:
            for name in ("alpha", "beta"):
                d = Path(root, name); d.mkdir()
                subprocess.run(["git", "init", "-q"], cwd=d, check=True)
                Path(d, "f").write_text("x")
                subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "add", "."], cwd=d, check=True)
                subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", f"first {name}"], cwd=d, check=True)
            Path(root, "notarepo").mkdir()
            out_dir = Path(root, "out")
            res = subprocess.run([sys.executable, str(ROOT / "scripts" / "project-digest.py"), "--all", root, str(out_dir)], capture_output=True, text=True)
            self.assertEqual(0, res.returncode, res.stderr)
            self.assertEqual({"alpha.md", "beta.md"}, {p.name for p in out_dir.iterdir()})
            self.assertIn("2 projects", res.stdout)

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
