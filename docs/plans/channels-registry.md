# Plan: one channel registry the stages read

**Status:** spike, 19 September 2026. For review; not for merge as it
stands.

**Problem:** Familiar's channel knowledge is split across three files, and
each stage reads only its own slice. `social-schedule.md` knows short-form
channels, accounts, limits and cadence. `longform-channels.md` knows one
long-form channel's job, form and CTA. `links.md` knows destinations and
tracking. Nothing holds the whole answer, so the selection question (which
channel is this for, and where does it send the reader) is answered per
stage, per week, by feel.

## Why this is a gap and not a boundary

The seams already exist; they are just not joined.

- `longform-channels.md` already declares a channel's job, audience, form,
  rhythm, CTA and tracking source. The registry generalises that block
  instead of inventing a new shape.
- `social-schedule.md` already declares limits and cadence, and
  `links.md` already owns destinations and UTM. The registry references
  both rather than duplicating them.
- The audience model plan already has triage proposing a "surface" per
  stub. A surface is a channel; the registry gives that word a declared
  list to point at.
- PR #52 already wrote one channel definition in the registry's shape.
  It becomes the `linkedin-newsletter` block, not the whole feature.

## The channel-versus-destination line

A **channel** is where, why and how a piece appears. A **destination** is
the single place its call to action sends the reader. The LinkedIn feed is
a channel; that post's destination is the newsletter list, the hub or the
product, never all three. The registry holds the first; `links.md` holds
the second; the one-destination rule binds them: one post, one
destination, declared before the post is written.

## Design decisions

### 1. One registry, `knowledge/channels.md`, referenced by id

One block per channel: job, audience (by id, from the audience model or
`positioning.md` Segments), voice overlay (a register over
`voice-guide.md`, never a second voice guide), form and length, cadence or
`evergreen`, allowed source material, default CTA and destination rule,
link placement, UTM source and medium, relationships to other channels
(including the ban on identical cross-posting), and the review and publish
gate. Channel ids are stable; stages and `social.md` name channels by id.

### 2. The stages read it at their existing seams

- **Strategist and triage** (per the audience-model plan): a proposal names
  theme, audience, channel by id, the evidence needed, and one
  destination. An unknown channel id stops the proposal; it is never
  guessed.
- **`repurpose`**, long branch: reads the channel's block from the
  registry where it read `longform-channels.md`. Job, form, length,
  audience and CTA come from one place; the standalone rule is unchanged.
- **`social`:** reads the channel's form, limits, cadence, link placement
  and relationships from the registry. Every post in `## Chosen` carries a
  `channel:` id and a `destination:` line, which is what makes the next
  two checks possible.
- **`publish`:** resolves the destination through the channel's rule and
  `links.md`, places the link per the channel (first comment versus
  inline), and refuses a post that names two destinations. Approved copy
  still does not change.

### 3. `social-schedule.md` and `links.md` keep their jobs

The registry does not swallow them. Scheduler accounts, slot times and
the week grid stay in `social-schedule.md`; URL building and tracking
stay in `links.md`. The registry holds what a channel is for and how a
piece appears there. `longform-channels.md` is absorbed: its one channel
becomes a registry block and its standalone rule moves into `repurpose`,
which already enforces it. What the registry adds is the cross-stage
view: every stage reads the same declaration.

### 4. Validation catches the four real failures

`scripts/channel_check.py`, wired into `doctor`, checks:

- **Unknown channels.** A channel id used in `social-schedule.md` or a
  piece's `social.md` that the registry does not declare.
- **Missing destinations.** A channel whose block declares no destination
  rule, or a `## Chosen` post with no `destination:` line.
- **Duplicate destinations.** One post naming two destinations, the exact
  failure the one-destination rule exists to prevent.
- **Contradictory cadence and limits.** The registry and
  `social-schedule.md` disagreeing about the same channel's weekly count
  or character limit, and a `utm_source` that breaks the `links.md`
  hostname convention.

It reports; it never edits. That is the house rule everywhere except
never-publish, and this is not never-publish.

## What the spike shows

The registry seeded with the five routes in use today: the LinkedIn feed,
the LinkedIn newsletter, the main newsletter, the site hub, and a product
destination restricted to career-evidence stories. The four public routes
are seeded in full. The product destination is seeded unnamed: this repo
is public and the product is not announced, so its named block belongs in
the writer's house copy of the file. A mergeable version of this change
ships the registry as a blank template with one worked example, the way
`themes.md` does; the seeded copy lives in the writer's house. The spike
seeds it here so the review can judge the real thing.

## Acceptance criteria

- `knowledge/channels.md` declares every field above per channel, and is
  registered in `knowledge/TEMPLATES`.
- `repurpose`, `social` and `publish` read the registry at the seams
  named above, and the triage section of the audience-model plan names
  channel and destination.
- `scripts/channel_check.py` flags all four failure classes on synthetic
  fixtures; `doctor` prints a channels block; tests cover the checks.
- No stage auto-posts, no analytics is ingested, and no gate changes.

## Open questions

1. **Template versus seeded.** Does the shipped file carry the writer's
   routes (as PR #52 does for one channel) or a blank template with the
   routes in the writer's house? The public-repo rule points at the
   template; PR #52 points the other way. One answer should cover both
   this file and that PR.
2. **UTM source for the LinkedIn newsletter.** `links.md` says
   `utm_source` is a hostname; PR #52 declares `linkedin_newsletter`.
   The registry follows `links.md` and the checker flags the mismatch.
   One convention should win, in `links.md`.
3. **Does `longform-channels.md` retire?** The spike absorbs it. Keeping
   both means two channel files again, which is the problem this change
   exists to close.
4. **Cadence authority.** When the registry and `social-schedule.md`
   disagree, which one does a stage follow? The spike treats the
   registry as the declaration and the schedule as the planner's grid,
   and has the checker flag the drift rather than pick a winner.

## Deliberately left out

- Publishing automation, schedulers beyond the existing Buffer seam, and
  any analytics or engagement ingestion.
- Any change to the stage gates themselves, the cadence cap, or the
  never-publish check.
- Changelog and version: the maintainer's call at merge time.
