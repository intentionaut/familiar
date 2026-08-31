---
description: "Familiar: Schedule already-approved posts; builds and counts URLs first, one confirm gate, never rewrites your copy"
---
Run the Familiar **publish** stage. Familiar lives at `{{FAMILIAR_HOME}}`.

1. Read `{{FAMILIAR_HOME}}/AGENTS.md` for the rules.
2. Read `{{FAMILIAR_HOME}}/prompts/publish.md` and follow every instruction in it exactly. It names the `knowledge/` files you must read first; all paths are relative to the Familiar folder above.
3. Arguments: $ARGUMENTS
4. This stage takes approved copy and schedules it. It never writes, re-picks or improves posts. If the copy is not finished, run `/familiar-social` instead.
5. Nothing reaches a scheduler without an explicit confirmation at the gate.
