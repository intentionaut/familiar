# Plan: the audience model, and the content strategy loop around it

**Status:** proposed, 14 September 2026.

**Problem:** Familiar frames every piece for one reader, described once in
`knowledge/positioning.md`, with optional segments. That was enough when the
publication was the only surface. It is not enough now: the same writer
publishes a newsletter, posts to two social channels with different registers,
queues original posts through a scheduler, and speaks on a talks circuit. Each
of those reaches a different mix of founders, product leaders, operators and
peers, and each wants something different from the same material.

Today none of that is declared anywhere. The audience lives in the writer's
head, so every stub, every interview and every social cut starts with the
writer restating who it is for. That does not scale, and worse, it means the
selection decision (is this stub worth writing, and for whom) happens late,
by feel, after the piece exists. And once a piece ships, nothing comes back:
Familiar records what the writer changed (`learn diff`) but not what the
readers did, so the next topic proposal knows no more than the last one.

## Why this is a gap and not a boundary

The seam already exists; it is just thin.

- `positioning.md` already declares segments, and its own text says segments
  stop being optional "the moment you have two readers who want different
  things from the same piece". That moment arrived; the file was not the
  problem, the depth was. A segment today is who, Wants, Win, Reads. It has
  no goals, no objections, and no standing rules for how it is addressed.
- `themes.md` already states the rule this plan leans on: audience is
  declared once, in one place, never restated per theme. Repeating an
  audience per piece is how a declared file ends up empty. The same argument
  applies to per-stub and per-interview restating, which is the current
  state.
- `harvest` already groups what it finds by audience segment, so a richer
  audience definition has a consumer on day one.
- `publish` already knows the channels. The audience model does not add a
  publishing concept; it names who is on the other end of channels that
  already exist.

## Design decisions

### 1. Audiences graduate to their own file: `knowledge/audiences.md`

One entry per named audience, in the writer's words, following the file
conventions already set by `themes.md`: the id never changes, every value
carries its source, and `unknown` is a legitimate resting state that no stage
fills by guessing.

    - `id`: who they are, in your own words.
      Goals: [what they are trying to do when they read you].
      Objects: [the objection or fatigue they bring: what they are tired of
      reading, what makes them stop].
      Wants: [what they want from a piece].
      Win: [what a win looks like, as a test].
      Reads: [where you actually see them, channel and evidence].
      source: declared

The writer's standing positioning rules are stated once, as defaults, in the
house's `positioning.md`, never in this repo. A stage that
frames for an audience inherits these; the writer should never have to
restake that ground per piece, per stub or per interview.

`positioning.md` keeps its one reader and its Segments section becomes the
one-line index pointing at this file, the same way `themes.md` points at
segments by id. One reader is still the default for a piece with no declared
audience, and a stage says so rather than inventing one.

### 2. Stub intake and triage

Stubs are the raw material this system currently wastes: the one-line idea
sent mid-flow, the session that felt like a piece, the clip saved with
`inspire`. They arrive faster than pieces and die in silence.

- `familiar stub "..."` captures a stub, one line plus an optional why, into
  `knowledge/stubs.md`. Append-only, like the build log: a stub is never
  edited in place, only triaged or retired.
- Triage is a proposal, not a promotion. When asked (or during `harvest`),
  each untriaged stub gets a mapping: the theme it serves, the audience or
  audiences it serves, the channel that fits, named by its id in
  `knowledge/channels.md`, the one destination the piece would send its
  readers to, and the evidence it would need. A stub that fits no audience goes to `knowledge/proposals/` as a
  candidate audience or is retired with a reason, and the writer decides
  both.
- The board counts untriaged stubs the way it counts open questions: a pile
  nobody can see is a pile nobody writes from.

### 3. The interview knows the reader

`interview` already reads the piece's theme and its evidence bar. It now
also reads the piece's declared audience, and the questions change shape:

- For an audience whose Win is evidence of judgement under a visible
  constraint, the interview digs for the constraint, the date and the
  number, not the lesson.
- For an audience that builds the same kind of thing, it digs for the method
  with the reasoning under it, not the method alone.
- For an audience that forwards to strangers, it digs for the one sentence
  that stands without the writer.

A question the audience file already answers is not asked. This is where the
model pays the writer back directly: fewer questions, sharper ones, and no
session that starts with "who is this for".

### 4. Engagement comes back

After `publish`, the outcome of a piece is currently nowhere. Add the
smallest honest loop:

- `familiar engagement add <piece>` records, in the writer's words and with
  numbers where the writer has them, what happened per channel: replies,
  shares, forwards, conversations started, a talk pitch accepted. Declared,
  not scraped. Nothing leaves the machine and no platform API is required;
  a writer with no numbers records "three replies, one from a founder who
  wants a call" and that is the data.
- The entry lands in the piece folder and is counted by `harvest`: which
  audiences responded to which themes, and which declared Wins were met.
- `learn decisions` may propose strengthening or retiring an audience's
  Wants or Win on that evidence, through the same accept/reject gate as
  every other proposal.

Reader response informs which theme and which audience takes the next slot.
It never touches the business-development cap in `positioning.md`, and it
never sets cadence. The cap belongs to the publication, per `themes.md`.

### 5. Selection scales because the audience is declared once

The compounding effect is the point of the plan. With audiences declared:

- `bring` and stub triage select before writing, not after.
- `interview` asks audience-shaped questions without being briefed.
- `social` and `repurpose` pick the cut that fits each channel's audience
  from the same file, instead of being told per channel per week.
- `harvest` proposes topics where an audience's Win is unmet, not only where
  evidence is fresh.

A new surface is a new `Reads:` line, not a new explanation.

## Acceptance criteria

- `knowledge/audiences.md` ships as a template in the same style as
  `positioning.md`, with one worked example entry marked `source: declared`
  and every other value `unknown`.
- `familiar stub` appends to `knowledge/stubs.md`; triage output names
  theme, audience, surface and needed evidence, and promotes nothing without
  the writer.
- `interview` reads the piece's declared audience and states in one line
  which Wants and Win it is asking from; a piece with no declared audience
  falls back to the one reader and says so.
- `familiar engagement add` writes a dated entry to the piece folder;
  `harvest` reports unmet Wins by audience.
- `tests/test_structure.py` holds the new files to the same declared-value
  conventions as `themes.md`.
- Nothing auto-posts, nothing scrapes, nothing invents an engagement number.

## Open questions

1. Does the Segments section in `positioning.md` migrate fully into
   `audiences.md`, or stay as the index? Both are argued above; the index
   reading is the smaller diff and keeps one front door.
2. Should platform exports (a LinkedIn analytics download, a beehiiv report)
   be a way in to `engagement add`, the way platform exports are a way in to
   `learn ingest`? Declared-by-hand is the honest baseline; ingest is a
   possible later seam.
3. A piece that serves two audiences: declare a primary and a secondary, or
   refuse? The themes rule (two or three segments is normal, all of them is
   not narrowed) suggests primary plus at most one secondary.

## Deliberately left out

- Scraping or API-ingesting engagement metrics. It conflicts with "nothing
  leaves your machine" only mildly, but with "declared before inferred"
  directly: a like count with no writer judgement attached is noise the
  loop would treat as signal.
- Any change to the publishing cap, cadence rules or the gates themselves.
- Changelog and version: the maintainer's call at merge time.
