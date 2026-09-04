# Familiar

Turns the coding session the writer just finished into a newsletter issue they
actually wrote. It interviews them one question at a time, drafts in their
voice from what they have already published, and hands back an editor's report
instead of a rewrite. Nothing is invented: what cannot be sourced becomes a
visible bracket.

Tool-agnostic. Runs from Claude Code, opencode, Codex or Gemini CLI, installs
as a plugin or a skill, and the `knowledge/` and `prompts/` markdown can be
pasted into a claude.ai Project.

## Pipeline

```
/bring      → source.md + spine.md + brief.md   (a draft or notes you already have; maps what is there, never rewrites it)
/case-study → brief.md + interview-questions.md   (from a build log or a session transcript; preps the interview, never runs it)
/interview  → notes.md        (one question at a time; thesis, stakes, evidence, themes)
/outline    → outline.md      (three structures; the writer picks)
/draft      → draft.md        (full draft in voice, [NEEDS SOURCE] brackets over inventions)
/dev-edit   → edits/dev-edit-report.md   (report only, never auto-apply)
/line-edit  → edits/line-edit-report.md  (mechanical pass, exact fixes per flag)
/finalise   → title, subject line, SEO   (the last creative act; repurpose and social need a settled title)
/repurpose  → short: social.md | long: a companion piece's brief.md (you pick first; long seeds the pipeline, never drafts)
/social     → social.md       (candidate pool → quality pass → the writer picks per channel → finalise; ends at approved copy)
/publish    → social.md ## Scheduled  (schedules approved copy only; builds and counts URLs first, one confirm gate)
/learn      → knowledge/proposals/*.md  (ingest past writing, or diff draft vs final; proposes rules, applies only what is accepted)
/reflect    → <reflections>/<project>.md  (two questions about the work, recorded verbatim; where the voice comes from)
/log        → a build log per project   (what shipped, decisions, went wrong, numbers; the hook writes an (auto) entry at session end)
/harvest    → knowledge/patterns.md     (cross-project pattern extraction: themes, growth signals, ready topics)
/inspire    → inspirations/<date>-<slug>.md  (clip a snippet, article, or quote for later; optional "why it stuck" note)
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

## Offering a voice review

The decisions and diffs pile up. The review is the moment they become rules, and
it will not happen unless Familiar notices it is due.

When a stage finishes and `knowledge/voice-review.md` says a review is due on
its cadence, offer one in a single line and stop:

> Six decisions since the last review. Run one? (y/n)

At a stage exit only, never during the work. Once per session. If they say no,
or say nothing about it, drop it and do not raise it again in that session.
Never offer when voice review is off, and never when the settings are still the
template.

A review is `learn decisions`, so it has a gate like any other and it proposes
rather than applies.

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

## The cutting room

Material gets cut for good reasons and it is still good material. A statistic
dropped because the thesis moved is still true. A section cut because it is its
own piece is a piece nobody has written down.

**Any stage that cuts something substantial writes it to `cuts.md` in the piece
folder**, at its exit. Not a sentence trimmed in a line edit: a section, an
argument, a scene, a set of evidence, a title that was seriously considered.

```markdown
### <what was cut>
From: <stage> · <YYYY-MM-DD>
Why: <one line>
Flag: dead | reusable | blocked
<the material itself, if it is short enough to keep here>
```

The flags, and they are the whole point of the file:

- **`dead`** means wrong, settled, do not revive. Recording it stops a later
  stage proposing the same thing again.
- **`reusable`** means right, but not here. It belongs in another piece.
- **`blocked`** means right and wanted, waiting on something: a source, a
  permission, a decision the writer has not made.

**The board reads `reusable`** and marks the piece with how many are waiting, so
a cut idea surfaces as work rather than being lost in a file nobody opens.

Never delete from `cuts.md`. If a reusable cut becomes a piece, change its flag
to `dead` and name the piece it went to.

## Offering options, and recording the pick

Every stage reaches points where there is more than one defensible answer. Those
are the moments the writer should be spending their judgement on, and they are
the moments most easily lost to conversation.

**Options go into the piece, not into the chat.** Any stage may write an options
block to the piece folder, in `options.md`, or inline in the file it is already
producing when the choice belongs there.

```markdown
## Option set: <what is being chosen>        [stage: draft · YYYY-MM-DD]

