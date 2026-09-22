# Stage: rough-draft

The pass between a raw voice capture and drafting. Structural only. It
reorders and cuts. It never rewrites a sentence and never adds one.

**Naming convention this stage establishes:** a raw voice-note capture is a
file matching `voice-*.md` in the piece folder (for example `voice-note.md`,
`voice-2026-09-22.md`). Nothing in this repo names that pattern before this
issue; `inspire.md`'s capture is a clipped snippet from someone else's work,
not the writer's own spoken material, and #97 (preserving raw voice notes into
stub slots) is open and unbuilt. This stage does not wait on it: it only reads
a file that already exists. If #97 or #102 later needs a different pattern,
change it here and this is the one place that has to move.

## Setup

1. Read the capture file given in `$ARGUMENTS`. If none is given, take the
   newest raw capture in the piece folder: every file matching `voice-*.md`,
   sorted by file modification time, newest first. If none exist, say so and
   stop; there is nothing for this stage to shape.
2. Read `knowledge/voice-guide.md` and `knowledge/style-rules.md` to know her
   voice, but do NOT apply them yet. They inform `prompts/line-edit.md`,
   later, not this pass. Reading them here is context for what the argument
   sounds like when it lands, not a licence to tidy it now.

## What this pass does

1. Reorder and group the material into the argument's natural order.
2. Cut tangents and circles. Log every cut in `cuts.md`, the cut text and one
   line on why, so any cut is reversible.
3. Surface the actual argument: the spark goes first. If no spark is present,
   say so and stop. Do not invent one.
4. Move her sentences, never rewrite them. No grammar fixes, no synonym
   swaps, no merging or splitting for style. Spoken constructions stay as
   spoken for now.

## What this pass excludes

- All sentence-level work: grammar, tense, de-duplication of phrasing,
  rhythm. Line-edit's job, afterwards, with a light touch.
- New content: nothing invented, no receipts added, no opinions she did not
  say. A missing fact gets a bracket.
- Polish of any kind. The output should still read as her speaking voice,
  ordered.

**Cuts.** Every tangent or circle cut here goes to `cuts.md` per AGENTS.md,
"The cutting room". Use `Flag: reusable`: a cut at this stage is right, but
not in the order the argument now takes, and it may resurface in this piece
or another one. It is not `dead` (this pass never rules on whether the
material is wrong, only on whether it belongs in this argument's order) and
not `blocked` (nothing is waited on). Never delete a cut; if it comes back in
this piece, say so in the piece's own words and change the flag when it lands
somewhere.

## Output

Write `rough-draft.md` in the piece folder: the ordered capture, her
sentences moved into place, plus a one-line note at the top naming the
argument the structure now serves. The cuts log sits beside it. Done when the
argument reads in one pass, every sentence is hers, every cut is logged.

Report which capture file you read, the one-line argument you surfaced, and
how many cuts went to `cuts.md`. Then stop. The writer's next move is
`draft`: with `rough-draft.md` written, the bring gate in `prompts/draft.md`,
"If the writer brought this piece in", treats it the way it treats
`source.md` and offers carrying it across or rebuilding on the chosen spine.

- **Context log:** append to the piece's own `SESSION-CONTEXT.md` per
  knowledge/context-log.md (status, files touched, what changed, the decision
  gate for the writer, next stage). Terse; this is what makes the article easy to
  resume later.
