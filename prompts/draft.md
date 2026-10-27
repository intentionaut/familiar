# Stage: draft

Write the piece. Your job is 80 percent of a draft they will make excellent,
in their voice, not in model voice.

## Setup

1. Read the piece's outline.md (chosen structure marked) and notes.md.
2. Read knowledge/voice-guide.md, knowledge/style-rules.md, knowledge/positioning.md, knowledge/examples/canonical.md. Internalise them before typing. If an `instance/` directory exists at the repo root, read every `instance/voice-*.md` the same way, except the overlays for other surfaces (`voice-comment.md`, `voice-sending.md`): it is the writer's personal voice layer and wins any conflict with the knowledge templates. `voice-long-form.md`, if present, is this stage's overlay and loads after the rest. If `instance/own-and-flip.md` exists, read it too: `dev-edit` and `social` gate the opening on it. If `Language:` in positioning.md is not English, read `knowledge/languages/<code>.md` too and write in that language's conventions, not English ones.
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

## The writer-first path

Familiar drafts from her outline and notes, and that is the default. She can
also write the first draft herself and have Familiar only edit and challenge.
Offer it once per piece, in one line, unless she has already said which: "I can
draft this from your outline and notes, or you write it and I edit and
challenge." It is an option, never the way in, and she does not need a reason.

If she writes it:

- Do not write a draft. Her sentences are the draft.
- She writes into `draft.md`, or pastes it. Add front matter to the file with
  `drafted_by: writer` and `title_settled: false`, and touch not one sentence of
  the body, the same as when carrying words across.
- Then dev-edit and line-edit, which edit and challenge and never rewrite. The
  self-check in the exit block does not run over prose she wrote.
- Note `Path: writer-first` in the piece's `SESSION-CONTEXT.md`.

`drafted_by: writer` is what tells `scripts/her-share.py` to measure that piece
against the rewrites the edits suggested, not against the draft, so the share it
reports at learn time is true for either path. No path is better by default: the
share, over several pieces, is what says whether one should be.

## If the writer brought this piece in

`source.md` in the piece folder means the words came from outside Familiar and
the writer already owns them. Do not put fresh prose over the top of them on
your own judgement. Offer an options block per AGENTS.md, both fully written:

- **Carry your words across.** `draft.md` becomes `source.md` exactly as it
  stands, with frontmatter added and not one sentence touched.
  `Buys:` the piece stays as they wrote it, and every edit stage from here works
  on their prose rather than on yours.
  `Costs:` the structure chosen at outline is not applied, so a spine that moved
  is theirs to move.
- **Rebuild on the chosen spine.** Draft normally from `outline.md` and
  `notes.md`, with `source.md` as evidence the notes do not hold.
  `Buys:` the piece follows the argument they settled on.
  `Costs:` sentences they liked are gone, and getting one back means going into
  `source.md` for it.

If the context log records `Register: tidied`, take the first and say so. That
is what tidied meant at the bring gate, and asking again spends the shortcut.

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
- **Her sentences go in as she wrote them.** A sentence of hers in notes.md (under
  Working thesis or Spark candidates, or in a block quote) goes into the body
  verbatim wherever it fits, not paraphrased. Build the sentences around it. Where
  it does not fit, leave it out and say so; do not reword it to fit.
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

## Voice proof

Only where the install carries a voice gate: `voice-gate.py`, in the `scripts` folder at the checkout root, beside
`modules/` (called `<voice gate>` below). This module does not ship one. If it is not there, say once in the report
"no voice gate: this draft is unbound, the writer's review is the only check", and change nothing else in this stage. If
it is there, the draft is an artifact, proved before it is written to the piece folder and again after every edit you make
to it. The personal voice layer you already read in Setup is the layer the gate binds.

**Proof.**

1. Write the gate's input for the exact words of the draft: `surface` `post`, `form` `long`, `text` the words, and a
   `receipt` that carries `ref`, the full `head_sha`, `draft_sha256`, the `files` read with their `sha256` and cited
   `sections`, `sources`, and an `artifact` object: `contract` 1, `id` `<piece folder name>:draft`, `version`, `kind`
   `draft`, `stage` `familiar-core:draft`, `output_sha256`, `installed.head_sha`, `private_layer` (each personal layer
   file by `label` and `sha256`), and `parent` from version 2. The sentences of hers you carried in word for word go under
   `provenance` as `owner_verbatim`; nothing else is typed.
