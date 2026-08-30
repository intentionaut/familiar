---
description: Familiar: Editorial report on the draft; nothing applied
---
Run the Familiar **dev-edit** stage. Familiar lives at `{{FAMILIAR_HOME}}`.

1. Read `{{FAMILIAR_HOME}}/AGENTS.md` for the rules.
2. Read `{{FAMILIAR_HOME}}/prompts/dev-edit.md` and follow every instruction in it exactly. It names the `knowledge/` files you must read first; all paths are relative to the Familiar folder above.
3. Arguments: $ARGUMENTS
4. Write outputs into the piece folders under `{{FAMILIAR_HOME}}/pieces/` as the prompt specifies.
5. Never skip a decision gate: the stage ends where the prompt says it ends, and waits for the writer.
