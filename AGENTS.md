# Familiar

A companion for writing about your own work. Tool-agnostic: runs from Claude
Code or opencode; the `knowledge/` and `prompts/` markdown can also be pasted
into a claude.ai Project.

## Pipeline

```
/case-study → brief.md + interview-questions.md   (from a build log or a session transcript; preps the interview, never runs it)
/interview  → notes.md        (one question at a time; thesis, stakes, evidence, themes)
/outline    → outline.md      (three structures; the writer picks)
/draft      → draft.md        (full draft in voice, [NEEDS SOURCE] brackets over inventions)
/dev-edit   → edits/dev-edit-report.md   (report only, never auto-apply)
/line-edit  → edits/line-edit-report.md  (mechanical pass, exact fixes per flag)
/social     → social.md       (candidate pool → the writer picks per channel → finalise → schedule on confirm)
/learn      → knowledge/proposals/*.md  (ingest past writing, or diff draft vs final; proposes rules, applies only what is accepted)
/reflect    → <reflections>/<project>.md  (two questions about the work, recorded verbatim; where the voice comes from)
/log        → a build log per project   (what shipped, decisions, went wrong, numbers; the hook writes an (auto) entry at session end)
```

Each piece lives in `pieces/YYYY-MM-DD-slug/`. Stages are gated: never advance
to the next stage without the writer asking. Every piece names its primary
theme (and any intersection) in notes.md; later stages serve that.

## Moving between stages

The gates exist to stop drift, and they also make it safe to move in both
directions. Treat these as the default, not the exception:

- **Going back is normal.** If a later stage shows that an earlier one missed
  something, run the earlier stage again on the same piece. It reads what is
  already there and adds to it. The interview appends to notes.md; the
  outline offers new shapes next to the chosen one; nothing is thrown away.
- **Reworks are scoped.** When `$ARGUMENTS` names a section, heading, or
  paragraph, work on that part only and leave the rest of the file exactly as
  it is. "dev-edit the opening", "line-edit section 3", "draft the ending
  again with the other structure" are all one-section runs.
- **Never restart a piece silently.** If a stage would overwrite a file that
  has content, say so and ask whether to replace it, add to it, or write a
  numbered variant beside it (`draft-2.md`).
- **Pick up at the writer's pace.** Read the piece's `SESSION-CONTEXT.md` on
  resume and say in one line where the piece is and what the open decision was.
  Do not summarise the whole history and do not push towards the next stage.

## Offering a reflection

Reflection is something Familiar does with the writer, so notice when one is due
rather than waiting to be asked.

When a stage finishes and `knowledge/reflection.md` says a reflection is due on
its cadence, offer one in a single line and stop. At a stage exit only, never
during the work. Once per session. If they say no, or say nothing about it, drop
it and do not raise it again in that session. Never offer when reflection is
off, and never when the settings are still the template.

A reflection is a stage, so it has a gate like any other: it ends where
`prompts/reflect.md` says it ends.

## Commands, and how they differ from stages

`board` is a command, not a stage. It makes no editorial decision, so it has no
gate: it reads the piece folders and writes HTML beside them, and changes
nothing.

```
scripts/board.py --open
scripts/board.py --pieces DIR --pieces DIR       pieces in more than one place
```

It writes `.board/index.html`: a column per state of the writing, Thinking,
Writing, Editing, Ready and Sent, with a card per piece. Every card carries the
next thing that piece needs, taken from the context log when a stage left a
note and worked out from the files when none did. Each piece also gets its own
page holding that decision, the unresolved brackets listed out, the supporting
files and the draft.

Run it when the writer asks what they have in flight, or when a piece has sat
long enough that they need catching up.

`--serve` adds Archive and Delete to each card, for the writer's hand only.
Archive moves a folder into `.archive/` and is reversible. Delete removes it.
A piece that has been sent, meaning it has a `final.md`, cannot be deleted from
the board: that file is the record of something that exists in the world and is
what `learn diff` reads. Never archive or delete a piece on the writer's
behalf.

## Rules for agents

- Read the stage's prompt file and every knowledge file it lists before acting.
- The house rules live in `knowledge/positioning.md` (language, spelling, dash
  policy, reading-ease target, whether pieces end on an invitation). Apply
  them; do not substitute your own defaults. If `Language:` is not English,
  read `knowledge/languages/<code>.md` and honour its skip/keep/replace table
  before any rule marked (en) in style-rules.md.
- Never invent evidence. Use `[NEEDS SOURCE: ...]` instead. Never invent a
  quote. Use `[ASK THE WRITER: ...]`.
- Edits surface decisions with exact rewrites; the writer accepts, rejects or
  revises. Never produce a "clean version".
- Write in the writer's voice as described in `knowledge/voice-guide.md`, using
  `knowledge/examples/canonical.md` as the reference. If the voice guide is still
  the unfilled template, say so and ask for a sample before drafting.
- The social stage never writes to a scheduler without the writer's explicit
  final confirmation, and only reaches a scheduler the way
  `knowledge/social-schedule.md` describes. Keys and tokens never go in that
  file.
- **Context log:** at the exit of every stage, append an entry to the piece's
  own `SESSION-CONTEXT.md` per `knowledge/context-log.md`: status, files
  touched, what changed, the decision gate for the writer, and next stage.
  One log per piece, inside the piece folder. Append, never replace. Read it on
  resume to pick work back up.

## File map

- `knowledge/positioning.md`: what the publication is, house rules, audience, themes
- `knowledge/voice-guide.md`: how the writer writes, with patterns
- `knowledge/style-rules.md`: mechanical checklist for line edits
- `knowledge/editor-report.md`: dev-edit taxonomy and report spec
- `knowledge/examples/canonical.md`: annotated excerpts of the writer's published work
- `knowledge/reflection.md`: whether reflection is on, its cadence, where the answers live, and the question bank
- `knowledge/social-schedule.md`: channels, cadence, send times, slot shapes; the scaffold the social stage fills
- `knowledge/languages/<code>.md`: per-language rule overrides and tells; `_template.md` to add one
- `knowledge/humanizer-check.md`: weekly diff against humanizer's tell list; candidates, never applied
- `knowledge/models.md`: per-stage model recommendations and fallback rule
- `knowledge/context-log.md`: the resume log format
- `prompts/*.md`: source of truth for each stage
- `.claude/commands/`: thin adapters calling the prompts; `scripts/setup.sh`
  installs them globally as `familiar-*`
- `skills/familiar/SKILL.md`: the single-skill entry point for `npx skills add`;
  routes on the first argument word to the same prompts

## Maintenance

When a real piece teaches you something about the voice, update
`knowledge/voice-guide.md` and prune or add to `canonical.md`. The second time
the writer makes the same edit by hand, encode it as a rule in
`style-rules.md`.
