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

## What the scripts kept getting wrong

The prompt was written against generated scripts, at all three settings, on
invented ideas that differ in kind (a technical claim, a workplace idea, a
personal-experience piece, a contrarian take, a half-formed hunch, and one
where the files hold almost nothing). Five failures came back often enough to
be worth a rule, and each rule in "Fireside scripts" that looks fussy is one
of them:

- The guess turned into an inventory when the files were thin ("your notes
  hold that one line and nothing else"), which tells the writer about the
  tool's problem rather than their idea. `files-talk` now flags it.
- Companion argued back anyway, putting a critic on the table before the
  gentle doubt question. `critic-at-companion` now flags it.
- Deep dive stacked the asks: something observable, what would change your
  mind, and what you would tell a friend to do on Monday, all in one answer
  shape. The observable moved to prompt 2 and the friend became a held
  follow-up.
- Deep dive built a tension out of the writer's idea versus a log entry, which
  reads as a catch rather than a question. Both halves have to be the writer's
  own words, and a bracketed tension stays out of what they read.
- Questions carried the interviewer's position as settled ("which of those
  four made the product worse?"), and every follow-up in every script opened
  "if you'd like" or "if it helps". The invitation check was widened so the
  wording can vary.

## Where the setting lives

`- Interview engagement:` in the House rules of the house's `positioning.md`.
The shipped template leaves it as a bracketed placeholder, which reads as
unset, which means fireside. `--engagement` overrides it for one run. A value
that is not one of the three is refused, not ignored.

## Not built here

Voice rendering (#102), transcript ingest (#97), the canvas (#96), and any
change to the live one-question-at-a-time interview.
