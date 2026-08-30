# Stage: case-study (from a build log or a coding session)

Turn a Captain's Log build log, or a Claude Code session transcript, into a
briefed, question-ready starting point for the standard interview stage. You do NOT run the interview. You prepare it:
read the log, write a brief and a set of drafted interview questions, then hand
off to /interview so the human can follow the normal one-question-at-a-time
process.

## Setup

1. Read knowledge/positioning.md and knowledge/voice-guide.md. You need the
   scope in positioning.md and the voice to classify the
   material and to phrase questions that draw specifics.
2. Take the source from $ARGUMENTS. It is one of:
   - a Captain's Log build log (`<PROJECT>-LOG.md`), optionally followed by a
     path to a REFLECTIONS.md. If only the log is given, look alongside it for
     a REFLECTIONS.md, or use the inline "<NAME>'s notes" sections.
   - a Claude Code session transcript (`.jsonl`), or the word `session` with
     an optional project folder, meaning the most recent session for that
     project. Run `scripts/session-digest.py <transcript> <piece>/session.md`
     (or `--latest <project-dir>`) and read the digest, not the raw file. The
     digest is what was said, in order, with tool use collapsed to a line
     each. A transcript has no "Went wrong" section; you find the wrong turns
     yourself, in the moments where the writer changed direction, corrected
     the assistant, or an error came back. Quote those moments.
   Several sources may be given together; a log plus the session that
   produced it is the strongest starting point there is.
3. Create or reuse `pieces/YYYY-MM-DD-short-slug/` (today's date; slug from the
   project named in the log). Write brief.md and interview-questions.md into it.

## Method

- Read the whole source. In a log, pay attention to: "Went wrong" (the agent's
  own mistakes and their cost), "Numbers" (anything measurable), "Decisions"
  (what was chosen and rejected, and why), and the human's own notes (a
  verbatim voice reference). In a session digest, the same things are there
  but unlabelled: the writer's own messages are the voice reference and the
  decisions; corrections and errors are the wrong turns; anything counted or
  timed is a number. Mark every item from a transcript as reconstructed, the
  way a log marks entries rebuilt from git history: it records what happened,
  and the reasoning only if it was said out loud.
- Build **brief.md**:
  - Intersection: which of the house's themes drives this, which are secondary,
    one sentence naming where they cross (mirror the interview exit schema).
  - Candidate theses: 2-3, each drawn strictly from something in the log, each
    with the entries it rests on. Say which you'd lead with and why.
  - Evidence inventory: bullet each concrete fact (a number, a wrong turn and its
    cost, a rejected approach) with status have / needs finding.
  - Contradictions: if the human's notes disagree with an earlier entry or with
    each other, flag it. That's where a view is changing, and it's interview gold.
- Draft **interview-questions.md**: an ordered list, one question per line, each
  grounded in a specific log entry. Follow Captain's Log's own interview rules:
  chase specifics (names, numbers, the moment of realising); ask about the ten
  minutes after a mistake, not "tell me more"; mark gaps that would need an
  [ASK THE WRITER: …] versus [NEEDS SOURCE: …]. Aim for 8-12 questions; the live
  interview will trim and reorder.

## Exit

- Save brief.md and interview-questions.md.
- Do NOT ask the human anything and do NOT run the interview. Instead hand off:
  tell the orchestrator to run /interview on this piece folder, passing
  interview-questions.md as the question seed and brief.md as context. /interview
  runs its normal one-question-at-a-time method to produce notes.md.
- Context log: append to SESSION-CONTEXT.md per knowledge/context-log.md (status,
  files touched, decision gate, next stage = interview).
