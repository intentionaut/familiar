"""Her share. A metric nobody can check is a feeling, so it is tested against invented draft and final pairs with
the counts worked out by hand: a final nodded through from the draft scores zero, a final written over scores
all of it, and the writer-first path measures against the model's rewrites instead of the draft.
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

spec = importlib.util.spec_from_file_location("her_share", ROOT / "scripts" / "her-share.py")
hs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hs)

CASES = json.loads((ROOT / "tests" / "fixtures" / "share-cases.json").read_text())["cases"]


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = hs.main(argv)
    return code, out.getvalue(), err.getvalue()


def piece(base, name, draft, final=None, files=None):
    p = Path(base) / name
    (p / "edits").mkdir(parents=True, exist_ok=True)
    (p / "draft.md").write_text(draft)
    if final is not None:
        (p / "final.md").write_text(final)
    for rel, body in (files or {}).items():
        (p / rel).write_text(body)
    return p


class Cases(unittest.TestCase):
    def test_every_case_has_the_counts_worked_out_by_hand(self):
        wrong = []
        for c in CASES:
            with tempfile.TemporaryDirectory() as d:
                got = hs.measure(piece(d, "2026-10-01-x", c["draft"], c["final"], c.get("files")))
            for k, v in c["want"].items():
                if got[k] != v:
                    wrong.append(f"{c['id']}: {k} want {v}, got {got[k]}")
        self.assertEqual(wrong, [])

    def test_the_share_counting_her_edits_is_shown_beside_it(self):
        c = next(c for c in CASES if c["id"] == "a-mix")
        with tempfile.TemporaryDirectory() as d:
            got = hs.measure(piece(d, "2026-10-01-x", c["draft"], c["final"]))
        self.assertEqual((got["her_share"], got["her_share_with_edits"]), (0.5, 0.75))

    def test_both_ends_are_reached(self):
        shares = []
        for c in CASES[:2]:
            with tempfile.TemporaryDirectory() as d:
                shares.append(hs.measure(piece(d, "2026-10-01-x", c["draft"], c["final"]))["her_share"])
        self.assertEqual(shares, [0.0, 1.0])


class Runs(unittest.TestCase):
    def test_a_piece_report_has_no_gate(self):
        c = next(c for c in CASES if c["id"] == "a-mix")
        with tempfile.TemporaryDirectory() as d:
            code, out, _ = run([str(piece(d, "2026-10-01-x", c["draft"], c["final"]))])
        self.assertEqual(code, 0)
        self.assertIn("her share 50%", out)
        self.assertIn("No gate and no threshold", out)

    def test_json(self):
        c = next(c for c in CASES if c["id"] == "a-mix")
        with tempfile.TemporaryDirectory() as d:
            code, out, _ = run([str(piece(d, "2026-10-01-x", c["draft"], c["final"])), "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["her_share"], 0.5)

    def test_a_piece_with_no_final_is_not_measured_not_zero(self):
        with tempfile.TemporaryDirectory() as d:
            code, out, err = run([str(piece(d, "2026-10-01-x", "The kettle broke on Monday.\n"))])
        self.assertEqual((code, out), (2, ""))
        self.assertIn("no final.md", err)

    def test_a_piece_with_no_draft_stops(self):
        with tempfile.TemporaryDirectory() as d:
            code, _, err = run([d])
        self.assertEqual(code, 2)
        self.assertIn("no draft.md", err)

    def test_nothing_given_stops(self):
        code, _, err = run([])
        self.assertEqual(code, 2)
        self.assertIn("give one piece folder", err)


class Trend(unittest.TestCase):
    def make(self, d):
        a, b, c = CASES[0], CASES[2], CASES[1]
        piece(d, "2026-10-01-first", a["draft"], a["final"])
        piece(d, "2026-10-08-second", b["draft"], b["final"])
        piece(d, "2026-10-15-third", c["draft"], c["final"])
        piece(d, "2026-10-16-unpublished", "The kettle broke on Monday.\n")
        (Path(d) / "README.md").write_text("not a piece")

    def test_pieces_are_listed_oldest_first_with_the_unpublished_named(self):
        with tempfile.TemporaryDirectory() as d:
            self.make(d)
            rows, skipped = hs.trend([d])
        self.assertEqual([r["piece"] for r in rows], ["2026-10-01-first", "2026-10-08-second", "2026-10-15-third"])
        self.assertEqual([r["her_share"] for r in rows], [0.0, 0.5, 1.0])
        self.assertEqual(skipped, ["2026-10-16-unpublished"])

    def test_the_trend_report_gives_numbers_and_no_verdict(self):
        with tempfile.TemporaryDirectory() as d:
            self.make(d)
            code, out, _ = run(["--trend", d])
        self.assertEqual(code, 0)
        self.assertIn("3 pieces measured. Latest 100%; mean of the earlier ones 25%.", out)
        self.assertIn("Not measured, no final.md: 2026-10-16-unpublished", out)
        self.assertIn("No gate and no threshold", out)

    def test_trend_with_nothing_to_measure_says_so(self):
        with tempfile.TemporaryDirectory() as d:
            code, out, _ = run(["--trend", d])
        self.assertEqual(code, 0)
        self.assertIn("No piece has both a draft.md and a final.md yet.", out)

    def test_a_missing_folder_stops(self):
        code, _, err = run(["--trend", "/nonexistent/pieces"])
        self.assertEqual(code, 2)
        self.assertIn("not found", err)


class Wiring(unittest.TestCase):
    def test_learn_reports_the_share_in_diff_mode(self):
        self.assertIn("scripts/her-share.py", (ROOT / "prompts" / "learn.md").read_text())

    def test_draft_offers_the_writer_first_path_and_records_it(self):
        text = (ROOT / "prompts" / "draft.md").read_text()
        self.assertIn("drafted_by: writer", text)
        self.assertIn("writer-first", text)


if __name__ == "__main__":
    unittest.main()
