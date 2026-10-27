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

**A post that changes after gate 2 comes back through this stage**, including
one already sitting in a scheduler. Facts move, dates slip, a link starts
resolving, and the post gets reworked out of parts to match. That is the moment a
post becomes two posts welded together, and it is the moment the pass is easiest
to skip because the copy was approved once already. Reworking a scheduled post is
writing a new one; run the quality pass on it again, then `publish` to put it back.

**Precondition: the title is settled.** These posts point at the piece by name,
and a title that changes afterwards leaves scheduled copy pointing at something
that no longer exists. If `draft.md` has `title_settled: false` or no such
field, say so and offer `finalise` first. The writer may override.

## Setup

1. Read AGENTS.md, knowledge/style-rules.md, knowledge/social-rules.md,
   knowledge/voice-guide.md, knowledge/positioning.md,
   knowledge/social-schedule.md, knowledge/channels.md,
   knowledge/examples/canonical.md. Internalise the voice before writing.
   Every channel you write for must be declared in channels.md; an
   undeclared channel is unknown, so stop and say so.
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
### C<n> · [<channel ids>] · <shape>
<the full post text; for a multi-channel candidate, the long text, then
 "--- <short channel>:" and the rewrite; for a thread, number the posts 1/ 2/ 3/>

channel: <the channel id from channels.md>
destination: <the one place this post's CTA sends the reader>
link: [the piece's URL if known, else [ADD POST URL]]
chars: <count per channel>
viewpoint: <the one thing this post says, in a sentence. If it needs an "and",
            the candidate is two posts and does not go in the pool>
source: <where in the piece it comes from: the section heading, or the
         quotable line or proof point from the building blocks>
review: <nothing, or what it fails and why>
```

Rules for every candidate:

- Built from something the source actually says. No new claims, no invented
  quotes or numbers. The `source:` line names the place; a candidate that
  cannot name one is not built from the piece and does not go in the pool.
  Two candidates with the same source and the same viewpoint are one
  candidate in different words: keep the stronger.
- One post, one destination. A candidate that wants to send the reader to
  two places is two candidates. Identical copy never goes to two channels:
  the channel's relationships in channels.md say what companion means.
- voice-guide.md exactly. No AI tells, no hype vocabulary, no résumé drops.
- Every post on a short channel makes sense to someone who has not read the
  piece. Only the tease may lead with the publication.
- Run each through style-rules.md and tests 1 to 3 of social-rules.md before
  listing it. Note what a candidate fails as `review: <reason>`. Do not fix it
  here: a candidate is raw material and the writer may not pick it. The real
  pass is the quality check at gate 2, on the posts they did pick.
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

### Voice proof

Only where the install carries a voice gate: `voice-gate.py`, in the `scripts` folder at the checkout root, beside
`modules/` (called `<voice gate>` below). This module does not ship one. If it is not there, say once in the gate 2
summary "no voice gate: these posts are unbound, the writer's review is the only check", and change nothing else in
this stage. If it is there, every post and first comment you finish is its own artifact, proved before the writer sees
it at gate 2, and proved again whenever a post changes after gate 2. Pool candidates are not handed off, so they are
not proved; only finished copy is.

**Personal voice layer (read, only when the gate is there).** Read every `instance/voice-*.md` at the checkout root, as
`draft.md` does. It wins any conflict with the knowledge templates. Before this section, this stage did not read it.

**Proof (per post, and per post in a thread).**

1. Write the gate's input for the exact words of the post: `surface` `post`, `form` `social`, `text` the words, and a
   `receipt` that carries `ref`, the full `head_sha`, `draft_sha256`, the `files` read with their `sha256` and cited
   `sections`, `sources`, and an `artifact` object: `contract` 1, `id` `<piece folder name>:<kind>:<number in Chosen>`,
   `version`, `kind` (`post`, or `first-comment` for a pinned first comment), `stage` `familiar-core:social`,
   `output_sha256`, `installed.head_sha`, `private_layer` (each personal layer file by `label` and `sha256`), and
   `parent` from version 2. Spans the writer supplied word for word go under `provenance` as `owner_verbatim`; nothing
   else is typed. Leave an unresolved link as its marker in the text.
2. Run, with the checkout root as `--repo`:

   ```sh
   python3 <voice gate> --repo <checkout root> --input <receipt.json> --private-layer <label>=<path to that layer file> --ledger <piece folder>/voice-ledger.jsonl --record
   ```

   One `--private-layer` per layer file. The ledger is a new sibling file in the piece folder, hashes only, never in the
   repo. `--record` writes a version only when it passed.
3. Put a post in `## Chosen` only when the gate passed or advised (exit 0). On FAIL (exit 1) or UNKNOWN (exit 2) the post
   is not shown; rewrite it or leave it out. ADVISE hits go under the post for the writer to keep, cut or rewrite.
4. Any change to a post's words after it was bound (the writer's edit at gate 2, a link that resolved, a rework of a
   scheduled post, your own rewrite) is the next version of the same artifact: version n+1, `parent` the version and
   `output_sha256` it replaces, then run the gate again. Do not reuse the old receipt for new bytes; the gate refuses it,
   and a revision with no ledger cannot pass. Reread `social.md` before any rewrite and never overwrite the writer's own
   edits. `publish` still sends approved copy byte for byte and never rewrites it.

