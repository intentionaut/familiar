"""question-check flags the questions AGENTS.md, "Asking the writer" rules out,
and passes the ones it asks for. Both directions, because a check that flags
good questions gets ignored. Examples are invented; no writer's material here.
"""
import importlib.util
import re
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


FIRESIDE_SECTION = re.compile(r"^## Fireside scripts\n.*?(?=^## Exit)", re.S | re.M)


def fireside_section():
    return FIRESIDE_SECTION.search((ROOT / "prompts" / "interview.md").read_text()).group(0)


def example_blocks():
    """Every fenced block inside the Fireside scripts section of the prompt."""
    return re.findall(r"^```\n(.*?)^```", fireside_section(), re.S | re.M)


def worked_example():
    """The full three-prompt example the prompt teaches from."""
    return next(b for b in example_blocks() if "1. **What I'm hearing" in b)


# The fixture: an invented reader (new team leaders in a care home), an invented
# idea (a written handover beats a spoken one), and nothing technical in it.
WHO = ("**Who this is for:** new team leaders in a care home, "
       "in their first year of running a shift.")
AIM = ("**What we're aiming at:** they can run one handover differently on Monday "
       "and see whether it holds.")
SWITCH = ('A relaxed set of three questions, at your pace. Say "gentler" or "push me" '
          'at any point and I will move the next question one step.')
OPENING = WHO + "\n" + AIM + "\n" + SWITCH

LENGTHS = {"companion": "30 to 60 seconds", "fireside": "1 to 2 minutes", "deep dive": "2 to 3 minutes"}
H1 = "   **Held, how it works:** If you'd like, walk me through the first hour of a late shift.\n"
A1 = "   **Held, another angle:** If it helps, say who notices first when something was missed.\n"
H2 = "   **Held, how it works:** If you'd like, say what the written note held that the spoken one did not.\n"
A2 = "   **Held, another angle:** If it helps, say what a new starter would have made of that shift.\n"
H3 = "   **Held, how it works:** If you'd like, say how you would tell a skimmed note from one nobody read.\n"
A3 = "   **Held, another angle:** If it helps, say what you would tell a friend to try on Monday.\n"
H3_DOUBT = "   **Held, how it works:** If you'd like, say what you would look at to check.\n"
Q3_DEEP_TAIL = " Add anything you could see by a date."
TENSION = " | tension: live, notes.md lines 4 and 9"
HEAR1 = ("Handover works better written down by the person leaving than said out loud. "
         "My own position: the spoken one serves the person leaving, not the person arriving.")
Q1 = "Who is carrying the gap when a handover is only spoken?"
HEAR2 = ("What would settle this for another team leader is one handover that went wrong, "
         "not the case for writing things down. I would guess one is already in mind.")
Q2 = "Which one handover shows the difference best?"
HOW2_TAIL = "Give one real handover, with the week it happened if you have it."
HEAR3 = ("A team leader reading this might say the note takes ten minutes nobody has at seven "
         "in the morning, and it gets skimmed anyway. "
         "I don't think that's the whole story, but I'd like to hear it from you.")
Q3_FIRESIDE = "What is your reaction to that?"
Q3_DOUBT = "Is there anything that would make you doubt this, even a little?"
HEAR3_DOUBT = "You think the written handover serves the person arriving, and the spoken one serves the person leaving."
OUT1 = "outcome: a team leader can see who pays for a spoken handover"
OUT2 = "outcome: a team leader can copy the note and the reasoning under it"
OUT3 = "outcome: a team leader can weigh the ten minutes against the risk"


