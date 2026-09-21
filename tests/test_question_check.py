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


OPENING = ('A relaxed set of three questions, at your pace. Say "gentler" or "push me" '
           'at any point and I will move the next question one step.')

LENGTHS = {"companion": "30 to 60 seconds", "fireside": "1 to 2 minutes", "deep dive": "2 to 3 minutes"}
ONE_HELD = "   **Held, how it works:** If you'd like, walk me through a Monday now.\n"
TWO_HELD = ONE_HELD + "   **Held, another angle:** If it helps, say who misses the meeting most.\n"
Q3_DEEP_TAIL = " Add anything you could see by a date."
TENSION = " | tension: live, notes.md lines 4 and 9"
Q3_FIRESIDE = "Picture a thoughtful person who disagrees. What is the best thing they would say?"
Q3_DOUBT = "Is there anything that would make you doubt this, even a little?"


def warm_set(engagement="fireside"):
    """A clean fireside-format set on an invented topic, at one setting."""
    length = LENGTHS[engagement]
    marker3 = "move: the strongest opposing case | job: challenge the premise | receipt: number | level: 3"
    if engagement == "companion":
        q3, how3 = Q3_DOUBT, f"About {length}. A word or two is fine, and you can pass."
        held, held3 = ONE_HELD, ONE_HELD
    else:
        q3 = Q3_FIRESIDE
        how3 = f"About {length}. Then say what would change your mind. Short is fine, and you can pass."
        held = held3 = TWO_HELD
    if engagement == "deep dive":
        marker3 += TENSION
        how3 = f"About {length}. Then say what would change your mind.{Q3_DEEP_TAIL} Pass if you like."
    return (
        "# Interview questions\n\n" + OPENING + "\n\n"
        "1. **What I'm hearing (my guess):** Small teams that drop the weekly status meeting keep track of the work. "
        "They lose the habit of looking busy together.\n"
        "   **Question:** Where does the work show up now, if it isn't in the meeting?\n"
        f"   **How to answer:** About {length}. Name a place, a person or a tool. Rough is fine, and you can pass.\n"
        + held +
        "   <!-- move: follow the value | job: buried lede, bigger context (why now, who benefits) | receipt: artifact | level: 1 -->\n"
        "2. **What I'm hearing (my guess):** One team tried it and it worked, and you think trust was the reason.\n"
        "   **Question:** Which one week shows the change best?\n"
        f"   **How to answer:** About {length}. Give one real week, with a date or a number if you have one. Rough is fine, or pass.\n"
        + held +
        "   <!-- move: the specific case | job: one real case | receipt: story | level: 2 -->\n"
        "3. **What I'm hearing (my guess):** You think the meeting mostly served the manager, and the team can do without it.\n"
        f"   **Question:** {q3}\n"
        f"   **How to answer:** {how3}\n"
        + held3 +
        f"   <!-- {marker3} -->\n")


class Reading(unittest.TestCase):
    def test_reading_ease_on_fixed_strings(self):
        def near(text, want):
            self.assertAlmostEqual(qc.reading_ease(text), want, places=1, msg=text)
        near("The cat sat on the mat.", 116.1)
        near("We tried it. It worked. Nobody missed the meeting.", 91.0)
        near("Teams that stop holding weekly meetings often keep written records.", 61.3)
        near("Teams that stop holding status meetings usually keep better records.", 52.9)

    def test_the_threshold_is_sixty(self):
        self.assertGreaterEqual(qc.reading_ease("Teams that stop holding weekly meetings often keep written records."), 60)
        self.assertLess(qc.reading_ease("Teams that stop holding status meetings usually keep better records."), 60)

    def test_syllable_heuristic(self):
        for word, n in (("cat", 1), ("meeting", 2), ("make", 1), ("table", 2), ("worked", 1),
                        ("wanted", 2), ("organisation", 5), ("the", 1)):
            self.assertEqual(n, qc.count_syllables(word), word)

    def test_hidden_comments_do_not_count(self):
        visible = "We tried it. It worked."
        hidden = visible + " <!-- move: institutional epistemology of commodity mechanisms -->"
        self.assertEqual(qc.reading_ease(visible), qc.reading_ease(qc.strip_hidden(hidden)))


