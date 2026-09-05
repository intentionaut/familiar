# Weekly check-in

Familiar can notice, once a session, whether it has been a while since you last
engaged with a project through it, and say so before you get to work — the same
block `familiar` already prints when you run it yourself, offered rather than
waited for.

It is off until you turn it on. Replace the bracketed values.

## Settings

- Check-in: [on / off]
- Cadence: [weekly / fortnightly / monthly]

**Cadence is a floor, not an alarm.** It is how long has to pass before
Familiar will offer a check-in at the start of a session. You can always run
`familiar` yourself, and a missed one costs nothing: the history is still
there next time you ask.

**Off means off.** No check at session start, no notification, no mention.

## What has to be true for anything to be said

Two conditions, both required:

1. The cadence above has elapsed since you last engaged with **any** project
   through Familiar. One clock, not one per project — a week spent deep in one
   codebase and none in the others still counts as checking in.
2. The session starts in a project Familiar has already engaged: a digest
   exists for it under `knowledge/digests/`.

A session in a project Familiar has never read produces nothing here, even
with check-in on and the cadence elapsed. This is a check for projects you
have already brought in, not an invitation into a new one — that invitation is
what `familiar` and `familiar engage --all` already are, and they still need
you to run them.

## What it says

One line, at the very start of a session, before anything else:

> It's been a week since you last checked in through Familiar. Run `familiar`
> to see what's changed in `<project>`?

A no is not asked again until the cadence next elapses. A yes runs the same
`familiar` block you would get by typing it yourself: observations, what
there is to work from, and nothing drafted until you say so.

## Why this offer works differently from the others

Voice review and reflection are offered once per session, then dropped,
because a session is already open to drop them within. A check-in fires
*before* any session content exists — "don't ask again this session" is not a
real limit here, because on that reading every session would ask exactly
once, forever. Its floor is the cadence itself, not the session: once
answered, satisfied or declined, it stays quiet until the cadence next
elapses, regardless of how many sessions happen in between.