### A. <short label>
<the full text, ready to use as it stands>
Buys: <one line>
Costs: <one line>

### B. <short label>
...

Chosen: B
Because: <the writer's reason, in their words, one line>
```

Three rules, and they are what make it work rather than ceremony:

1. **Fully written, never described.** "A version that names him" is not an
   option; the paragraph is. A writer can pick between two things they can read
   in seconds. They cannot pick between two summaries without asking questions
   first, and the questions are the cost this is avoiding.
2. **Buys and costs on every option, one line each.** An option set without
   trade-offs is a quiz. With them it is a decision.
3. **Two to four options.** One is a recommendation wearing a costume. Five is
   an abdication.

**`Chosen` never appears without `Because`.** The pick is bookkeeping. The
reason is the evidence: it is a rule the writer already holds, said out loud
once, and `learn decisions` reads exactly these. One line in their words beats
three in yours. If they gave no reason, ask for one before logging it, or write
`Because: not given` rather than inventing it.

Record both in the piece's `SESSION-CONTEXT.md` as well, per
`knowledge/context-log.md`, so a decision survives without the options file
having to be read.

**Options the writer rejected are kept, never deleted.** They are the record of
what was considered, and the next stage should know a thing was looked at and
turned down.

## Posts get an edit pass too

A piece gets `dev-edit` and `line-edit` before it goes out. Posts went without
one, on the assumption that something short is something simple. Short is where
a bad decision is cheapest to make and hardest to see.

The `social` stage includes that pass at gate 2. Two things make it different
from the other edit stages, and both come from the shape of the work rather than
from taste:

**It runs in the conversation, not into a report.** A report exists so a writer
can work through it against the draft, in an editor, at their own pace. For a
five-line post, reading the report costs more than reading the post. Findings
are shown, answered and applied in the terminal, and only the result is written
down.

**When a post has no single viewpoint, it does not get findings.** A post with
two ideas welded together is not a post with nine problems, and handing over
nine problems sends the writer off patching sentences in something that should
not have been assembled. It gets a pick instead: two to four viewpoints the
material already supports, fully written, with an escape. Then at most two
questions, asking for judgement and never for recall, and the post is written
from the answers.

**A post reworked after approval comes back through social.** Including one
already in a scheduler. An amendment is where a post gets built out of parts, so
it is where the viewpoint test earns its keep, and it is the one moment the pass
is easiest to skip because the copy was approved once already.

## Titles are provisional until the argument is

A title written at draft stage was chosen before the piece knew what it was
arguing. Treat it as a label, not a decision.

`draft` writes a working title and sets `title_settled: false`. Until that flag
is true, **no stage may edit the piece to serve its title**. If a section fits
the argument but not the headline, the headline is what is wrong.

`finalise` settles it, after the editing is done. It offers options drawn from
the piece's own strongest lines, and the writer sets `title_settled: true`.

It goes last because a title summarises the whole journey of positioning and
crafting, and that journey is not over until the editing is. Settling it at
dev-edit, which is what 0.7.0 did, was still too early: the piece can move
through a line edit.

The failure this prevents: a good-sounding title generated early becomes an
attractor. Later stages tune towards it, the piece over-commits to a direction
the content was not going, and the drift is invisible because every individual
edit looked like an improvement.

## Opening the file at an edit stage

An edit stage produces a report the writer has to work through by hand, usually
against the draft at the same time. Reading that in a terminal is the wrong
shape for the job.

So at the exit of `dev-edit` and `line-edit`, after saying the report is ready,
**ask whether to open it**. One line, a yes or no, and nothing else in the
question:

> Open the report and the draft? (y/n)

On yes, open the report and the draft together, because the writer works one
against the other. Use whatever the host platform provides: `open` on macOS,
`xdg-open` on Linux, `start` on Windows. On no, drop it and do not ask again in
that session.

Ask only at an edit stage exit. Never mid-report, never at the other stages,
never twice for the same report.

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

## Where knowledge lives

**Every prompt says `knowledge/<file>.md`. That is a name, not a path.**

The `knowledge/` folder in this repo holds the shipped templates, full of
bracketed prompts. Most writers keep their filled-in copies somewhere else: a
vault, a private repo, a synced folder. Resolve the name before reading it.

Order, highest first, first hit wins:

1. `FAMILIAR_KNOWLEDGE`, or `FAMILIAR_CONFIG` which is the older name and still
   works
2. a `knowledge = ` line in a `.familiar` file, next to this repo or in the
   current folder
3. `./knowledge`
4. `~/.familiar/knowledge`
5. this repo's `knowledge/`, which means the templates

`python3 scripts/paths.py` prints what resolves, and whether it landed on the
writer's files or the templates. Run it if you are unsure; it is cheaper than
editing against the wrong house.

**Check rather than assume.** A stage that reads the templates without noticing
falls back to defaults for spelling and house rules, and every correction it
then makes is against rules the writer never set. Nothing errors. The output
looks like a bad edit rather than a missing file, so it gets argued with instead
of investigated.

**Pieces resolve the same way**: `FAMILIAR_PIECES`, then `pieces = ` lines in
`.familiar`, then this repo's `pieces/`. There can be more than one.

## Stating a finding

Every stage that reports back is describing the writer's own work to them, and
the register is neutral. Neutral is harder than it sounds, because the usual
way to make a finding sound substantial is to imply a standard it fell short
of. Four rules, and they apply to every report, every proposal and every
summary Familiar produces.

**Do not measure against a standard nobody set.** "The system does not yet
cover this case" assumes it was meant to. "The audience has not moved" assumes
it should have. "An audit caught it rather than a user" assumes a complaint was
the expected route. In each one the fact is fine and the clause around it is a
verdict on a target the writer never named. Say what is true and what follows
from it. Where a standard genuinely exists, say whose it is.

**A difference is not a deficiency.** One thing not fitting another is a fact
about scope. It is a problem only if somebody needed the fit, so name who
needed it or leave it as the fact. A boundary found is a finding in its own
right: it is the thing that was not known last week.

**Watch the words that smuggle in a schedule.** "Yet", "still", "already" and
"finally" all imply the writer is behind something, and nothing in the material
says they are. "Only" and "even" work the same way on a quantity.

**The opposite of a verdict is not a compliment.** Do not correct for this by
praising instead. `prompts/log.md` bans both directions in the same line, and
for the same reason: the reader made every call being described.

The test, when a sentence feels off: rewrite it as a discovery rather than a
shortfall. If nothing is lost, it was carrying a verdict.

## Rules for agents

- Resolve `knowledge/` before reading it. See "Where knowledge lives" above.
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
- `knowledge/social-rules.md`: the four tests a short post passes before it ships, and what to do instead of a findings list when one fails
- `knowledge/editor-report.md`: dev-edit taxonomy and report spec
- `knowledge/examples/canonical.md`: annotated excerpts of the writer's published work
- `knowledge/reflection.md`: whether reflection is on, its cadence, where the answers live, and the question bank
- `knowledge/social-schedule.md`: channels, cadence, send times, slot shapes; the scaffold the social stage fills, plus the optional `## Scheduler` block publish reads
- `knowledge/links.md`: where posts point and how clicks are tracked; publish builds every URL from it before counting characters
- `knowledge/longform-channels.md`: channels that take a full companion piece; the scaffold the long branch of repurpose fills
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
