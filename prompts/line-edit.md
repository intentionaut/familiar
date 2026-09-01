# Stage: line-edit (mechanical pass)

The pattern screen. Run this after the developmental edit is resolved and the
draft is stable. This is a top-edit pass:
mechanical, exhaustive, boring on purpose.

## Setup

1. Read the piece's draft.md (newest `pieces/*/` if not given).
2. Read knowledge/style-rules.md and knowledge/voice-guide.md. Check `Language:`
   in knowledge/positioning.md; if not English, read `knowledge/languages/<code>.md`
   and apply its skip/keep/replace table before anything marked (en).

**Scope:** if `$ARGUMENTS` names a section, heading or paragraph, work on that part only and leave everything else in the file untouched. Say which part you worked on. If the target file already has content and no scope is given, ask before replacing it: replace, add to, or write a numbered variant beside it.

## Method

Sweep the entire draft against every rule in knowledge/style-rules.md:

- Em dashes (absolute)
- American spellings
- Banned/hype vocabulary
- Every AI-tell pattern listed there
- Unsourced quotes, statistics, factual claims
- Reading ease and grade level (report the numbers)

For each finding output exactly:

```
[line N] "<quoted text>"
Issue: <rule or pattern>
Why it matters: <one sentence>
Fix: <exact rewritten line in the writer's voice>
```

For hedged positions where they could take a firmer stance, use this instead:

```
[line N] "<quoted text>"
Issue: hedge → could be a firm position
Why it matters: <one sentence on what a firmer stance changes>
Tradeoff: <the two (or more) defensible positions and what each costs>
Question to the writer: <ask them to choose a side>
```

Do not quietly firm up a hedge for them. Surface the tradeoff and let them decide the stance.

## Rules

- Every flag gets a concrete rewritten line. Vague notes are useless.
- Do not touch anything outside the checklist: structure and argument belong to dev-edit.
- If a fragment or staccato list is doing deliberate work in their voice, leave it and note that you left it.
- False positives are worse than missed flags. When unsure whether something is an AI tell or their dry wit, flag it as UNCERTAIN with your reasoning.
- A firm stance is not stridency. It is a position with a reason they can defend. When a hedge hides a real choice with tradeoffs, ask them which way they want to lean.

**Options.** Where this stage reaches a choice with more than one defensible
answer, write it as an options block per AGENTS.md, "Offering options, and
recording the pick": fully written alternatives, `Buys:` and `Costs:` on each,
and `Chosen` with `Because` once the writer picks. Never only in conversation.

## Exit

Write to `edits/line-edit-report.md`: findings, then the summary table from the
spec (flags per category, reading ease, grade level, top three highest-impact fixes).
They apply what they agree with. Nothing is auto-applied.

Then ask whether to open the report and the draft, one line, yes or no. See
AGENTS.md, "Opening the file at an edit stage". Open both on yes; drop it on no.

- **Context log:** append to the piece's own `SESSION-CONTEXT.md` per
  knowledge/context-log.md (status, files touched, what changed, the decision
  gate for the writer, next stage). Terse; this is what makes the article easy to
  resume later.
