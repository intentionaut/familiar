---
description: Familiar: Teach it your voice. 'ingest <path>' drafts the voice files from past writing; 'diff <piece>' turns your edits into rules. Proposes, never applies without you
---
Run the Familiar **learn** stage. Familiar lives at `{{FAMILIAR_HOME}}`.

1. Read `{{FAMILIAR_HOME}}/AGENTS.md` for the rules.
2. **Knowledge lives at `{{FAMILIAR_KNOWLEDGE}}`.** Every `knowledge/<file>.md` a prompt names is read from there, not from the Familiar folder. If that path ends in the repo's own `knowledge/`, those are the shipped templates: say so and do not edit against them.
3. Read `{{FAMILIAR_HOME}}/prompts/learn.md` and follow every instruction in it exactly. It names the knowledge files you must read first.
4. Arguments: $ARGUMENTS
5. Write outputs into the writer's piece folder as the prompt specifies.
6. Never skip a decision gate: the stage ends where the prompt says it ends, and waits for the writer.
