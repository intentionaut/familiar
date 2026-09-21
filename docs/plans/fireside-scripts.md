# Fireside interview scripts

Status: built (issue #107), builds on prepared sets (#95).

## The idea

A prepared question set can read like a form or like a conversation. A
fireside script is the second: three prompts that listen first, ask one
thing, say how to answer, and hold two follow-ups back. One setting,
`Interview engagement`, runs from `companion` to `deep dive`, and warmth and
plain language are checked by `scripts/question-check.py --warm`, not hoped
for. The format, the three settings and the arc are in `prompts/interview.md`,
"Fireside scripts".

## Where the moves come from

The five moves are techniques borrowed from public interviews, as we
understand them. They are influences, not quotations, and nothing in the
prompts speaks in anyone's voice. The prompts name each move by what it does.

- Ben Thompson: follow the value, asking where it goes as things change.
- Tyler Cowen: the specific case, asking for one real instance over a general claim.
- Dwarkesh Patel: the tension between two things said, and how the thing works.
- Ezra Klein: the strongest opposing case, put fairly.
- Kara Swisher: what you would tell a friend to do on Monday.

## Where the setting lives

`- Interview engagement:` in the House rules of the house's `positioning.md`.
The shipped template leaves it as a bracketed placeholder, which reads as
unset, which means fireside. `--engagement` overrides it for one run. A value
that is not one of the three is refused, not ignored.

## Not built here

Voice rendering (#102), transcript ingest (#97), the canvas (#96), and any
change to the live one-question-at-a-time interview.
