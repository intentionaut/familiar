---
description: "Familiar: Extract patterns across projects for low-energy days"
---
Run the Familiar **harvest** stage. Familiar lives at `{{FAMILIAR_HOME}}`.

1. Read `{{FAMILIAR_HOME}}/AGENTS.md` for the rules.
2. **Knowledge lives at `{{FAMILIAR_KNOWLEDGE}}`.** Every `knowledge/<file>.md` a prompt names is read from there, not from the Familiar folder. If that path ends in the repo's own `knowledge/`, those are the shipped templates: say so and do not edit against them.
3. Read `{{FAMILIAR_HOME}}/prompts/harvest.md` and follow every instruction in it exactly. It names the knowledge files you must read first.
4. Arguments: $ARGUMENTS
5. Write the result to `knowledge/patterns.md` in the resolved knowledge folder.
6. Report what was found and suggest next steps.
