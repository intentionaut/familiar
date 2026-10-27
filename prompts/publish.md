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
2. Read `knowledge/channels.md` for each channel's destination rule and
   link placement. Every post must name a channel the registry declares
   and exactly one destination; a post that names none, or two, stops the
   run until the writer settles it. Approved copy does not change to fix
   either.
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
- **`handoff`:** another scheduler of yours takes the posts from this file.
  Carry on through the URLs, the count, the never-publish check and the
  confirm gate exactly as for `buffer`, then follow *Hand off* instead of
  *Schedule*. Call no scheduler.

## Build every URL before you count anything

In this order, per post. The order is the point.

1. **Resolve the destination.** Take the post's declared destination and
   turn it into a real URL from `knowledge/links.md`, under the channel's
   destination rule in `knowledge/channels.md`. If the piece has not published and its URL does
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

## Check the never-publish list

Run it before the gate, so anything it finds is in front of the writer while
they are deciding:

```sh
python3 scripts/never-publish.py <the file>
```

- **Exit 0, nothing printed but "clean" or a warning:** carry on. Warnings are
  for the writer to read, not for you to act on.
- **Exit 1, blocked:** stop. Say which strings matched and where they are. Do
  not schedule, do not edit them out yourself, and do not offer to. A string on
  that list is there because the writer decided it must never go out, and what
  to do about it is theirs.
- **Exit 2, could not run:** stop. Say why, in one line. The list did not
  load, so nothing was checked and the draft is not clean, it is unexamined.
  A house that will not resolve or a list that has gone stale both land here.
  Do not publish, and do not treat it as the list being off.
- **The list is off or empty:** nothing happens and nothing is said. That is a
  supported way to work. Off is a choice the writer made. Exit 2 is not.

This is the only place Familiar refuses rather than reports. It refuses to send,
never to write.

## Voice proof

Only where the install carries a voice gate: `voice-gate.py`, in the `scripts` folder at the checkout root, beside
`modules/` (called `<voice gate>` below). This module does not ship one. If it is not there, say once above the confirm
gate "no voice gate: these posts reach the scheduler unbound, the writer's confirm is the only check", and change nothing
else in this stage. If it is there, every post is proved as the finished string, exactly as it will be sent: URL built,
tracking parameters appended, counted. Run it for buffer, handoff and off alike, before the confirm gate shows anything as
ready, and before the by-hand text is printed. The proof never rewrites a word: this stage only sends what was approved, so
the gate can refuse a post here and cannot change one.

Read every `instance/voice-*.md` at the checkout root first, as `social` does: the receipt must carry the personal voice
layer the post was bound with.

**Proof (per post, and per post in a thread).**

1. Write the gate's input for the finished string: `surface` `post`, `form` `social`, `text` the string, and a `receipt`
   that carries `ref`, the full `head_sha`, `draft_sha256`, the `files` read with their `sha256` and cited `sections`,
   `sources`, and an `artifact` object: `contract` 1, `id` the id `social` bound, `<piece folder name>:<kind>:<number in
   Chosen>`, `version`, `kind` `post`, `stage` `familiar-core:publish`, `output_sha256`, `installed.head_sha`,
   `private_layer` (each personal layer file by `label` and `sha256`), and `parent` from version 2. If the finished
   string is byte for byte the version `social` bound, check it at that version with the same `parent`. If building the
   URL changed the bytes, it is the next version of the same artifact: version n+1, `parent` the version and
   `output_sha256` it replaces.
2. Run, with the checkout root as `--repo`:

   ```sh
   python3 <voice gate> --repo <checkout root> --input <receipt.json> --private-layer <label>=<path to that layer file> --ledger <piece folder>/voice-ledger.jsonl --record
   ```

   One `--private-layer` per layer file. The ledger is the piece folder's own `voice-ledger.jsonl`, the one `social`
   wrote; hashes only, never in the repo. `--record` writes a version only when it passed.
3. Read the exit code. **Exit 0** (PASS or ADVISE): the post goes under "Ready to schedule". Each ADVISE hit goes under
   the post at the gate with its rule file, line and date, for the writer to keep, cut or send back to `social`; a hit
   never blocks. **Exit 1** (a receipt error: the bytes are not the bound artifact, a guideline file changed, a newer
   version exists): the post is not scheduled, not handed off and not shown as ready. Say what the gate named and send
   the writer back to `social`. Do not edit the post to make it pass. **Exit 2** (no kill list found): say "Familiar
   unavailable", schedule nothing and make no substitute.
