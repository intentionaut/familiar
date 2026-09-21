#!/usr/bin/env python3
"""Flag questions that break AGENTS.md, "Asking the writer".

Reads a prepared question file (interview-questions.md, or any markdown list of
questions) or a piece's SESSION-CONTEXT.md, where it checks the latest decision
gate. It catches the mechanical failures only. Whether the files already answer
a question is the asking stage's job; this cannot know.

  compound   more than one ask in one question
  memory     asks the writer to recall what they did rather than judge it now
  vague      an opener with no edges ("tell me more", "what are you noticing")
  internal   a theme id, a file name or a backticked label in the question
  shape      nothing says what a complete answer looks like
  not-asked  a decision gate that holds no question at all

With --prepared, the file is treated as a prepared question set and the set is
checked as a whole (see prompts/interview.md, "Prepared question sets"):

  too-many      more than three prompts
  no-receipt    a prompt that does not ask for a story, a number or an artifact
  no-challenge  no prompt challenges the premise or asks what would falsify it
  no-lede       no prompt hunts the buried lede
  no-context    no prompt interrogates the bigger context

With --warm (which implies --prepared), a set written in the fireside format
(see prompts/interview.md, "Fireside scripts") is also checked for warmth and
plain language, on the VISIBLE text only (hidden <!-- --> comments are
stripped first). Flags, by name:

  hard-to-read     Flesch reading ease of the visible text (each prompt, and the opening) is under 60
  jargon           an internal word (receipt, steelman, mechanism...) is visible
  files-talk       the visible text reports what the writer's files do not hold
  second-ask       the answer shape asks for a second thing ("one real week, and what changed")
  no-way-out       a prompt gives no way out ("rough is fine", "pass")
  no-switch        the opening does not name the "gentler" and "push me" switch
  no-listening     a prompt does not start from what the writer said, labelled a guess
  verdict-voice    the opposing case is the interviewer's verdict, not an imagined person's
  praise           a praise or hype word
  accusing         an accusing phrase
  follow-ups       the wrong number of held follow-ups for the setting
  not-invitation   a held follow-up that is not an invitation
  repeated-follow-up  a held follow-up identical to another prompt's (or its own sibling's), or one that repeats its own question
  no-position      prompt 1's guess carries no labelled position of the interviewer's own
  no-comment       the hidden comment lacks move, receipt or level
  wrong-length     the answer length asked does not match the setting
  no-gentle-doubt  companion: prompt 3 is not the gentle doubt question
  critic-at-companion  companion: prompt 3 puts a critic on the table instead of restating the writer's own idea
  no-fair-critic   fireside and deep dive: prompt 3's guess carries no imagined thoughtful person's case, or its question does not ask for a reaction
  no-mind-change   fireside and deep dive: prompt 3 does not ask what would change their mind
  no-tension       deep dive: no live tension marker pointing at the writer's own files
  tension-quote    deep dive: the tension marker quotes text instead of pointing at a file
  tension-in-text  deep dive: the tension is bracketed as missing, and the writer can still read one
  no-observable    deep dive: nothing asks for something observable with a date or number
  not-fireside-format  --warm was given but no prompt is in the fireside format

--engagement picks the setting; without it the house's `Interview engagement`
line in positioning.md is used, and unset means fireside. `Receipt:` may be a
line of its own or live in the hidden comment as `receipt: story`.

The cap of three is for a prepared set. It is not the live "ask up to three
times" follow-up rule, which counts re-asks of one question.

Usage:
  question-check.py <file> [<file> ...]
  question-check.py --prepared interview-questions.md
  question-check.py --warm [--engagement companion|fireside|"deep dive"] interview-questions.md
  question-check.py --all SESSION-CONTEXT.md   every gate, not just the latest

Exit 0 clean, 1 flagged, 2 could not run.
"""
import argparse
import importlib.util
import re
import sys
from pathlib import Path

MEMORY = re.compile(
    r"\b(remember|recall|back then|at the time|take the \w+ minutes"
    r"|what were you (looking at|doing|thinking)"
    r"|what did you (check|do|see|say|try|notice)( next| first)?"
    r"|when did you (first )?(realise|realize|notice|decide|know)"
    r"|the moment (you|of|when))\b", re.I)
VAGUE = re.compile(
    r"^\W*(\*\*)?(tell me (more|about (it|that|this|the week|your week))|what are you noticing|how (do|did) you feel"
    r"|any thoughts|thoughts\?|what('s| is) on your mind|anything else)", re.I)
