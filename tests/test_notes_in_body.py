"""Her wording in the body. A list nobody trusts is noise, so it is tested both ways: each synthetic case
it must list, each it must leave alone, and every way it can fail to run (notes with none of her sentences
are unknown, never clean).
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

spec = importlib.util.spec_from_file_location("notes_in_body", ROOT / "scripts" / "notes-in-body.py")
nb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nb)

CASES = json.loads((ROOT / "tests" / "fixtures" / "notes-cases.json").read_text())["cases"]


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = nb.main(argv)
    return code, out.getvalue(), err.getvalue()


def piece(d, notes, draft):
    (Path(d) / "notes.md").write_text(notes)
    (Path(d) / "draft.md").write_text(draft)
    return d


class Cases(unittest.TestCase):
    def test_every_case_both_ways(self):
        self.assertTrue(any(c["want"] == "flag" for c in CASES) and any(c["want"] == "spare" for c in CASES))
        wrong = []
        for c in CASES:
            got = len(nb.check(c["notes"], c["draft"])["paraphrased"])
            if (got > 0) != (c["want"] == "flag"):
                wrong.append(f"{c['id']}: want {c['want']}, listed {got}")
        self.assertEqual(wrong, [])

    def test_verbatim_and_left_out_are_counted_not_listed(self):
        notes = ("## Working thesis\nThe kettle broke on Monday and nobody told the office.\n"
                 "## Spark candidates\n- Small teams ship faster because nobody waits for a meeting.\n")
        res = nb.check(notes, "The kettle broke on Monday and nobody told the office.\n")
        self.assertEqual((res["checked"], res["verbatim"], res["left_out"], res["paraphrased"]), (2, 1, 1, []))

    def test_the_list_names_both_lines(self):
        c = next(c for c in CASES if c["id"] == "reordered")
        p = nb.check(c["notes"], c["draft"])["paraphrased"][0]
        self.assertEqual((p["notes_line"], p["draft_line"]), (2, 1))
        self.assertIn("kettle", p["hers"])

    def test_frontmatter_in_the_draft_is_not_read(self):
        notes = "## Working thesis\nThe kettle broke on Monday and nobody told the office.\n"
        draft = '---\ntitle: "On Monday the kettle broke and nobody in the office was told"\n---\nNothing else here.\n'
        self.assertEqual(nb.check(notes, draft)["paraphrased"], [])

    def test_sections_can_be_named(self):
        notes = "## In her words\nThe kettle broke on Monday and nobody told the office.\n"
        draft = "On Monday the kettle broke, and nobody in the office was told.\n"
        with self.assertRaises(nb.CannotRun):
            nb.check(notes, draft)
        self.assertEqual(len(nb.check(notes, draft, ["in her words"])["paraphrased"]), 1)


class Runs(unittest.TestCase):
    def test_a_piece_folder_is_read_and_a_list_exits_zero(self):
        c = next(c for c in CASES if c["id"] == "reordered")
        with tempfile.TemporaryDirectory() as d:
            code, out, _ = run([piece(d, c["notes"], c["draft"])])
        self.assertEqual(code, 0)
        self.assertIn("paraphrased: 1", out)
        self.assertIn("put her wording back, or let it go?", out)

    def test_json(self):
        c = next(c for c in CASES if c["id"] == "reordered")
        with tempfile.TemporaryDirectory() as d:
            code, out, _ = run([piece(d, c["notes"], c["draft"]), "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(len(json.loads(out)["paraphrased"]), 1)

    def test_notes_with_none_of_her_sentences_is_unknown_not_clean(self):
        with tempfile.TemporaryDirectory() as d:
            code, out, err = run([piece(d, "## Evidence\n- a bulleted fact about the rota\n", "Some draft text here.\n")])
        self.assertEqual((code, out), (2, ""))
        self.assertIn("unknown, not clean", err)

    def test_a_missing_file_stops(self):
        with tempfile.TemporaryDirectory() as d:
            code, _, err = run([d])
        self.assertEqual(code, 2)
        self.assertIn("not found", err)

    def test_nothing_given_stops(self):
        code, _, err = run([])
        self.assertEqual(code, 2)
        self.assertIn("give a piece folder", err)


class Wiring(unittest.TestCase):
    def test_draft_names_the_script_and_the_rule(self):
        text = (ROOT / "prompts" / "draft.md").read_text()
        self.assertIn("scripts/notes-in-body.py", text)
        self.assertIn("verbatim", text)


if __name__ == "__main__":
    unittest.main()
