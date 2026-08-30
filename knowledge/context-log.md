# Context log

`SESSION-CONTEXT.md` at the project root is how a piece survives a closed
terminal. Every stage appends an entry on exit. Nothing is ever replaced or
tidied; read the last few entries to pick work back up.

## Entry format

```
## YYYY-MM-DD HH:MM  <stage>  <piece folder>

Status: <done / waiting on the writer / blocked>
Files: <what was created or changed, relative paths>
What changed: <two or three lines, facts only>
Decision gate: <the exact question the writer needs to answer before the next stage>
Next stage: <name, or "none until the writer decides">
```

## Rules

- Terse. If it takes longer than a minute to read, it is too long.
- Append only. Newest at the bottom.
- The decision gate is the important line. It is what the next session reads
  first.
- Ignored by git by default; it is working state, not a record.
