# Stage: publish

Approved copy goes to a scheduler. That is the whole job.

This stage does not write posts, choose posts, or improve posts. If the copy is
not finished, you are in the wrong stage: `social` produces and finalises it,
and it ends at approved copy for a reason. `publish` takes what a human already
said yes to and gets it scheduled without changing a word of it.

**Never regenerate a candidate pool here.** If you find yourself proposing
alternatives, stop. The writer approved these words, possibly days ago, possibly
in another session. Re-opening that decision wastes their afternoon and is the
failure this stage was split out to prevent.

## Setup

1. Read `knowledge/social-schedule.md` for channels, cadence, send times,
   character limits and the `## Scheduler` block.
2. Read `knowledge/links.md` for the tracking convention and destinations.
3. Read `knowledge/style-rules.md`. You will need it only if the writer edits
   something at the gate.

## Input

`$ARGUMENTS` may name a file. If it does not, use the current piece's
`social.md`. Either way the input needs a `## Chosen` section: finished posts,
per channel, with their slots. Anything under a "held", "candidates" or
"not scheduled" heading is **not** input. Leave it alone.

If there is no `## Chosen` section, say so and stop. Do not improvise one.

## Is the scheduler on?

Read `scheduler:` in the `## Scheduler` block.

- **`none`, missing, or the block deleted:** the feature is off. Skip to
  *Output when the scheduler is off*. This is a supported way to work, not a
  failure, and it gets no warning tone.
- **`buffer`:** carry on. If channel ids are still placeholders, treat that
  channel as off and say which.

## Build every URL before you count anything

In this order, per post. The order is the point.

1. **Resolve the destination.** Turn "the piece" or "the index" into a real URL
   from `knowledge/links.md`. If the piece has not published and its URL does
   not resolve yet, either point at the index or keep the placeholder and say
   the schedule cannot complete for that post. A URL that 404s is not a URL.
2. **Append tracking parameters** per the convention. Source is the channel's
   hostname, medium is the placement, campaign is usually the piece's slug.
3. **Assemble the finished string** exactly as it will appear.
4. **Count it.** Report the count for every post.
5. **Validate** against the channel's limit.

On an over-limit post: **stop and report.** Give the count, the limit and the
overage. Never truncate. Never rewrite the writer's words to make room. You may
propose shortening the tracking parameters, because the writer did not write
those, and if you do, say what is lost: dropping to source alone still
attributes the click to the channel but no longer to the piece.

## Map to slots

One table per channel:

| # | Day | Date | Time (local) | Shape | Chars | Post opens |
|---|-----|------|--------------|-------|-------|------------|

Convert each send time to the exact timestamp you will pass to the scheduler,
with its offset. State every assumption you are relying on, especially a
publish time you were told rather than verified.

Check the slot is in the future. A slot that has already passed cannot be
scheduled; say so and offer the next one on that channel.

## What the scheduler cannot do

Read the **Link goes** column. A link in a pinned first comment must be added
and pinned by hand after the post is live, because schedulers create posts, not
comments. Collect these into an explicit checklist with times. Do not drop them,
and do not quietly move the link inline instead, which changes a post the writer
approved.

## Gate: confirm

Stop. Show, grouped by channel:

```
Ready to schedule:

<channel> (<account>)
1. <Day> <date> <time>  <shape>  <n> chars
2. ...

By hand afterwards:
- <Day> <date>, shortly after <time>: add and pin the first comment on post 1

Confirm to schedule all of these.
```

Wait for an explicit confirmation. Anything less than a clear yes is a no. If
the writer edits a post here, apply the edit verbatim, re-run
`knowledge/style-rules.md` on what changed, and recount it before continuing.

## Schedule

Only after confirmation, and only the posts under `## Chosen`.

For each post, call the scheduler's create operation with the channel id, the
finished text and the timestamp. With Buffer that is `create_post`; if the
client has no Buffer MCP configured, run `scripts/buffer-mcp.sh` and drive it
over stdio.

For a thread, create the posts in order and link them if the API supports it.
If it does not, schedule them a minute apart and tell the writer they may need
to thread them by hand.

**If a channel fails** (not connected, a refused id, an API error): schedule the
channels that work, leave the failed channel's posts untouched in the file, and
report the exact error. Do not retry silently. Do not partially reschedule
without saying exactly what landed and what did not.

## Output when the scheduler is off

Print the table, and stop. No apology, no setup instructions unless asked.

| Channel | Day | Date | Time | Chars | Post |
|---------|-----|------|------|-------|------|

Full text per post underneath, ready to copy, with its URL already built and
counted. Then the by-hand checklist. This is the whole deliverable in this mode
and it should be good enough to work from.

## Exit

Append to the input file:

```
## Scheduled
<per post: channel, local time, the scheduler's post id, or the exact error>
## By hand
<the pinned-comment and threading checklist, with times>
```

Then one line: what is scheduled, on which channels, and what still needs a
human. If anything failed, that line says so first.

- **Context log:** append to `SESSION-CONTEXT.md` per `knowledge/context-log.md`
  (status, files touched, what changed, the decision gate, the next stage).
- **Reflection:** if `knowledge/reflection.md` says one is due, offer it. Never
  insist.
