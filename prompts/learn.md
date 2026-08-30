# Stage: learn

Teach Familiar the writer's voice from real material. Two modes. Both
propose; neither edits a knowledge file without the writer saying yes.

- **Ingest**: read a body of previously published writing in bulk and draft
  the voice files from it. For a new setup, or a refresh.
- **Diff**: compare Familiar's draft of a piece with the version the writer
  actually published, and turn the differences into rules.

## Setup

1. Read AGENTS.md, knowledge/positioning.md, knowledge/voice-guide.md,
   knowledge/style-rules.md, knowledge/examples/canonical.md. Note which are
   still unfilled templates.
2. Read `$ARGUMENTS`:
   - `ingest <path or paths>`: a folder, files, or a text export. Markdown,
     plain text, HTML and common newsletter exports are all fine. If a URL is
     given and you can fetch it, fetch it; if not, ask for a file.
   - `diff <piece folder>`: a piece folder containing `draft.md` and a
     `final.md` (the writer's published version). If `final.md` is missing,
     ask for it; a URL or pasted text is fine, save it as `final.md`.
   - Nothing: ask which mode, in one line.

## Ingest

1. Read everything. For a large corpus (more than about 30 pieces), sample:
   the 10 most recent, 10 spread across the rest, and any the writer names.
   Say what you sampled.
2. Work out, from evidence only:
   - **Register**: who the pieces are written to, how early personal stakes
     appear, direct address, warmth.
   - **Sentence craft**: typical length, punctuation habits (count them:
     dashes per thousand words, semicolons, fragments), rhythm.
   - **Recurring moves**: how pieces open, where they are grounded, how
     sources are handled, whether terms are coined, what headings sound like,
     how pieces end. Quote two examples of each.
   - **Hard noes**: things that never appear. Absence is evidence too.
   - **Themes**: what the publication is actually about, from the titles and
     the arguments, for positioning.md.
   - **Tells that are the writer's**: repetition, fragments, rhetorical
     questions used on purpose, so the line edit leaves them alone.
3. Write `knowledge/proposals/YYYY-MM-DD-ingest.md` containing a proposed
   `voice-guide.md`, a proposed `examples/canonical.md` (real quotes only,
   with their source), and suggested lines for `positioning.md`. Mark every
   claim with the evidence count ("short declaratives: 61% of sentences under
   12 words across 14 pieces"). Never invent a quote. If the corpus does not
   support a section, leave it as the template's bracketed prompt and say so.
4. Show the writer a summary: five things you are confident about, three you
   are not, and anything that contradicted the current voice guide.

### Gate

Stop. Ask the writer which sections to apply. On their answer, copy only
those sections into the knowledge files, replacing the matching section, and
keep the proposal file as the record. Anything not applied stays in the
proposal.

## Diff

1. Read `draft.md` and `final.md` side by side.
2. List every change the writer made, grouped:
   - **Mechanical**: words removed or swapped, punctuation, spelling. If the
     same swap appears twice, it is a rule.
   - **Structural**: paragraphs moved, cut or added; openings and endings
     changed.
   - **Voice**: sentences rewritten to say the same thing differently. Quote
     both versions.
   - **Facts**: claims removed, softened, sourced or corrected. These are the
     most important: a removed claim usually means the draft invented or
     overstated.
3. Turn the recurring changes into proposed rules, each with the quote pair
   as its example, and say which file it belongs in: `voice-guide.md` (how
   to write), `style-rules.md` (what to flag), or `examples/canonical.md`
   (a line from the final worth keeping as reference).
4. Write `knowledge/proposals/YYYY-MM-DD-diff-<slug>.md`.

### Gate

Stop. Show the proposed rules. The writer accepts, rejects or edits each.
Apply only the accepted ones, appending to the right file under a dated
comment so the origin is traceable. Keep the proposal file.

## Rules

- Evidence only. Every rule cites the pair or the count it came from.
- Do not smooth the writer's habits into general advice. If they always open
  with a question, the rule is "open with a question", not "consider a
  strong opening".
- Do not touch `pieces/`. This stage reads there; it never writes there
  except to save a `final.md` the writer supplied.
- If `knowledge/proposals/` does not exist, create it. It is gitignored.

## Exit

One line: what was proposed, what was applied, where the record is.

- **Context log:** append to the project root `SESSION-CONTEXT.md` per
  knowledge/context-log.md.
