# Familiar

Turns the coding session the writer just finished into a newsletter issue they
actually wrote. It interviews them one question at a time, drafts in their
voice from what they have already published, and hands back an editor's report
instead of a rewrite. Nothing is invented: what cannot be sourced becomes a
visible bracket.

Tool-agnostic. Runs from Claude Code, opencode, Codex or Gemini CLI, installs
as a plugin or a skill, and the `knowledge/` and `prompts/` markdown can be
pasted into a claude.ai Project.

## This repository is public

Anyone can read every branch, commit message, pull request title and
description here, and deleting them afterwards takes GitHub support. So the
test for anything you push is whether a stranger could read it and learn
nothing about the writer who uses this copy of Familiar.

**What may open here:** changes to the tool that would serve any writer.
Prompts, scripts, tests, docs, and blank templates under `knowledge/`.

**What never opens here, in a file, a commit message or a PR:**

- Anything the writer declared: their stubs, themes, positioning, voice,
  audience, banned phrases, reference voices, or any other filled-in value.
- Their words: drafts, approved copy, quotes from a conversation, the
  angles they picked.
- Names they would not publish: people they read or work with, employers,
  clients, unannounced products, the publications they compare themselves to.
- Anything in `pieces/`, `knowledge/private/` or `knowledge/proposals/`.

