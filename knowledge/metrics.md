# Metrics

Every line edit already computes the numbers that answer "is it learning my
voice": flags per category, reading ease, grade level. This file is where they
stop being thrown away. The line-edit stage appends one line per piece at its
exit; nothing else writes here.

## The log

| Date | Piece | Words | Flags per 1000 | Reading ease | Grade | By rule |
|------|-------|-------|----------------|--------------|-------|---------|

One row per line edit, in order, newest at the bottom. `Flags per 1000` is
total flags divided by the draft's word count, times 1000, so a long piece
and a short one can sit in the same column. `By rule` is the tally behind it:
`overused-words: 2, hedging: 1, ...`, one entry per rule that fired.

## What it is for

- **The learning curve.** Flags per 1000 words across drafts, over time. A
  falling line is the drafts arriving closer to the voice; a flat one is the
  loop teaching nothing.
- **The quiet rules.** The by-rule tally is how `learn` sees a rule that has
  stopped firing. A rule silent across the last [five] pieces is proposed
  for retirement or scoping, at the same gate as any other proposal.
- **The false-positive generators.** Read beside the dispositions in the
  line-edit reports: a rule that fires often and is rejected often is not a
  rule, it is a cost.
