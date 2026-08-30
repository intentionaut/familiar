---
description: Familiar: Teach it your voice. 'ingest <path>' drafts the voice files from past writing; 'diff <piece>' turns your edits into rules. Proposes, never applies without you
---
Run the Familiar **learn** stage. Familiar lives at `{{FAMILIAR_HOME}}`.

1. Read `{{FAMILIAR_HOME}}/AGENTS.md` for the rules.
2. Read `{{FAMILIAR_HOME}}/prompts/learn.md` and follow every instruction in it exactly. It names the `knowledge/` files you must read first; all paths are relative to the Familiar folder above.
3. Arguments: $ARGUMENTS
4. Write proposals into `{{FAMILIAR_HOME}}/knowledge/proposals/` as the prompt specifies; apply to knowledge files only what the writer accepts.
5. Never skip a decision gate: the stage ends where the prompt says it ends, and waits for the writer.
