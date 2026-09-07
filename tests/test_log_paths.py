"""A build log that lives outside the project it describes.

A public repository cannot hold a candid build log: it carries defect notes,
hours budgets and plan of record. Gitignoring it leaves one copy on one disk.
So the registry records where the log went, and every reader resolves it the
same way.
"""
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("flog", ROOT / "scripts" / "log.py")
flog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flog)


class ResolveLog(unittest.TestCase):
    def test_a_bare_name_is_inside_the_project(self):
        got = flog.resolve_log(Path("/tmp/proj"), "PROJ-LOG.md")
        self.assertEqual(Path("/tmp/proj/PROJ-LOG.md"), got)

    def test_a_path_is_used_as_it_stands(self):
        got = flog.resolve_log(Path("/tmp/proj"), "/vault/logs/PROJ-LOG.md")
        self.assertEqual(Path("/vault/logs/PROJ-LOG.md"), got)

    def test_a_tilde_path_expands(self):
        got = flog.resolve_log(Path("/tmp/proj"), "~/vault/PROJ-LOG.md")
        self.assertEqual(Path.home() / "vault/PROJ-LOG.md", got)
        self.assertNotIn("~", str(got))

    def test_nothing_recorded_resolves_to_nothing(self):
        self.assertIsNone(flog.resolve_log(Path("/tmp/proj"), None))


