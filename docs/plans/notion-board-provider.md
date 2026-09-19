# Notion as an optional board provider

Plan for the provider boundary and a Notion provider behind it. The built-in
board stays as it is and is not extended; new board capability lands here.

## What a provider is

`scripts/board_provider.py` defines the contract: read every row, read one,
create one, update named fields against the version that was read. A row holds
board fields only (title, state, next decision, last activity, blockers, links).
Everything else on a row is carried through untouched.

- The built-in board is one provider. It is read-only, because its record is
  the piece folders.
- A writer selects a provider in `knowledge/board-provider.md` in their own
  house. The shipped template leaves it unset, which means the built-in board.
- No provider deletes or archives, and none resolves a clash. A row that changed
  since it was read raises `BoardConflict`, and Familiar puts one question to the
  writer as a decision gate.

## What leaves the machine

Only when a writer selects a provider that lives off the machine, and only board
fields: the piece's title, its state, the next decision as the writer worded it in
the context log, a last-activity time, and blocker counts. A bracket's text is the
draft's, so blockers are counts. Draft text, notes and reports never leave.

## Decision: how a piece keeps one ID

A piece needs an ID that survives a renamed folder and works from the first
stage. The provider treats the ID as opaque. Until one is picked, the built-in
provider uses the folder name.

### A. `id:` in the draft's front matter
Buys: one place, already parsed by the board.
Costs: no draft exists at the interview and outline stages, and a stub has none,
so the pieces that most need a row have no ID.

### B. A small file in the piece folder holding a generated ID
Buys: exists from the first stage, independent of every other file, and survives a
rename. Reconciliation can add one to existing pieces without touching any file the
writer wrote.
Costs: one more file per piece folder, and existing pieces need it added once.

### C. Front matter in the context log
Buys: no new file, and the log exists from the first stage exit.
Costs: the log is append-only by rule, so editing its front matter breaks that
rule, and a piece has no log before its first stage exits.

### D. The folder name
Buys: nothing to add or migrate.
Costs: a rename or a same-day slug clash breaks the mapping, which is the failure
a stable ID exists to prevent.

Recommended: B.

Chosen:
Because:

## Order of work

1. This change: the boundary, the built-in provider behind it, provider selection,
   contract tests, and this decision.
2. The Notion provider: connection from the writer's house and the environment,
   field mapping, create, update, read, unknown-property preservation, stale writes,
   rate limits, an unreachable Notion.
3. `board` and `next` read through the selected provider.
4. Reconciliation of existing pieces and stubs, with a plan before any write.
