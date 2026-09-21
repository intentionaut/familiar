"""question-check flags the questions AGENTS.md, "Asking the writer" rules out,
and passes the ones it asks for. Both directions, because a check that flags
good questions gets ignored. Examples are invented; no writer's material here.
"""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("question_check", ROOT / "scripts" / "question-check.py")
qc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qc)


class Flags(unittest.TestCase):
    def flags(self, q):
        return qc.flags_for(q)

    def test_a_pick_with_one_ask_passes(self):
        q = ("Who should feel caught by this?\n"
             "**A.** The team lead. **B.** The director above them. "
             "**C.** Both. Or something else.")
        self.assertEqual([], self.flags(q))

    def test_a_named_shape_passes(self):
        for q in ("If you could only keep 400 words, which section survives?",
                  "Did the migration run before the launch, yes or no?",
                  "How many customers saw the error?",
                  "What is one decision about the project you have not made yet?"):
            self.assertEqual([], self.flags(q), q)

    def test_three_asks_in_one_are_compound(self):
        q = "What did the email say, what did you reply, and why does it matter?"
        self.assertIn("compound", self.flags(q))
        self.assertIn("compound", self.flags("Was it planned? Who decided?"))

    def test_option_lines_are_not_extra_asks(self):
        q = "Which matters more?\nA. Speed?\nB. Cost?\nOr something else."
        self.assertNotIn("compound", self.flags(q))

    def test_recall_is_flagged(self):
        for q in ("Take the ten minutes after the outage. What did you check next?",
                  "When did you first realise it was a product? A. Day one. B. Later.",
                  "What were you looking at when it broke? Yes or no"):
            self.assertIn("memory", self.flags(q), q)

    def test_judgement_now_is_not_recall(self):
        self.assertNotIn("memory", self.flags("Which of these matters more to you today? A. X. B. Y."))

    def test_edgeless_openers_are_vague(self):
        self.assertIn("vague", self.flags("Tell me more about the launch?"))
        self.assertIn("vague", self.flags("What are you noticing about how it is going?"))
        self.assertNotIn("vague", self.flags("Tell me about one hire where the deck misled you: which one?"))

    def test_internal_labels_are_flagged(self):
        self.assertIn("internal", self.flags("Does this sit under T3? Yes or no"))
        self.assertIn("internal", self.flags("Should `dev-edit` run next? Yes or no"))
        self.assertIn("internal", self.flags("Is notes.md right? Yes or no"))
        self.assertNotIn("internal", self.flags("Is the date right? Yes or no [ASK THE WRITER: notes.md]"))

    def test_no_answer_shape_is_flagged(self):
        self.assertIn("shape", self.flags("What would you have needed to see?"))

    def test_a_statement_is_not_a_question(self):
        self.assertEqual(["not-asked"], self.flags("Line-edit, after she works the report."))


class Files(unittest.TestCase):
    def write(self, name, text):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        p = Path(d.name) / name
        p.write_text(text)
        return p

    def test_a_question_list_is_read_item_by_item(self):
        p = self.write("interview-questions.md", "# Questions\n\n"
                       "1. Which matters more today?\n   A. Speed. B. Cost.\n"
                       "2. Tell me more?\n\n- How many users?\n")
        found = qc.check(p)
        self.assertEqual([(5, "vague"), (5, "shape")], [(n, f) for n, f, _ in found])

    def test_only_the_latest_gate_counts_unless_asked(self):
        p = self.write("SESSION-CONTEXT.md",
                       "## 2026-01-01 10:00  draft  x\n\nDecision gate: Tell me more?\nNext stage: none\n\n"
                       "## 2026-01-02 10:00  draft  x\n\nDecision gate: which section survives,\n"
                       "  the first or the last?\nNext stage: none\n")
        self.assertEqual([], qc.check(p))
        self.assertTrue(qc.check(p, every=True))

    def test_a_gate_of_none_is_skipped(self):
        p = self.write("SESSION-CONTEXT.md", "Decision gate: none. Title was settled.\nNext stage: x\n")
        self.assertEqual([], qc.check(p))


CLEAN_SET = """# Questions

1. Which failure changed how you work most? Pick one: A. one you fixed, B. one you left alone. Or something else.
   Receipt: one story, number or artifact showing what changed. Buried lede: the claim your audience is not already hearing.
2. Who carries the cost today? Pick one: A. the team, B. the customer. Or something else.
   Receipt: a number or artifact from one case. Bigger context: why now, who benefits and what incentive keeps it in place.
3. Where might the premise fail? Name one case in a sentence.
   Receipt: an artifact or story that would falsify it.
"""


class PreparedSets(unittest.TestCase):
    def write(self, text):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        p = Path(d.name) / "interview-questions.md"
        p.write_text(text)
        return p

    def flags(self, text):
        return sorted({f for _, f, _ in qc.check(self.write(text), prepared=True)})

    def test_a_clean_set_passes(self):
        self.assertEqual([], self.flags(CLEAN_SET))

    def test_a_fourth_prompt_is_too_many(self):
        extra = CLEAN_SET + "4. How many users?\n"
        self.assertIn("too-many", self.flags(extra))

    def test_a_prompt_without_a_receipt_is_flagged(self):
        bad = CLEAN_SET.replace("Receipt: one story, number or artifact showing what changed. ", "")
        found = qc.check(self.write(bad), prepared=True)
        self.assertEqual([(3, "no-receipt")], [(n, f) for n, f, _ in found if f == "no-receipt"])

    def test_a_set_with_no_challenge_is_flagged(self):
        bad = CLEAN_SET.replace("Where might the premise fail?", "What else matters?").replace(
            "would falsify it", "would help")
        self.assertIn("no-challenge", self.flags(bad))

    def test_lede_and_context_are_required(self):
        bad = CLEAN_SET.replace("Buried lede: the claim your audience is not already hearing.", "Note.").replace("why now", "so")
        self.assertIn("no-lede", self.flags(bad))
        bad = CLEAN_SET.replace("Who carries the cost today?", "Which one?").replace(
            "Bigger context: why now, who benefits and what incentive keeps it in place.", "")
        self.assertIn("no-context", self.flags(bad))

    def test_the_set_check_is_opt_in(self):
        p = self.write("1. Which matters more today?\n   A. Speed. B. Cost.\n")
        self.assertEqual([], qc.check(p))


if __name__ == "__main__":
    unittest.main()
