---
description: "Familiar: reuse a finished piece. Short-form posts, or a longform companion for another channel; you choose first, and the gates stay"
---
Run the Familiar **repurpose** stage. Familiar lives at `{{FAMILIAR_HOME}}`.

1. Read `{{FAMILIAR_HOME}}/AGENTS.md` for the rules.
2. Read `{{FAMILIAR_HOME}}/prompts/repurpose.md` and follow every instruction in it exactly. It names the `knowledge/` files you must read first; all paths are relative to the Familiar folder above.
3. Arguments: $ARGUMENTS
4. Gate 0 is the choice between short-form and long-form. If the arguments do not name it, ask and stop. Never guess.
5. The long branch is a seeder: it writes a brief and interview questions, then hands off to /interview. It never drafts the companion piece.
6. Write outputs into the piece folders under `{{FAMILIAR_HOME}}/pieces/` as the prompt specifies.
7. Never skip a decision gate: the stage ends where the prompt says it ends, and waits for the writer.
