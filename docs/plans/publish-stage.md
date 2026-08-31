# Plan: the publish stage

**Status:** proposed, 31 August 2026.
**Problem:** Familiar takes a writer from an idea to approved social copy, then
stops. The last step, getting the posts into a scheduler, is missing from the
public tool. Anyone who adopts Familiar reaches the end of `social` holding a
markdown file and no way to ship it.

## Why this is a gap and not a boundary

The publishing step is already generic. It was kept private by a blunt
`.gitignore` line, not because it contains anything personal.

- The Buffer adapter is fifteen lines. It reads an API key and execs Buffer's
  own hosted MCP at `mcp.buffer.com`. There is nothing user-specific in it.
- The queue check is sixty-six lines with exactly one hardcoded value, a
  LinkedIn channel id. It already reads the other channel's id out of
  `knowledge/social-schedule.md`, so the fix pattern is in the file.
- The private `social` prompt already drives the scheduler generically: channel
  ids come from config, it calls `create_post`, and it documents a fallback for
  clients where the MCP is unavailable.

The split Familiar already makes everywhere else applies cleanly here. The
capability is public; the credentials and channel ids are the user's config.
Voice works that way. Cadence works that way. Publishing should too.

## Design decisions

### 1. A separate stage, not the tail of `social`

The private version has scheduling as part two of the social prompt. Split it.

- **Re-runnable.** Scheduling can fail, or be deferred a day, without
  regenerating a candidate pool over copy the writer already approved. That
  failure mode is real: it had to be prevented by hand with a README in a
  staged folder.
- **Serves the off week.** A week with no new issue still needs posts scheduled
  from the back catalogue. `publish` takes approved copy from anywhere.
- **Degrades honestly.** A writer with no scheduler still gets full value from
  `social`. `publish` is the optional last mile, not a dependency.

### 2. The scheduler is a feature you turn on, defaulting to Buffer

Confirmed 31 August. One `## Scheduler` block in
`knowledge/social-schedule.md`, shipped with `scheduler: buffer`. Setting it to
`none`, or leaving it unconfigured, turns the feature off and `publish` prints
the table instead. Nothing about the rest of the stage changes.

Buffer is the only implementation and that is deliberate. The block documents
the two operations any scheduler must support, so a fork can be written against
a spec rather than by reading the Buffer code:

- create a post on a channel at a given timestamp
- list scheduled posts on a channel

An adapter framework with one adapter is overbuilt. A documented seam with one
implementation, and a flag that turns it off, is not.

### 3. No scheduler is a supported state

If no scheduler is configured, `publish` prints the final table: post text,
channel, exact local time, character count. That is a paste-and-go list for
someone scheduling by hand, and it matches the existing "no terminal" path in
the README. Familiar should never require a paid third-party account to be
useful.

### 4. Build the URL, then measure, then validate

A post approved at 291 characters went to 337 once its tracking parameters were
appended, and only a manual recount caught it. The cause is ordering: the copy
was approved before the link existed. So `publish` fixes the order.

1. Resolve the destination URL.
2. Append tracking parameters from `knowledge/links.md`, which holds the
   convention (which parameter carries the channel, and how a channel names
   itself) and the user's own values.
3. Assemble the finished string.
4. Count it, and validate against the channel's limit.
5. Only then schedule.

`publish` stops on an over-limit post and shows the count and the overage. It
never truncates, and it never shortens the writer's words on its own. Shortening
the tracking parameters is a suggestion it may offer, because that is the part
the writer did not write.

Tracking parameters are built for Buffer's channels for now. Other schedulers
name their channels differently; a fork implements that alongside its own
`create_post`.

### 5. Surface what the scheduler cannot do

Buffer schedules a post but not a pinned first comment. If the copy carries a
comment, `publish` must emit it as an explicit manual checklist item with its
time, not silently drop it. Any scheduler will have holes like this; the stage's
job is to name them, not paper over them.

## What moves

| From (private repo) | To | Change needed |
|---|---|---|
| `tools/buffer-mcp.sh` | `scripts/buffer-mcp.sh` | Read `$BUFFER_API_KEY` from the environment. The current version greps the user's `~/.zshrc` for it, which is not a pattern to ship publicly. |
| `tools/buffer-week-check.sh` | `scripts/queue-check.sh` | Read every channel id from config, as it already does for one of them. Rename: it answers "is the coming week's queue full", which is not Buffer-specific. |
| `prompts/social.md` part 2 | `prompts/publish.md` | Genericise. Keep the gate discipline: nothing is created without per-post confirmation. |
| n/a | `.claude/commands/publish.md` | Thin adapter, same shape as the others. |
| n/a | `knowledge/social-schedule.md` | Add the `## Scheduler` block to the shipped template. |

Also: `skills/familiar/SKILL.md` and `dex/familiar/SKILL.md` gain the stage,
`dex/familiar/evals/trigger-cases.yaml` gains its trigger phrases, and
`AGENTS.md` gains the row.

## Config shape

```markdown
## Scheduler

- scheduler: buffer        # or `none` to print the table and stop
- key: $BUFFER_API_KEY     # env var name, never the key itself

| Channel  | Id                | Limit | Notes                          |
|----------|-------------------|-------|--------------------------------|
| linkedin | <your channel id> | 3000  | Link in a pinned first comment |
| bluesky  | <your channel id> | 300   | Link inline                    |
```

## Open questions

1. Does Buffer's API require a paid plan? If it does, say so in the README next
   to the scheduler block rather than letting someone discover it at the last
   step.
2. Should `queue-check.sh` ship at all, or is it Dex-specific? It exists to let
   a planning tool decide whether to raise a "schedule next week" task. That is
   a real job for any user with a weekly cadence, so it ships, but its Dex
   wiring stays in the Dex skill.
3. `publish` needs a piece-independent input path, since the off-week case has
   no piece folder. Probably a path to any file with a `## Chosen` section.
