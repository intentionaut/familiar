"""The list of questions waiting on the writer, and recording an answer.

A gate that cannot be found is a piece that does not move, so the finding side
has to be right about which pieces are holding a question. Recording has to be
right about the words: `learn decisions` reads these for the reasoning, and a
paraphrase is worth nothing to it.
"""
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "scripts" / "familiar"

spec = importlib.util.spec_from_file_location("decisions", ROOT / "scripts" / "decisions.py")
dec = importlib.util.module_from_spec(spec)

ENTRY = """## 2026-09-02 10:40  bring  {name}

Status: waiting on the writer
Files: source.md (new)
What changed: mapped what is there.
Decision gate: {gate}
Next stage: interview, when asked.
"""


class Gates(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.pieces = Path(self.tmp.name) / "pieces"
        self.pieces.mkdir()
        self._env = {k: os.environ.pop(k, None)
                     for k in ("FAMILIAR_PIECES", "FAMILIAR_KNOWLEDGE", "FAMILIAR_CONFIG")}
        spec.loader.exec_module(dec)
        # Point the module at one folder. Not via FAMILIAR_PIECES: that adds to
        # the configured folders rather than replacing them, so a test setting
        # it would still read whatever this machine's writer has in flight.
        dec.pieces_dirs = lambda: [self.pieces]

    def tearDown(self):
        os.environ.pop("FAMILIAR_PIECES", None)
        for k, v in self._env.items():
            if v:
                os.environ[k] = v
        self.tmp.cleanup()

    def piece(self, name, gate="Is this the argument you meant?", sent=False):
        p = self.pieces / name
        p.mkdir()
        (p / "SESSION-CONTEXT.md").write_text(ENTRY.format(name=name, gate=gate))
        if sent:
            (p / "final.md").write_text("sent\n")
        return p

    def test_an_open_gate_is_found(self):
        self.piece("2026-09-02-one")
        gates = dec.open_gates()
        self.assertEqual(1, len(gates))
        self.assertEqual("Is this the argument you meant?", gates[0]["gate"])

    def test_a_sent_piece_is_not_waiting_on_anyone(self):
        self.piece("2026-09-02-sent", sent=True)
        self.assertEqual([], dec.open_gates())

    def test_a_stage_saying_it_needs_nothing_is_not_a_gate(self):
        self.piece("2026-09-02-clear", gate="none. Title was already settled")
        self.assertEqual([], dec.open_gates())

    def test_an_answer_is_recorded_in_the_writers_words(self):
        p = self.piece("2026-09-02-two")
        dec.cmd_answer("two", "The three-part frame was the plan, keep it")
        text = (p / "SESSION-CONTEXT.md").read_text()
        self.assertIn("Answer: The three-part frame was the plan, keep it", text)
        self.assertIn("Gate: Is this the argument you meant?", text)

    def test_recording_does_not_advance_the_piece(self):
        p = self.piece("2026-09-02-three")
        dec.cmd_answer("three", "yes")
        text = (p / "SESSION-CONTEXT.md").read_text()
        self.assertIn("no stage was run", text)
        self.assertEqual([], [f for f in p.iterdir() if f.name.startswith("draft")])

    def test_an_ambiguous_slug_refuses_rather_than_guesses(self):
        self.piece("2026-09-02-alpha-note")
        self.piece("2026-09-02-alpha-essay")
        self.assertEqual(1, dec.cmd_answer("alpha", "yes"))

    def test_the_cli_reaches_it(self):
        self.piece("2026-09-02-four")
        r = subprocess.run([sys.executable, str(CLI), "decisions"],
                           capture_output=True, text=True,
                           env={**os.environ, "FAMILIAR_PIECES": str(self.pieces)})
        self.assertEqual(0, r.returncode, r.stderr)
        self.assertIn("2026-09-02-four", r.stdout)


if __name__ == "__main__":
    unittest.main()