**Where it goes instead:** the writer's house. Run `python3
scripts/paths.py`; when it says "yours", write there. When you cannot reach
the house (a session with only GitHub access, say), do not write it anywhere:
give it to the writer in the conversation and say where it belongs.

**A fix to the tool that a writer's material prompted** is written in general
terms. "Tell the story" as an AI tell is fine; "banned by <writer> on
<date>" is not. The PR describes the change, never the conversation.

`scripts/public-check.py` refuses what it can catch, on every pull request
and in the tests: a file under `knowledge/` that `knowledge/TEMPLATES` does not
list, a template with a dated or attributed `source: declared`, and a private
term from the writer's list in any added line, commit message, title or
description. It is a backstop, not permission: a change it passes can still
be wrong for this repo. A `public-ok` label skips the terms check, and only a
person adds it.

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
/harvest    → knowledge/patterns.md     (cross-project pattern extraction: themes, growth signals, ready topics by audience segment)
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

## Answering the open gates

Every stage stops and asks something. Over a fortnight that becomes a pile of
questions in separate folders, and a question nobody can find is a piece that
does not move. `scripts/decisions.py` reads the decision gate out of every
piece's context log and prints them as one list.

```
familiar decisions                      every question waiting on you
familiar decisions answer <piece> "..." record an answer against that piece
```

When the writer asks what is waiting, or picks the list up on a low day, work
it as a batch:

- **One question at a time**, in the order the list gives, and their answer
  goes down in their words. This is the interview's rule and it is the same
  reason: `learn decisions` reads these for the reasoning, and a paraphrase is
  worth nothing to it.
- **Recording is not advancing.** An answered gate does not start the next
  stage. Say what the piece is now waiting for and stop.
- **A pass is an answer.** "Not today" is recorded as skipped, and the gate
  stays open rather than being asked again in the same sitting.
- **Never answer one for them**, however obvious it looks. The gate exists
  because a stage found something only the writer can settle.

## Asking the writer

Every question costs the writer an answer, and a question the files could have
answered costs them patience too. Every stage that asks anything (interview,
case study, bring, reflect, a decision gate, a question asked while waiting on
a build) runs each question through five tests before asking it.

1. **Look it up first.** Read what the piece and the project already hold: the
   brief, `interview-questions.md`, `spine.md`, `notes.md`, the context log,
   the session digest and the build log. If they answer it, do not ask. Show
   the fact with its file instead. Ask the writer to confirm it only when the
   evidence is thin: one source, an inference, or anything a wrong answer would
   carry into print.
2. **One ask per question.** No "and why", no second question mark, no list.
   Three things needed is three turns.
3. **Judgement now, not memory then.** Ask what the writer thinks today about
   what happened, not what they remember doing. A past moment is asked for only
   when no file holds it, and then with the closest evidence beside it: "The
   log has the rollback at 14:10 and nothing before it. What made you roll
   back?"
4. **Say what a complete answer looks like.** By default a pick: two to four
   options written out in full, drawn from the files and the conversation, each
   with what it buys and what it costs where there is a trade-off, and always
   "or something else". One letter is a complete answer. Where a pick cannot
   work, name the shape: yes or no, a number, one sentence.
5. **The writer's words, not the system's.** No theme ids, stage names, file
   names or internal labels in the question, and no verdict built into it.

**At most three questions in one sitting.** After the third, stop, say what the
answers settled, and offer to carry on. A decision gate in the context log
carries one question, never a list; the next one waits its turn.

**A question that fails gets rewritten, not softened.** `scripts/question-check.py`
flags the mechanical failures (a compound question, a memory prompt, a vague
opener, an internal id, no answer shape) in prepared question files and decision
gates. Run it on anything you wrote before the writer sees it.

**Record the answer word for word.** An answer is evidence, and a paraphrase of
it is worth nothing to `learn`.

## Offering a voice review

The decisions and diffs pile up. The review is the moment they become rules, and
it will not happen unless Familiar notices it is due.

When a stage finishes and `knowledge/voice-review.md` says a review is due on
its cadence, offer one in a single line and stop:

> Six decisions since the last review. Run one? (y/n)

At a stage exit only, never during the work. Once per session. If they say no,
or say nothing about it, drop it and do not raise it again in that session.
Never offer when voice review is off.

**A loop nobody has opened is different from one that is off**, and the rule
above used to cover both. Where the settings are still the template and
decisions have been accumulating, say so **once, ever**, at a stage exit, in
one line naming what it would do and the file that turns it on:

> Eleven decisions recorded and no voice review set up yet. `voice-review.md`
> turns it on. (This is the only time I will mention it.)

Then never again, in that session or any other, unless the writer asks. Not
nagging is right; never introducing means a writer can only find a loop by
reading a file they have no reason to open. The same applies to any other
setting-gated loop that has never been switched on: one introduction, at a
moment it would have paid, and then silence.

A review is `learn decisions`, so it has a gate like any other and it proposes
rather than applies.

## Teaching it in the moment

Corrections arrive in conversation more often than they arrive in edits.
"Never use that word." "That sentence sounds like a model." The diff catches
what the writer changed in a file; it cannot catch what they said between
files, and a correction that lives only in the chat is one the next draft
will earn again.

So the moment the writer bans something, propose the rule right then:

- **The trigger is theirs.** They say "never use X", "that is not me", "stop
  writing Y", or they correct the same phrasing a second time. One correction
  is a preference; the second time is a rule they are already keeping by hand.
- **The proposal is quoted and dated.** The exact words they banned, the line
  that earned the ban, the date. A rule that cannot point at the moment it
  came from is a guess.
- **The gate is the same as learn's.** Propose the addition to
  `knowledge/style-rules.md`, or to Hard noes in `knowledge/voice-guide.md`,
  in the writer's house and never this repo's templates, and apply it only
  when they say yes. A rejected proposal goes to
  `knowledge/rejected-rules.md` with their one-line reason, so it is never
  proposed again.
- **In the moment, not in a batch.** Do not save it for the next review. The
  review aggregates decisions and diffs; a spoken correction is already
  settled, and the only question is whether it gets written down before it
  is forgotten.

Where the rule belongs: `style-rules.md` for what to flag mechanically,
`voice-guide.md` for how to write. When unsure, `style-rules.md`: a rule
that flags is seen at every line edit, a rule that advises is read once.

## Offering a reflection

Reflection is something Familiar does with the writer, so notice when one is due
rather than waiting to be asked.

When a stage finishes and `knowledge/reflection.md` says a reflection is due on
its cadence, offer one in a single line and stop. At a stage exit only, never
during the work. Once per session. If they say no, or say nothing about it, drop
it and do not raise it again in that session. Never offer when reflection is
off.

**When the settings are still the template, introduce it once, ever**, the way
voice review is introduced: at a stage exit, in one line naming what it does and
the file that turns it on, then never again in that session or any other unless
the writer asks. The CLI does the same the first time it does real work, and
records that it has. A loop nobody has opened is different from one that is
off, and a writer should not have to open a file they have no reason to open
to learn the loop exists.

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

**Options go into the piece, not into the chat.** The block goes inline in the
file the stage is already producing, which is where most of them belong: an
edit report, `social.md`, a draft. `options.md` is for a choice that is not
tied to one file, and it is the exception rather than the default.

Whichever home it takes, `learn decisions` reads the `Chosen:` and `Because:`
lines, so it looks in both and a block is never left somewhere neither can
find.

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

`--serve` also makes each piece's page a document to write in. Every paragraph
is typed into where it sits and shows its markdown while the cursor is in it,
so nothing is converted on the way back to the file, and the draft saves
itself a moment after typing stops. The writer selects words to comment on
them, or comments on the whole draft; comments wait in `edits/rework.md` until
they send them to an agent, and the agent's suggestion comes back beside the
paragraph, where they accept it, edit it and accept that, reply, or reject it.
`scripts/board_edit.py` holds the rules each write follows:

- **Only the writer changes `draft.md` from the board**, by typing or by
  accepting a suggestion. A version of what is replaced is kept in
  `.versions/` inside the piece folder: at most every ten minutes while typing,
  every time for a suggestion. A save made against a version of the file that
  has changed since (an edit in Obsidian, a stage running) is refused, never
  merged. A sent piece's draft is never written, because `learn diff` reads it.
- **An agent answers comments and never edits `draft.md`.** `familiar rework
  open` lists what has been sent with everything needed to answer it, and
  `familiar rework propose <piece> <id> <file>` hands a suggestion back. While
  the writer is on the board, run `familiar rework watch` in the background,
  answer what it reports, and start it again. Stop when the writer says so.
- **A suggestion is written the way the draft stage writes**, per
  `prompts/draft.md`, "Comments from the board": the replacement for that
  paragraph only (or the whole draft, for a comment on it), in the writer's
  voice, house rules applied, nothing invented.
- **Nothing in `edits/rework.md` is removed.** A comment only gains rounds, and
  a later round's text is the writer's reply to the last suggestion.
- **Picks and answers go where they always did**: `Chosen` and `Because` under
  the option set, and the answer in the context log in the writer's words.

The board shows each edit-report finding beside the paragraph it quotes, so
edit reports number every finding in a heading of its own, quote the words it
is about, and never reuse a number. Never use any of these controls on the
writer's behalf.

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

**A repo opts itself out of the automatic loops with `engage = off` in its own
`.familiar` file.** Check-in and first engagement default to on wherever the
skill is installed, per `knowledge/checkin.md`; this line is how a project that
should never hear from Familiar unprompted (client work, a codebase that is
not the writer's to narrate) says so. It silences the session-start offer in
that repo only. A `familiar` the writer types there by hand still runs: the
line takes a project out of the ambient loop, it does not disable the tool.

**Check rather than assume.** A stage that reads the templates without noticing
falls back to defaults for spelling and house rules, and every correction it
then makes is against rules the writer never set. Nothing errors. The output
looks like a bad edit rather than a missing file, so it gets argued with instead
of investigated.

**Pieces resolve slightly differently, and the difference is deliberate.**
Knowledge is one folder, so the first hit wins. Pieces can be several, so
`FAMILIAR_PIECES` and the `pieces = ` lines in `.familiar` are **added
together**, in that order, falling back to this repo's `pieces/` when neither
says anything. A writer with the environment variable set in their shell and a
second folder in their config gets both, which is the point: dropping one of
them would take a piece off the board with nothing to say why.

## The one thing Familiar refuses

Every other check reports. The writer accepts it, rejects it, or revises it, and
nothing is applied without them. `knowledge/never-publish.md` is the exception.

It holds strings that must never appear in anything sent out: a client under an
agreement, a salary, an unannounced product, a metric nobody cleared. `publish`
and `social` run `scripts/never-publish.py` before their gate. A match on the
block list stops the run.

The line, and it matters: **Familiar never refuses to write something. It can
refuse to send it.** Drafting is private and reversible; publishing is not. No
drafting or editing stage reads this list, and none of them should.

When it blocks:

- Say which strings matched. Do not edit them out and carry on.
- Do not offer to remove them. The writer put them on that list; what to do
  about a match is theirs.
- Do not suggest turning the check off to get past it.

The list is literal-string matching and nothing more. It cannot spot a
paraphrase. Never describe it to a writer as making a draft safe to publish:
it is the last catch for a mistake they already knew they could make.

An empty or absent list is off. Say nothing about it.

## Declared before inferred

A writer's themes, their audience and what they are trying to be known for are
theirs to state. A stage that works them out from the writing produces something
plausible, unfalsifiable and slightly wrong, and the writer has no obvious place
to correct it because nobody ever asked them.

**The ladder, and stages take it in order.**

1. **Declared.** Read what the writer wrote down. This is the default and it is
   where every field should end up.
2. **Asked.** Where a field is empty and the work needs it, ask. One question,
   in the stage that needs the answer, recorded in their words.
3. **Inferred.** Only where the writer has said they cannot name it. An
   inference is a suggestion, it is labelled as one, it carries the evidence it
   was drawn from, and it stays labelled until they confirm it.

**Never silently infer, and never fill a gap with a sensible default.** A
default is how one writer's shape becomes everyone's, which is the failure
`prompts/harvest.md` already names about the writer's shape. The same failure is
available wherever a stage wants a theme, an audience, an intersection or a
target query and does not have one.

**Make the provenance a field, not a habit.** Every declared knowledge value
carries how it got there:

- `source: declared` - the writer said it.
- `source: inferred (unconfirmed)` - a stage suggested it; the evidence sits
  beside it and it is offered back for confirmation.
- `source: unknown` - nobody has said, and no stage may proceed as though
  somebody had.

A stage reports its unknowns rather than resolving them. `doctor` counts fields
still sitting at `inferred (unconfirmed)`, because an unconfirmed guess that
nobody revisits becomes a fact by sitting still.

**Enough writing lowers the cost of the suggestion, never the bar for asking.**
A large archive makes an inference better. It does not make it wanted.

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
- Write a writer's material only to their house, never to this public repo.
  See "This repository is public" above.
- Read the stage's prompt file and every knowledge file it lists before acting.
- Before asking the writer anything, apply "Asking the writer" above.
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
- **Board sync:** when `knowledge/board-provider.md` in the writer's house names
  a provider, run `familiar board sync <piece>` after the context log entry. It
  prints one line. A failure is reported in that line and never blocks the stage
  or repeats. With no provider set it does nothing, so a stage never needs to
  check first.

## File map

- `knowledge/positioning.md`: what the publication is, house rules, audience, themes
- `knowledge/updates.md`: whether doctor may check for a newer Familiar; off in the template, one check a day, never updates anything
- `knowledge/themes.md`: what you are trying to be known for; the declared spine harvest maps evidence onto, with a stable id and a source per value
- `knowledge/voice-guide.md`: how the writer writes, with patterns
- `knowledge/style-rules.md`: mechanical checklist for line edits
- `knowledge/social-rules.md`: the four tests a short post passes before it ships, and what to do instead of a findings list when one fails
- `knowledge/editor-report.md`: dev-edit taxonomy and report spec
- `knowledge/examples/canonical.md`: annotated excerpts of the writer's published work
- `knowledge/checkin.md`: whether the session-start check-in is on and its cadence; the offer that notices a project has gone quiet
- `knowledge/reflection.md`: whether reflection is on, its cadence, where the answers live, and the question bank
- `knowledge/social-schedule.md`: channels, cadence, send times, slot shapes; the scaffold the social stage fills, plus the optional `## Scheduler` block publish reads
- `knowledge/links.md`: where posts point and how clicks are tracked; publish builds every URL from it before counting characters
- `knowledge/longform-channels.md`: channels that take a full companion piece; the scaffold the long branch of repurpose fills
- `knowledge/languages/<code>.md`: per-language rule overrides and tells; `_template.md` to add one
- `knowledge/humanizer-check.md`: weekly diff against humanizer's tell list; candidates, never applied
- `knowledge/metrics.md`: the line-edit numbers kept, one line per piece; how learn sees a rule that has gone quiet
- `knowledge/rejected-rules.md`: the index of rules the writer turned down, kept in their house; learn reads it before proposing
- `knowledge/TEMPLATES`: every file this repo may ship under `knowledge/`; public-check refuses any other
- `scripts/build_log_entry.py`: the automatic log entry: where it goes, what survives, and one entry per session
- `scripts/question-check.py`: flags questions that break "Asking the writer"; run on prepared questions and decision gates
- `scripts/public-check.py`: refuses a writer's own material in this public repo; runs on every pull request
- `knowledge/models.md`: per-stage model recommendations and fallback rule
- `knowledge/board-provider.md`: which provider supplies the board's state; unset means the built-in board
- `scripts/board_sync.py`: `familiar board`, `familiar board sync <piece>` and `familiar next`, reading and writing through the provider; a sync never blocks a stage, and `next` names and starts nothing
- `scripts/notion_board.py`: the Notion provider behind that boundary; board fields only, never a delete or an archive
- `scripts/board_provider.py`: the provider boundary `board` and `next` read through; the built-in board is the default provider
- `knowledge/board.md`: optional; the board's colours, fonts (installed or from Google Fonts), text size, and whether it stays light in dark mode
- `knowledge/context-log.md`: the resume log format
- `knowledge/never-publish.md`: strings that must never be sent; the block and warn lists publish and social check before their gate
- `scripts/never-publish.py`: the check itself; exit 1 blocks, 0 is clean or warnings only
- `prompts/*.md`: source of truth for each stage
- `.claude/commands/`: thin adapters calling the prompts; `scripts/setup.sh`
  installs them globally as `familiar-*`
- `skills/familiar/SKILL.md`: the single-skill entry point for `npx skills add`;
  routes on the first argument word to the same prompts

## Maintenance

When a real piece teaches you something about the voice, update
`voice-guide.md` and prune or add to `examples/canonical.md` in the writer's
house. The second time the writer makes the same edit by hand, encode it as a
rule in the house's `style-rules.md`. This repo's copies stay blank templates.
