---
description: Familiar: Mechanical pass: AI tells, house rules, exact fixes
---
Run the Familiar **line-edit** stage. Familiar lives at `{{FAMILIAR_HOME}}`.

1. Read `{{FAMILIAR_HOME}}/AGENTS.md` for the rules.
2. Read `{{FAMILIAR_HOME}}/prompts/line-edit.md` and follow every instruction in it exactly. It names the `knowledge/` files you must read first; all paths are relative to the Familiar folder above.
3. Arguments: $ARGUMENTS
4. Write outputs into the piece folders under `{{FAMILIAR_HOME}}/pieces/` as the prompt specifies.
5. Never skip a decision gate: the stage ends where the prompt says it ends, and waits for the writer.
