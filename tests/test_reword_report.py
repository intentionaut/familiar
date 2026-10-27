"""The reword change report. Report only, so it is tested both ways: each synthetic draft it must call red or amber,
each it must call green, and every way it can fail to run (an unreadable file is unknown, never clean).
Synthetic text only.
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

spec = importlib.util.spec_from_file_location("reword_report", ROOT / "scripts" / "reword-report.py")
rr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rr)

SRC = ("The rota changed in March and nobody told the night team. "
       "Handover notes were two lines long, so the gaps grew. "
       "The fix could take six weeks and cost 4,000 pounds. "
       "She said \"we will not do this again\" at the review.")


def rules(rep):
    return sorted({f["rule"] for f in rep["flags"]})


class Green(unittest.TestCase):
    def test_identical_text_is_green_at_every_tier(self):
        for t in (1, 2, 3, 4):
            rep = rr.check(SRC, SRC, t)
            self.assertEqual((rep["status"], rep["kept_percent"], rep["flags"]), ("green", 100, []), t)

    def test_punctuation_and_case_fixes_are_not_word_changes(self):
        rep = rr.check(SRC, SRC.replace("The rota", "the rota").replace("long, so", "long so"), 2)
        self.assertEqual(rep["status"], "green")

    def test_a_small_light_edit_stays_inside_tier_two(self):
        long_src = "Handover notes were two lines long so the gaps kept growing across every single team on the rota."
        rep = rr.check(long_src, long_src.replace("every single team", "every team"), 2)
        self.assertNotIn("over-limit", rules(rep))


PARA = ("The rota changed in March and nobody told the night team. "
        "Handover notes were two lines long, so the gaps grew. "
        "Cover was thin on Fridays and the early shift ran short. "
        "Nobody owned the weekend list and it went stale.")


class EditCap(unittest.TestCase):
    """Per-paragraph edit cap: three edits for the first run (#639). An edit is a changed or added sentence."""

    def test_four_edits_in_one_paragraph_is_amber(self):
        d = (PARA.replace("changed in March", "moved in March").replace("two lines long", "very short")
             .replace("thin on Fridays", "low on Fridays").replace("went stale", "went out of date"))
        rep = rr.check(PARA, d, 3)
        self.assertIn("edit-cap", rules(rep))

    def test_three_edits_is_inside_the_cap(self):
        d = (PARA.replace("changed in March", "moved in March").replace("two lines long", "very short")
             .replace("thin on Fridays", "low on Fridays"))
        self.assertNotIn("edit-cap", rules(rr.check(PARA, d, 3)))

    def test_the_cap_is_per_paragraph_not_per_text(self):
        src = PARA + "\n\n" + PARA
        one = (PARA.replace("changed in March", "moved in March").replace("two lines long", "very short")
               .replace("thin on Fridays", "low on Fridays"))
        self.assertNotIn("edit-cap", rules(rr.check(src, one + "\n\n" + one, 3)))

    def test_identical_text_never_trips_it(self):
        self.assertNotIn("edit-cap", rules(rr.check(PARA, PARA, 3)))


class Amber(unittest.TestCase):
    def test_a_rewrite_passes_the_tier_two_limit(self):
        rep = rr.check(SRC, SRC.replace("two lines long", "brief"), 2)
        self.assertIn("over-limit", rules(rep))
        self.assertEqual(rep["status"], "amber")

    def test_the_same_rewrite_is_allowed_at_tier_three_but_marked(self):
        rep = rr.check(SRC, SRC.replace("two lines long", "brief"), 3)
        self.assertNotIn("over-limit", rules(rep))
        self.assertEqual((rep["status"], rules(rep)), ("amber", ["reworked"]))

    def test_a_dropped_hedge_is_flagged(self):
        rep = rr.check(SRC, SRC.replace("could take", "takes"), 2)
        self.assertIn("modal-changed", rules(rep))

    def test_a_cut_sentence_is_listed(self):
        rep = rr.check(SRC, SRC.replace("Handover notes were two lines long, so the gaps grew. ", ""), 2)
        self.assertIn("removed", rules(rep))

    def test_a_plain_added_sentence_is_amber_and_listed(self):
        rep = rr.check(SRC, SRC + " That is the short version.", 4)
        self.assertEqual((rep["status"], rep["sentences_added"]), ("amber", 1))

    def test_length_outside_the_band_at_tier_three(self):
        rep = rr.check(SRC, "The rota changed and nobody told the night team.", 3)
        self.assertIn("length", rules(rep))


class Red(unittest.TestCase):
    def test_a_changed_number_is_red(self):
        rep = rr.check(SRC, SRC.replace("4,000", "5,000"), 2)
        self.assertEqual(rep["status"], "red")
        self.assertIn("number-changed", rules(rep))

    def test_a_reworded_quote_is_red(self):
        rep = rr.check(SRC, SRC.replace("we will not do this again", "this will not happen again"), 3)
        self.assertEqual(rep["status"], "red")
        self.assertIn("quote-changed", rules(rep))

    def test_tier_one_any_change_is_red(self):
        rep = rr.check(SRC, SRC.replace("nobody told", "no one told"), 1)
        self.assertEqual(rep["status"], "red")

    def test_an_added_first_person_anecdote_is_red(self):
        rep = rr.check(SRC, SRC + " I remember the smell of the ward that night.", 4)
        self.assertEqual(rep["status"], "red")

    def test_an_added_number_is_red(self):
        rep = rr.check(SRC, SRC + " Turnover rose by 30 percent afterwards.", 4)
        self.assertEqual(rep["status"], "red")

    def test_an_added_joke_is_red(self):
        rep = rr.check(SRC, SRC + " A nurse walks into a bar and asks for the handover!!", 4)
        self.assertEqual(rep["status"], "red")

    def test_report_only_the_inputs_are_not_touched(self):
        with tempfile.TemporaryDirectory() as d:
            s, t = Path(d) / "s.md", Path(d) / "d.md"
            s.write_text(SRC)
            t.write_text(SRC.replace("4,000", "5,000"))
            run([str(s), str(t)])
            self.assertEqual((s.read_text(), t.read_text()), (SRC, SRC.replace("4,000", "5,000")))


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = rr.main(argv)
    return code, out.getvalue(), err.getvalue()


class Runs(unittest.TestCase):
    def files(self, d, src, draft):
        s, t = Path(d) / "s.md", Path(d) / "d.md"
        s.write_text(src)
        t.write_text(draft)
        return [str(s), str(t)]

    def test_red_still_exits_zero_and_says_what_was_not_run(self):
        with tempfile.TemporaryDirectory() as d:
            code, out, _ = run(self.files(d, SRC, SRC.replace("4,000", "5,000")))
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("RED"))
        self.assertIn("meaning drift", out)
        self.assertIn("voice-file check", out)

    def test_json(self):
        with tempfile.TemporaryDirectory() as d:
            code, out, _ = run(self.files(d, SRC, SRC) + ["--json", "--tier", "3"])
        rep = json.loads(out)
        self.assertEqual((code, rep["status"], rep["tier"]), (0, "green", 3))
        self.assertEqual(len(rep["not_run"]), 2)

    def test_a_missing_file_is_unknown(self):
        code, out, err = run(["/nonexistent/a.md", "/nonexistent/b.md"])
        self.assertEqual((code, out), (2, ""))
        self.assertIn("not found", err)

    def test_an_empty_draft_is_unknown_not_clean(self):
        with tempfile.TemporaryDirectory() as d:
            code, out, err = run(self.files(d, SRC, "  \n"))
        self.assertEqual((code, out), (2, ""))
        self.assertIn("unknown, not clean", err)


if __name__ == "__main__":
    unittest.main()