INTERNAL = re.compile(r"`[^`]+`|\bT\d{1,2}\b|\b[\w-]+\.(md|py|json|html)\b")
PICK = re.compile(r"(^|\s|\*\*)A[.:)]", re.M)
SHAPE = re.compile(
    r"\b(yes or no|a number|how many|one (sentence|word|line|name|thing|moment"
    r"|decision|person|habit)|name one|which (one|of these|\w+ (survives|matters|goes|stays|first))|pick one"
    r"|or something else)\b", re.I)
RECEIPT = re.compile(r"\breceipt\b[^\n]*\b(story|number|artifact|artefact)\b", re.I)
CHALLENGE = re.compile(
    r"\b(falsif\w*|premise|where (it|this|the (piece|argument|claim)) (may|might|could) (fail|break)"
    r"|what evidence would (change|disprove|count against))", re.I)
LEDE = re.compile(r"\b(buried lede|non-obvious claim|the claim (the|your) audience (is not|isn't|has not))", re.I)
CONTEXT = re.compile(
    r"\b(why now|who (else )?(carries|bears|pays)|who benefits|what repeats|incentive|power)\b", re.I)
MAX_PREPARED = 3
LIST_ITEM = re.compile(r"^(\s{0,3})([-*+]|\d+[.)])\s+(.*)")
GATE_KEY = re.compile(r"^[A-Z][A-Za-z ]+:")


def asks(text):
    """Count the separate asks in one question."""
    body = re.sub(r"(^|\n)\s*(\*\*)?[A-D][.:)].*", "", text)  # option lines are not asks
    joined = len(re.findall(r",\s+and (why|what|how|when|who|where)\b", body, re.I))
    return body.count("?") + joined


def flags_for(text):
    out = []
    first = text.strip().splitlines()[0] if text.strip() else ""
    if "?" not in text:
        return ["not-asked"]
    if asks(text) > 1:
        out.append("compound")
    if MEMORY.search(text):
        out.append("memory")
    if VAGUE.search(first):
        out.append("vague")
    if INTERNAL.search(re.sub(r"\[(ASK THE WRITER|NEEDS SOURCE)[^\]]*\]", "", text)):
        out.append("internal")
    if not (PICK.search(text) and re.search(r"(^|\s|\*\*)B[.:)]", text)) and not SHAPE.search(text):
        out.append("shape")
    return out


def question_items(text):
    """(line number, text) for each question in a markdown list or paragraph."""
    items, cur, start = [], [], 0
    for n, line in enumerate(text.splitlines(), 1):
        m = LIST_ITEM.match(line)
        top = m and len(m.group(1)) == 0 and not re.match(r"\s*(\*\*)?[A-D][.:)]", m.group(3))
        if line.startswith("#") or not line.strip():
            if cur:
                items.append((start, "\n".join(cur)))
            cur = []
            continue
        if top:
            if cur:
                items.append((start, "\n".join(cur)))
            cur, start = [m.group(3)], n
        elif cur:
            cur.append(line.strip())
        elif "?" in line:
            cur, start = [line.strip()], n
    if cur:
        items.append((start, "\n".join(cur)))
    return [(n, t) for n, t in items if "?" in t]


def gates(text, every=False):
    found, cur, start = [], None, 0
    for n, line in enumerate(text.splitlines(), 1):
        if line.startswith("Decision gate:"):
            cur, start = [line[len("Decision gate:"):].strip()], n
        elif cur is not None and line.strip() and not GATE_KEY.match(line) and not line.startswith("#"):
            cur.append(line.strip())
        elif cur is not None:
            found.append((start, " ".join(cur)))
            cur = None
    if cur is not None:
        found.append((start, " ".join(cur)))
    found = [(n, g) for n, g in found if not re.match(r"(none|n/a)\b", g, re.I)]
    return found if every else found[-1:]


def set_flags(items):
    """Whole-set flags for a prepared question set: [(line, flag, text)]."""
    out = []
    if not items:
        return out
    for n, q in items[MAX_PREPARED:]:
        out.append((n, "too-many", q))
    for n, q in items[:MAX_PREPARED]:
        if not RECEIPT.search(q):
            out.append((n, "no-receipt", q))
    whole = "\n".join(q for _, q in items[:MAX_PREPARED])
    first = items[0]
    for flag, rx in (("no-challenge", CHALLENGE), ("no-lede", LEDE), ("no-context", CONTEXT)):
        if not rx.search(whole):
            out.append((first[0], flag, "set of prompts"))
    return out


