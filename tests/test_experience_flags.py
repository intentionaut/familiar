"""Provenance for experience and humour. A flag nobody trusts is noise, so it is tested both ways: each synthetic
sentence it must flag, each it must leave alone, and every way it can fail to run (a draft with nothing to
trace against is unknown, never clean).
"""
import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

spec = importlib.util.spec_from_file_location("experience_flags", ROOT / "scripts" / "experience-flags.py")
ef = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ef)

FIX = json.loads((ROOT / "tests" / "fixtures" / "experience-cases.json").read_text())
CASES, NOTES = FIX["cases"], FIX["notes"]
SOURCES = ef.source_sentences(NOTES)


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = ef.main(argv)
    return code, out.getvalue(), err.getvalue()


def piece(d, draft, notes=NOTES, **extra):
    (Path(d) / "draft.md").write_text(draft)
    (Path(d) / "notes.md").write_text(notes)
    for name, body in extra.items():
        (Path(d) / name).write_text(body)
    return d


class Cases(unittest.TestCase):
    def test_every_case_both_ways(self):
        self.assertTrue(any(c["want"] == "flag" for c in CASES) and any(c["want"] == "spare" for c in CASES))
        wrong = []
        for c in CASES:
            flags = ef.check(c["draft"], SOURCES)
            shapes = {s for f in flags for s in f["shapes"]}
            if c["want"] == "flag" and c["shape"] not in shapes:
                wrong.append(f"{c['id']}: want {c['shape']}, got {sorted(shapes)}")
            if c["want"] == "spare" and flags:
                wrong.append(f"{c['id']}: want nothing, got {flags}")
        self.assertEqual(wrong, [])

    def test_a_flag_carries_its_line_and_the_bracket_to_ask(self):
        flags = ef.check("A plain opening.\nI stood in the car park and watched the rain.\n", SOURCES)
        self.assertEqual([(f["line"], f["shapes"]) for f in flags], [(2, ["first-person"])])
        self.assertTrue(flags[0]["ask"].startswith("[ASK THE WRITER:"))

    def test_the_same_sentence_traces_or_not_by_the_notes(self):
        draft = "I stayed late to fix the schedule.\n"
        self.assertEqual(ef.check(draft, SOURCES), [])
        self.assertEqual(len(ef.check(draft, ef.source_sentences("## Evidence\n- Nothing about it here at all.\n"))), 1)


class Runs(unittest.TestCase):
    def test_a_piece_folder_is_read_and_a_flag_exits_zero(self):
        with tempfile.TemporaryDirectory() as d:
            code, out, _ = run([piece(d, "The office smelled of burnt toast all week.\n")])
        self.assertEqual(code, 0)
        self.assertIn("1 sentence with no trace", out)
        self.assertIn("[ASK THE WRITER", out)

    def test_source_md_in_the_folder_is_also_traced_against(self):
        draft = "We argued about the biscuits for an hour.\n"
        with tempfile.TemporaryDirectory() as d:
            self.assertIn("1 sentence", run([piece(d, draft)])[1])
        with tempfile.TemporaryDirectory() as d:
            code, out, _ = run([piece(d, draft, **{"source.md": "We argued about the biscuits for an hour.\n"})])
        self.assertIn("0 sentences", out)
        self.assertIn("source.md", out)

    def test_also_adds_a_source(self):
        with tempfile.TemporaryDirectory() as d:
            extra = Path(d) / "said.md"
            extra.write_text("We argued about the biscuits for an hour.\n")
            code, out, _ = run([piece(d, "We argued about the biscuits for an hour.\n"), "--also", str(extra)])
        self.assertIn("0 sentences", out)

    def test_json(self):
        with tempfile.TemporaryDirectory() as d:
            code, out, _ = run([piece(d, "Spoiler: it did not go well.\n"), "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["flags"][0]["shapes"], ["joke"])

    def test_notes_with_no_sentences_are_unknown_not_clean(self):
        with tempfile.TemporaryDirectory() as d:
            code, out, err = run([piece(d, "I stood in the car park.\n", notes="## Evidence\n")])
        self.assertEqual((code, out), (2, ""))
        self.assertIn("unknown, not clean", err)

    def test_a_missing_file_stops(self):
        with tempfile.TemporaryDirectory() as d:
            code, _, err = run([d])
        self.assertEqual(code, 2)
        self.assertIn("not found", err)

    def test_a_named_source_that_is_missing_stops(self):
        with tempfile.TemporaryDirectory() as d:
            code, _, err = run([piece(d, "x\n"), "--also", str(Path(d) / "nope.md")])
        self.assertEqual(code, 2)
        self.assertIn("nope.md", err)

    def test_nothing_given_stops(self):
        code, _, err = run([])
        self.assertEqual(code, 2)
        self.assertIn("give a piece folder", err)


class Wiring(unittest.TestCase):
    def test_draft_names_the_script_and_the_bracket(self):
        text = (ROOT / "prompts" / "draft.md").read_text()
        self.assertIn("scripts/experience-flags.py", text)


if __name__ == "__main__":
    unittest.main()
