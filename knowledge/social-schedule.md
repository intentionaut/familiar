# Social schedule

The scaffold the `/familiar-social` stage fills: which channels, how many posts
a week, which days and times, what shape each slot wants. Fill it in once; edit
it here when the cadence changes. The stage reads it every run.

The social stage only produces the **scheduled posts**. Replies, conversation
and anything live are yours. A schedule is not a presence; it is the part of a
presence that can be planned.

## Channels

One row per channel you actually use. Delete the rest. The character limits
are what the stage checks against.

| Channel | Account | Voice | Limit | Scheduler |
|---------|---------|-------|-------|-----------|
| LinkedIn | [your profile or page] | [first person / studio "we"] | ~1300 chars comfortable, 3000 hard | [Buffer / native scheduler / by hand] |
| Bluesky | [handle] | first person | 300 chars | [Buffer / by hand] |
| Mastodon | [handle] | first person | 500 chars (instance-dependent) | [by hand] |
| Threads | [handle] | first person | 500 chars | [by hand] |
| X | [handle] | first person | 280 chars | [by hand] |

## Scheduler

Optional. The `publish` stage reads this block; the `social` stage does not care.
Set `scheduler: none`, or delete this block, and `publish` prints a paste-ready
table instead of calling anything. Nothing else about the stage changes.

- **scheduler:** buffer
- **key:** `$BUFFER_API_KEY`, the *name* of an environment variable. Never
  write a key or token in this file.

| Channel | Channel id | Limit | Link goes |
|---------|-----------|-------|-----------|
| linkedin | [id from your scheduler] | 3000 | pinned first comment |
| bluesky | [id from your scheduler] | 300 | inline |

`publish` counts against the **Limit** column after tracking parameters are
appended, and stops rather than truncating.

**Link goes** tells `publish` what the scheduler cannot do for you. A link in a
pinned first comment has to be added and pinned by hand after the post is live,
because schedulers create posts, not comments. `publish` emits those as a
checklist with times rather than dropping them.

### Writing another scheduler

Buffer is the only one implemented. A fork needs two operations:

- create a post on a channel at a given timestamp
- list scheduled posts on a channel

`scripts/buffer-mcp.sh` is fifteen lines and is the worked example.

If a shared account carries both your work posts and your personal ones, say
which the stage may write (usually: work topics only) and what it must never
touch (anything you posted yourself).

## Cadence

| Channel | Days | Count | Default time | Timezone |
|---------|------|-------|--------------|----------|
| [LinkedIn] | [Mon, Wed, Fri] | [3/week] | [08:30] | [Europe/London] |
| [Bluesky] | [Tue, Wed, Thu] | [3/week] | [12:30] | [Europe/London] |

A week runs Monday to Friday unless you say otherwise. "Next week" means the
Monday coming. Fewer, better posts beat a full grid; leave a slot empty rather
than fill it with something you would not say.

### The matrix

Draw it so the stage can see the week at a glance:

```
        Mon   Tue   Wed   Thu   Fri
[LI]     X           X           X
[BS]           X     X     X
```

## Slot shapes

Starting points, not cages. If the strongest candidate for a slot is a
different shape, the stage should use it and say so.

The shapes the stage knows: **pillar** (the piece's main argument with proof
and ending), **tease** (one to three lines pointing at the piece, no spoiler),
**story** (a scene from the piece), **contrarian** (the angle that pushes
against the obvious take), **question** (written to be answered), **quote** (a
line that stands alone), **proof** (a claim with its evidence), **hook** (the
opening line, alone), **evergreen** (from something older that still holds).

### On a week a piece ships

The publish day comes from the piece's `draft.md` frontmatter `date:`.

| Slot | Shape | Source |
|------|-------|--------|
| First slot of the week | [pillar] | the new piece |
| Slot on or nearest the publish day | [tease + link] | the new piece |
| Remaining slots | [story or contrarian] | the new piece |

### On a week nothing ships

| Slot | Shape | Source |
|------|-------|--------|
| [Mon] | [question] | past pieces |
| [Wed] | [evergreen] | past pieces |
| [Fri] | [quote or proof] | past pieces |

If you keep an index of past pieces for this, name it here:
[knowledge/back-catalogue.md, or "pieces/*/ only"].

## Rules for short channels

Posts under 300 characters are their own form, not a chopped LinkedIn post.
One idea, written to be answerable, and it must make sense to someone who has
not read the piece. The tease is the only post allowed to lead with the
publication itself.

Threads: the stage may propose one short thread (2 to 4 posts) for the pillar
idea when the idea needs the room. Every post in it stands alone. No "a thread"
hook.

## Sourcing rules

- Every post is built from something the source actually says. No new claims,
  no invented quotes or numbers.
- Do not repost the same angle to the same channel twice in a quarter.
- All posts pass `knowledge/style-rules.md`.
- Say which pieces the posts drew from.

## The candidate pool

The stage generates one blended pool of about [14] candidates, tagged by
channel, and asks you to pick [3] per channel. Set the numbers to match the
cadence above; a pool of roughly twice the slots gives real choice without
reading fatigue.