class MoveAndFind(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.project = base / "proj"
        self.project.mkdir()
        self.log = self.project / "PROJ-LOG.md"
        self.log.write_text("# proj build log\n\n## 2026-09-04\n\nkept\n")
        self.vault = base / "vault"
        self.vault.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_find_log_accepts_a_recorded_external_path(self):
        moved = self.vault / "PROJ-LOG.md"
        self.log.replace(moved)
        watched = {str(self.project.resolve()): str(moved)}
        self.assertEqual(str(moved), flog.find_log(self.project, watched))

    def test_find_log_ignores_a_recorded_path_that_is_not_there(self):
        watched = {str(self.project.resolve()): "/nowhere/PROJ-LOG.md"}
        # Falls back to what is actually in the folder rather than insisting.
        self.assertEqual("PROJ-LOG.md", flog.find_log(self.project, watched))


class ProjectByName(unittest.TestCase):
    """`add`, `move` and `--path` take the same argument and must read it alike.

    They did not. The first two fell back to the projects root when the target
    was not a directory; `--path` resolved it against the current directory and
    gave up. So `log.py --path intentionaut` answered nothing from anywhere but
    the projects root, silently, because `--path` is called by a hook that has
    to stay quiet in a repo with no log.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "proj").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_bare_name_resolves_against_the_projects_root(self):
        got = flog.project_folder("proj", self.root)
        self.assertEqual((self.root / "proj").resolve(), got)

    def test_a_path_is_taken_as_it_stands(self):
        got = flog.project_folder(str(self.root / "proj"), self.root)
        self.assertEqual((self.root / "proj").resolve(), got)

    def test_a_name_that_is_no_project_resolves_to_nothing(self):
        # None, not an exception: the hook wants silence, a person wants a
        # reason, and which to give is the caller's business.
        self.assertIsNone(flog.project_folder("not-a-project", self.root))


class ExitCode(unittest.TestCase):
    """The exit code is the answer, so it has to be the exit code.

    `main()` returned it and `__main__` dropped it, so every run exited 0 -
    including a `--path` that found nothing. The session-end hook guards on
    `returncode == 0`, which was therefore always true and never guarded
    anything.
    """

    def test_main_is_wired_to_sys_exit(self):
        source = (ROOT / "scripts" / "log.py").read_text()
        self.assertIn("sys.exit(main())", source)

    def test_path_reports_failure_when_there_is_no_log(self):
        with tempfile.TemporaryDirectory() as d:
            out = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "log.py"), "--path", d],
                capture_output=True, text=True,
            )
            self.assertEqual(1, out.returncode)
            self.assertEqual("", out.stdout.strip())


class TheOneTimeAsk(unittest.TestCase):
    """Where build logs go is a setting, asked once.

    Before this, `log add` put the log at the project root and you found out it
    was the wrong place by having a commit refused -- or worse, by not having it
    refused, because a build log carries defect notes and plan of record and a
    public repository is the one place it must not be. The remedy was a second
    command you only knew to run after the mistake.

    So: one question, at the moment the writer has the context to answer it,
    written into the Settings block, and never asked again.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "build-logs.md"
        self.settings.write_text(
            "# Build logs\n\n## Settings\n\n- Projects live in: ~/Projects\n",
            encoding="utf-8")
        self.real = flog.settings_path
        flog.settings_path = lambda: self.settings

    def tearDown(self):
        flog.settings_path = self.real
        self.tmp.cleanup()

    def test_never_answered_reads_as_not_answered(self):
        self.assertIsNone(flog.read_log_home())

    def test_a_template_placeholder_is_not_an_answer(self):
        """The shipped template carries a bracketed placeholder. Reading that
        as a real path is how a writer ends up with logs in a folder called
        [path, or "none"]."""
        for placeholder in ("[a folder]", "[path]", "none", ""):
            self.settings.write_text(
                f"## Settings\n\n- Build logs live in: {placeholder}\n", encoding="utf-8")
            self.assertIsNone(flog.read_log_home(), placeholder)

    def test_the_answer_is_written_beside_the_other_settings(self):
        flog.write_log_home("~/vault/{Project}")
        text = self.settings.read_text()
        self.assertIn("- Build logs live in: ~/vault/{Project}", text)
        # Directly after the setting it belongs with, not appended to the file.
        lines = [l for l in text.splitlines() if l.startswith("- ")]
        self.assertEqual(lines[0], "- Projects live in: ~/Projects")
        self.assertEqual(lines[1], "- Build logs live in: ~/vault/{Project}")

    def test_answering_again_replaces_rather_than_repeats(self):
        flog.write_log_home("~/one/{Project}")
        flog.write_log_home("~/two/{Project}")
        text = self.settings.read_text()
        self.assertEqual(text.count("- Build logs live in:"), 1)
        self.assertIn("~/two/", text)

    def test_it_survives_a_round_trip(self):
        flog.write_log_home("~/vault/{Project}")
        self.assertEqual(flog.read_log_home(), "~/vault/{Project}")

    def test_in_the_project_keeps_the_old_behaviour(self):
        """A bare filename is what resolve_log has always read as "inside the
        project", so choosing that must produce exactly that and not a path."""
        got = flog.log_destination(Path("/x/widget"), "WIDGET-LOG.md", "in the project")
        self.assertEqual(got, "WIDGET-LOG.md")
        self.assertEqual(flog.resolve_log(Path("/x/widget"), got),
                         Path("/x/widget/WIDGET-LOG.md"))

    def test_a_folder_answer_produces_a_path_resolve_log_understands(self):
        got = flog.log_destination(Path("/x/widget"), "WIDGET-LOG.md", "~/vault/{Project}")
        self.assertEqual(flog.resolve_log(Path("/x/widget"), got),
                         Path.home() / "vault/Widget/WIDGET-LOG.md")

    def test_both_project_tokens_are_understood(self):
        """{project} is the folder as it is; {Project} is what a person would
        call it, because a vault folder is read by a human."""
        lower = flog.log_destination(Path("/x/cv-coach"), "L.md", "~/v/{project}")
        upper = flog.log_destination(Path("/x/cv-coach"), "L.md", "~/v/{Project}")
        self.assertIn("/v/cv-coach/", lower)
        self.assertIn("/v/CvCoach/", upper)


class ThingsThatShouldNotNeedAsking(unittest.TestCase):
    """Two steps that were printed as instructions and therefore skipped."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self.tmp.name) / "widget"
        self.folder.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_the_log_block_goes_into_the_project_instructions(self):
        """Skipping the paste is easy and its cost is invisible: the hooks
        still fire at session end, so a log appears and looks fine, while the
        entries written during the work never happen."""
        (self.folder / "CLAUDE.md").write_text("# widget\n", encoding="utf-8")
        wrote = flog.wire_instructions(self.folder, "widget")
        self.assertIsNotNone(wrote)
        text = (self.folder / "CLAUDE.md").read_text()
        self.assertIn("Keep a build log for this project", text)
        self.assertIn("widget-LOG.md", text)
        self.assertNotIn("<PROJECT>", text)

    def test_it_does_not_add_the_block_twice(self):
        (self.folder / "CLAUDE.md").write_text("# widget\n", encoding="utf-8")
        flog.wire_instructions(self.folder, "widget")
        first = (self.folder / "CLAUDE.md").read_text()
        self.assertIsNone(flog.wire_instructions(self.folder, "widget"))
        self.assertEqual(first, (self.folder / "CLAUDE.md").read_text())

    def test_with_no_instructions_file_it_writes_nothing(self):
        self.assertIsNone(flog.wire_instructions(self.folder, "widget"))
        self.assertEqual(list(self.folder.iterdir()), [])

    def test_the_machine_specific_settings_file_is_excluded_locally(self):
        """.git/info/exclude rather than .gitignore: the hook path is this
        machine's, the exclusion needs no commit, and it does not modify a
        tracked file somebody else on the project owns."""
        (self.folder / ".git" / "info").mkdir(parents=True)
        wrote = flog.hide_local_settings(self.folder)
        self.assertIsNotNone(wrote)
        self.assertIn(".claude/settings.json",
                      (self.folder / ".git" / "info" / "exclude").read_text())
        self.assertFalse((self.folder / ".gitignore").exists())

    def test_excluding_twice_does_not_repeat_the_line(self):
        (self.folder / ".git" / "info").mkdir(parents=True)
        flog.hide_local_settings(self.folder)
        self.assertIsNone(flog.hide_local_settings(self.folder))
        text = (self.folder / ".git" / "info" / "exclude").read_text()
        self.assertEqual(text.count(".claude/settings.json"), 1)

    def test_a_project_that_is_not_a_repository_is_not_a_problem(self):
        self.assertIsNone(flog.hide_local_settings(self.folder))


class EveryCommandResolvesTheLogTheSameWay(unittest.TestCase):
    """`log move` writes a ~ path. `log entry` has to be able to read it.

    A recorded value is a bare filename, an absolute path, or a ~ path, and
    resolve_log exists to turn any of the three into a real one. cmd_log_entry
    built `Path(project) / recorded` itself instead, and `Path("/x/proj") /
    "~/vault/L.md"` is `/x/proj/~/vault/L.md`, because a tilde is not absolute.

    So an absolute recorded path worked and a ~ path did not, which is the
    exact form `log move` writes -- the two commands disagreed about what the
    registry means, and the failure looked like a missing project.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "home"
        self.know = self.home / "knowledge"
        self.proj = Path(self.tmp.name) / "Projects" / "widget"
        self.know.mkdir(parents=True)
        self.proj.mkdir(parents=True)
        # knowledge_dir only accepts a candidate that holds positioning.md, so
        # without this the temp house is skipped and the real one answers.
        (self.know / "positioning.md").write_text("# Positioning\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_entry(self, recorded):
        (self.know / "build-logs.md").write_text(
            "# Build logs\n\n## Settings\n\n"
            f"- Projects live in: {self.proj.parent}\n\n"
            "## Watched\n\n"
            f"- `{self.proj}`: `{recorded}`\n", encoding="utf-8")
        env = dict(os.environ, HOME=str(self.home),
                   FAMILIAR_KNOWLEDGE=str(self.know))
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "familiar"),
             "log", "entry", "widget"],
            capture_output=True, text=True, env=env)

    def test_a_tilde_path_is_found(self):
        target = self.home / "vault" / "WIDGET-LOG.md"
        target.parent.mkdir(parents=True)
        target.write_text("# widget build log\n", encoding="utf-8")
        out = self.run_entry("~/vault/WIDGET-LOG.md")
        self.assertIn("2026", out.stdout + out.stderr,
                      msg=f"stdout={out.stdout!r} stderr={out.stderr!r}")
        self.assertIn("**Shipped**", target.read_text())

    def test_a_bare_filename_still_means_inside_the_project(self):
        target = self.proj / "WIDGET-LOG.md"
        target.write_text("# widget build log\n", encoding="utf-8")
        out = self.run_entry("WIDGET-LOG.md")
        self.assertIn("**Shipped**", target.read_text(),
                      msg=f"stdout={out.stdout!r} stderr={out.stderr!r}")