class Fireside(unittest.TestCase):
    def write(self, text, name="interview-questions.md"):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        p = Path(d.name) / name
        p.write_text(text)
        return p

    def flags(self, text, engagement="fireside", warm=True):
        p = self.write(text)
        return sorted({f for _, f, _ in qc.check(p, warm=warm, engagement=engagement)})

    def test_a_clean_set_passes_at_each_setting(self):
        for e in qc.ENGAGEMENTS:
            self.assertEqual([], self.flags(warm_set(e), e), e)

    def test_the_comment_receipt_satisfies_the_prepared_check(self):
        self.assertEqual([], sorted({f for _, f, _ in qc.check(self.write(warm_set()), prepared=True)}))

    def test_the_old_receipt_line_form_still_passes(self):
        self.assertEqual([], sorted({f for _, f, _ in qc.check(self.write(CLEAN_SET), prepared=True)}))

    def test_the_comment_form_is_still_held_to_three_and_a_challenge(self):
        s = warm_set().replace("job: challenge the premise", "job: something else")
        self.assertIn("no-challenge", self.flags(s))
        extra = warm_set() + "4. **What I'm hearing (my guess):** x.\n   **Question:** How many?\n"
        self.assertIn("too-many", self.flags(extra))
        self.assertIn("no-receipt", self.flags(warm_set().replace("receipt: story", "kind: story")))

    def test_hard_to_read(self):
        s = warm_set().replace("Where does the work show up now, if it isn't in the meeting?",
                               "Notwithstanding organisational reconfiguration, where does undocumented "
                               "interdepartmental coordination materialise subsequently, "
                               "considering institutional communication expectations, "
                               "administrative accountability requirements and geographically "
                               "distributed collaboration arrangements?")
        self.assertIn("hard-to-read", self.flags(s))

    def test_reading_ease_ignores_the_hidden_comment(self):
        s = warm_set().replace("level: 1 -->", "level: 1 | note: institutional epistemological "
                               "considerations notwithstanding unquestionably characteristically -->")
        self.assertEqual([], self.flags(s))

    def test_jargon_in_visible_text(self):
        for word in ("receipt", "steelman", "mechanism", "plumbing", "commodity", "falsifier"):
            s = warm_set().replace("Which one week shows the change best?", f"Which one week is your {word}?")
            self.assertIn("jargon", self.flags(s), word)

    def test_jargon_is_fine_in_the_hidden_comment(self):
        self.assertEqual([], self.flags(warm_set()))  # the comment already says "receipt" and "premise"

    def test_no_way_out(self):
        s = warm_set().replace("Give one real week, with a date or a number if you have one. Rough is fine, or pass.",
                               "Give one real week, with a date or a number if you have one.")
        self.assertIn("no-way-out", self.flags(s))

    def test_no_switch_in_the_opening(self):
        s = warm_set().replace('Say "gentler" or "push me" at any point and I will move the next question one step.',
                               "Take your time.")
        self.assertIn("no-switch", self.flags(s))

    def test_no_listening(self):
        self.assertIn("no-listening", self.flags(warm_set().replace("(my guess)", "")))
        self.assertIn("no-listening", self.flags(warm_set().replace("(my guess):** Small teams that drop the weekly status meeting keep track of the work. They lose the habit of looking busy together.", "):**")))
        self.assertIn("not-fireside-format", self.flags("1. Which matters more today?\n   A. Speed. B. Cost.\n"))

    def test_verdict_voice(self):
        s = warm_set().replace(Q3_FIRESIDE, "I think you are wrong here. What is the best thing you can say?")
        self.assertIn("verdict-voice", self.flags(s))
        s = warm_set().replace(Q3_FIRESIDE, "What is the best case against the meeting going?")
        self.assertIn("no-fair-critic", self.flags(s))

    def test_praise_and_hype(self):
        for word in ("great", "brilliant", "fascinating", "game-changing"):
            s = warm_set().replace("One team tried it and it worked", f"One team tried it and it was {word}")
            self.assertIn("praise", self.flags(s), word)

    def test_accusing(self):
        for phrase in ("why didn't you", "you failed", "against you", "you're wrong"):
            s = warm_set().replace("Which one week", f"{phrase.capitalize()}? Which one week")
            self.assertIn("accusing", self.flags(s), phrase)

    def test_follow_up_counts(self):
        self.assertIn("follow-ups", self.flags(warm_set().replace(TWO_HELD, ONE_HELD, 1), "fireside"))
        self.assertNotIn("follow-ups", self.flags(warm_set("companion").replace(ONE_HELD, TWO_HELD), "companion"))
        three = warm_set().replace(TWO_HELD, TWO_HELD + "   **Held, a third:** If you'd like, say more.\n", 1)
        self.assertIn("follow-ups", self.flags(three))

    def test_follow_ups_are_invitations(self):
        s = warm_set().replace("If you'd like, walk me through a Monday now.", "Explain a Monday now.", 1)
        self.assertIn("not-invitation", self.flags(s))

    def test_the_hidden_comment_carries_move_receipt_and_level(self):
        for word in ("move", "level"):
            self.assertIn("no-comment", self.flags(warm_set().replace(f"{word}:", "x:", 1)), word)

    def test_answer_length_follows_the_setting(self):
        self.assertIn("wrong-length", self.flags(warm_set("fireside"), "companion"))
        self.assertIn("wrong-length", self.flags(warm_set("companion"), "deep dive"))

    def test_companion_prompt_three_is_the_gentle_doubt_question(self):
        self.assertIn(Q3_DOUBT, warm_set("companion"))
        s = warm_set("companion").replace(Q3_DOUBT, "What would a critic say?")
        self.assertIn("no-gentle-doubt", self.flags(s, "companion"))

    def test_fireside_asks_what_would_change_their_mind(self):
        self.assertIn("no-mind-change", self.flags(warm_set().replace("Then say what would change your mind. ", "")))

    def test_deep_dive_carries_a_live_tension_marker_that_quotes_nothing(self):
        s = warm_set("deep dive")
        self.assertIn("tension: live, notes.md", s)
        self.assertEqual([], self.flags(s, "deep dive"))
        self.assertIn("no-tension", self.flags(s.replace(TENSION, ""), "deep dive"))
        quoted = s.replace("notes.md lines 4 and 9", 'notes.md, "we never needed it" and "we always needed it"')
        self.assertIn("tension-quote", self.flags(quoted, "deep dive"))
        unsourced = s.replace("tension: live, notes.md lines 4 and 9", "tension: live, between two things you said")
        self.assertIn("no-tension", self.flags(unsourced, "deep dive"))

    def test_deep_dive_asks_for_something_observable(self):
        s = warm_set("deep dive").replace(Q3_DEEP_TAIL, "")
        s = s.replace("with a date or a number if you have one", "if you have one")
        self.assertIn("no-observable", self.flags(s, "deep dive"))

    def test_the_prepared_check_alone_does_not_run_warmth(self):
        self.assertEqual([], self.flags(warm_set().replace("(my guess)", ""), warm=False))


