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
H1 = "   **Held, how it works:** If you'd like, walk me through what a Monday looks like now.\n"
A1 = "   **Held, another angle:** If it helps, say who misses the meeting most.\n"
H2 = "   **Held, how it works:** If you'd like, say what the team did that week in place of the meeting.\n"
A2 = "   **Held, another angle:** If it helps, say what a newcomer would have seen that week.\n"
H3 = "   **Held, how it works:** If you'd like, say how you would tell whether that person had a point.\n"
A3 = "   **Held, another angle:** If it helps, say what you would tell a friend to try on Monday.\n"
H3_DOUBT = "   **Held, how it works:** If you'd like, say what you would look at to check.\n"
Q3_DEEP_TAIL = " Add anything you could see by a date."
TENSION = " | tension: live, notes.md lines 4 and 9"
HEAR3 = ("Someone thoughtful might say the meeting is where trust gets built, and a written update cannot do that. "
         "I don't think that's the whole story, but I'd like to hear it from you.")
Q3_FIRESIDE = "What is your reaction to that?"
Q3_DOUBT = "Is there anything that would make you doubt this, even a little?"
HEAR3_DOUBT = "You think the meeting mostly served the manager, and the team can do without it."
HEAR2 = "One team tried it and it worked, and you think trust was the reason."


