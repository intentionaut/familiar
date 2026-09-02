# Stage: social

Turn a finished piece (or, on a quiet week, the back catalogue) into a week of
posts across the channels in `knowledge/social-schedule.md`. One stage, three
moves, two gates:

1. **Pool**: building blocks, then one blended pool of candidates tagged by
   channel, in voice, self-checked. Shown, not filed yet.
2. **Shortlist** *(gate)*: the writer picks the posts for each channel and
   names the week.
3. **Finalise**: map the picks onto that week's slots, finish the copy, propose
   exact send times. *(gate)* The writer edits and approves each one.

This stage ends at approved copy. Getting it into a scheduler is the `publish`
stage, which exists so that scheduling can be re-run, deferred or done a week
later without anyone re-opening copy the writer already said yes to. Never skip
a gate.

This stage only produces the **scheduled posts**. Replies, quote-posts and
conversation are the writer's live work, not this stage's.

**A post that changes after gate 2 comes back through `social-edit`**, including
one already sitting in a scheduler. Facts move, dates slip, a link starts
resolving, and the post gets reworked out of parts to match. That is the moment a
post becomes two posts welded together, and it is the moment the pass is easiest
to skip because the copy was approved once already. Reworking a scheduled post is
writing a new one; run `social-edit` on it, then `publish` to put it back.

**Precondition: the title is settled.** These posts point at the piece by name,
and a title that changes afterwards leaves scheduled copy pointing at something
that no longer exists. If `draft.md` has `title_settled: false` or no such
field, say so and offer `finalise` first. The writer may override.

## Setup

1. Read AGENTS.md, knowledge/style-rules.md, knowledge/social-rules.md,
   knowledge/voice-guide.md, knowledge/positioning.md,
   knowledge/social-schedule.md, knowledge/examples/canonical.md.
   Internalise the voice before writing.
2. If `social-schedule.md` is still the unfilled template (bracketed
   placeholders in the Channels or Cadence tables), stop and ask the writer to
   fill in channels, cadence and times first. Do not guess a cadence.
3. Work out which piece and which week:
   - `$ARGUMENTS` may name a piece folder and/or a week ("next", a Monday date).
   - Default piece: the newest `pieces/*/` with a finished `draft.md`.
   - Default week: the Monday coming. Check the piece's `draft.md` frontmatter
     `date:` against that week to decide whether a piece ships this week.
4. Quiet week with no new piece: draw from the back catalogue named in
   `social-schedule.md` (or from earlier `pieces/*/` if none is named) and from
   canonical examples. Say which pieces you drew from.

## Part 1: The pool

### Building blocks (raw material, not posts)

- Quotable lines: 3 to 5 sentences from the source that stand alone.
- Proof points: each claim with its evidence, ready to cite.
- The spark line, isolated.

### Candidate posts

Generate one blended pool, sized per `social-schedule.md` (about twice the
number of slots), each candidate tagged with the channel(s) it suits. Use the
channel short codes from the schedule file. A candidate that works on two
channels carries the long text and then a separate rewrite for the shorter
channel; a short-channel post is never a truncated long one.

Spread candidates across the slot shapes in the schedule file (pillar, tease,
story, contrarian, question, quote, proof, hook, evergreen). Include at most
one thread candidate, only if the pillar idea needs the room; every post in it
must stand alone.

For each candidate:

```
### C<n> · [<channel tags>] · <shape>
<the full post text; for a multi-channel candidate, the long text, then
 "--- <short channel>:" and the rewrite; for a thread, number the posts 1/ 2/ 3/>

link: [the piece's URL if known, else [ADD POST URL]]
chars: <count per channel>
viewpoint: <the one thing this post says, in a sentence. If it needs an "and",
            the candidate is two posts and does not go in the pool>
review: <nothing, or what it fails and why>
```

Rules for every candidate:

- Built from something the source actually says. No new claims, no invented
  quotes or numbers.