4. A post the writer edits at the confirm gate is the next version of the same artifact: version n+1, `parent` the
   version and `output_sha256` it replaces, then run the gate again before it is counted. Do not reuse the old receipt
   for new bytes; the gate refuses it, and a revision with no ledger cannot pass.

A pass says these exact bytes were bound to this revision and these guideline bytes. It is not the writer's approval:
every result still ends `EDITOR REVIEW REQUIRED`, and the confirm gate is still her yes.

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

## Hand off

Only with `scheduler: handoff`, only after confirmation, and only the posts
under `## Chosen`.

First read `## Scheduled` in the input file. A post that already has a line
there (an id, `pending`, `unresolved` or `handed off`) is not handed off
again; say which.

For each post, append to the input file, under `## Handed off` (create the
heading once, after `## Chosen`), the finished string: the URL built, tracking
parameters appended, counted, exactly what would have gone to a scheduler.

````
```post
channel: linkedin
at: 2026-09-02T08:30:00+01:00
---
The finished post, byte for byte.
```
````

`channel` is the channel's name in `## Scheduler`; `at` is the exact timestamp,
with its offset. If a post contains three backticks, fence it with four. Then
add its line under `## Scheduled`:

```
- <channel> <YYYY-MM-DD HH:MM>: handed off
```

Never edit a block that is already there. A post the writer changes after
handing off is a new post: hand it off again and say the old block stands until
the other scheduler drops it.

Then stop and say, in one line, how many posts were handed off and that the
other scheduler takes it from here. Nothing has been scheduled yet, so do not
say it has.

## Schedule

Only with `scheduler: buffer`, only after confirmation, and only the posts
under `## Chosen`.

**One post per call, in order, and confirm each before starting the next.**
Never batch several creates into one command. Two reasons, and the first is
the one that matters:

- A batch that fails halfway leaves you unable to say what landed. One call
  per post means the id and time come back for each, and a failure names
  exactly one post.
- Observed in practice: a compound command that both built a payload and
  posted it was refused by a permission layer, while the same call on its own
  went through. Keep the local work and the outward call in separate steps.

**Look before you create.** First read `## Scheduled` in the input file. A
line that says `pending` or `unresolved` is a create that may already have
landed. For each one, list the scheduler's queue for that channel and look for
the exact text at that minute. Found: replace the line with the post id. Not
found, or the list fails: leave it `unresolved`, say so, and do not schedule
that post. Only the writer, after checking the scheduler themselves, can say
it never landed.

**Write the intent before the call.** For each post, append one line under
`## Scheduled` in the input file before calling the scheduler:

```
- <channel> <YYYY-MM-DD HH:MM>: pending
```

The channel is its name in `## Scheduler`; the time is the slot's local time.
Keep to this shape, here and under *Hand off*: other tools read these lines to
know what may already be in a scheduler.

Then call the scheduler's create operation with the channel id, the finished
text and the timestamp. With Buffer that is `create_post`; if the client has no
Buffer MCP configured, run `scripts/buffer-mcp.sh` and drive it over stdio.
Buffer wants `status` as an array when listing, and a timestamp with an explicit
offset, built from the account's own timezone.

- **An id came back:** replace `pending` with the id.
- **No answer, a timeout, or an answer with no id:** do not create it again.
  The post may be in the queue. List the queue for that channel and look for
  the exact text at that minute. One match: record its id. None, or the list
  fails: mark the line `unresolved`, say so, and stop scheduling. A second
  create for the same post is how one post goes out twice.

When every post is created, list the queue back and check what is actually in
it against what you meant to schedule. A create that returned an id is not the
same as a post sitting in the queue at the right minute.

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

`## Scheduled` is already in the input file, one line per post, written as you
went. Make sure each line now ends in an id, `unresolved`, `handed off`, or
the exact error, never `pending`. Then append:

```
## By hand
<the pinned-comment and threading checklist, with times>
```

Then one line: what is scheduled, on which channels, and what still needs a
human. If anything failed, that line says so first.

- **Context log:** append to `SESSION-CONTEXT.md` per `knowledge/context-log.md`
  (status, files touched, what changed, the decision gate, the next stage).
- **Reflection:** if `knowledge/reflection.md` says one is due, offer it. Never
  insist.
