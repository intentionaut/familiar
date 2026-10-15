"""harvest reads what this prints in place of the digests, so it has to say
exactly what the digest says: every observation word for word, with its dates
and commit ids, and counts that match the history. And it has to tell a digest
it could not read from a project with nothing in it.
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "digest-observations.py"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pd = _load("pd", "project-digest.py")
do = _load("do", "digest-observations.py")

# Tagging goes in and comes out a fortnight later, so the digest carries an
# observation with two dates and two commit ids in it.
PLAN = [("2026-07-01", "start", ""),
        ("2026-07-02", "add tagging", "people asked"),
        ("2026-07-03", "tweak colours", ""),
        ("2026-07-16", "revert tagging", "four tags in two weeks"),
        ("2026-07-16", "fix the index", "")]


def make_repo(tmp, plan=PLAN):
    def g(*a, **k):
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=tmp,
                              capture_output=True, text=True, check=True, env={**os.environ, **k})
    g("init", "-q")
    for i, (day, subject, body) in enumerate(plan):
        Path(tmp, f"f{i}").write_text("x")
        g("add", ".")
        g("commit", "-q", "-m", subject, *(["-m", body] if body else []),
          GIT_AUTHOR_DATE=f"{day}T10:00:00", GIT_COMMITTER_DATE=f"{day}T10:00:00")


def run(*args, env=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True,
                          env={**os.environ, **(env or {})})


class DigestObservations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # One history for the class: the commits are the slow part.
        cls.repo_tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.repo_tmp.cleanup)
        repo = Path(cls.repo_tmp.name, "alpha")
        repo.mkdir()
        make_repo(repo)
        cls.history = pd.history(repo)
        cls.digest_text = pd.digest_repo(repo)[1]

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.digests = Path(self.tmp.name, "digests")
        self.digests.mkdir()
        self.digest = self.digests / "alpha.md"
        self.digest.write_text(self.digest_text, encoding="utf-8")

    def test_observations_are_the_digests_own_lines(self):
        want = [f"{text} ({ev})" for text, ev, _ in pd.observations(self.history)]
        got = do.read_digest(self.digest)
        self.assertEqual("read", got["state"])
        self.assertTrue(want, "the fixture history should yield at least one observation")
        self.assertEqual(want, got["observations"])
        for line in got["observations"]:
            self.assertIn(f"- {line}\n", self.digest.read_text(encoding="utf-8"))

    def test_dates_and_commit_ids_come_through(self):
        undone = [o for o in do.read_digest(self.digest)["observations"] if "was undone" in o]
        self.assertEqual(1, len(undone), undone)
        added, reverted = (c["sha"] for c in self.history["commits"] if "tagging" in c["subject"])
        self.assertIn("(2026-07-02) was undone 14 days later", undone[0])
        self.assertTrue(undone[0].endswith(f"({added} then {reverted})"), undone[0])

    def test_counts_match_the_history(self):
        got = do.read_digest(self.digest)
        self.assertEqual(len(self.history["with_body"]), got["commits_carrying_reasoning"])
        self.assertEqual(len(self.history["turns"]), got["corrections"])
        self.assertEqual((len(self.history["commits"]), "2026-07-01", "2026-07-16"),
                         (got["commits"], got["first"], got["last"]))
        self.assertEqual("alpha", got["project"])

    def test_an_empty_section_is_zero_and_a_missing_one_is_null(self):
        quiet = Path(self.tmp.name, "quiet")
        quiet.mkdir()
        make_repo(quiet, [("2026-07-01", "start", "")])
        path = self.digests / "quiet.md"
        path.write_text(pd.digest_repo(quiet)[1], encoding="utf-8")
        got = do.read_digest(path)
        self.assertEqual(("read", [], 0, 0),
                         (got["state"], got["observations"], got["commits_carrying_reasoning"], got["corrections"]))

        cut = self.digest.read_text(encoding="utf-8")
        cut = cut[:cut.index("## Corrections the messages admit to")] + cut[cut.index("## The history, by day"):]
        path.write_text(cut, encoding="utf-8")
        got = do.read_digest(path)
        self.assertEqual("read", got["state"])
        self.assertIsNone(got["corrections"], "no section to count from is null, never 0")
        self.assertIsNotNone(got["commits_carrying_reasoning"])

    def test_a_file_that_is_not_a_digest_is_unreadable_not_empty(self):
        for name, body in (("notes.md", "# Notes\n\nSome notes.\n"),
                           ("half.md", "# half: what the history says\n\nNo sections here.\n")):
            (self.digests / name).write_text(body, encoding="utf-8")
            got = do.read_digest(self.digests / name)
            self.assertEqual("unreadable", got["state"], name)
            self.assertTrue(got["reason"], name)
            self.assertIsNone(got["observations"], "unknown is not an empty list")
        self.assertEqual("no such file", do.read_digest(self.digests / "gone.md")["reason"])

    def test_the_command_prints_each_line_and_exits_2_on_a_gap(self):
        ok = run(str(self.digests))
        self.assertEqual(0, ok.returncode, ok.stderr)
        self.assertIn("alpha (alpha.md)", ok.stdout)
        for line in do.read_digest(self.digest)["observations"]:
            self.assertIn(f"  - {line}\n", ok.stdout)

        (self.digests / "notes.md").write_text("# Notes\n", encoding="utf-8")
        gap = run(str(self.digests))
        self.assertEqual(2, gap.returncode)
        self.assertIn("notes.md: UNREADABLE", gap.stdout)
        self.assertIn("alpha (alpha.md)", gap.stdout, "one bad file does not hide the good ones")

        data = json.loads(run("--json", str(self.digests)).stdout)
        self.assertEqual("gaps", data["state"])
        self.assertEqual(["read", "unreadable"], [d["state"] for d in data["digests"]])

    def test_the_default_folder_is_the_houses_digests(self):
        house = Path(self.tmp.name, "house")
        house.mkdir()
        (house / "positioning.md").write_text("# Positioning\n", encoding="utf-8")
        env = {"FAMILIAR_KNOWLEDGE": str(house)}
        none = run(env=env)
        self.assertEqual(0, none.returncode, none.stderr)
        self.assertIn("No digests folder", none.stdout)
        self.assertEqual({"dir": str((house / "digests").resolve()), "state": "ok", "digests": []},
                         json.loads(run("--json", env=env).stdout))

        (house / "digests").mkdir()
        (house / "digests" / "alpha.md").write_text(self.digest.read_text(encoding="utf-8"), encoding="utf-8")
        found = run(env=env)
        self.assertEqual(0, found.returncode, found.stderr)
        self.assertTrue(re.match(r"1 digest in .*digests\n", found.stdout), found.stdout)

    def test_it_changes_nothing_on_disk(self):
        def snapshot():
            return {p: (p.stat().st_mtime_ns, p.read_bytes()) for p in sorted(self.digests.rglob("*")) if p.is_file()}
        before = snapshot()
        run(str(self.digests))
        run("--json", str(self.digests))
        self.assertEqual(before, snapshot())


if __name__ == "__main__":
    unittest.main()