# ---------------------------------------------------------------------------
# Fireside scripts: warmth and plain language (prompts/interview.md)
# ---------------------------------------------------------------------------

ENGAGEMENTS = ("companion", "fireside", "deep dive")
DEFAULT_ENGAGEMENT = "fireside"
READING_EASE_TARGET = 60  # knowledge/style-rules.md: Flesch 60+
ENGAGEMENT_LABEL = "Interview engagement"
LENGTH = {"companion": "30 to 60 seconds", "fireside": "1 to 2 minutes", "deep dive": "2 to 3 minutes"}
GENTLE_DOUBT = "is there anything that would make you doubt this, even a little?"

COMMENT = re.compile(r"<!--.*?-->", re.S)
FIELD = re.compile(r"^\s*(?:\d+[.)]\s+)?\*\*([^*]+?):\*\*\s*(.*)$")
BLOCK_START = re.compile(r"^\s*\d+[.)]\s+\*\*What I.m hearing")
JARGON = re.compile(
    r"\b(commodit\w*|steelman\w*|falsif\w*|receipts?|mechanisms?|plumbing|premise|lede|paradigm|stakeholders?"
    r"|epistemic|leverag\w*|framework)\b", re.I)
WAY_OUT = re.compile(r"\b(rough is fine|pass|skip|no need|not sure is fine|short is fine|fine to (say|stop|skip))\b", re.I)
PRAISE = re.compile(
    r"\b(great|brilliant|fascinating|amazing|incredible|excellent|wonderful|insightful|smart|powerful|"
    r"game-?changing|revolutionary|groundbreaking|love (that|this|it)|good question|you'?re right)\b", re.I)
ACCUSING = re.compile(
    r"(against you|you'?re wrong|you are wrong|you failed|why didn'?t you|why did you not|you should have|you missed|your mistake)", re.I)
CRITIC = re.compile(
    r"\ba (thoughtful|fair|reasonable) (person|critic|colleague|reader)\b"
    r"|\bsomeone (thoughtful|fair|reasonable)\b[^.?]*\b(might|would|could) say\b", re.I)
IMAGINED = re.compile(
    r"\b(picture|imagine|suppose)\b[^.?]*\b(person|colleague|reader|friend|critic|someone)\b"
    r"|" + CRITIC.pattern, re.I)
# The guess restates the idea and the evidence in hand. An inventory of what the
# files do not hold is the tool describing its own problem to the writer.
FILES_TALK = re.compile(
    r"\bno (dates?|numbers?|names?|examples?)\b[^.?!]{0,50}\b(yet|in (them|the files|your files|your notes))\b"
    r"|\b(nothing|no example|not much|little)\b[^.?!]{0,40}\bto (work from|go on)\b"
    r"|\byour (notes|files|brief|log|records?)\b[^.?!]{0,60}\b(nothing else|only that|just that|one line)\b"
    r"|\bthat('s| is) all (they|it) (say|says)\b"
    r"|\ball (you have|you've) (saved|got)\b", re.I)
# A tension named in what the writer reads, for the case where the marker says
# there are no two statements to name.
TENSION_TEXT = re.compile(
    r"\btwo things (you|in your)\b|\bsits? (oddly|awkwardly)\b|\byou('ve| have) said both\b"
    r"|\bI (also )?notice you say\b|\byou also say\b", re.I)
POSITION = re.compile(r"\b(my (own )?(position|view|take)|I lean|I suspect|I'd guess|I would guess)\b", re.I)
REACTION = re.compile(
    r"\b(react\w*|make of (it|that|this)|think of (it|that|this)|land\w*|sit with you"
    r"|how much of (that|this)|your (read|take) on (that|this)|(that|this) holds?)\b", re.I)
VERDICT = re.compile(r"\bI (think|believe|doubt|say) (that )?(you|this|it|the)\b|\bthe (real )?problem (is|with)\b", re.I)
# An invitation, not an instruction. Written as two wide tests rather than a list
# of accepted phrasings: a fixed list made every script offer things in the same
# two ways, which is its own failure. A follow-up is an invitation unless it
# offers nothing at all, or reads as a bare order.
OFFER = re.compile(
    r"\b(if|when|whenever|any ?time|only|up to you|feel free|no need|happy|glad|ready|open|available"
    r"|fancy|room|more (here|on this)|worth (hearing|a look)|second read|no pressure|your call"
    r"|in your own time|spare|sometime)\b", re.I)
