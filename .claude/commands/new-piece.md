---
description: "Familiar: start a new piece. Scaffolds the folder, then begins the interview that turns your idea into notes"
---
Start a new Familiar **piece**. Familiar lives at `{{FAMILIAR_HOME}}`.

`new-piece` is a command, not a stage. It makes no editorial decision, so it
has no gate: it scaffolds a folder and hands you to the interview.

1. Take the slug from `$ARGUMENTS`. It is a short, descriptive name, not a
   title: `my-essay-title`, not `"My Essay Title"`. The date is added for you.
   If the writer gave you a title or a sentence instead, propose a slug from it
   and check before you run anything.

2. Run it:

   ```
   python3 {{FAMILIAR_HOME}}/scripts/familiar new-piece <slug>
   ```

   It creates the folder, an `edits/` subfolder, a `SESSION-CONTEXT.md` opened
   at the init entry, and a `notes.md` with Thesis, Evidence and Open questions
   headings. It refuses to overwrite a folder that already exists.

3. Report the path it printed, then **begin the interview**: read
   `{{FAMILIAR_HOME}}/prompts/interview.md` and follow it exactly. Knowledge
   lives at `{{FAMILIAR_KNOWLEDGE}}`; every `knowledge/<file>.md` a prompt names
   is read from there, not from the Familiar folder. If that path ends in the
   repo's own `knowledge/`, those are the shipped templates: say so and do not
   draft against them.

The interview is where the piece actually starts. The folder is just somewhere
to put it, so do not stop at the scaffold and wait to be asked.
