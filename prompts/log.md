# Build log

Paste the block below into a project's `CLAUDE.md` or `AGENTS.md`, or straight
into a conversation. Replace `<PROJECT>` with the project name.

There is no install. If you want the entries written automatically when a
session ends or the context is compacted, run `familiar log add <project>`
instead, which wires a hook and records the project.

**If the project is public, put the log somewhere else.** A log worth keeping
records what broke and what it cost, and neither belongs in a repository
strangers read. `familiar log move <project> <folder>` moves it and records
where it went, so the hooks keep writing to it and there is still only one of
it.

A build log is where the material for writing about your work comes from. The
`case-study` stage reads one and turns it into a brief and a set of interview
questions.

---

```
Keep a build log for this project at <PROJECT>-LOG.md, and maintain it as we work.

WHAT IT'S FOR

Working docs (CLAUDE.md, README) describe what's true now and get pruned when
something is superseded, which is correct for working and useless for looking
back. Git history has what changed but not why. This file holds the rest:
decisions, what we got wrong, and what the numbers were at the time.

Assume I'll use it to reflect on the project and possibly write publicly about
it. It's raw material for me, not a finished account. My framing goes on top
later; yours should stay out of the way.

RECORD, DON'T DRAMATISE

This is the rule that matters most, because the failure mode is subtle.

Write down what happened and what it cost. Don't narrate it. No "the day
everything changed", no "a hard-won lesson", no calling a normal bug a crisis or
a normal week a turning point. If something took three attempts, say it took
three attempts. That's more interesting than any adjective, and it lets me
decide later whether it was a big deal.

Specifically:
  - Prefer numbers to intensifiers. "Cost 4 hours and one destructive migration"
    over "a painful detour".
  - No superlatives about the project's trajectory. You don't know yet.
  - Don't editorialise my decisions, and don't praise them.
  - Section headings should say what the entry contains, not sell it.

ENTRY FORMAT

One entry per working session, dated, newest at the bottom. Scannable first,
prose only where prose earns it.

  ## YYYY-MM-DD

  **Shipped**
  - One line each. What now exists that didn't before.

  **Decisions**
  - What was decided, what was rejected, and the reason. Include mine and yours.

  **Went wrong**
  - Wrong turns, surprising bugs, wasted work. Name the cause, and the cost in
    time, money or rework. Include your own mistakes. This is the section that's
    worth reading later and the one you'll be tempted to skip.

  **Numbers**
  - Anything measurable: users, cost per operation, spend, conversion, timings.
    Unrecoverable if not written down now.

  **Open**
  - Carried forward: unresolved questions, known risks, things waiting on me.

Omit any section with nothing real in it. An empty "Went wrong" is fine; a
padded one is not.

ASK ME THINGS

At the end of a working session, write the entry and show me a short recap: what
shipped, what's open, what needs me next. Keep it to something I can read in
twenty seconds.

Ask in the moment, rather than at session end, when you notice:
  - I made a call you don't fully understand the reasoning for. Get the reason
    while I still remember it.
  - Something didn't work and I seemed to have a view on why.
  - I changed direction. Capture what prompted it, not just the new direction.

COMPACTION

When the session is compacted, treat it as a real event worth recording rather
than a housekeeping blip. Before the context is summarised away, append a dated
entry closing out what the compaction is compressing, headed
"## YYYY-MM-DD (compacted)". Keep it to what a future reader would actually
need. The compaction summary is a view; the log entry is the record. If nothing
happened since the last entry, append a one-line Open carry-forward rather than
padding.

MAINTENANCE

  - Append-only. Never edit or delete an earlier entry to tidy the history. A
    corrected entry loses the mistake, which was the point of keeping it.
  - Write entries as part of the work, not batched at the end. The reasoning is
    gone by then, and the reasoning is what this is for.
  - Plain language. No "leveraged", "streamlined", "robust". If a thing broke,
    say it broke.
  - If there's history before today, reconstruct a skeleton from git log and
    file history, but mark those entries as reconstructed. They record what
    happened and not why, and that difference matters.
  - Keep a note in the working doc pointing here, so this doesn't get orphaned.
```

---

## Why the entry trigger is a judgement call

An enumerated list of commit types that qualify would be followed mechanically
and produce a changelog. *Would this be hard to reconstruct from the diff?* is
the actual question, and a capable model answers it better than any list could.

## Why the agent's own mistakes are asked for explicitly

Most agents will summarise what they built and quietly omit what they got wrong.
That instruction is what makes the output readable rather than a sanitised
changelog. It is the single most load-bearing line in the block above.
