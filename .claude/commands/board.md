---
description: "Familiar: a board of every piece you have in flight, what each one needs next, and a page per piece for picking one back up"
---
Run the Familiar **board**. Familiar lives at `{{FAMILIAR_HOME}}`.

`board` is a command, not a stage. It makes no editorial decision, so it has no
gate: it reads the piece folders and writes static HTML beside them.

1. **First, catch up on anything that has been sent.** Run
   `python3 {{FAMILIAR_HOME}}/scripts/pull-final.py`. It writes `final.md` for
   any piece whose title matches a published post, which is what moves a piece
   from Ready to Sent and what `learn diff` reads. It never overwrites an
   existing one and never guesses at a match. With no publication key
   configured it says so and changes nothing, which is fine: carry on.

2. You do not need to work out where the pieces are. `board.py` resolves them
   itself: `--pieces` flags first, then `$FAMILIAR_PIECES`, then any `pieces =`
   lines in a `.familiar` file, then `{{FAMILIAR_HOME}}/pieces`. Pass `--pieces`
   only when the writer names a folder in `$ARGUMENTS`.

3. Run it, adding `--serve` when the writer wants to work on a piece or tidy up
   rather than only look, and `--open` otherwise:

   ```
   python3 {{FAMILIAR_HOME}}/scripts/board.py --open
   ```

   `--serve` keeps running until it is stopped. Run it in the background and
   give the writer the address it prints.

4. Report what it printed: how many pieces, how many carry a note from you, and
   the path. Do not summarise the board itself; the writer is about to look at
   it.

`--serve` starts a local server so the board can be worked on as well as read.
On a piece's page the draft is a document the writer types into, and they
comment on any words for an agent to answer. Each card also gets Archive,
which moves the folder into `.archive/` and can be undone, and Delete, which
removes it. A piece that has
been sent, meaning it has a `final.md`, shows no Delete and cannot be edited.

**Answering the comments is your part.** While the writer is on the board, run
`familiar rework watch` in the background. When it returns, run `familiar
rework open`, write a suggestion for each comment per
`{{FAMILIAR_HOME}}/prompts/draft.md`, "Comments from the board", and hand each
back with `familiar rework propose <piece> <id> <file>`. Then start the watch
again. The writer accepts, edits, replies to or rejects each suggestion on the
board. Stop watching when they say so.

Never accept, reject, archive or delete anything on the writer's behalf. Those
controls are for their hand, not yours.
