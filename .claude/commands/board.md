---
description: "Familiar: a board of every piece you have in flight, what each one needs next, and a page per piece for picking one back up"
---
Run the Familiar **board**. Familiar lives at `{{FAMILIAR_HOME}}`.

`board` is a command, not a stage. It makes no editorial decision, so it has no
gate: it reads the piece folders and writes static HTML beside them.

1. Work out where the writer's pieces live. Check in this order and use every
   folder that exists, passing `--pieces` once for each:
   - any folder the writer names in `$ARGUMENTS`
   - `$FAMILIAR_PIECES` (colon-separated)
   - `{{FAMILIAR_HOME}}/pieces`
   - in a Dex vault, `<vault>/04-Projects/Writing`
   If the writer keeps pieces somewhere else as well, ask once and remember it
   for the session.

2. Run it, adding `--serve` when the writer wants to tidy up rather than only
   look, and `--open` otherwise:

   ```
   python3 {{FAMILIAR_HOME}}/scripts/board.py --open --pieces <dir> [--pieces <dir>]
   ```

3. Report what it printed: how many pieces, how many carry a note from you, and
   the path. Do not summarise the board itself; the writer is about to look at
   it.

`--serve` starts a local server so the board can be tidied as well as read.
Each card gets Archive, which moves the folder into `.archive/` and can be
undone, and Delete, which removes it. A piece that has been sent, meaning it
has a `final.md`, shows no Delete and the server refuses one. Everything else
is working material and is the writer's to clear out.

Never archive or delete anything on the writer's behalf. Those controls are for
their hand, not yours.
