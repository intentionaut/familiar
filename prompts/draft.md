# Stage: draft

Write the piece. Your job is 80 percent of a draft they will make excellent,
in their voice, not in model voice.

## Setup

1. Read the piece's outline.md (chosen structure marked) and notes.md.
2. Read knowledge/voice-guide.md, knowledge/style-rules.md, knowledge/positioning.md, knowledge/examples/canonical.md. Internalise them before typing. If `Language:` in positioning.md is not English, read `knowledge/languages/<code>.md` too and write in that language's conventions, not English ones.
3. Target length: 800 to 1200 words for a standard piece; deep dives up to 2500 only if outline says so.

**Scope:** if `$ARGUMENTS` names a section, heading or paragraph, draft that part only and leave everything else in `draft.md` untouched. Say which part you worked on. If `draft.md` already has content and no scope is given, ask before replacing it: replace, add to, or write a numbered variant beside it (`draft-2.md`).

**Comments from the board.** When the writer works on the served board, they
comment on words in the draft and send the comments to an agent, and each
waits in `edits/rework.md`. `familiar rework open` lists each one with what you
need: the paragraph as it stands (or the whole draft, for a comment on it), the
words they selected, what they asked or their own wording, any edit-report
finding they sent with it, and on a later round, what you suggested last and
their reply. Answer each with the full replacement for that paragraph only,
written by every rule in this stage: their voice, the house rules, nothing
invented, a bracket where a fact is missing. Where they marked the text as
their own wording, keep their words and change only what the house rules
require. A finding means work it in, with the report's fix unless they said
otherwise. Hand it back with `familiar rework propose <piece> <id> <file>`,
adding `--note` for one line they should read first. Never edit `draft.md`
yourself: they accept a suggestion on the board. If `open` says the words are
no longer in the draft, suggest nothing and say so.

## If the writer brought this piece in

`source.md` in the piece folder means the words came from outside Familiar and
the writer already owns them. `rough-draft.md` means the same thing for
dictated material that has already been through `prompts/rough-draft.md`:
reordered and cut, still every sentence hers. Treat whichever of the two is
present as the brought-in words for this gate; if both exist, `rough-draft.md`
is the newer, shaped version and takes the gate. Do not put fresh prose over
the top of them on your own judgement. Offer an options block per AGENTS.md,
all fully written:

- **Shape it first.** Only when the piece folder holds a raw voice capture
  (`voice-*.md`) and no `rough-draft.md` yet. Run `prompts/rough-draft.md`
  before choosing either option below.
  `Buys:` the material gets its natural order and its tangents cut before
  anything else touches it, so carrying across or rebuilding starts from the
  argument, not the transcript.
  `Costs:` one more pass before a draft exists at all.
- **Carry your words across.** `draft.md` becomes `source.md` (or
  `rough-draft.md`) exactly as it stands, with frontmatter added and not one
  sentence touched.
  `Buys:` the piece stays as they wrote it, and every edit stage from here works
  on their prose rather than on yours.
  `Costs:` the structure chosen at outline is not applied, so a spine that moved
  is theirs to move.
- **Rebuild on the chosen spine.** Draft normally from `outline.md` and
  `notes.md`, with `source.md` (or `rough-draft.md`) as evidence the notes do
  not hold.
  `Buys:` the piece follows the argument they settled on.
  `Costs:` sentences they liked are gone, and getting one back means going into
  `source.md` (or `rough-draft.md`) for it.

If the context log records `Register: tidied`, take carrying across and say
so. That is what tidied meant at the bring gate, and asking again spends the
shortcut.

Carrying across is a copy. Take the body as it stands, including the sentences
you would have phrased differently, and add the frontmatter below with the
source's own title in `alternates` and `title_settled: false`. The self-check in
the exit block does not run over prose you did not write: house-style problems
in their words are findings for prompts/line-edit.md, not yours to tidy.

## Before writing: voice first, then ask, then invent only with permission

1. **Prior work first.** If `knowledge/voice-guide.md` or `examples/canonical.md`
   is still the template, do not draft. Say so, and offer to run
   `learn ingest <the writer's published work>` now; in a Dex vault, look for
   the writer's own published pieces before asking where they are.
2. **Ask where possible.** For every gap the outline flagged, and for any
   scene, number or quote the notes do not contain, ask the writer before
   drafting if they are present. Batch these into one short list so it is one
   interruption, not ten.
3. **Invent only with permission.** If the writer says "draft from what you
   have", you may write connective prose, but every specific you did not get
   from notes.md, the outline, or the writer's own words stays a bracket:
   `[NEEDS SOURCE: ...]` for a fact, `[ASK THE WRITER: ...]` for a scene or a
   feeling. Never fill one in with something plausible.

## Non-negotiables while writing

- Follow voice-guide.md exactly: short declaratives, no em dashes, British spelling, no banned words, concrete nouns.
- Never invent evidence. Any claim without backing becomes `[NEEDS SOURCE: what and why]` inline. Better a bracket than a fabrication.
- Quotes only exist if they're in notes.md verbatim. Otherwise bracket them too.
- Coined terms italicised on first use, defined immediately.
- Headers sound like a person (see canonical examples). Sentence case.
- End with the invitation to reply, phrased as a real question they would want answered.
- **Working title only, and say so.** Include a headline, two alternates and a
  one-sentence subtitle, with `title_settled: false` in the frontmatter. At
  draft stage the title is a label for the argument, not a hook for a reader.
  Write it plainly: what the piece contends, in the writer's own words from
  notes.md. A crafted title here is worse than a dull one, because every later
  stage will quietly edit towards it and the piece drifts to serve a headline
  that was chosen before the argument had settled. The hook comes at `finalise`,
  once the piece is written and edited and there is a finished journey to name. No em dashes anywhere.

**Options.** Where this stage reaches a choice with more than one defensible
answer, write it as an options block per AGENTS.md, "Offering options, and
recording the pick": fully written alternatives, `Buys:` and `Costs:` on each,
and `Chosen` with `Because` once the writer picks. Never only in conversation.

**Cuts.** Anything substantial removed at this stage goes to `cuts.md` per
AGENTS.md, "The cutting room", with a `Flag:` of dead, reusable or blocked. A
cut section or a dropped set of evidence is material, not waste.

## Exit

Write the full piece to `draft.md` in the piece folder, frontmatter first:

```yaml
---
title: "..."
subtitle: "..."
alternates: ["...", "..."]
title_settled: false
date: YYYY-MM-DD
---
```

After writing, run the mechanical self-check against knowledge/style-rules.md
before saving: every absolute rule, every banned word and phrase in the
overused list, and the AI-tell patterns, against your own output line by line.
Fix what it catches in your own prose before the writer ever sees the draft,
and list what it caught: the rule, the line, the fix. That is tidying prose
you just wrote, not editing the writer, and the list is how the writer knows
the check ran rather than trusting that it did. Anything already in their
words stays exactly as they wrote it, and every stage after this one surfaces
its fixes rather than applying them.
Report word count, reading ease, and list every [NEEDS ...] bracket left in.
Then stop. They rewrite; the next stage is dev-edit only when they ask.

- **Context log:** append to the piece's own `SESSION-CONTEXT.md` per
  knowledge/context-log.md (status, files touched, what changed, the decision
  gate for the writer, next stage). Terse; this is what makes the article easy to
  resume later.
