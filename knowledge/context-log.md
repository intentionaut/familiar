# Context log

`SESSION-CONTEXT.md` **inside the piece folder** is how a piece survives a
closed terminal. Every stage appends an entry on exit. Nothing is ever replaced
or tidied; read the last few entries to pick work back up.

One log per piece, so a piece is self contained. Moving or archiving a piece
takes its history with it, and nothing collides with a session file belonging
to whatever else lives in that folder. If you have an older log at the project
root, it can be split: every entry names its piece in the heading, so the split
is a filter and needs no guessing.

## Entry format

```
## YYYY-MM-DD HH:MM  <stage>  <piece folder>

Status: <done / waiting on the writer / blocked>
Files: <what was created or changed, relative paths>
What changed: <two or three lines, facts only>
Chosen: <what the writer picked, when a stage offered options. Omit if none.>
Because: <their reason, in their words, one line. Required whenever Chosen is present.>
Decision gate: <the exact question the writer needs to answer before the next stage>
Next stage: <name, or "none until the writer decides">
```

## Rules

- Terse. If it takes longer than a minute to read, it is too long.
- Append only. Newest at the bottom.
- The decision gate is the important line. It is what the next session reads
  first.
- **`Chosen` never appears without `Because`.** The pick is bookkeeping; the
  reason is the evidence `learn decisions` reads. One line in the writer's own
  words beats three in yours. If they did not give a reason, ask for one before
  logging, or write `Because: not given`.
- Ignored by git by default; it is working state, not a record.
- Keep the heading format exactly as above, including the piece folder.
  It is read by a person and by `status`, which quotes the decision gate
  back verbatim and never paraphrases it.
