# The four records

**Status: proposal, 25 September 2026.** Approved in principle on #160; the shape below is not yet approved. Nothing is built.

Nine open issues each propose somewhere to keep something. Read together they describe **eleven records for four things**. This names the four, so that each issue writes into one instead of inventing its own.

This document defines shape and rules. It does not choose a storage engine, and it does not describe a migration.

## Why this comes first

| Concept | Records proposing to hold it |
| --- | --- |
| A source, and where it came from | `inspirations/*.md` (shipped), #98's source ledger, #51's snapshot provenance, #97's voice-note record, #150's registry |
| The writer judged something | the `Disposition:` line in line-edit reports (shipped), #118's receipts, #138's golden pairs, #141's detect-only receipts, #153's labelled edits, #159's routing corrections |

Two are already on disk in different formats. Nine are proposed. Every one of them was a reasonable local decision; together they are a data model nobody designed.

The cost of waiting is not neutral. Each issue that ships its own store adds a migration to this work, and the writer's material moves into a shape that then has to be moved again.

## A correction to #160

#160 said two records. Working through the actual field lists, it is **four**. The run record and the claim record are genuinely neither of the other two, and forcing them in would produce a record with optional halves — which is how you get eleven again, one layer down.

Four nouns:

- **Source** — a thing we know about, and where it came from
- **Claim** — something the writing asserts, and what backs it
- **Run** — what a machine did
- **Judgement** — what the writer decided

## 1. Source

One record per thing Familiar knows about, whatever kind it is.

**Core, on every source:**