class Engagement(unittest.TestCase):
    def house(self, line):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        (Path(d.name) / "positioning.md").write_text("## House rules\n\n" + line + "\n- Pieces end with: nothing\n")
        return d.name

    def test_the_shipped_template_leaves_it_unset_and_resolves_to_fireside(self):
        shipped = ROOT / "knowledge"
        self.assertIn("- Interview engagement: [", (shipped / "positioning.md").read_text())
        self.assertIsNone(qc.house_engagement(shipped))
        self.assertEqual("fireside", qc.resolve_engagement(knowledge_dir=shipped))

    def test_a_house_value_is_read(self):
        self.assertEqual("deep dive", qc.resolve_engagement(knowledge_dir=self.house("- Interview engagement: deep dive")))
        self.assertEqual("companion", qc.resolve_engagement(knowledge_dir=self.house("- Interview engagement: Companion")))

    def test_a_missing_line_or_an_empty_value_is_unset(self):
        self.assertEqual("fireside", qc.resolve_engagement(knowledge_dir=self.house("")))
        self.assertEqual("fireside", qc.resolve_engagement(knowledge_dir=self.house("- Interview engagement:")))

    def test_the_run_override_beats_the_house(self):
        h = self.house("- Interview engagement: companion")
        self.assertEqual("deep dive", qc.resolve_engagement("deep-dive", h))

    def test_an_unknown_value_is_refused_not_ignored(self):
        with self.assertRaises(ValueError):
            qc.resolve_engagement("intense")
        with self.assertRaises(ValueError):
            qc.resolve_engagement(knowledge_dir=self.house("- Interview engagement: intense"))

    def test_the_house_setting_drives_the_check(self):
        h = self.house("- Interview engagement: companion")
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        p = Path(d.name) / "interview-questions.md"
        p.write_text(warm_set("companion"))
        self.assertEqual([], qc.check(p, warm=True, knowledge_dir=h))
        p.write_text(warm_set("fireside"))
        self.assertIn("wrong-length", {f for _, f, _ in qc.check(p, warm=True, knowledge_dir=h)})

    def test_gentler_and_push_me_move_one_step_and_stop_at_the_ends(self):
        self.assertEqual(("companion", True), qc.step_engagement("fireside", "gentler"))
        self.assertEqual(("deep dive", True), qc.step_engagement("fireside", "push me"))
        self.assertEqual(("companion", False), qc.step_engagement("companion", "gentler"))
        self.assertEqual(("deep dive", False), qc.step_engagement("deep dive", "Push me"))
        self.assertEqual(("fireside", True), qc.step_engagement("deep dive", "gentler"))
        with self.assertRaises(ValueError):
            qc.step_engagement("fireside", "harder")

    def test_the_prompt_describes_the_switch(self):
        text = (ROOT / "prompts" / "interview.md").read_text()
        for needle in ("## Fireside scripts", "gentler", "push me", "one step", "notes.md",
                       "companion", "fireside", "deep dive", "Interview engagement", "--engagement"):
            self.assertIn(needle, text, needle)
        cs = (ROOT / "prompts" / "case-study.md").read_text()
        self.assertIn("Fireside scripts", cs)
        self.assertIn("--warm", cs)

    def test_the_prompts_name_moves_by_technique_not_person(self):
        text = (ROOT / "prompts" / "interview.md").read_text() + (ROOT / "prompts" / "case-study.md").read_text()
        for name in ("Thompson", "Cowen", "Patel", "Klein", "Swisher"):
            self.assertNotIn(name, text)


if __name__ == "__main__":
    unittest.main()