MODAL = re.compile(r"\b(would|could|can|might|may)\b", re.I)
OBSERVABLE = re.compile(r"\b(date|dated|number|how many|how much|by when)\b|\d", re.I)
GUESS = re.compile(r"\b(guess|as i understand|i might be wrong|tell me if)\b", re.I)


def _load_paths():
    spec = importlib.util.spec_from_file_location("familiar_paths", Path(__file__).with_name("paths.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def normalise_engagement(value):
    v = re.sub(r"[\s_-]+", " ", (value or "").strip().lower())
    if v not in ENGAGEMENTS:
        raise ValueError(f"unknown engagement {value!r}; use one of: companion, fireside, deep dive")
    return v


def house_engagement(knowledge_dir=None):
    """The house's `- Interview engagement:` value from positioning.md, or None.

    Unset, absent or still the shipped bracketed placeholder is None, the same
    convention notion_board.read_field uses: a value that starts with `[` is unset.
    """
    kdir = Path(knowledge_dir) if knowledge_dir else _load_paths().knowledge_dir()[0]
    f = kdir / "positioning.md"
    if not f.is_file():
        return None
    m = re.search(rf"^- {re.escape(ENGAGEMENT_LABEL)}:[ \t]*(.*?)[ \t]*$", f.read_text(encoding="utf-8"), re.M)
    if not m or not m.group(1) or m.group(1).startswith("["):
        return None
    return normalise_engagement(m.group(1))


def resolve_engagement(override=None, knowledge_dir=None):
    """Per-run override, then the house, then fireside."""
    if override:
        return normalise_engagement(override)
    return house_engagement(knowledge_dir) or DEFAULT_ENGAGEMENT


def step_engagement(current, request):
    """Move one step for "gentler" or "push me"; stop at the ends. Returns (new, changed).

    The caller logs one line in notes.md when changed is True.
    """
    i = ENGAGEMENTS.index(normalise_engagement(current))
    r = re.sub(r"\s+", " ", request.strip().lower())
    if r == "gentler":
        j = max(0, i - 1)
    elif r == "push me":
        j = min(len(ENGAGEMENTS) - 1, i + 1)
    else:
        raise ValueError(f"unknown request {request!r}; use 'gentler' or 'push me'")
    return ENGAGEMENTS[j], j != i


def count_syllables(word):
    """Heuristic English syllable count: vowel groups, less a silent final e, at least one."""
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    n = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and not w.endswith(("le", "ee", "ye")) and n > 1:
        n -= 1
    elif re.search(r"[^aeiouy]ed$", w) and not re.search(r"[td]ed$", w) and n > 1:
        n -= 1
    return max(1, n)


def reading_ease(text):
    """Flesch reading ease: 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words).

    Words are runs of letters (apostrophes kept). A sentence ends at . ! or ?
    (or the end of the text); syllables come from count_syllables. Higher is
    easier; knowledge/style-rules.md asks for 60 or more. Empty text scores 100.
    """
    words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)*", text)
    if not words:
        return 100.0
    sentences = max(1, len([s for s in re.split(r"[.!?]+(?:\s+|$)", text.strip()) if re.search(r"[A-Za-z]", s)]))
    syll = sum(count_syllables(w) for w in words)
    return 206.835 - 1.015 * (len(words) / sentences) - 84.6 * (syll / len(words))


def is_invitation(text):
    """A held follow-up offers something rather than ordering it.

    "Explain a Monday now" offers nothing. Everything that holds a condition, a
    permission or a modal passes, however it is worded.
    """
    return bool(OFFER.search(text) or MODAL.search(text))


def _norm(text):
    return " ".join(re.findall(r"[a-z']+", text.lower()))


def strip_hidden(text):
    return COMMENT.sub("", text)


def warm_blocks(text):
    """(opening, [(line, block_text)]) for a set in the fireside format."""
    lines = text.splitlines()
    starts = [i for i, l in enumerate(lines) if BLOCK_START.match(l)]
    if not starts:
        return text, []
    opening = "\n".join(lines[:starts[0]])
    blocks = []
    for k, s in enumerate(starts):
        end = starts[k + 1] if k + 1 < len(starts) else len(lines)
        chunk = []
        for l in lines[s:end]:
            if l.startswith("#") or (chunk and not l.strip()):
                break
            chunk.append(l)
        blocks.append((s + 1, "\n".join(chunk)))
    return opening, blocks


def parse_block(block):
    """Visible fields by lowercased label, plus the hidden comment text."""
    hidden = " ".join(COMMENT.findall(block))
    fields = {}
    for l in strip_hidden(block).splitlines():
        m = FIELD.match(l)
        if m:
            fields[m.group(1).strip().lower()] = m.group(2).strip()
    return fields, hidden


def _field(fields, prefix):
    return next((v for k, v in fields.items() if k.startswith(prefix)), "")


def warm_flags(text, engagement):
    """Warmth and plain-language flags for a fireside-format set: [(line, flag, detail)]."""
    engagement = normalise_engagement(engagement)
    opening, blocks = warm_blocks(text)
    out = []
    parsed = [parse_block(b) for _, b in blocks]
    vis_opening = strip_hidden(opening)
    if not (re.search(r"\bgentler\b", vis_opening, re.I) and re.search(r"\bpush me\b", vis_opening, re.I)):
        out.append((1, "no-switch", "opening does not name 'gentler' and 'push me'"))
    # Reading ease is scored on the visible text only, per prompt and for the
    # opening, so one dense question cannot hide behind easy ones.
    scored = [(1, "the opening", vis_opening)]
    scored += [(n, f"prompt at line {n}", " ".join(f.values())) for (n, _), (f, _) in zip(blocks, parsed)]
    for n, label, body in scored:
        if not body.strip():
            continue
        score = reading_ease(re.sub(r"\[[^\]]*\]", "", body))
        if score < READING_EASE_TARGET:
            out.append((n, "hard-to-read", f"{label}: reading ease {score:.1f}, target {READING_EASE_TARGET}+"))
    for (n, _), (fields, hidden) in zip(blocks, parsed):
        vis = " ".join(fields.values())
        hearing, question, how = _field(fields, "what i"), _field(fields, "question"), _field(fields, "how to answer")
        held = [(k, v) for k, v in fields.items() if k.startswith("held")]
        if m := JARGON.search(vis):
            out.append((n, "jargon", m.group(0)))
        if m := FILES_TALK.search(vis):
            out.append((n, "files-talk", m.group(0)))
        if not WAY_OUT.search(how):
            out.append((n, "no-way-out", how[:80]))
        first_label = next(iter(fields), "")
        if not hearing or not first_label.startswith("what i") or not GUESS.search(first_label + " " + hearing):
            out.append((n, "no-listening", "starts without a labelled guess at what the writer said"))
        if m := PRAISE.search(vis):
            out.append((n, "praise", m.group(0)))
        if m := ACCUSING.search(vis):
            out.append((n, "accusing", m.group(0)))
        if VERDICT.search(hearing + " " + question):
            out.append((n, "verdict-voice", (hearing + " " + question)[:80]))
        lo, hi = (1, 2) if engagement == "companion" else (2, 2)
        if not lo <= len(held) <= hi:
            out.append((n, "follow-ups", f"{len(held)} held follow-ups"))
        for k, v in held:
            if not is_invitation(v):
                out.append((n, "not-invitation", v[:80]))
        if n == blocks[0][0] and not POSITION.search(hearing):
            out.append((n, "no-position", "prompt 1 needs a labelled position of the interviewer's own to react to"))
        for k, v in held:
            key = _norm(v)
            others = [_norm(ov) for (on, _), (of, _) in zip(blocks, parsed) if on != n
                      for ok, ov in of.items() if ok.startswith("held")]
            same_prompt = [_norm(ov) for ok, ov in held if ok != k]
            qn = _norm(question)
            if key in others or key in same_prompt or (qn and (qn in key or key in qn)):
                out.append((n, "repeated-follow-up", v[:80]))
        if not all(re.search(rf"\b{w}\s*:", hidden, re.I) for w in ("move", "receipt", "level")):
            out.append((n, "no-comment", "hidden comment needs move, receipt and level"))
        if not re.search(rf"(?<!\d){LENGTH[engagement]}", how):
            out.append((n, "wrong-length", f"{engagement} asks for {LENGTH[engagement]}"))
    if len(blocks) >= 3:
        n3, (f3, h3) = blocks[2][0], parsed[2]
        q3, how3 = _field(f3, "question"), _field(f3, "how to answer")
        hear3 = _field(f3, "what i")
        if engagement == "companion":
            if GENTLE_DOUBT not in " ".join(q3.lower().split()):
                out.append((n3, "no-gentle-doubt", q3[:80]))
            if CRITIC.search(hear3):
                out.append((n3, "critic-at-companion", "the gentlest setting puts no critic on the table"))
        else:
            if not IMAGINED.search(hear3 + " " + q3):
                out.append((n3, "no-fair-critic", "the guess should carry an imagined thoughtful person's case"))
            elif not REACTION.search(q3):
                out.append((n3, "no-fair-critic", "the question should ask for the writer's reaction to that case"))
            if not re.search(r"change your mind", how3, re.I):
                out.append((n3, "no-mind-change", how3[:80]))
        if engagement == "deep dive":
            hidden_all = " ".join(h for _, h in parsed)
            tm = re.search(r"tension:([^|>]*)", hidden_all, re.I)
            marker = tm.group(1) if tm else ""
            # Either it is live and names the file, or it says the two statements
            # are missing. An apostrophe is not a quotation, so only quote marks
            # count against it.
            live = re.search(r"\blive\b", marker, re.I) and re.search(r"\b[\w./-]+\.md\b", marker)
            missing = "NEEDS SOURCE" in marker
            if not (live or missing):
                out.append((n3, "no-tension", "needs `tension: live` with the file it comes from"))
            elif live and re.search(r"[\"“”]", marker):
                out.append((n3, "tension-quote", "the marker points at a file; it never quotes"))
            elif missing and TENSION_TEXT.search(hear3):
                out.append((n3, "tension-in-text", "bracketed as missing, so it stays out of what the writer reads"))
            asked = [re.sub(r"\b\d+ to \d+ (seconds|minutes)", "", v) for f, _ in parsed
                     for k, v in f.items() if k.startswith(("question", "how to answer"))]
            if not any(OBSERVABLE.search(v) for v in asked):
                out.append((n3, "no-observable", "ask for something observable with a date or number"))
    return out


def fireside_flags(line, block):
    """Mechanical flags for one fireside prompt: the question and its answer shape.

    The guess and the held follow-ups are separate fields and are not asks. Two
    differences from any other question. The "How to answer" line is the answer
    shape, so `shape` never applies. And a second ask hidden in that line ("one
    real week, and what changed") is reported as `second-ask` rather than
    `compound`, because the question itself is fine and the shape is what needs
    rewriting.
    """
    fields, _ = parse_block(block)
    question, how = _field(fields, "question"), _field(fields, "how to answer")
    joined = question + " " + how
    out = [(line, f, joined) for f in flags_for(joined) if f not in ("shape", "compound")]
    if asks(question) > 1:
        out.append((line, "compound", question))
    elif asks(how + "?") > 1:
        out.append((line, "second-ask", how))
    return out


def check(path, every=False, prepared=False, warm=False, engagement=None, knowledge_dir=None):
    text = Path(path).read_text()
    fireside = False
    if warm:
        prepared = True
    if Path(path).name == "SESSION-CONTEXT.md":
        items = gates(text, every)
    elif warm_blocks(text)[1]:
        items, fireside = warm_blocks(text)[1], True
    else:
        items = question_items(text)
    if fireside:
        found = [f for n, b in items for f in fireside_flags(n, b)]
    else:
        found = [(n, f, q) for n, q in items for f in flags_for(q)]
    if prepared and Path(path).name != "SESSION-CONTEXT.md":
        found += set_flags(items)
    if warm and fireside:
        found += warm_flags(text, resolve_engagement(engagement, knowledge_dir))
    elif warm and Path(path).name != "SESSION-CONTEXT.md":
        found.append((1, "not-fireside-format", "no prompt starts with **What I'm hearing (my guess):**"))
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--all", action="store_true", help="every decision gate, not only the latest")
    ap.add_argument("--prepared", action="store_true",
                    help="also check the file as a prepared set: at most three prompts, a receipt in each, a premise challenge")
    ap.add_argument("--warm", action="store_true",
                    help="implies --prepared; also check a fireside-format set for warmth and plain language")
    ap.add_argument("--engagement", help="companion, fireside or deep dive; default is the house setting, else fireside")
    ap.add_argument("--house", help="knowledge folder to read the engagement setting from (default: resolved like paths.py)")
    a = ap.parse_args()
    total = 0
    for f in a.files:
        try:
            found = check(f, a.all, a.prepared, a.warm, a.engagement, a.house)
        except (OSError, ValueError) as e:
            print(f"question-check could not run on {f}: {e}", file=sys.stderr)
            return 2
        for n, flag, q in found:
            print(f"{f}:{n}: {flag}: {q.splitlines()[0][:100]}")
        total += len(found)
    if total:
        print(f"\n{total} flag(s). Rewrite per AGENTS.md, \"Asking the writer\", before the writer sees them.")
        return 1
    print("question-check: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