| Field | Notes |
| --- | --- |
| `id` | stable, assigned once, never reused |
| `kind` | `clip` · `page` · `transcript` · `document` · `conversation` |
| `title` | as observed, not as tidied |
| `pointer` | canonical URL, page id, or path |
| `hash` | of the captured bytes |
| `captured_at` | when the material was made or said; may be unknown |
| `ingested_at` | when Familiar first saw it |
| `origin_piece` | **which piece first brought it in. Write-once.** Null for house-level material |
| `origin_how` | `writer-supplied` · `researched` · `swept` · `clipped` |
| `verification` | `supplied` · `read` · `needs-access` · `superseded` (#98's states) |
| `superseded_by` | id of a newer version. **A source is never overwritten** |

**Kind-specific, hanging off the core:**

- `clip` — `why_it_stuck` (the field `inspire` already writes)
- `page` — `revision` (ETag or last-edited), `last_checked`, `fetch_state`: `unchanged` · `drifted` · `blocked` · `gone` · `unknown` (#152)
- `transcript` — `raw`, immutable; excerpt spans (#97)

**Spans.** Any source may carry exact spans — a quote, an excerpt, a cited passage — each with its offsets into the captured bytes. #98's source spans, #97's excerpt spans and #151's quotes are the same structure, and a span is what #151 fingerprints and #152 checks for survival.

**`used_in` is derived, never maintained.** It is a query over claims and judgements. A hand-maintained list of uses is a list that goes wrong.

**Rules.**
- Origin is written once and never edited. An origin that can change is not an origin.
- A changed source creates a new version; the previous one and its links survive (#51, #97).
- `blocked` is never reported as `drifted`, and `unknown` is never reported as empty (#152, and the house rule `queue-check` already follows).

## 2. Claim

One record per thing the writing asserts. This is #98's claim record, unchanged in substance.

| Field | Notes |
| --- | --- |
| `id` | stable |
| `text` | the exact claim as written |
| `piece` + `span` | where it sits |
| `provenance_class` | `writer-said` · `source-supplied` · `researched` (#98) |
| `evidence_state` | `needs-receipt` · `supported` · `contested` · `inference` (#98) |
| `sources[]` | supporting and challenging, each a source id plus span |

**Rules.**
- A claim links to many sources; a source supports many claims. Neither duplicates the other.
- `writer-said` keeps a pointer to her own material and is **never converted to researched prose** (#98).
- Adding a source never promotes a claim to `supported`. Only a judgement does.
- Per-paragraph evidence (#155) is a query: the claims in that paragraph, with their states and the checks that ran.

## 3. Run

One record per machine action. High-volume, automatic, and the only one of the four a human never writes by hand.

Field names follow **OpenTelemetry's GenAI semantic conventions**, because they already standardise exactly this and cost nothing to adopt. Use the names; skip the infrastructure.

| Field | OTel name |
| --- | --- |
| run id | — |
| grouping | `gen_ai.workflow.name` |
| agent name and version | `gen_ai.agent.name`, `gen_ai.agent.version` |
| started, ended | — |
| model asked for | `gen_ai.request.model` |
| model that answered | `gen_ai.response.model` |
| parameters | `gen_ai.request.*` |
| tokens | `gen_ai.usage.input_tokens`, `.output_tokens` |
| source commit | — |
| status or error | `error.type` |

**Checks that ran** are the event `gen_ai.evaluation.result`: `gen_ai.evaluation.name` (required), `score.label`, `explanation`.

The spec's own note is the rule this project already wanted: *"a score value of 1 could mean 'relevant' in one evaluation system and 'not relevant' in another."* **A number is meaningless without the named check that produced it.** Score is a foreign key to a check, never a bare float.

**Rules.**
- The model asked for and the model that answered are different fields, because they differ.
- A check that could not run is recorded as such. It is not a pass and not a fail (#149).
- No composite score (#154). If a number is wanted it is a count: *three checks flagged*.

## 4. Judgement

One record per decision the writer made. Low-volume, deliberate, and **the asset**.

| Field | Notes |
| --- | --- |
| `id` | |
| `at` | |
| `subject_kind` | `question` · `flag` · `gap` · `quote` · `source` · `rule` · `routing` · `claim` |
| `subject_ref` | what was judged |
| `quoted` | the exact text it is about |
| `proposed` | what the machine suggested, where there was a proposal |
| `verdict` | `accepted` · `rejected` · `revised` · `kept-on-purpose` · `pending` |
| `rejection_reason` | `wrong` · `not-applicable-here`. Only when `rejected` |
| `why` | **her words, verbatim** |
| `provisional` | true while a machine proposal awaits her confirmation |
| `proposed_by` | `machine` or `writer` — the provenance stamp |
| `expires_at` | decay for unreviewed provisional items |
| `run` | the run that produced the finding, where there was one |

**The split rejection reason is the most valuable field here.** Borrowed from Adobe's violation API, which distinguishes `incorrectAssessment` from `notApplicable`. *The check was wrong* and *the check doesn't apply here* mean opposite things: the first says fix the rule, the second says narrow its scope. Collapsing them into one "rejected" throws away the only signal that says which.

**Rules.**
- **Blank is not rejected.** A subject with no judgement is *unreached* and is counted as nothing. Line-edit already states this: a rejected flag is evidence the rule is wrong; a blank one says nothing. Silence must never be read as approval.
- **Append-only.** A correction supersedes; it never rewrites. A changed mind is itself evidence.
- **Verbatim.** A paraphrase of her reason is worth nothing to `learn` (AGENTS.md).
- **Nothing is a rule until she confirms it.** A machine proposal is `provisional` with `proposed_by: machine`, and stays that way until she rules. Confirmed patterns graduate to the rule registry (#114); rejected ones go to `rejected-rules.md`, which `learn` already reads before proposing.
- **Show the evidence, not an argument.** Explanations raise acceptance regardless of correctness (Bansal et al., CHI 2021), so a provisional item shows what produced it and nothing more. No confidence score.

## What each issue writes into

| Issue | Record |
| --- | --- |
| `inspire` (shipped) | Source, kind `clip` |
| #51 Notion snapshots | Source, kind `page` |
| #97 voice notes | Source, kind `transcript`, plus spans |
| #150 registry | **is** the Source record, plus origin and derived `used_in` |
| #98 | Source (its ledger half) + **Claim** (its claim half) |
| #152 source revisits | Source `fetch_state`, `last_checked`, `revision` |
| #151 quote ledger | Spans on Source + Judgement, `subject_kind: quote` |
| #118 receipts | **Run** (machine half) + Judgement (human half) |
| #141 detect-only receipts | Run findings + Judgement dispositions |
| #138 golden set | **a query** over Judgements where verdict is `revised`. Not a corpus |
| #153 labelled edits | Judgement, `subject_kind: flag` |
| #159 routing corrections | Judgement, `subject_kind: routing` |
| #158 emerging patterns | Judgement, `provisional: true`, `proposed_by: machine` |
| #149 readiness queue | **a query** over Judgements and Claims. Not a store |
| #155 per-paragraph evidence | **a query** over Claims and Runs. Not a store |

**Five of the fifteen turn out to be queries rather than stores.** That is the finding: much of what looked like new infrastructure is a view over two tables.

## Boundaries

- **The records hold the writer's material and never enter the public repo.** The repo carries the schema, the checks and synthetic fixtures. `public-check` and `never-publish` refuse a fixture that looks like real material.
- **Enforced, not documented.** A duplicate id, a mutated origin or a rewritten judgement is *refused*, not discouraged. A limit nothing enforces is worse than none, because it buys the confidence without the guarantee.
- **Nothing depends on a remote read succeeding.** An unreachable store is never reported as an empty one.

## Open questions for the writer

1. **Storage.** One store for all four, or files for sources (greppable, diffable, survive the tool) and a database for the rest? The rules above hold either way.
2. **`expires_at`.** Wikidata expires unreviewed items at six months. For a voice pattern that has not recurred, a month is probably closer.
3. **Backfill.** `inspirations/` has real clips in it and the board carries 31 hand-made `Needs her` judgements. Migrate both into the records, or start the records fresh and leave those as history?
