# Origin notes

Written while Captain's Log was a separate tool, before it was merged into
Familiar on 2026-08-30. Kept as written, because the reasoning is the record.
The drafting loop these notes argue for is now Familiar's outline, draft,
dev-edit and line-edit stages; the capture and reflection halves are its `log`
and `reflect` stages.

---

## Why the prompt is shaped this way

**The entry trigger is a judgement call on purpose.** An enumerated list of commit
types that qualify would be followed mechanically and produce a changelog. *"Would
this be hard to reconstruct from the diff?"* is the actual question, and a capable
model answers it better than any list could. This is the main reason the prompt is
written for Opus rather than something cheaper.

**Append-only is the load-bearing constraint.** The instinct when revisiting a log
is to tidy it — correct the entry where you got it wrong at the time. That deletes
exactly what you were keeping the log for. Wrong turns are the content.

**Numbers are the part people forget.** Everything else can be half-remembered.
"Cost per analysis was £0.04 in August" cannot, and it's unrecoverable a month
later.

**Asking for the human's reasoning matters more than it looks.** A log written
entirely in the agent's voice reads as a machine's account of someone else's
project — useless as raw material for the person whose project it was. Several
decisions in any build are the human's, and they need to be in there in their
terms.

**Plain language is specified explicitly** because the failure mode is corporate
mush. "Leveraged", "streamlined", "robust". If a thing broke, the entry should say
it broke.

## Origin

Written while building [Friday](https://fridayforwork.com), a career coaching tool
for people getting their first jobs in film and TV. Five days in, we wanted to
look back at the build and found the first three days were unrecoverable — the git
history recorded what happened and nothing about why, and the working doc had
pruned every superseded decision.

The first Friday log entry had to be reconstructed from `git log`, and it reads
like a changelog. That's the whole argument for the tool, demonstrated
accidentally.
