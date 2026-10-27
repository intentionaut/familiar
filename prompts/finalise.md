# Stage: finalise

The piece is written and edited. This is where it gets its name and its way in.
Three decisions, in order: title and framing, then the subject line, then how it
will be found. They come last on purpose. A title chosen early is a guess; a
title chosen now summarises the whole journey of positioning and crafting.

Runs after `line-edit`, before `repurpose` and `social`. Those stages need a
settled title to point at.

## Setup

1. Read the piece's `draft.md`, `notes.md` and `outline.md`, and the reports in
   `edits/`. Read the whole finished piece before proposing anything.
2. Read knowledge/positioning.md, knowledge/voice-guide.md, knowledge/links.md. If `brief.md` has a `Reader language and intent evidence` section, read the writer's chosen primary buyer/query target, excluded adjacent targets, observed language and receipts. If no choice is recorded, leave target-derived metadata provisional; do not silently choose a target here.
3. If the writer keeps SEO notes of their own, read those and work from them.
   Look first for a filled `## Search` section at the foot of
   `knowledge/themes.md`, and read that section only; nothing else in that
   file is this stage's business. Then look for a file named for search or SEO
   in the knowledge folder, and in a vault, in the publication's own resources. Their practice outranks anything
   generic in this prompt. If there are none, say so once and use section 3.

4. Run `python3 scripts/claim-flags.py <piece folder>`. It reports claim flags a
   research tool left in the piece folder as `flags.md`: `none`, `ok` or
   `refused`. On `ok` with anything open, show the writer its list before
   section 1, as it printed it: the claims still to keep or drop, and the kept
   ones that still need a source in the piece. Then carry on. Open flags never
   stop this stage; whether a claim stands is the writer's call. On `refused`,
   say the reason in one line and carry on; never open `flags.md` yourself to
   read part of it, and never edit it.

**Scope:** if `$ARGUMENTS` names one of the three jobs ("finalise the title",
"just the SEO"), do that one and leave the rest. Say which you did.

## 1. Title and framing

The last creative act, not an afterthought.

- Read the finished piece and say in one sentence what it actually argues. Not
  what the outline said it would argue. Pieces move.
- **Propose three titles, drawn from the piece's own strongest lines**, never
  invented from outside it. Quote where each comes from.
- Each carries `Buys:` and `Costs:`, one line each. Open rate, memorability,
  precision and how it reads forwarded to someone else are the axes that matter.
- Name the framing the title implies, and check it against what the piece does.
  A title that flatters the ending over the argument is the common failure. Say
  so when you see it.
- Propose a subtitle in one sentence, and two alternates for the title.

**The trap to name out loud:** the working title from the draft has had the
whole editing pass to become familiar. Familiar is not the same as right. Treat
it as one candidate among the three, with no advantage.

On the writer's pick, set `title_settled: true` in the frontmatter and record
`Chosen` and `Because` in the context log.

## 2. The subject line

A separate decision, and it is not the title.

A title labels the argument for someone who is already reading. A subject line
earns the open from someone who is not. The same words rarely do both.

Propose two, one descriptive and one curiosity-led, each with what it costs.
Say plainly that this is a guess until there is open-rate evidence, and note in
the context log which kind was chosen, so a pattern can be seen across issues.

**Preview text.** For each subject line, propose the line an inbox shows after
it: about 90 characters, saying what the reader gets. It carries on from the
subject line and never repeats it. Write it under its subject line as
`Preview: <text>`.

## 3. How it will be found

Only for pieces that get a web version. Skip it for email-only, and say you did.

Work from the writer's own SEO notes when they exist. If the optional intent check has a chosen target, use it as the starting point for the meta title, description and slug, checking each against the finished article and the actual reader words. Explain how the proposed metadata answers that buyer question, what it does not promise, and which adjacent query it deliberately leaves out. Do not invent new targets at finalise. If no intent check ran, carry on with the finished article and the writer's own SEO notes; do not block this stage. When there are no notes:

