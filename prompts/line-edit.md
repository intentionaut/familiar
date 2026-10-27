# Stage: line-edit (mechanical pass)

The pattern screen. Run this after the developmental edit is resolved and the
draft is stable. This is a top-edit pass:
mechanical, exhaustive, boring on purpose.

## Setup

1. Read the piece's draft.md (newest `pieces/*/` if not given).
2. Read knowledge/style-rules.md and knowledge/voice-guide.md. If an `instance/` directory exists at the repo root, read every `instance/voice-*.md` as well, except the overlays for other surfaces (`voice-comment.md`, `voice-sending.md`), then `voice-long-form.md`, this stage's overlay, if present: the personal voice layer, which wins on conflict with the templates. Check `Language:`
   in knowledge/positioning.md; if not English, read `knowledge/languages/<code>.md`
   and apply its skip/keep/replace table before anything marked (en).

**Scope:** if `$ARGUMENTS` names a section, heading or paragraph, work on that part only and leave everything else in the file untouched. Say which part you worked on. If the target file already has content and no scope is given, ask before replacing it: replace, add to, or write a numbered variant beside it.

## Method

Run `python3 scripts/tell-check.py <the draft>` first. Each line it prints is a
candidate finding: weigh it like any other (a word on the list can be the
writer's own, a term of art or doing real work), and write up the ones that
stand in the format below. A flag you leave out gets one line in the summary
saying why. If it says kills were not checked, or that it could not run, say
that in the report; it is not a clean result.

Then sweep the entire draft against every rule in knowledge/style-rules.md:

- Em dashes (absolute)
- American spellings
- Banned/hype vocabulary
- Every AI-tell pattern listed there
- Unsourced quotes, statistics, factual claims
- Reading ease and grade level (report the numbers)

For each finding output exactly this, numbered in order. Never reuse a number
in a later look at the same draft: the board finds findings by these headings
and shows each beside the paragraph it quotes.

```
### <n>. <the issue, in a few words>

[line N] "<quoted text>"
Issue: <rule or pattern, with its number from style-rules.md>
Why it matters: <one sentence>
Fix: <exact rewritten line in the writer's voice>
```

For hedged positions where they could take a firmer stance, use this instead:

```
### <n>. <the hedge, in a few words>

[line N] "<quoted text>"
Issue: hedge → could be a firm position
Why it matters: <one sentence on what a firmer stance changes>
Tradeoff: <the two (or more) defensible positions and what each costs>
Question to the writer: <ask them to choose a side>
```

Do not quietly firm up a hedge for them. Surface the tradeoff and let them decide the stance.

## Rules

- Every flag gets a concrete rewritten line. Vague notes are useless.
- Do not touch anything outside the checklist: structure and argument belong to dev-edit.
- Weigh each tell by its strength in style-rules.md. Patterns 1 to 5 are flagged on one
  sighting; a pattern marked *weak alone* is flagged only when other tells share the
  passage, and the flag names them.
- If a fragment or staccato list is doing deliberate work in their voice, leave it and note that you left it.
- False positives are worse than missed flags. When unsure whether something is an AI tell or their dry wit, flag it as UNCERTAIN with your reasoning.
- A firm stance is not stridency. It is a position with a reason they can defend. When a hedge hides a real choice with tradeoffs, ask them which way they want to lean.

**Options.** Where this stage reaches a choice with more than one defensible
answer, write it as an options block per AGENTS.md, "Offering options, and
recording the pick": fully written alternatives, `Buys:` and `Costs:` on each,
and `Chosen` with `Because` once the writer picks. Never only in conversation.

**Cuts.** Anything substantial removed at this stage goes to `cuts.md` per
AGENTS.md, "The cutting room", with a `Flag:` of dead, reusable or blocked. A
cut section or a dropped set of evidence is material, not waste.

**Framing people and products fairly.** Run the check in
knowledge/style-rules.md, "Framing people and products fairly": a named
person or company talked down, the writer's own earlier work, or a product
the piece describes. Flag with the exact rewrite, as with any other finding.

## Voice proof

Only where the install carries a voice gate: `voice-gate.py`, in the `scripts` folder at the checkout root, beside
`modules/` (called `<voice gate>` below). This module does not ship one. If it is not there, say once in the summary
"no voice gate: these rewrites are unbound, the writer's review is the only check", and change nothing else in this
stage. If it is there, every `Fix:` line you write is its own artifact, proved before the report is written and again
whenever you reword it. The personal voice layer you already read in Setup is the layer the gate binds.

**Proof (per Fix).**

1. Write the gate's input for the exact words of the `Fix:` line: `surface` `post`, `form` `long`, `text` the words, and a
   `receipt` that carries `ref`, the full `head_sha`, `draft_sha256`, the `files` read with their `sha256` and cited
   `sections`, `sources`, and an `artifact` object: `contract` 1, `id` `<piece folder name>:line:<finding number>`,
   `version`, `kind` `line`, `stage` `familiar-core:line-edit`, `output_sha256`, `installed.head_sha`, `private_layer`
   (each personal layer file by `label` and `sha256`), and `parent` from version 2. Words that are the writer's own,
   carried unchanged from the draft, go under `provenance` as `owner_verbatim`; nothing else is typed.
2. Run, with the checkout root as `--repo`:

   ```sh
   python3 <voice gate> --repo <checkout root> --input <receipt.json> --private-layer <label>=<path to that layer file> --ledger <piece folder>/voice-ledger.jsonl --record
   ```

   One `--private-layer` per layer file. The ledger is a new sibling file in the piece folder, hashes only, never in the
   repo. `--record` writes a version only when it passed.
3. Read the exit code. **Exit 0** (PASS or ADVISE): the Fix goes in the report. Each ADVISE hit goes under the Fix with its
   rule file, line and date, for the writer to keep, cut or rewrite; a hit never blocks. **Exit 1** (a receipt error): the
   Fix is not shown. Say what the gate named, then rebuild the receipt or reword the Fix. **Exit 2** (no kill list found):
   say "Familiar unavailable", write no report and make no substitute.
4. Any later change to a Fix's words (a rewrite after the critique check, a correction, your own second look) is the next
   version of the same artifact: version n+1, `parent` the version and `output_sha256` it replaces, then run the gate
   again. Do not reuse the old receipt for new bytes; the gate refuses it, and a revision with no ledger cannot pass. A
   hedge finding has no Fix line and is not proved.

A pass says these exact words were bound to this revision and these guideline bytes. It is not the writer's approval:
every result still ends `EDITOR REVIEW REQUIRED`, and nothing is applied until she accepts it.

## Exit

Run the voice proof above over every `Fix:` line, then write to `edits/line-edit-report.md`: findings, then the summary table from the
spec (flags per category, reading ease, grade level, top three highest-impact fixes).
They apply what they agree with. Nothing is auto-applied.

Then run `python3 scripts/edge-diff.py edits/line-edit-report.md`. It compares
each quoted line with its `Fix:` and flags what the polish costs: a contraction
expanded, an idiom lost, short sentences joined, a length moved. Under each
finding it flags, add one line, `Edge cost: <rule>, <detail>`, so she sees the
cost beside the suggestion before she decides. Do not drop or soften a Fix
because it was flagged; the cost is hers to weigh. If it says it could not run,
or that a suggestion had no rewritten line, say so in the summary; that is not
a clean result.

Then run `python3 scripts/critique-lint.py edits/line-edit-report.md`. It flags
praise or agreement that quotes no line (a compliment opener, a finding that
only says it is fine) and any finding that quotes none of the draft's words.
Fix what it flags in your own report before she sees it: quote the line, or cut
the praise. Do not invent a fault to fill a gap; a firm "this works", said once
and quoting the line, stays. If it says it could not run, say so in the summary.

Then run `python3 scripts/revival-check.py edits/line-edit-report.md --piece <the piece
folder>`. It flags a Fix that brings back a dead cut, an option the writer chose
against, or a rule they rejected. Under each finding it flags, add one line,
`Revival: <the original kill and its reason>`, and leave the Fix as it is: she
decides whether the evidence changed. If it says it could not run, or that
rejected rules were not checked, say so in the summary.

Every finding in the report carries a `Disposition:` line, left for the writer
to fill as they work through it: `accepted`, `rejected` or `revised`, and a
rejection earns one line of why in their words. The report lives in the piece
folder, so the record survives the session, and `learn decisions` reads
exactly these lines. A rejected flag is evidence the rule is wrong for them;
a flag that stays blank is one they never reached, which says nothing.

Then append one line to the log in `knowledge/metrics.md`: the date, the
piece, the word count, flags per 1000 words by category, reading ease, grade
level, and the per-rule tally. Those numbers are already computed for the
summary table; the log is what stops them being thrown away. It is the answer
to "is it learning my voice", and it is how `learn` sees a rule that has gone
quiet.

Then ask whether to open the report and the draft, one line, yes or no. See
AGENTS.md, "Opening the file at an edit stage". Open both on yes; drop it on no.

- **Context log:** append to the piece's own `SESSION-CONTEXT.md` per
  knowledge/context-log.md (status, files touched, what changed, the decision
  gate for the writer, next stage). Terse; this is what makes the article easy to
  resume later.