def warm_set(engagement="fireside"):
    """A clean fireside-format set on an invented topic, at one setting."""
    length = LENGTHS[engagement]
    marker3 = "move: the strongest opposing case | job: challenge the premise | receipt: number | level: 3"
    if engagement == "companion":
        hear3, q3, how3 = HEAR3_DOUBT, Q3_DOUBT, f"About {length}. A word or two is fine, and you can pass."
        h1, h2, h3 = H1, H2, H3_DOUBT
    else:
        hear3, q3 = HEAR3, Q3_FIRESIDE
        how3 = f"About {length}. Then say what would change your mind. Short is fine, and you can pass."
        h1, h2, h3 = H1 + A1, H2 + A2, H3 + A3
    if engagement == "deep dive":
        marker3 += TENSION
        how3 = f"About {length}. Then say what would change your mind.{Q3_DEEP_TAIL} Pass if you like."
    return (
        "# Interview questions\n\n" + OPENING + "\n\n"
        "1. **What I'm hearing (my guess):** Small teams that drop the weekly status meeting keep track of the work. "
        "They lose the habit of looking busy together. My own position: the meeting was mostly for the people in it.\n"
        "   **Question:** Where does the work show up now, if it isn't in the meeting?\n"
        f"   **How to answer:** About {length}. Name a place, a person or a tool. Rough is fine, and you can pass.\n"
        + h1 +
        "   <!-- move: follow the value | job: buried lede, bigger context (why now, who benefits) | receipt: artifact | level: 1 -->\n"
        f"2. **What I'm hearing (my guess):** {HEAR2}\n"
        "   **Question:** Which one week shows the change best?\n"
        f"   **How to answer:** About {length}. Give one real week, with a date or a number if you have one. Rough is fine, or pass.\n"
        + h2 +
        "   <!-- move: the specific case | job: one real case | receipt: story | level: 2 -->\n"
        f"3. **What I'm hearing (my guess):** {hear3}\n"
        f"   **Question:** {q3}\n"
        f"   **How to answer:** {how3}\n"
        + h3 +
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
        s = warm_set().replace(HEAR3, "I think you are wrong here, and the meeting matters.")
        self.assertIn("verdict-voice", self.flags(s))
        # a case with no imagined person behind it
        s = warm_set().replace(HEAR3, "The meeting is where trust gets built. I'd like to hear it from you.")
        self.assertIn("no-fair-critic", self.flags(s))
        # the question must ask for a reaction, not a blank-page essay
        s = warm_set().replace(Q3_FIRESIDE, "What is the best case against the meeting going?")
        self.assertIn("no-fair-critic", self.flags(s))

    def test_prompt_three_puts_the_opposing_case_on_the_table_first(self):
        s = warm_set()
        self.assertIn("Someone thoughtful might say", s)
        self.assertIn("I don't think that's the whole story", s)
        self.assertNotIn("Picture a thoughtful person", s)

    def test_prompt_one_carries_a_position_of_its_own(self):
        s = warm_set().replace(" My own position: the meeting was mostly for the people in it.", "")
        self.assertIn("no-position", self.flags(s))

    def test_repeated_follow_ups(self):
        # identical to another prompt's
        s = warm_set().replace(H2, H1, 1)
        self.assertIn("repeated-follow-up", self.flags(s))
        # repeats its own prompt's question
        s = warm_set().replace("say what the team did that week in place of the meeting.",
                               "say which one week shows the change best.")
        self.assertIn("repeated-follow-up", self.flags(s))
        # two identical follow-ups in one prompt
        s = warm_set().replace(A1, H1.replace("how it works", "another angle"), 1)
        self.assertIn("repeated-follow-up", self.flags(s))

    def test_the_worked_example_has_no_repeated_follow_ups(self):
        text = (ROOT / "prompts" / "interview.md").read_text()
        block = text.split("```\n")[1]
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        p = Path(d.name) / "interview-questions.md"
        p.write_text(block)
        self.assertEqual([], qc.check(p, warm=True, engagement="fireside"))

    def test_praise_and_hype(self):
        for word in ("great", "brilliant", "fascinating", "game-changing"):
            s = warm_set().replace("One team tried it and it worked", f"One team tried it and it was {word}")
            self.assertIn("praise", self.flags(s), word)

    def test_accusing(self):
        for phrase in ("why didn't you", "you failed", "against you", "you're wrong"):
            s = warm_set().replace("Which one week", f"{phrase.capitalize()}? Which one week")
            self.assertIn("accusing", self.flags(s), phrase)

    def test_follow_up_counts(self):
        self.assertIn("follow-ups", self.flags(warm_set().replace(A1, "", 1), "fireside"))
        self.assertNotIn("follow-ups", self.flags(warm_set("companion").replace(H1, H1 + A1), "companion"))
        three = warm_set().replace(A1, A1 + "   **Held, a third:** If you'd like, say more about the newest hire.\n", 1)
        self.assertIn("follow-ups", self.flags(three))

    def test_follow_ups_are_invitations(self):
        s = warm_set().replace("If you'd like, walk me through what a Monday looks like now.", "Explain a Monday now.", 1)
        self.assertIn("not-invitation", self.flags(s))

    def test_a_bare_question_is_not_an_invitation(self):
        s = warm_set().replace("If you'd like, walk me through what a Monday looks like now.",
                               "What does a Monday look like now.", 1)
        self.assertIn("not-invitation", self.flags(s))

    def test_an_invitation_can_be_worded_any_way(self):
        # The check stops an instruction. It does not make every script offer
        # things in the same two phrases, which is what made scripts read alike.
        for line in ("There is more here if you want it: what a Monday looks like now.",
                     "Whenever you want it: what a Monday looks like now.",
                     "Say what a Monday looks like now, if that is easy.",
                     "No need to take this one: what a Monday looks like now.",
                     "We can go into what a Monday looks like now.",
                     "Ready when you are: what a Monday looks like now.",
                     "Glad to hear what a Monday looks like now.",
                     "Open any time: what a Monday looks like now.",
                     "A second read, if you fancy it: what a Monday looks like now.",
                     "Happy to go further into what a Monday looks like now.",
                     "Up to you whether we go into what a Monday looks like now."):
            s = warm_set().replace("If you'd like, walk me through what a Monday looks like now.", line, 1)
            self.assertNotIn("not-invitation", self.flags(s), line)

    def test_the_guess_never_reports_what_the_files_lack(self):
        for line in ("Your notes hold that one line and nothing else.",
                     "There are no dates or numbers in them yet.",
                     "All you have saved is one link with a title.",
                     "You ran four of these last year. That is all they say about them.",
                     "I have no example to work from yet."):
            self.assertIn("files-talk", self.flags(warm_set().replace(HEAR2, line)), line)

    def test_evidence_the_files_do_hold_is_not_files_talk(self):
        held = "Your build log for 4 November has 31 flags gone, and the build down from 9 minutes to 6."
        self.assertEqual([], self.flags(warm_set().replace(HEAR2, held)))

    def test_a_second_ask_in_the_answer_shape(self):
        s = warm_set().replace("Give one real week, with a date or a number if you have one.",
                               "Give one real week, and what changed that week.")
        self.assertIn("second-ask", self.flags(s))
        self.assertNotIn("compound", self.flags(s))

    def test_two_questions_in_the_question_are_still_compound(self):
        s = warm_set().replace("Which one week shows the change best?",
                               "Which one week shows the change best? Who noticed?")
        self.assertIn("compound", self.flags(s))

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

    def test_companion_puts_no_critic_on_the_table(self):
        self.assertNotIn("critic-at-companion", self.flags(warm_set("companion"), "companion"))
        s = warm_set("companion").replace(
            HEAR3_DOUBT, "Someone thoughtful might say the meeting is where trust gets built. " + HEAR3_DOUBT)
        self.assertIn("critic-at-companion", self.flags(s, "companion"))

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
        # an apostrophe in the file note is not a quotation
        apostrophe = s.replace("notes.md lines 4 and 9", "notes.md, the writer's own two lines")
        self.assertEqual([], self.flags(apostrophe, "deep dive"))

    def test_the_tension_may_be_bracketed_as_missing(self):
        bracketed = warm_set("deep dive").replace(
            TENSION, " | tension: [NEEDS SOURCE: two statements to set side by side]")
        self.assertEqual([], self.flags(bracketed, "deep dive"))
        # and then the writer must not be able to read a tension anyway
        visible = bracketed.replace(HEAR3, HEAR3 + " Two things in your notes sit oddly together for me.")
        self.assertIn("tension-in-text", self.flags(visible, "deep dive"))

    def test_a_bracket_elsewhere_does_not_stand_in_for_the_marker(self):
        s = warm_set("deep dive").replace(TENSION, "")
        s = s.replace("receipt: artifact", "receipt: artifact | note: [NEEDS SOURCE: a number]")
        self.assertIn("no-tension", self.flags(s, "deep dive"))

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