def warm_set(engagement="fireside"):
    """A clean fireside-format set on an invented topic, at one setting."""
    length = LENGTHS[engagement]
    marker3 = f"move: the strongest opposing case | job: challenge the premise | {OUT3} | receipt: number | level: 3"
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
        f"1. **What I'm hearing (my guess):** {HEAR1}\n"
        f"   **Question:** {Q1}\n"
        f"   **How to answer:** About {length}. Name a person or a job. Rough is fine, and you can pass.\n"
        + h1 +
        "   <!-- move: follow the value | job: buried lede, bigger context (why now, who benefits) | "
        f"{OUT1} | receipt: artifact | level: 1 -->\n"
        f"2. **What I'm hearing (my guess):** {HEAR2}\n"
        f"   **Question:** {Q2}\n"
        f"   **How to answer:** About {length}. {HOW2_TAIL} Rough is fine, or pass.\n"
        + h2 +
        f"   <!-- move: the specific case | job: one real case | {OUT2} | receipt: story | level: 2 -->\n"
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
        s = warm_set().replace(Q1,
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
            s = warm_set().replace(Q2, f"Which one handover is your {word}?")
            self.assertIn("jargon", self.flags(s), word)

    def test_jargon_is_fine_in_the_hidden_comment(self):
        self.assertEqual([], self.flags(warm_set()))  # the comment already says "receipt" and "premise"

    def test_no_way_out(self):
        s = warm_set().replace(f"{HOW2_TAIL} Rough is fine, or pass.", HOW2_TAIL)
        self.assertIn("no-way-out", self.flags(s))

    def test_the_opening_names_the_reader(self):
        self.assertIn("no-audience-line", self.flags(warm_set().replace(WHO + "\n", "")))
        self.assertIn("no-audience-line", self.flags(warm_set().replace(AIM + "\n", "")))
        self.assertIn("no-audience-line", self.flags(warm_set().replace(WHO, "**Who this is for:**")))

    def test_nothing_declared_must_fall_back_rather_than_stop(self):
        stops = "**Who this is for:** no audience is declared for this piece."
        self.assertIn("no-audience-line", self.flags(warm_set().replace(WHO, stops)))
        for honest in (stops[:-1] + ", so I am writing to your one reader: governors of a small school.",
                       "**Who this is for:** none declared. [ASK THE WRITER: who is this for?]"):
            self.assertNotIn("no-audience-line", self.flags(warm_set().replace(WHO, honest)), honest)

    def test_the_comment_says_what_changes_for_the_reader(self):
        self.assertIn("no-outcome", self.flags(warm_set().replace(OUT1, "note: none")))
        self.assertIn("no-outcome", self.flags(warm_set().replace("outcome:", "x:")))
        self.assertIn("no-outcome", self.flags(warm_set().replace(OUT3, "outcome:")))

    def test_the_objection_may_be_voiced_by_the_reader(self):
        # the fireside fixture already voices it as the reader's own objection
        self.assertNotIn("no-fair-critic", self.flags(warm_set()))
        generic = ("Someone thoughtful might say the note takes ten minutes nobody has. "
                   "I don't think that's the whole story, but I'd like to hear it from you.")
        self.assertNotIn("no-fair-critic", self.flags(warm_set().replace(HEAR3, generic)))
        nobody = ("The note takes ten minutes nobody has at seven in the morning. "
                  "I'd like to hear it from you.")
        self.assertIn("no-fair-critic", self.flags(warm_set().replace(HEAR3, nobody)))

    def test_no_switch_in_the_opening(self):
        s = warm_set().replace('Say "gentler" or "push me" at any point and I will move the next question one step.',
                               "Take your time.")
        self.assertIn("no-switch", self.flags(s))

    def test_no_listening(self):
        self.assertIn("no-listening", self.flags(warm_set().replace("(my guess)", "")))
        self.assertIn("no-listening", self.flags(warm_set().replace(f"(my guess):** {HEAR1}", "):**")))
        self.assertIn("not-fireside-format", self.flags("1. Which matters more today?\n   A. Speed. B. Cost.\n"))

    def test_a_guess_about_the_writer_is_not_a_verdict(self):
        for line in ("I think you already have one in mind.",
                     "I would guess you have one in mind.",
                     "I think this is the one you keep coming back to, and I might be wrong."):
            self.assertNotIn("verdict-voice", self.flags(warm_set().replace(HEAR2, HEAR2 + " " + line)), line)

    def test_a_reaction_can_be_asked_for_in_more_than_one_way(self):
        for q in ("What do you make of that?", "What would you say back to that trustee?",
                  "How does that land with you?", "How much of that holds?"):
            self.assertNotIn("no-fair-critic", self.flags(warm_set().replace(Q3_FIRESIDE, q)), q)
        blank = "What is the best case against writing it down?"
        self.assertIn("no-fair-critic", self.flags(warm_set().replace(Q3_FIRESIDE, blank)))

    def test_the_answer_shape_may_ask_for_what_was_visible_at_the_time(self):
        shape = "One thing anyone could have seen at the time, with its date or its figure."
        self.assertNotIn("memory", self.flags(warm_set().replace(HOW2_TAIL, shape)))
        self.assertIn("memory", self.flags(warm_set().replace(Q2, "What did you check first that week?")))

    def test_verdict_voice(self):
        s = warm_set().replace(HEAR3, "I think you are wrong here, and the spoken handover is fine.")
        self.assertIn("verdict-voice", self.flags(s))
        # a case with no imagined person behind it
        s = warm_set().replace(HEAR3, "The spoken handover is where the trust gets built. I'd like to hear it from you.")
        self.assertIn("no-fair-critic", self.flags(s))
        # the question must ask for a reaction, not a blank-page essay
        s = warm_set().replace(Q3_FIRESIDE, "What is the best case against writing it down?")
        self.assertIn("no-fair-critic", self.flags(s))

    def test_prompt_three_puts_the_opposing_case_on_the_table_first(self):
        s = warm_set()
        self.assertIn("A team leader reading this might say", s)
        self.assertIn("I don't think that's the whole story", s)
        self.assertNotIn("Picture a thoughtful person", s)

    def test_prompt_one_carries_a_position_of_its_own(self):
        s = warm_set().replace(" My own position: the spoken one serves the person leaving, not the person arriving.", "")
        self.assertIn("no-position", self.flags(s))

    def test_repeated_follow_ups(self):
        # identical to another prompt's
        s = warm_set().replace(H2, H1, 1)
        self.assertIn("repeated-follow-up", self.flags(s))
        # repeats its own prompt's question
        s = warm_set().replace("say what the written note held that the spoken one did not.",
                               "say which one handover shows the difference best.")
        self.assertIn("repeated-follow-up", self.flags(s))
        # two identical follow-ups in one prompt
        s = warm_set().replace(A1, H1.replace("how it works", "another angle"), 1)
        self.assertIn("repeated-follow-up", self.flags(s))

    def test_the_worked_example_passes_every_check(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        p = Path(d.name) / "interview-questions.md"
        p.write_text(worked_example())
        self.assertEqual([], qc.check(p, warm=True, engagement="fireside"))

    def test_praise_and_hype(self):
        for word in ("great", "brilliant", "fascinating", "game-changing"):
            s = warm_set().replace("one handover that went wrong", f"one handover that was {word}")
            self.assertIn("praise", self.flags(s), word)

    def test_accusing(self):
        for phrase in ("why didn't you", "you failed", "against you", "you're wrong"):
            s = warm_set().replace("Which one handover", f"{phrase.capitalize()}? Which one handover")
            self.assertIn("accusing", self.flags(s), phrase)

    def test_follow_up_counts(self):
        self.assertIn("follow-ups", self.flags(warm_set().replace(A1, "", 1), "fireside"))
        self.assertNotIn("follow-ups", self.flags(warm_set("companion").replace(H1, H1 + A1), "companion"))
        three = warm_set().replace(A1, A1 + "   **Held, a third:** If you'd like, say more about the newest hire.\n", 1)
        self.assertIn("follow-ups", self.flags(three))

    def test_follow_ups_are_invitations(self):
        s = warm_set().replace("If you'd like, walk me through the first hour of a late shift.", "Explain a late shift now.", 1)
        self.assertIn("not-invitation", self.flags(s))

    def test_a_bare_question_is_not_an_invitation(self):
        s = warm_set().replace("If you'd like, walk me through the first hour of a late shift.",
                               "What does a late shift look like now.", 1)
        self.assertIn("not-invitation", self.flags(s))

    def test_an_invitation_can_be_worded_any_way(self):
        # The check stops an instruction. It does not make every script offer
        # things in the same two phrases, which is what made scripts read alike.
        for line in ("There is more here if you want it: what a late shift looks like.",
                     "Whenever you want it: what a late shift looks like.",
                     "Say what a Monday looks like now, if that is easy.",
                     "No need to take this one: what a late shift looks like.",
                     "We can go into what a late shift looks like.",
                     "Ready when you are: what a late shift looks like.",
                     "Glad to hear what a late shift looks like.",
                     "Open any time: what a late shift looks like.",
                     "A second read, if you fancy it: what a late shift looks like.",
                     "Happy to go further into what a late shift looks like.",
                     "Up to you whether we go into what a Monday looks like now."):
            s = warm_set().replace("If you'd like, walk me through the first hour of a late shift.", line, 1)
            self.assertNotIn("not-invitation", self.flags(s), line)

    def test_the_guess_never_reports_what_the_files_lack(self):
        for line in ("Your notes hold that one line and nothing else.",
                     "There are no dates or numbers in them yet.",
                     "All you have saved is one link with a title.",
                     "You ran four of these last year. That is all they say about them.",
                     "I have no example to work from yet."):
            self.assertIn("files-talk", self.flags(warm_set().replace(HEAR2, line)), line)

    def test_evidence_the_files_do_hold_is_not_files_talk(self):
        held = "Your notes have the date, 4 November, and the count: 31 calls that week, down from 60."
        self.assertEqual([], self.flags(warm_set().replace(HEAR2, held)))

    def test_a_second_ask_in_the_answer_shape(self):
        s = warm_set().replace(HOW2_TAIL, "Give one real handover, and what changed that week.")
        self.assertIn("second-ask", self.flags(s))
        self.assertNotIn("compound", self.flags(s))

    def test_two_questions_in_the_question_are_still_compound(self):
        s = warm_set().replace(Q2, Q2 + " Who noticed?")
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
        s = s.replace(HOW2_TAIL, "Give one real handover.")
        self.assertIn("no-observable", self.flags(s, "deep dive"))

    def test_an_observable_need_not_use_the_word_date(self):
        # "with the week or the count of swaps if you have it" is observable
        for asked in ("with the week it happened if you have it",
                      "with the month you last said it, if you have that",
                      "with the count of swaps that shift",
                      "something anyone could have seen from outside"):
            s = warm_set("deep dive").replace(Q3_DEEP_TAIL, "").replace(HOW2_TAIL, f"Give one real handover, {asked}.")
            self.assertNotIn("no-observable", self.flags(s, "deep dive"), asked)

    def test_the_prepared_check_alone_does_not_run_warmth(self):
        self.assertEqual([], self.flags(warm_set().replace("(my guess)", ""), warm=False))


SOFTWARE = re.compile(
    r"\b(code|codebase|coding|api|apis|deploy\w*|repo|repos|repositor\w+|commit|commits|committed"
    r"|pull request|merge|refactor\w*|debug\w*|database|server|servers|software|sprint|backlog"
    r"|endpoint\w*|developer\w*|engineer\w*|staging|rollback|outage|algorithm\w*|dashboard"
    r"|saas|startup|app|apps|product|products|users?|launch\w*|migration|kill switch)\b", re.I)


class NothingTechnical(unittest.TestCase):
    """Every example a reader of this module or the prompt meets is non-technical.

    The scripts are for writers who are not engineers, and an example written
    about shipping code teaches the wrong shape for every other reader. The
    guard is here because examples drift back towards what is easiest to write.
    """

    def assert_plain(self, label, text):
        found = sorted({m.group(0).lower() for m in SOFTWARE.finditer(text)})
        self.assertEqual([], found, f"{label} uses software words: {found}")

    def test_the_prompts_examples_are_not_technical(self):
        for i, block in enumerate(example_blocks()):
            self.assert_plain(f"prompts/interview.md example {i + 1}", block)

    def test_the_fixtures_are_not_technical(self):
        for e in qc.ENGAGEMENTS:
            self.assert_plain(f"warm_set({e})", warm_set(e))

    def test_the_plan_examples_are_not_technical(self):
        self.assert_plain("docs/plans/fireside-scripts.md", (ROOT / "docs" / "plans" / "fireside-scripts.md").read_text())

    def test_the_guard_catches_a_technical_example(self):
        with self.assertRaises(AssertionError):
            self.assert_plain("x", "Which one deploy shows the change best?")


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

    def test_the_prompt_tells_the_reader_ladder_and_the_win_shapes(self):
        text = fireside_section()
        for needle in ("audiences.md", "Segments", "Declared before inferred", "Who this is for:",
                       "What we're aiming at:", "one reader", "outcome:",
                       "the constraint, the date and the number", "the reasoning under it",
                       "stands up without the writer"):
            self.assertIn(needle, text, needle)

    def test_the_prompt_shows_the_no_audience_fallback(self):
        block = next(b for b in example_blocks() if "nothing is declared" in b)
        self.assertEqual([], qc.audience_flags(block))
        self.assertIn("one reader", block)

    def test_the_prompts_name_moves_by_technique_not_person(self):
        text = (ROOT / "prompts" / "interview.md").read_text() + (ROOT / "prompts" / "case-study.md").read_text()
        for name in ("Thompson", "Cowen", "Patel", "Klein", "Swisher"):
            self.assertNotIn(name, text)


if __name__ == "__main__":
    unittest.main()
