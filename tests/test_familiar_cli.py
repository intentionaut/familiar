"""Tests for the familiar CLI entry point."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "scripts" / "familiar"


class FamiliarCLI(unittest.TestCase):
    def test_help_exits_cleanly(self):
        result = subprocess.run(
            ["python3", str(CLI), "--help"],
            capture_output=True, text=True)
        self.assertEqual(0, result.returncode)
        self.assertIn("familiar", result.stdout)

    def test_new_piece_help(self):
        result = subprocess.run(
            ["python3", str(CLI), "new-piece", "--help"],
            capture_output=True, text=True)
        self.assertEqual(0, result.returncode)
        self.assertIn("slug", result.stdout.lower())

    def test_skill_install_help(self):
        result = subprocess.run(
            ["python3", str(CLI), "skill", "install", "--help"],
            capture_output=True, text=True)
        self.assertEqual(0, result.returncode)
        self.assertIn("agent", result.stdout.lower())

    def test_init_creates_config_and_knowledge(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                ["python3", str(CLI), "init", "--force"],
                capture_output=True, text=True, cwd=tmp,
                env={**os.environ,
                     "FAMILIAR_KNOWLEDGE": "",
                     "FAMILIAR_CONFIG": "",
                     "FAMILIAR_PIECES": ""})
            self.assertEqual(0, result.returncode,
                             f"init failed: {result.stderr}")
            self.assertTrue((Path(tmp) / ".familiar").is_file())
            self.assertTrue((Path(tmp) / "knowledge").is_dir())
            self.assertTrue((Path(tmp) / "pieces").is_dir())
            # Knowledge files should be copied
            self.assertTrue((Path(tmp) / "knowledge" / "positioning.md").is_file())

    def test_new_piece_scaffolds_correctly(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Set up a minimal .familiar
            pieces_dir = Path(tmp) / "pieces"
            pieces_dir.mkdir()
            knowledge_dir = Path(tmp) / "knowledge"
            knowledge_dir.mkdir()
            (knowledge_dir / "positioning.md").write_text("# test\n")
            (Path(tmp) / ".familiar").write_text(
                f"knowledge = {knowledge_dir}\npieces = {pieces_dir}\n")

            result = subprocess.run(
                ["python3", str(CLI), "new-piece", "test-essay"],
                capture_output=True, text=True, cwd=tmp,
                env={**os.environ,
                     "FAMILIAR_KNOWLEDGE": "",
                     "FAMILIAR_CONFIG": "",
                     "FAMILIAR_PIECES": ""})
            self.assertEqual(0, result.returncode,
                             f"new-piece failed: {result.stderr}")
            # Should create a dated folder
            folders = list(pieces_dir.iterdir())
            piece_folders = [f for f in folders if f.is_dir()]
            self.assertEqual(1, len(piece_folders))
            self.assertIn("test-essay", piece_folders[0].name)
            # Should have the right files
            self.assertTrue((piece_folders[0] / "SESSION-CONTEXT.md").is_file())
            self.assertTrue((piece_folders[0] / "notes.md").is_file())
            self.assertTrue((piece_folders[0] / "edits").is_dir())

    def test_new_piece_rejects_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            pieces_dir = Path(tmp) / "pieces"
            pieces_dir.mkdir()
            knowledge_dir = Path(tmp) / "knowledge"
            knowledge_dir.mkdir()
            (knowledge_dir / "positioning.md").write_text("# test\n")
            (Path(tmp) / ".familiar").write_text(
                f"knowledge = {knowledge_dir}\npieces = {pieces_dir}\n")

            env = {**os.environ,
                   "FAMILIAR_KNOWLEDGE": "",
                   "FAMILIAR_CONFIG": "",
                   "FAMILIAR_PIECES": ""}
            # Create once
            subprocess.run(
                ["python3", str(CLI), "new-piece", "dup-test"],
                capture_output=True, text=True, cwd=tmp, env=env)
            # Try again without --force
            result = subprocess.run(
                ["python3", str(CLI), "new-piece", "dup-test"],
                capture_output=True, text=True, cwd=tmp, env=env)
            self.assertNotEqual(0, result.returncode)


if __name__ == "__main__":
    unittest.main()


class HarvestAndInspire(unittest.TestCase):
    """The two commands that feed the harvest stage.

    `inspire` is the only way to create a clip and it raised on every run, so
    the inspirations half of harvest had never worked end to end. `harvest`
    listed the registry with a second parser that matched *-LOG.md only, so a
    log named anything else, which the registry explicitly supports, was
    missing from the list a writer checks before running the stage.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.house = Path(self.tmp.name) / "knowledge"
        self.house.mkdir()
        (self.house / "positioning.md").write_text("# marks this as a house\n")
        self.env = {**os.environ, "FAMILIAR_KNOWLEDGE": str(self.house)}

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args):
        return subprocess.run(["python3", str(CLI), *args],
                              capture_output=True, text=True, env=self.env)

    def test_inspire_clips_without_raising(self):
        r = self.run_cli("inspire", "a line worth keeping", "--url", "https://example.com")
        self.assertEqual(0, r.returncode, r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        clips = list((self.house.parent / "inspirations").glob("*.md"))
        self.assertEqual(1, len(clips), "the clip goes next to the knowledge folder")

    def test_harvest_finds_a_clip_where_inspire_put_it(self):
        self.run_cli("inspire", "a line worth keeping", "--url", "https://example.com")
        r = self.run_cli("harvest")
        self.assertEqual(0, r.returncode, r.stderr)
        self.assertIn("1", r.stdout.split("Inspirations")[-1][:40],
                      "harvest must look where inspire writes")

    def test_harvest_lists_a_log_not_named_LOG(self):
        project = Path(self.tmp.name) / "someproject"
        project.mkdir()
        (project / "PROJECT-PROGRESS.md").write_text("# log\n")
        (self.house / "build-logs.md").write_text(
            "# Build logs\n\n## Settings\n\n"
            f"- Projects live in: {self.tmp.name}\n\n## Watched\n\n"
            f"- `{project}`: `PROJECT-PROGRESS.md`\n")
        r = self.run_cli("harvest")
        self.assertEqual(0, r.returncode, r.stderr)
        self.assertIn("PROJECT-PROGRESS.md", r.stdout,
                      "the registry supports a log called anything at all")

    def test_introduces_the_loops_once(self):
        """First real use says what reflection and session capture are, then never again.

        HOME is pointed at a temp dir so the marker never touches the real one,
        and the knowledge folder is the shipped template, where reflection is
        unset.
        """
        with tempfile.TemporaryDirectory() as home:
            env = {**os.environ, "HOME": home, "FAMILIAR_KNOWLEDGE": str(ROOT / "knowledge")}
            first = subprocess.run(["python3", str(CLI), "reflect"], capture_output=True, text=True, env=env)
            self.assertEqual(0, first.returncode, first.stderr)
            self.assertIn("One thing, once.", first.stdout)
            self.assertTrue((Path(home) / ".familiar" / "introduced").is_file())
            second = subprocess.run(["python3", str(CLI), "reflect"], capture_output=True, text=True, env=env)
            self.assertEqual(0, second.returncode, second.stderr)
            self.assertNotIn("One thing, once.", second.stdout)

    def _repo(self, tmp, commits):
        g = lambda *a: subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a],
                                      cwd=tmp, capture_output=True, text=True, check=True)
        g("init", "-q")
        for i, (subj, body) in enumerate(commits):
            Path(tmp, f"f{i}").write_text("x")
            g("add", ".")
            g("commit", "-q", "-m", subj, *(["-m", body] if body else []))

    def test_bare_familiar_engages_on_the_project_it_stands_in(self):
        """`familiar` with no arguments in a repo reads the history first: the
        engagement line, the commits that carried reasoning, and the digest
        written where the agent looks. The form comes later, and says so."""
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as kn:
            for name in ("positioning.md", "voice-guide.md"):
                (Path(kn) / name).write_text((ROOT / "knowledge" / name).read_text())
            self._repo(tmp, [("start", ""), ("move to sqlite", "Json files corrupted twice."), ("fix: dedupe", "")])
            env = {**os.environ, "HOME": home, "FAMILIAR_KNOWLEDGE": kn, "FAMILIAR_CONFIG": kn}
            r = subprocess.run(["python3", str(CLI)], capture_output=True, text=True, cwd=tmp, env=env)
            self.assertEqual(0, r.returncode, r.stderr)
            name = Path(tmp).resolve().name
            self.assertIn(f"I've engaged on {name}, the project you're working on", r.stdout)
            self.assertIn("move to sqlite", r.stdout)
            self.assertIn("Json files corrupted twice.", r.stdout)
            self.assertIn("fix: dedupe", r.stdout)
            self.assertTrue((Path(kn) / "digests" / f"{name}.md").is_file())
            self.assertEqual(1, r.stdout.count("I'm here watching you work"))
            self.assertNotIn("usage:", r.stdout)
            # The first job is gathering context: the screen ends on what there
            # is to work from and how to gather more, never on a story to pick.
            self.assertIn("What I have to work from:", r.stdout)
            self.assertIn("Projects read        1", r.stdout)
            self.assertIn("familiar engage --all", r.stdout)
            self.assertIn(f"familiar log add {name}", r.stdout)
            self.assertNotIn("worth telling", r.stdout)
            self.assertIn("nothing is drafted until you do", r.stdout)
            # Observations are the tier one repo supports, and a correction is one.
            self.assertIn("Observations, from the history alone:", r.stdout)
            self.assertIn("earlier work", r.stdout)

    def test_bare_familiar_outside_a_repo_falls_back_to_status(self):
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "HOME": home, "FAMILIAR_KNOWLEDGE": str(ROOT / "knowledge"), "FAMILIAR_CONFIG": str(ROOT / "knowledge")}
            r = subprocess.run(["python3", str(CLI)], capture_output=True, text=True, cwd=tmp, env=env)
            self.assertEqual(0, r.returncode, r.stderr)
            self.assertIn("not a git repository", r.stdout)
            self.assertIn("Voice:", r.stdout)

    def test_familiar_does_not_engage_on_its_own_folder(self):
        with tempfile.TemporaryDirectory() as home:
            env = {**os.environ, "HOME": home, "FAMILIAR_KNOWLEDGE": str(ROOT / "knowledge"), "FAMILIAR_CONFIG": str(ROOT / "knowledge")}
            r = subprocess.run(["python3", str(CLI)], capture_output=True, text=True, cwd=ROOT, env=env)
            self.assertEqual(0, r.returncode, r.stderr)
            self.assertIn("Familiar's own folder", r.stdout)
            self.assertNotIn("I've engaged on", r.stdout)

    def test_init_says_the_welcome_once_and_points_at_the_project(self):
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as tmp:
            Path(home, ".claude").mkdir()
            self._repo(tmp, [("start", ""), ("the reason", "Because it was slow.")])
            env = {**os.environ, "HOME": home, "FAMILIAR_KNOWLEDGE": "", "FAMILIAR_CONFIG": "", "FAMILIAR_PIECES": ""}
            r = subprocess.run(["python3", str(CLI), "init", "--force"], capture_output=True, text=True, cwd=tmp, env=env)
            self.assertEqual(0, r.returncode, r.stderr)
            self.assertEqual(1, r.stdout.count("I'm here watching you work"), r.stdout)
            self.assertIn("I've engaged on", r.stdout)
            self.assertIn("Because it was slow.", r.stdout)
            self.assertNotIn("Installing agent commands", r.stdout)
            self.assertNotIn("Three ways in", r.stdout)
            self.assertIn("One thing, once.", r.stdout)

    def test_whats_new_is_said_once_after_an_update_and_never_on_first_install(self):
        with tempfile.TemporaryDirectory() as home:
            env = {**os.environ, "HOME": home, "FAMILIAR_KNOWLEDGE": str(ROOT / "knowledge")}
            first = subprocess.run(["python3", str(CLI), "reflect"], capture_output=True, text=True, env=env)
            self.assertNotIn("New in", first.stdout)
            stamp = Path(home) / ".familiar" / "seen-version"
            self.assertTrue(stamp.is_file())
            stamp.write_text("0.0.1\n")
            second = subprocess.run(["python3", str(CLI), "reflect"], capture_output=True, text=True, env=env)
            self.assertIn("New in", second.stdout)
            third = subprocess.run(["python3", str(CLI), "reflect"], capture_output=True, text=True, env=env)
            self.assertNotIn("New in", third.stdout)

    def test_engage_all_reads_nothing_without_a_yes(self):
        """A folder the writer did not say yes to is never opened. Without a
        terminal to ask in, --all lists what it would read and stops."""
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as kn:
            # The knowledge folder has to look like a house for paths.py to pick
            # it over the shipped templates, and a house has a positioning file.
            for name in ("positioning.md", "voice-guide.md"):
                (Path(kn) / name).write_text((ROOT / "knowledge" / name).read_text())
            (Path(kn) / "build-logs.md").write_text(f"- Projects live in: {root}\n")
            for name in ("alpha", "beta"):
                d = Path(root, name); d.mkdir()
                self._repo(str(d), [("start", ""), ("add x", "why"), ("revert x", "because")])
            env = {**os.environ, "HOME": home, "FAMILIAR_KNOWLEDGE": kn, "FAMILIAR_CONFIG": kn}
            r = subprocess.run(["python3", str(CLI), "engage", "--all"], capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL)
            self.assertEqual(0, r.returncode, r.stderr)
            self.assertIn("2 projects", r.stdout)
            self.assertIn("Nothing read", r.stdout)
            self.assertFalse((Path(kn) / "digests").exists())
            r = subprocess.run(["python3", str(CLI), "engage", "--all", "--yes"], capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL)
            self.assertEqual(0, r.returncode, r.stderr)
            for name in ("alpha", "beta"):
                self.assertTrue((Path(kn) / "digests" / f"{name}.md").is_file())
            self.assertIn("Projects read        2", r.stdout)
            self.assertIn("reverse", r.stdout, "each project shows its top observation")

    def test_help_never_introduces(self):
        with tempfile.TemporaryDirectory() as home:
            env = {**os.environ, "HOME": home}
            result = subprocess.run(["python3", str(CLI), "--help"], capture_output=True, text=True, env=env)
            self.assertNotIn("One thing, once.", result.stdout)
            self.assertFalse((Path(home) / ".familiar" / "introduced").exists())

