# Voice review

Familiar collects two kinds of evidence about how you write, and this file
decides when it hands them back to you.

- **Decisions.** Every time a stage offered you options and you picked one, it
  wrote down which and why. The why is the part that matters: it is a rule you
  already hold, said out loud once.
- **Diffs.** Every time you edited a draft before publishing, the gap between
  the two is evidence of the same thing.

Left alone, both pile up and neither becomes a rule. The review is the moment
they do.

It is off until you turn it on. Replace the bracketed values.

## Settings

- Voice review: [on / off]
- Cadence: [weekly / fortnightly / monthly / every N decisions]
- Proposals live in: knowledge/proposals/

**Cadence is a floor, not an alarm.** It is how long has to pass, or how many
decisions have to accumulate, before Familiar will offer a review at the end of
a stage. You can always run `learn decisions` yourself, and a missed review
costs nothing: the evidence keeps.

**Off means off.** No offer at the end of a stage, no counting, no mention.

## What a review does

It reads every `CHOSEN` and `BECAUSE` pair recorded since the last one, plus any
`final.md` written since, groups the reasons that recur, and proposes rules with
the picks they came from as evidence.

It proposes. It never edits a knowledge file. Same gate as the rest of `learn`:
you accept, reject or revise each rule, and the proposal file stays as the
record either way.

## How it is offered

One line at the exit of a stage, never during the work, once per session:

> Six decisions since the last review. Run one? (y/n)

If you say no, it drops it and does not raise it again that session.

## What makes a rule worth proposing

- **It recurs.** One pick is a preference. The same reason given three times is
  a rule.
- **It is yours, not general.** "Prefer the more generous option when the cost
  is only length" is a rule. "Consider your audience" is advice, and advice does
  not go in these files.
- **It cites its evidence.** Every proposed rule names the picks it came from,
  the way `learn diff` names the quote pair.

## Why decisions and diffs are both needed

A diff catches what you changed. It cannot catch what you chose, because
choosing happens before there is any text to compare. A title picked over two
others, a structure taken because the story was real, a passage kept because it
was the most generous version: none of that appears in a diff, and all of it is
voice.
