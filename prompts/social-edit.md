# Stage: social-edit (the pass a post gets before it ships)

The edit stage for short posts. `dev-edit` and `line-edit` do this for a piece,
and posts went without one, which is why an assembled post could reach a
scheduler having been checked for em dashes and nothing else.

**This stage runs in the conversation.** It writes no report file. A report is
the right shape for a 1,200 word draft read against a marked-up copy; it is the
wrong shape for a five-line post, where reading the report costs more than
reading the post. Findings are shown, answered and applied here, one post at a
time, and only the result is written down.

It runs inside `social` at gate 2, and on its own for a post that changed after
approval. Both are the same pass.

## Setup

1. Read AGENTS.md, knowledge/social-rules.md, knowledge/style-rules.md,
   knowledge/voice-guide.md, knowledge/positioning.md,
   knowledge/social-schedule.md, knowledge/examples/canonical.md.
   Check `Language:` in positioning.md; if it is not English, read
   `knowledge/languages/<code>.md` and apply its skip/keep/replace table before
   anything marked (en) in style-rules.md.
2. Work out what you are editing. `$ARGUMENTS` may name a piece folder, a
   channel and a day ("linkedin friday"), a candidate id ("C1"), or nothing.
   With nothing: every post under `## Chosen` in the newest `social.md` that has
   not shipped yet. Say what you picked up and how many posts it is.
3. If the post is already in a scheduler, say so before you start. It can still
   be edited, and `publish` is what puts a change back; this stage never
   touches a scheduler.

## Method

### First, the week

Test 4 from social-rules.md, before any single post. It is the only test that
cannot be run on a post alone, and it is the one most likely to change what you
do with the individual posts, because a repetition found here is usually fixed
by rewriting one post rather than trimming both.

Report it in a line or two: what repeats, in which posts, and which one you
would change. If nothing repeats, one line saying so.

### Then each post, in order

For each, run tests 1 to 3 from social-rules.md, then the mechanical sweep from
style-rules.md and the channel's limit from social-schedule.md.

**If it passes test 1**, show the findings inline, in style-rules.md's format:

```
"<quoted text>"
Issue: <rule or test>
Why it matters: <one sentence>
Fix: <the exact rewritten line, in the writer's voice>
```

Then stop and let the writer take each one. Apply what they accept, verbatim.
Nothing is applied before they answer, including mechanical findings: a quiet
fix is a decision made on the writer's behalf about their own voice.

If a post genuinely has nothing wrong with it, say which tests it passed and
that it is ready. Never say only "clean". A pass has to show what it checked or
it is indistinguishable from not having run.

**If it fails test 1**, do not list findings. Go to the pick.

### The pick

Per social-rules.md, "When a post has no single viewpoint", and AGENTS.md,
"Offering options, and recording the pick".

Two to four viewpoints the material already supports, each written out: the
opening line as it would stand, plus one line on where the post goes. `Buys:`
and `Costs:` on each. An escape at the end. One letter is a complete answer.

Say in one line why the post as it stands has no single viewpoint, and name the
ideas you found in it. That is what makes the options readable.

### Then the questions

At most two, one at a time, after the writer has picked.

They ask for judgement, never for recall. What happened is in the piece, the
notes, the context log or the record, and finding it is your job, not a
question. Ask what they think, what they would say to one person about this,
what they want the reader left holding, which of two readings they meant.

If the answer to the first question is enough, do not ask the second.

### Then write it

One post, from their answers, in their words wherever their words will carry
it. Voice guide exactly. Run the mechanical sweep and the character count on
what you wrote before showing it. Show the post and say what you took from
which answer, in a line.

The writer approves, edits or sends you back. An edit they make is applied
verbatim, and anything they changed goes through the mechanical sweep again.

## Rules

- **Never produce a clean version.** Same rule as every edit stage. The writer
  accepts, rejects or revises.
- **Never invent evidence or a quote** to make a post work. `[NEEDS SOURCE: ]`
  and `[ASK THE WRITER: ]`, as everywhere else.
- **A rewrite that loses a specific is not a rewrite.** style-rules.md,
  "Tightening that costs a specific". Posts are where this does the most damage,
  because the pressure to be short is constant and a number is the easiest thing
  to drop.
- **False positives cost more here than in a piece.** A post is short enough
  that one wrong flag is a large fraction of the conversation. When you cannot
  tell a tell from the writer's dry wit, say UNCERTAIN and give your reasoning.
- **Do not touch a post the writer did not ask you to touch.** If the week test
  says two posts repeat, name both and change one, the one the writer picks.

## Exit

Write the approved copy back into `social.md` under `## Chosen`, replacing what
was there. That section is what `publish` reads, so it holds approved copy and
nothing else.

Everything else goes in the same file, below:

- Any viewpoint pick, as an options block with `Chosen` and `Because` in the
  writer's own words. The options they turned down stay; they are the record of
  what was considered.
- One line per post on what changed, or that nothing did.

If a post that was already scheduled has changed, say so plainly at the end,
name the posts, and say that `publish` is what puts the change back. Do not
schedule anything from here.

Then one line: how many posts you read, how many changed, and whether anything
is still open.

- **Context log:** append to the piece's own `SESSION-CONTEXT.md` per
  knowledge/context-log.md (status, files touched, what changed, the decision
  gate for the writer, next stage: `publish` if copy is approved and unscheduled,
  otherwise none).
