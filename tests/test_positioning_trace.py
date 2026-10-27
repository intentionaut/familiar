"""Claim trace for a positioning one-pager (#563). Report only, so a wrong report is the failure: a line that
traces must not be called untraced, a quoted line must not be read at all, and a mis-cited line must not pass.
Keep-cases come first. Synthetic text only; no real positioning, buyer or source.
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

spec = importlib.util.spec_from_file_location("positioning_trace", ROOT / "scripts" / "positioning-trace.py")
pt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pt)

FIX = json.loads((ROOT / "tests" / "fixtures" / "positioning-cases.json").read_text())
CASES, ANCHOR = FIX["cases"], FIX["anchor"]
SOURCES = {i: pt.ef.source_sentences(t) for i, t in FIX["sources"].items()}


def status_of(line, anchor=None):
    rows, _ = pt.check(line + "\n", SOURCES, anchor)
    return rows[0]["status"] if rows else "unread"


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = pt.main(argv)
    return code, out.getvalue(), err.getvalue()


def files(d, onepager):
    d = Path(d)
    (d / "one.md").write_text(onepager)
    args = [str(d / "one.md")]
    for i, t in FIX["sources"].items():
        (d / f"{i}.md").write_text(t)
        args += ["--source", f"{i}={d / f'{i}.md'}"]
    return args


def cases(want):
    return [c for c in CASES if c["want"] == want]


class KeepCases(unittest.TestCase):
    def test_a_fully_traced_line_passes(self):
        wrong = [c["id"] for c in cases("traced") if status_of(c["line"]) != "traced"]
        self.assertEqual(wrong, [])
        self.assertTrue(cases("traced"))

    def test_a_traced_line_quotes_its_source(self):
        rows, _ = pt.check("The studio cut onboarding from 14 days to 5 days. [src: S1]\n", SOURCES)
        self.assertEqual(rows[0]["quote"], {"S1": "The studio cut onboarding from 14 days to 5 days."})

    def test_a_quoted_or_set_apart_line_is_not_read(self):
        wrong = [c["id"] for c in cases("unread") if status_of(c["line"]) != "unread"]
        self.assertEqual(wrong, [])
        self.assertTrue(cases("unread"))

    def test_the_one_pager_is_byte_for_byte_the_same_after_a_run(self):
        text = "# Title\n\n\"A quote, 40 days.\"\nThe studio cut onboarding from 14 days to 3 days. [src: S1]\nEvery client doubled revenue.\n"
        with tempfile.TemporaryDirectory() as d:
            args = files(d, text)
            before = Path(args[0]).read_bytes()
            self.assertEqual(run(args)[0], 0)
            self.assertEqual(run(args + ["--json"])[0], 0)
            self.assertEqual(Path(args[0]).read_bytes(), before)

    def test_a_partly_quoted_line_is_read_without_the_quotation(self):
        rows, _ = pt.check('The studio said "unmatched speed" and cut onboarding from 14 days to 5 days. [src: S1]\n', SOURCES)
        self.assertNotIn("unmatched", rows[0]["sentence"])

    def test_a_mixed_one_pager_is_each_line_its_own_status(self):
        text = "\n".join(c["line"] for c in CASES) + "\n"
        rows, _ = pt.check(text, SOURCES)
        self.assertEqual([r["status"] for r in rows],
                         [c["want"] for c in CASES if c["want"] != "unread"])


class Untraced(unittest.TestCase):
    def test_a_line_with_no_citation_is_untraced(self):
        wrong = [c["id"] for c in cases("untraced") if status_of(c["line"]) != "untraced"]
        self.assertEqual(wrong, [])

    def test_an_untraced_line_says_which_source_holds_it(self):
        rows, _ = pt.check("The studio cut onboarding from 14 days to 5 days.\n", SOURCES)
        self.assertEqual(list(rows[0]["could_cite"]), ["S1"])

    def test_an_invented_line_has_no_could_cite(self):
        rows, _ = pt.check("Every client doubled revenue in a year.\n", SOURCES)
        self.assertNotIn("could_cite", rows[0])


class MisCited(unittest.TestCase):
    def test_every_way_to_cite_wrongly_is_mis_cited(self):
        wrong = [c["id"] for c in cases("mis-cited") if status_of(c["line"]) != "mis-cited"]
        self.assertEqual(wrong, [])
        self.assertGreaterEqual(len(cases("mis-cited")), 5)

    def test_a_differing_figure_is_not_held_by_the_source(self):
        rows, _ = pt.check("The studio cut onboarding from 14 days to 3 days. [src: S1]\n", SOURCES)
        self.assertEqual(rows[0]["status"], "mis-cited")
        self.assertIn("does not say this", rows[0]["why"])

    def test_the_right_source_under_the_wrong_id_is_named(self):
        rows, _ = pt.check("The studio cut onboarding from 14 days to 5 days. [src: S2]\n", SOURCES)
        self.assertEqual(list(rows[0]["could_cite"]), ["S1"])

    def test_an_unknown_id_is_named(self):
        rows, _ = pt.check("The studio cut onboarding from 14 days to 5 days. [src: S9]\n", SOURCES)
        self.assertIn("S9, which was not given", rows[0]["why"])


class Anchor(unittest.TestCase):
    def test_a_line_that_shares_words_is_linked(self):
        rows, _ = pt.check("Teams make better bets once a real product problem is solved. [src: S1]\n", SOURCES, ANCHOR)
        self.assertTrue(rows[0]["anchor"])

    def test_a_line_that_shares_none_is_marked_and_not_changed(self):
        rows, _ = pt.check("The pilot ran with 12 teams. [src: S2]\n", SOURCES, ANCHOR)
        self.assertFalse(rows[0]["anchor"])
        self.assertEqual(rows[0]["status"], "traced")

    def test_no_anchor_no_key(self):
        rows, _ = pt.check("The pilot ran with 12 teams. [src: S2]\n", SOURCES)
        self.assertNotIn("anchor", rows[0])


class Runs(unittest.TestCase):
    def test_text_report_counts_and_exits_zero(self):
        text = "The studio cut onboarding from 14 days to 5 days. [src: S1]\nEvery client doubled revenue in a year.\n"
        with tempfile.TemporaryDirectory() as d:
            code, out, _ = run(files(d, text))
        self.assertEqual(code, 0)
        self.assertIn("2 lines read: 1 traced, 1 untraced, 0 mis-cited", out)
        self.assertIn("the one-pager is untouched", out)

    def test_json(self):
        with tempfile.TemporaryDirectory() as d:
            code, out, _ = run(files(d, "Every client doubled revenue in a year.\n") + ["--json"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["lines"][0]["status"], "untraced")

    def test_sources_dir_uses_the_stem_as_id(self):
        with tempfile.TemporaryDirectory() as d:
            one = Path(d) / "one.md"
            one.write_text("The studio cut onboarding from 14 days to 5 days. [src: S1]\n")
            src = Path(d) / "sources"
            src.mkdir()
            for i, t in FIX["sources"].items():
                (src / f"{i}.md").write_text(t)
            code, out, _ = run([str(one), "--sources-dir", str(src)])
        self.assertIn("1 traced", out)

    def test_anchor_flag_marks_lines(self):
        with tempfile.TemporaryDirectory() as d:
            a = Path(d) / "anchor.md"
            a.write_text(ANCHOR)
            code, out, _ = run(files(d, "The pilot ran with 12 teams. [src: S2]\n") + ["--anchor", str(a)])
        self.assertIn("shares no words with the buyer-belief line", out)


class CannotRun(unittest.TestCase):
    def test_no_sources_is_unknown(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "one.md"
            p.write_text("Every client doubled revenue.\n")
            code, out, err = run([str(p)])
        self.assertEqual((code, out), (2, ""))
        self.assertIn("at least one --source", err)

    def test_an_empty_source_is_unknown_not_clean(self):
        with tempfile.TemporaryDirectory() as d:
            args = files(d, "Every client doubled revenue.\n")
            Path(d, "S2.md").write_text("## Heading only\n")
            code, out, err = run(args)
        self.assertEqual((code, out), (2, ""))
        self.assertIn("unknown, not clean", err)

    def test_a_one_pager_with_nothing_to_read_is_unknown_not_clean(self):
        with tempfile.TemporaryDirectory() as d:
            code, out, err = run(files(d, "# Title\n\n\"All quoted, 40 days.\"\n"))
        self.assertEqual((code, out), (2, ""))
        self.assertIn("unknown, not clean", err)

    def test_missing_files_stop(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(run([str(Path(d) / "nope.md"), "--source", "S1=x"])[0], 2)
            args = files(d, "Every client doubled revenue.\n")
            code, _, err = run(args + ["--source", f"S3={Path(d) / 'gone.md'}"])
        self.assertEqual(code, 2)
        self.assertIn("gone.md", err)

    def test_a_bad_source_pair_stops(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "one.md"
            p.write_text("x y z w\n")
            code, _, err = run([str(p), "--source", "nonsense"])
        self.assertEqual(code, 2)
        self.assertIn("ID=FILE", err)

    def test_nothing_given_stops(self):
        code, _, err = run([])
        self.assertEqual(code, 2)
        self.assertIn("give the one-pager", err)


if __name__ == "__main__":
    unittest.main()
