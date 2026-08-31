---
description: "Familiar: what it can see and what it still needs, with the one thing to do next"
---
Run Familiar's status check. Familiar lives at `{{FAMILIAR_HOME}}`.

1. Run `python3 {{FAMILIAR_HOME}}/scripts/doctor.py` and show the output as it is.
2. It reports three honest states per file: ready, still a template, or not there yet. A missing optional file is fine and gets no warning tone.
3. Do not fill in any knowledge file yourself. If the writer's voice files are still templates, offer `learn ingest <path to their past writing>`, which proposes and never applies without them.