class Quip(unittest.TestCase):
    """One line into today's entry, without stopping.

    The build log's own instructions already say to ask in the moment, because
    the reasoning is gone by session end. This is the other direction: the
    writer volunteering a line without opening a file or filling in five empty
    sections.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.home = root / "home"
        self.know = self.home / "knowledge"
        self.proj = root / "Projects" / "widget"
        self.other = root / "Projects" / "unwatched"
        (self.proj / "sub").mkdir(parents=True)
        self.other.mkdir(parents=True)
        self.know.mkdir(parents=True)
        (self.know / "positioning.md").write_text("# Positioning\n", encoding="utf-8")
        (self.know / "build-logs.md").write_text(
            "# Build logs\n\n## Settings\n\n"
            f"- Projects live in: {self.proj.parent}\n\n"
            "## Watched\n\n"
            f"- `{self.proj}`: `WIDGET-LOG.md`\n", encoding="utf-8")
        self.log = self.proj / "WIDGET-LOG.md"
        self.log.write_text("# widget build log\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def quip(self, *args, cwd=None):
        env = dict(os.environ, HOME=str(self.home), FAMILIAR_KNOWLEDGE=str(self.know))
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "familiar"), "quip", *args],
            capture_output=True, text=True, env=env, cwd=str(cwd or self.proj))

    def test_a_line_lands_under_today(self):
        import datetime
        self.quip("the box-sizing thing was mine")
        text = self.log.read_text()
        self.assertIn(f"## {datetime.date.today().isoformat()}", text)
        self.assertIn("**Quips**", text)
        self.assertIn("- the box-sizing thing was mine", text)

    def test_quips_stay_in_the_order_they_were_said(self):
        """A day read back out of order is a day misremembered."""
        for q in ("first", "second", "third"):
            self.quip(q)
        lines = [l for l in self.log.read_text().splitlines() if l.startswith("- ")]
        self.assertEqual(lines, ["- first", "- second", "- third"])

    def test_the_section_is_not_jammed_against_its_heading(self):
        self.quip("one")
        self.quip("two")
        self.assertNotIn("**Quips**-", self.log.read_text())

    def test_it_works_from_a_subdirectory(self):
        out = self.quip("from below", cwd=self.proj / "sub")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("- from below", self.log.read_text())

    def test_an_unregistered_project_is_refused_not_guessed(self):
        """The bug this test exists for: walking up from the current folder,
        a substring match made ~/Projects match ~/Projects/widget, so a quip
        typed in an unregistered sibling landed in another project's log. A
        note in the wrong log is worse than no note."""
        out = self.quip("should not be filed", cwd=self.other)
        self.assertEqual(out.returncode, 1)
        self.assertIn("No build log registered", out.stdout)
        self.assertNotIn("should not be filed", self.log.read_text())

    def test_it_never_edits_an_earlier_day(self):
        """Append-only. A quip filed under yesterday is a small lie about when
        the thought happened."""
        self.log.write_text(
            "# widget build log\n\n## 2026-01-01\n\n**Shipped**\n- old work\n",
            encoding="utf-8")
        self.quip("today's thought")
        text = self.log.read_text()
        older = text.index("## 2026-01-01")
        self.assertIn("- old work", text)
        self.assertGreater(text.index("- today's thought"), older)
        self.assertNotIn("**Quips**", text[older:text.index("- old work")])

    def test_it_joins_an_entry_that_already_has_sections(self):
        import datetime
        today = datetime.date.today().isoformat()
        self.log.write_text(
            f"# widget build log\n\n## {today}\n\n**Shipped**\n- a thing\n",
            encoding="utf-8")
        self.quip("a thought")
        text = self.log.read_text()
        self.assertEqual(text.count(f"## {today}"), 1)
        self.assertIn("- a thing", text)
        self.assertGreater(text.index("**Quips**"), text.index("**Shipped**"))

    def test_saying_nothing_explains_itself_and_writes_nothing(self):
        before = self.log.read_text()
        out = self.quip()
        self.assertEqual(out.returncode, 1)
        self.assertIn("familiar quip", out.stdout)
        self.assertEqual(before, self.log.read_text())


class EveryCommandReportsWhetherItWorked(unittest.TestCase):
    """A verb that fails has to exit non-zero.

    main() does not return its result -- `__main__` calls it and drops the
    value -- so a dispatch branch that says `return cmd_x(args)` exits 0
    whatever happened. `_finish` is the one that calls sys.exit, and it is also
    what prints the once-per-version line, so an outlier loses both.

    Twelve branches used `_finish` and one used `return`, which is exactly the
    shape that survives review: it reads like the others.
    """

    def dispatch(self):
        src = (ROOT / "scripts" / "familiar").read_text()
        start = src.index("    args = parser.parse_args()")
        return src[start:]

    def test_no_dispatch_branch_drops_its_exit_code(self):
        import re
        bad = re.findall(r"^\s+return (cmd_\w+)\(args\)", self.dispatch(), re.M)
        self.assertEqual(
            bad, [],
            "these exit 0 however they finished, and skip the New in line; "
            f"wrap them in _finish(...): {bad}")

    def test_a_failing_verb_actually_exits_non_zero(self):
        out = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "familiar"), "log"],
            capture_output=True, text=True)
        self.assertEqual(out.returncode, 1, out.stdout + out.stderr)
