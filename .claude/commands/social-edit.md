---
description: "Familiar: Edit a post before it ships. Viewpoint first, then the mechanics"
---
Run the Familiar **social-edit** stage. Familiar lives at `{{FAMILIAR_HOME}}`.

1. Read `{{FAMILIAR_HOME}}/AGENTS.md` for the rules.
2. **Knowledge lives at `{{FAMILIAR_KNOWLEDGE}}`.** Every `knowledge/<file>.md` a prompt names is read from there, not from the Familiar folder. If that path ends in the repo's own `knowledge/`, those are the shipped templates: say so and do not edit against them.
3. Read `{{FAMILIAR_HOME}}/prompts/social-edit.md` and follow every instruction in it exactly. It names the knowledge files you must read first.
4. Arguments: $ARGUMENTS
5. This stage runs in the conversation and writes no report. Only the approved copy and the recorded picks go into `social.md`.
6. Never skip a decision gate: the stage ends where the prompt says it ends, and waits for the writer. It never touches a scheduler; `publish` does that.
