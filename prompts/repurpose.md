# Stage: repurpose

One finished piece, two ways to reuse it. The first thing this stage does is
find out which. It never guesses.

| Choice | What it means | Where it goes |
|---|---|---|
| **short** | A week of posts on the writer's cadence | `prompts/social.md`, unchanged |
| **long** | A companion longform piece for a second channel | the long branch below |

## The choice (gate 0)

`$ARGUMENTS` may name it: `repurpose short`, `repurpose long <channel>`,
optionally followed by a piece folder. If it does, take it and go.

If it does not, ask in one line and stop:

> Short-form or long-form? Short is a week of posts on your cadence. Long is a
> companion piece for another channel, built from how this one was made.

Do not proceed on an assumption. A writer who wanted posts and got a 1,200-word
companion draft has lost the afternoon.

---

# Short branch

Hand off. Read `prompts/social.md` and follow it exactly, including both of its
gates. Nothing about the social stage changes because it was reached from here.

---

# Long branch

Turn the piece, and the working files that produced it, into a briefed,
question-ready starting point for a **different longform piece on a different
channel**. You do NOT write that piece. You prepare it: read the working files,
write a brief and drafted interview questions, then hand off to /interview.

## Why this branch is a seeder, not a generator

The material for a companion piece is the record of how the first piece was
made: the thesis that changed, the argument that got cut, the outline nobody
picked, the thing that turned out to be false. Those files say **what**
happened. They do not say why it mattered, what it felt like, or what the
writer now thinks. That half only exists in the writer's head, and a model
asked to write a making-of will invent it fluently.

So this branch stops where the evidence stops, and the standard gated pipeline
does the rest: interview, outline, draft, dev-edit, line-edit. Do not shortcut
it. A companion piece drafted straight from the working files is the failure
mode this branch exists to prevent, and the writer will be reworking it a dozen
times to get their own voice back into it.

## Setup

1. Read knowledge/positioning.md and knowledge/voice-guide.md.
2. Read knowledge/longform-channels.md and find the channel named in
   `$ARGUMENTS`. It gives the channel's job, form, length, audience and CTA.
   If the file is still the unfilled template, or the channel is not in it,
   stop and ask the writer to fill it in. Do not guess a form.
3. Take the source piece from `$ARGUMENTS`, or the newest `pieces/*/` with a
   finished draft.
4. Read, in this order, and note which exist:
   - `draft.md` and any `final.md`: what actually shipped.
   - `notes.md`: the interview, the thesis, superseded theses, open questions.
   - `outline.md`: every structure, including the ones not chosen, and the
     stated risk of each.
   - `edits/*.md`: every report, and what the writer accepted or rejected.
   - `SESSION-CONTEXT.md`: the decision trail, in order, with timestamps.
   - Superseded or hidden drafts beside the piece.
   - `git log` for the piece folder, if it is in a repository.

## What you are looking for

Six things. Each is a candidate spine.

1. **A thesis that changed.** Quote the superseded thesis and the final one,
   and find the moment where it turned.
2. **Material that was cut.** The strongest deletions, verbatim, and where they
   live now. Cut writing is not failed writing; it is usually writing for a
   different piece.
3. **A structure that was rejected.** What was offered, what was picked, and
   the risk that decided it.
4. **A thing that turned out to be false.** A claim that did not survive
   sourcing, a citation that could not be found, a fact the writer corrected.
5. **What it cost.** Rewrites, restarts, passes, anything the context log
   records about effort.
6. **What is next.** Briefs spawned, open questions, the piece the cut material
   is waiting to become.

Record the verbatim text and the file for each. If you cannot source it, it does
not go in the brief.

## Write brief.md

Into a **new** piece folder, `pieces/YYYY-MM-DD-<slug>/`, named for the
companion piece, not the source. Never write into the source piece's folder.

```
# Brief: <companion working title>

## Source
Which piece, which channel, and the channel's job in one line.

## The standalone rule
This channel's reader has not read the source piece. Restate the constraint
from longform-channels.md so every later stage sees it.

## What happened (sourced)
The six things above, each with verbatim quotes and file paths. Mark each
"have" or "needs the writer".

## Candidate spines
Two or three, one line each: what the companion could be about, and which of
the six it is built on.

## What only the writer has
The questions the files cannot answer: why a decision was made, what it felt
like, what they would do differently, what they now think.

## Do not assume
Anything a reader of the working files might infer that is not actually
stated, listed so no later stage treats it as fact.
```

## Write interview-questions.md

Six to ten questions, ordered, each aimed at a gap the files cannot fill. The
first goes after lived experience, per prompts/interview.md. Ask about the
decision the writer actually made, not about the topic in general.

Bad: "What did you learn from the thesis changing?"
Good: "You cut the whole argument section and called it bad. What did you see
in it that made you say that?"

Follow the interview stage's rule: ask up to three times, and make the third
ask a different angle rather than the same question again.

## Rules for the long branch

- Never invent the making-of. No reconstructed feelings, no tidy narrative of a
  process that was messier than the files show. `[ASK THE WRITER: ...]`.
- Never quote the writer saying something they did not write. Quotes are
  verbatim from the working files, or they are brackets.
- The companion is not a summary of the source and must never become one. If
  the only spine you can find is "here is what the piece said", say so and
  stop. There is no companion piece this time, and that is a real answer.
- Do not write to the source piece's folder, and do not edit the source piece.

## Exit (long branch)

- Save brief.md and interview-questions.md in the new piece folder.
- Do NOT ask the writer anything else and do NOT run the interview. Hand off:
  tell the orchestrator to run /interview on the new piece folder, passing
  interview-questions.md as the seed and brief.md as context.
- One line: which source piece, which channel, how many sourced items the brief
  carries, how many questions are waiting.
- **Context log:** append to the new piece's own `SESSION-CONTEXT.md` per
  knowledge/context-log.md (status, files touched, what changed, decision gate,
  next stage = interview). Also append one line to the **source** piece's
  SESSION-CONTEXT.md recording that a companion was seeded from it, so the
  source piece's trail shows where its cut material went.
