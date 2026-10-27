"""The SessionStart check-in hook is silent by design: hooks/session-checkin.sh
sends its stderr to /dev/null and puts its stdout into the session. These tests
pin what each failure does (nothing, exit 0), and one happy path so the silence
tests cannot pass on a hook that is simply broken."""
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "checkin.py"
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("checkin", SCRIPT)
checkin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checkin)

DUE_SETTINGS = "# Check-in\n\n- Check-in: on\n- Cadence: weekly\n"


def make_house(tmp):
    house = Path(tmp) / "house"
    house.mkdir()
    (house / "positioning.md").write_text("# Positioning\n")
    (house / "checkin.md").write_text(DUE_SETTINGS)
    return house


def make_repo(tmp):
    repo = Path(tmp) / "work"
    repo.mkdir()
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com"]
    subprocess.run(git + ["init", "-q"], cwd=repo, check=True)
    subprocess.run(git + ["commit", "-q", "--allow-empty", "-m", "first"], cwd=repo, check=True)
    return repo


def run_hook(tmp, *, stdin, house=None, path=None):
    """Run `checkin.py hook` the way the shell hook does. Returns (stdout, stderr, code)."""
    env = {"PATH": path if path is not None else os.environ.get("PATH", ""),
           "HOME": str(Path(tmp) / "home")}
    if house is not None:
        env["FAMILIAR_KNOWLEDGE"] = str(house)
    r = subprocess.run([sys.executable, str(SCRIPT), "hook"], input=stdin, env=env,
                       cwd=tmp, capture_output=True, text=True)
    return r.stdout, r.stderr, r.returncode


class HookIsSilent(unittest.TestCase):
    def test_bad_stdin_prints_nothing_and_exits_0(self):
        with tempfile.TemporaryDirectory() as tmp:
            out, err, code = run_hook(tmp, stdin="{not json")
        self.assertEqual(("", "", 0), (out, err, code))

    def test_valid_json_that_is_not_an_object_prints_nothing_and_exits_0(self):
        # Issue 389: payload.get raised AttributeError on [] and exited 1.
        for stdin in ("[]", "null", "3", '"cwd"', "[{\"cwd\": \"/\"}]", '{"cwd": 5}', '{"cwd": ["/"]}'):
            with self.subTest(stdin=stdin), tempfile.TemporaryDirectory() as tmp:
                out, err, code = run_hook(tmp, stdin=stdin)
            self.assertEqual(("", "", 0), (out, err, code))

    def test_no_house_prints_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            out, err, code = run_hook(tmp, stdin=json.dumps({"cwd": str(repo)}))
        self.assertEqual(("", "", 0), (out, err, code))

    def test_a_git_failure_prints_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            house = make_house(tmp)
            empty = Path(tmp) / "empty-path"
            empty.mkdir()
            out, err, code = run_hook(tmp, stdin=json.dumps({"cwd": str(repo)}),
                                      house=house, path=str(empty))
        self.assertEqual(("", "", 0), (out, err, code))

    def test_closed_stdout_does_not_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            house = make_house(tmp)
            stdin = io.StringIO(json.dumps({"cwd": str(repo)}))
            cwd = os.getcwd()
            try:
                with mock.patch.object(sys, "stdin", stdin), \
                     mock.patch("paths.knowledge_dir", return_value=(house, "yours")), \
                     mock.patch("builtins.print", side_effect=BrokenPipeError):
                    self.assertIsNone(checkin.cmd_hook())
            finally:
                os.chdir(cwd)


class HookSpeaksWhenDue(unittest.TestCase):
    def test_a_due_offer_prints_one_json_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            house = make_house(tmp)
            out, err, code = run_hook(tmp, stdin=json.dumps({"cwd": str(repo)}), house=house)
        self.assertEqual((0, ""), (code, err))
        lines = out.strip().splitlines()
        self.assertEqual(1, len(lines))
        payload = json.loads(lines[0])["hookSpecificOutput"]
        self.assertEqual("SessionStart", payload["hookEventName"])
        self.assertIn("work", payload["additionalContext"])


if __name__ == "__main__":
    unittest.main()
