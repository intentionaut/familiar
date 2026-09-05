# Weekly check-in

Familiar can notice, at the start of a session, whether it has been a while
since it last spoke with you, and say so before you get to work: the same
block `familiar` already prints when you run it yourself, offered rather than
waited for.

On by default, everywhere the skill is installed. A repo opts itself out; the
house does not have to turn itself off to exclude one project.

## Settings

- Check-in: on
- Cadence: weekly
- Last engaged: [set automatically]
- Last offered: [set automatically]

Set by `familiar` the first time it does real work, the same way the two-loops
introduction is. Change `Check-in` to `off` to turn it off everywhere, or the
cadence to `fortnightly` or `monthly` to ask less often. `Last engaged` and
`Last offered` are bookkeeping; edit the settings above them, not these.

**Two clocks, not one.** `Last engaged` moves only when real engagement
happens: a `familiar` run, `engage --all`, or a check-in you said yes to. It
is what makes "it's been a while" a true claim about the work rather than
about the calendar. `Last offered` moves every time the line below actually
gets said, yes or no. It is what stops the same quiet week being mentioned
every session between now and the next one.

**Cadence is a floor, not an alarm.** It is how long has to pass since `Last
engaged` before Familiar will offer a check-in at the start of a session. You
can always run `familiar` yourself, and a missed one costs nothing: the
history is still there next time you ask.

**Off means off.** No check at session start, no notification, no mention.

## Taking a project out, without turning the house off

Check-in and first engagement both default to on because the skill is meant to
work the moment it is installed, not after a setup step in every repo. A repo
that should never hear from Familiar (client work under someone else's name,
a codebase that is not yours to narrate) opts itself out with a line in that
project's `.familiar` file:

```
engage = off
```

This silences the automatic session-start offer in that repo only. It does not
touch a `familiar` the writer types there by hand: taking a project out of the
ambient loop and disabling the tool for it are different requests, and only
the first one is what an exclusion is for.

## What has to be true for anything to be said

Four conditions, all required:

1. Check-in is on.
2. The cadence has elapsed since `Last engaged`.
3. The cadence has elapsed since `Last offered`, so a week already mentioned
   is not mentioned again before the next one is due.
4. The session starts inside a git repository with commits, whose
   `.familiar`, if it has one, does not say `engage = off`.

Unlike the first draft of this file, a project Familiar has never read is not
excluded on that basis alone: first engagement now happens the same way a
returning check-in does, at session start, rather than only when the writer
remembers to run `familiar` by hand. What is excluded is stated explicitly, by
the writer, per repo, not implied by silence.

## What it says

One line, at the very start of a session, before anything else. For a project
already engaged:

> It's been a week since you last checked in through Familiar. Run `familiar`
> to see what's changed in `<project>`?

For a project seen for the first time:

> I haven't read this project yet. Run `familiar` to see what its history
> says?

A no is not asked again until the cadence next elapses. A yes runs the same
`familiar` block you would get by typing it yourself: observations, what
there is to work from, and nothing drafted until you say so.

## Why this offer works differently from the others

Voice review and reflection are offered once per session, then dropped,
because a session is already open to drop them within. A check-in fires
*before* any session content exists, so "don't ask again this session" is not
a real limit here: on that reading every session would ask exactly once,
forever. Its floor is `Last offered`, not the session: once answered,
satisfied or declined, it stays quiet until the cadence next elapses,
regardless of how many sessions happen in between.