A pass says these exact words were bound to this revision and these guideline bytes. It is not the writer's approval:
every result still ends `EDITOR REVIEW REQUIRED`, and gate 2 is still her yes.

### Gate 2

Before showing anything, run the quality pass on the picked posts. Two passes,
in order.

#### First, the week

Test 4 from social-rules.md, before any single post. It is the only test that
cannot be run on a post alone, and it is the one most likely to change what you
do with the individual posts, because a repetition found here is usually fixed
by rewriting one post rather than trimming both.

Report it in a line or two: what repeats, in which posts, and which one you
would change. If nothing repeats, one line saying so.

#### Then each post, in order

For each, run tests 1 to 3 from social-rules.md, then the mechanical sweep from
style-rules.md and the channel's limit from social-schedule.md.

**A post that passes test 1 then gets the opening gate.** If
`instance/own-and-flip.md` exists at the repo root, read it first: it holds the
writer's own rules and anchors for these checks and wins on conflict. Three
binary checks, each answered yes or no with the quoted line that settles it:

a. The draft names its most pokeable fact (the thing a sceptical reader would
   poke at first) in the first third.
b. One concrete scene lands before the first claim.
c. A flip line (one sentence that turns that sore spot into the point) sits in
   the first third.

A no on any of them sends the post back to be redrafted, not polished: say
which check failed, quote the line that shows it, and write the post again
before running findings on it. These are judgement checks; nothing about them
goes into the mechanical sweep.

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

**If it fails test 1**, do not list findings. Go to the pick: two to four
viewpoints the material already supports, each written out: the opening line as
it would stand, plus one line on where the post goes. `Buys:` and `Costs:` on
each. An escape at the end. One letter is a complete answer.

Say in one line why the post as it stands has no single viewpoint, and name the
ideas you found in it. That is what makes the options readable.

After the writer picks, ask at most two questions, one at a time. They ask for
judgement, never for recall. What happened is in the piece, the notes, the
context log or the record, and finding it is your job, not a question. Ask what
they think, what they would say to one person about this, what they want the
reader left holding, which of two readings they meant. If the answer to the
first question is enough, do not ask the second.

Then write the post from their answers, in their words wherever their words will
carry it. Voice guide exactly. Run the mechanical sweep and the character count
on what you wrote before showing it. Show the post and say what you took from
which answer, in a line. The writer approves, edits or sends you back. An edit
they make is applied verbatim, and anything they changed goes through the
mechanical sweep again.

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

## Check the never-publish list

Before the writer approves anything, run
`python3 scripts/never-publish.py <the file>` over `## Chosen`. A block means
stop and tell them what matched; a warning means show it and carry on. Off or
empty means nothing happens and nothing is said. See `prompts/publish.md` for
the full behaviour.

Exit 2 means it could not run: the list did not load, so nothing was
checked. Stop and say why. That is not the same as the list being off.

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

Before that line, run `python3 scripts/revival-check.py social.md --piece <the
piece folder>`. It flags a post or candidate that brings back a dead cut, an
option the writer chose against, or a rule they rejected. Move a flagged item
out of `## Chosen` into `## Held` with the original kill and its reason beside
it, so the writer decides whether the evidence changed. If it says it could not
run, or that rejected rules were not checked, say so in the line.

Then one line: the copy is approved, what is in it, and anything still missing
before it can be scheduled (a link that has not resolved, a channel not
connected).

- **Context log:** append to the piece's own `SESSION-CONTEXT.md` per
  knowledge/context-log.md (status, files touched, what changed, the decision
  gate for the writer, next stage: `publish`).