2. Run, with the checkout root as `--repo`:

   ```sh
   python3 <voice gate> --repo <checkout root> --input <receipt.json> --private-layer <label>=<path to that layer file> --ledger <piece folder>/voice-ledger.jsonl --record
   ```

   One `--private-layer` per layer file. The ledger is a new sibling file in the piece folder, hashes only, never in the
   repo. `--record` writes a version only when it passed.
3. Read the exit code. **Exit 0** (PASS or ADVISE): hand the draft on. Each ADVISE hit goes under the draft with its rule
   file, line and date, for the writer to keep, cut or rewrite; a hit never blocks. **Exit 1** (a receipt error): the
   draft stops. Say what the gate named, write nothing, and rebuild the receipt or the text. **Exit 2** (no kill list
   found): say "Familiar unavailable", write nothing and make no substitute.
4. Run it first on the composed text, before `draft.md` is written, so a stop leaves no file behind. Run it again at the
   Exit, after the mechanical self-checks, whenever they changed a word: those bytes are the next version of the same
   artifact (version n+1, `parent` the version and `output_sha256` it replaces). The same applies to every later edit of
   yours: reread `draft.md` first, never overwrite the writer's own edits, and never reuse the old receipt for new bytes.
   The gate refuses it, and a revision with no ledger cannot pass.

A pass says these exact words were bound to this revision and these guideline bytes. It is not the writer's approval:
every result still ends `EDITOR REVIEW REQUIRED`, and her review is still the gate to the next stage.

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
Start with `python3 scripts/tell-check.py <the draft>`: it flags the quoted
phrases from style-rules.md, the writer's kill list if one is set, and forced
groups of three, each with its line. It is the mechanical half; the patterns it
cannot match are still yours to sweep. If it says it could not run, say so in
the list rather than reporting the check as clean.
Fix what it catches in your own prose before the writer ever sees the draft,
and list what it caught: the rule, the line, the fix. That is tidying prose
you just wrote, not editing the writer, and the list is how the writer knows
the check ran rather than trusting that it did. Anything already in their
words stays exactly as they wrote it, and every stage after this one surfaces
its fixes rather than applying them.
Then run `python3 scripts/notes-in-body.py <the piece folder>`. It lists the
sentences of hers in notes.md that the draft paraphrased, each beside the draft
sentence that replaced it. Show her the list as it is, with the question it
asks: restore her wording, or let it go. Do not restore or drop anything
yourself, and do not report the check as clean if it says it could not run.

Then run `python3 scripts/experience-flags.py <the piece folder>` over your own
draft. It flags first-person, sensory, anecdote and joke-shaped sentences that
trace to nothing in her notes (or `source.md`, `session.md`): you have no lived
experience, so each one is either hers or invented. For every sentence it flags,
replace it with the `[ASK THE WRITER: ...]` it suggests, worded for what is
missing, or cut it. Never keep one because it reads well. Whether a line lands
stays hers; this only makes sure she is asked. If it says it could not run, say
so in the list rather than reporting the check as clean. Do not run it over
prose she wrote or carried across.

Then run `python3 scripts/unsourced-run.py <the draft>`. It marks runs of three
or more flat claims in one paragraph with no source, quote, hedge or bracket
attached, so the weak paragraph shows next to the strong one. For each run, say
which claim she can back and bracket the rest as `[NEEDS SOURCE: ...]` in your
own prose, or cut it. It cannot tell whether a claim is true; it only shows that
nothing in the text holds it up. Never add a source you have not been given. If
it says it could not run, say so in the list rather than reporting the check as
clean.

Then run `python3 scripts/revival-check.py <the draft> --piece <the piece folder>`.
It compares the draft with this piece's dead cuts, the options the writer chose
against, and the rules they rejected at the learn gate. A flag names the
original kill and its reason: take the revived passage out of your own prose, or
leave it in and tell the writer what changed since the kill, so they can decide.
Kills stay killed until they say the evidence moved. If it says it could not run,
or that rejected rules were not checked, say so in the list rather than reporting
the check as clean.
Then run the voice proof above on the final text if a check changed it, and show any ADVISE hits with the draft.
Report word count, reading ease, and list every [NEEDS ...] bracket left in.
Then stop. They rewrite; the next stage is dev-edit only when they ask.

- **Context log:** append to the piece's own `SESSION-CONTEXT.md` per
  knowledge/context-log.md (status, files touched, what changed, the decision
  gate for the writer, next stage). Terse; this is what makes the article easy to
  resume later.

