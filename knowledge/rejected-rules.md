# Rejected rules

The record of rules the writer does not want. `knowledge/proposals/` is
gitignored, so a proposal file can vanish on a fresh clone; this index is
committed on purpose. Without it, `learn` will cheerfully propose again what
was already turned down.

One line per rejection, written at the gate the moment it happens:

| Date | Rule | Why not, in the writer's words |
|------|------|--------------------------------|

Slim on purpose: the rule and the reason, never the proposal itself. The
proposal file holds the evidence; this line holds the verdict.

`learn` reads this index before proposing, in every mode, and does not bring
a rule back unless the evidence has changed. When it does bring one back, it
says what changed.