- **Slug.** Short, readable, stable. It is a permanent address, so it outlives
  the title and must not be regenerated later.
- **Meta title and description.** A title and one-sentence description written for a person deciding whether to click, not stuffed. Keep the description around 150 characters; if the writer selected a buyer/query target, use its observed language only where it fits the article, not as a keyword pasted in. Check the on-page title and platform title template before proposing a separate meta title. A meta title is a proposal until the writer picks it.
- **Headings.** The finished piece already has them. Check they read as a
  sensible outline on their own, because that is how a search engine and a
  skimming reader both use them.
- **Internal links.** Two or three to the writer's own related pieces, in the
  body where they are genuinely useful. Name the pieces you mean.
- **One target.** The single thing a person might plausibly search that this
  piece deserves to answer. If there is not one, say so rather than inventing
  it. Most good essays do not have one and are not worse for it.

**Never trade the writing for the ranking.** If a recommendation would change a
sentence the writer chose, it is a proposal for them to reject, not a fix.

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
"no voice gate: these options are unbound, the writer's review is the only check", and change nothing else in this stage. If it is there, every title, subtitle, subject line, preview text and
meta title or description you propose is its own artifact, proved before the writer sees it.

**Personal voice layer (read, only when the gate is there).** Read every `instance/voice-*.md` at the checkout root, as
`draft.md` does. It wins any conflict with the knowledge templates. Before this section, this stage did not read it.

**Proof (per option).**

1. Write the gate's input for the exact words of the option: `surface` `post`, `form` `long`, `text` the words, and a
   `receipt` that carries `ref`, the full `head_sha`, `draft_sha256`, the `files` read with their `sha256` and cited
   `sections`, `sources`, and an `artifact` object: `contract` 1, `id` `<piece folder name>:<kind>:<option number>`,
   `version`, `kind` (`title`, `subtitle`, `subject` or `metadata`), `stage` `familiar-core:finalise`, `output_sha256`,
   `installed.head_sha`, `private_layer` (each personal layer file by `label` and `sha256`), and `parent` from version 2.
   Spans the writer supplied word for word go under `provenance` as `owner_verbatim`; nothing else is typed.
2. Run, with the checkout root as `--repo`:

   ```sh
   python3 <voice gate> --repo <checkout root> --input <receipt.json> --private-layer <label>=<path to that layer file> --ledger <piece folder>/voice-ledger.jsonl --record
   ```

   One `--private-layer` per layer file. The ledger is a new sibling file in the piece folder, hashes only, never in the
   repo. `--record` writes a version only when it passed.
3. Show an option only when the gate passed or advised (exit 0). On FAIL (exit 1) or UNKNOWN (exit 2) the option is not
   shown; regenerate it or leave it out. ADVISE hits go under the option for the writer to keep, cut or rewrite.
4. Any change to an option's words after it was bound (the writer's correction, your own rewrite) is the next version of
   the same artifact: version n+1, `parent` the version and `output_sha256` it replaces, then run the gate again. Do not
   reuse the old receipt for new bytes; the gate refuses it, and a revision with no ledger cannot pass. Reread
   `draft.md` before any rewrite and never overwrite the writer's own edits.

A pass says these exact words were bound to this revision and these guideline bytes. It is not the writer's approval:
every result still ends `EDITOR REVIEW REQUIRED`, and the writer's pick is still the gate to `draft.md`.

## Exit

Write the decisions into `draft.md` frontmatter (`title`, `subtitle`,
`alternates`, `title_settled: true`, `slug`, `description`, and a `meta_title` only when the platform supports and the writer picks a separate value) and everything
proposed but not taken into the piece as an options block.

Report in one line what is settled and what is still open.

Then stop. `repurpose` and `social` are next, only when the writer asks.

- **Context log:** append to the piece's own `SESSION-CONTEXT.md` per
  knowledge/context-log.md, including `Chosen` and `Because` for the title.
