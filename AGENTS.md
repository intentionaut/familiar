# Familiar

A companion for writing about your own work. Tool-agnostic: runs from Claude
Code or opencode; the `knowledge/` and `prompts/` markdown can also be pasted
into a claude.ai Project.

## Pipeline

```
/case-study → brief.md + interview-questions.md   (from a Captain's Log build log; preps the interview, never runs it)
/interview  → notes.md        (one question at a time; thesis, stakes, evidence, themes)
/outline    → outline.md      (three structures; the writer picks)
/draft      → draft.md        (full draft in voice, [NEEDS SOURCE] brackets over inventions)
/dev-edit   → edits/dev-edit-report.md   (report only, never auto-apply)
/line-edit  → edits/line-edit-report.md  (mechanical pass, exact fixes per flag)
```

Each piece lives in `pieces/YYYY-MM-DD-slug/`. Stages are gated: never advance
to the next stage without the writer asking. Every piece names its primary
theme (and any intersection) in notes.md; later stages serve that.

## Rules for agents

- Read the stage's prompt file and every knowledge file it lists before acting.
- The house rules live in `knowledge/positioning.md` (spelling, dash policy,
  reading-ease target, whether pieces end on an invitation). Apply them; do not
  substitute your own defaults.
- Never invent evidence. Use `[NEEDS SOURCE: ...]` instead. Never invent a
  quote. Use `[ASK THE WRITER: ...]`.
- Edits surface decisions with exact rewrites; the writer accepts, rejects or
  revises. Never produce a "clean version".
- Write in the writer's voice as described in `knowledge/voice-guide.md`, using
  `knowledge/examples/canonical.md` as the reference. If the voice guide is still
  the unfilled template, say so and ask for a sample before drafting.
- **Context log:** at the exit of every stage, append an entry to the project
  root `SESSION-CONTEXT.md` per `knowledge/context-log.md`: status, files
  touched, what changed, the decision gate for the writer, and next stage.
  Append, never replace. Read it on resume to pick work back up.

## File map

- `knowledge/positioning.md`: what the publication is, house rules, audience, themes
- `knowledge/voice-guide.md`: how the writer writes, with patterns
- `knowledge/style-rules.md`: mechanical checklist for line edits
- `knowledge/editor-report.md`: dev-edit taxonomy and report spec
- `knowledge/examples/canonical.md`: annotated excerpts of the writer's published work
- `knowledge/models.md`: per-stage model recommendations and fallback rule
- `knowledge/context-log.md`: the resume log format
- `prompts/*.md`: source of truth for each stage
- `.claude/commands/`: thin adapters calling the prompts; `scripts/setup.sh`
  installs them globally as `familiar-*`

## Maintenance

When a real piece teaches you something about the voice, update
`knowledge/voice-guide.md` and prune or add to `canonical.md`. The second time
the writer makes the same edit by hand, encode it as a rule in
`style-rules.md`.