- voice-guide.md exactly. No AI tells, no hype vocabulary, no résumé drops.
- Every post on a short channel makes sense to someone who has not read the
  piece. Only the tease may lead with the publication.
- Run each through style-rules.md and tests 1 to 3 of social-rules.md before
  listing it. Note what a candidate fails as `review: <reason>`. Do not fix it
  here: a candidate is raw material and the writer may not pick it. The real
  pass is `social-edit` at gate 2, on the posts they did pick.
- If the schedule file says an account is shared with the writer's personal
  posts, write work-topic posts only.

### Gate 1

Stop. Present the building blocks and the numbered pool. Say which candidate
you would put in each slot and why, in a line each. Then ask the writer to pick
for each channel and confirm the week. Do not proceed until they answer.

## Part 2: Finalise

Once the writer has picked and named the week:

### Map to slots

Read `social-schedule.md` for that week's slot shapes, send times and
timezone. Assign each pick to its day. If a pick fits a different day better,
say so and let the writer move it.

### Finish each post

- Resolve `[ADD POST URL]` to the real link. If still unknown, keep the marker
  and flag that the schedule cannot complete without it.
- Tighten flab. Keep proof points and endings.
- For a pillar post on a long channel, add a one or two line first comment for
  pinning (the link plus a one-line takeaway), same voice and rules.
- Confirm every post is within its channel's limit from the schedule file. For
  a thread, confirm each post individually and that each stands alone.
- Report character counts. Flag anything over a limit.

### Propose the schedule

One table per channel:

| # | Day | Date | Time (<timezone>) | Shape | Chars | Post opens |
|---|-----|------|-------------------|-------|-------|------------|

Convert each send time to the exact ISO timestamp a scheduler would need. List
any assumption ("piece ships Wednesday 3 September").

### Gate 2

**Run `social-edit` on the picked posts before showing anything.** Read
`prompts/social-edit.md` and follow it: the week as a set first, then each post
against social-rules.md and style-rules.md. A post that has no single viewpoint
gets a pick and two questions there, not a list of fixes here.

This is the gate. It is not passed by a self-check: a post reaches the schedule
tables once the writer has answered every finding on it, and "clean" is not
something this stage may conclude about its own work without showing what it
checked.

Then show the finished posts and the schedule tables. Ask the writer to edit
inline and approve each one. Apply their edits verbatim. Anything they changed
goes back through the mechanical sweep.

### Hand off to publish

Only after every post is approved. This stage does not schedule anything.

Write the approved copy and the schedule tables into `social.md` under
`## Chosen`, which is the section `publish` reads. Everything the writer did not
pick goes under a clearly separate heading (`## Held` or `## Candidate pool`);
`publish` ignores those by design, so a held post cannot be scheduled by
accident.

Leave any unresolved link as its marker rather than guessing. `publish` builds
every URL, appends tracking parameters and counts the finished string before it
schedules, which is where an unresolved link gets caught.

Then say, in one line: the copy is approved and `publish` will schedule it.

## Exit

Write `social.md` in the piece folder (for a quiet week, in a dated folder
`pieces/<monday-date>-social/`):

```
# Social: <piece title or "quiet week of <date>">
## Building blocks
## Candidate pool (all of them, with tags, shape, self-check)
## Chosen (final copy per channel, first comment if any, threads numbered)
## Schedule (a table per channel, with slots and timestamps)
## Held (anything finished but deliberately not run this week, and why)
## Email framing (two sentences the writer could send someone directly)
```

`## Chosen` and `## Schedule` are what `publish` reads. `## Held` and
`## Candidate pool` are what it must ignore, so keep the headings distinct.

Then one line: the copy is approved, what is in it, and anything still missing
before it can be scheduled (a link that has not resolved, a channel not
connected).

- **Context log:** append to the piece's own `SESSION-CONTEXT.md` per
  knowledge/context-log.md (status, files touched, what changed, the decision
  gate for the writer, next stage: `publish`).
