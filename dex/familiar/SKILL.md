---
name: familiar
description: "Write and edit a newsletter issue about your own work with Familiar: interview yourself one question at a time, get three structures, a draft in your voice with brackets over anything unsourced, then editor's reports you work through yourself, a week of social posts on your cadence, and a learn stage that turns your edits into voice rules. Use when the user says 'familiar', 'familiar-custom', 'interview me about', 'draft my newsletter', 'dev edit this piece', 'line edit', 'turn this issue into posts', or 'learn my voice'. Not for a product requirements doc or feature spec; use `product-brief`. Not for a decision record; use `decision-log`. Not for reflecting on how the week felt; use `weekly-reflection`."
---

## Execution mode

Run inline in the current conversation by default, so this work can see what the
user has already discussed, decided, or settled this session. Do not fork merely
because this skill was selected. Only run in the background when the user
explicitly asks for a background run or the host has already obtained a specific
background-work approval for this run.

## What this does

Familiar is a gated editorial pipeline for writing about your own work. Seven
stages, each a plain markdown prompt, each ending at a decision the writer
makes. Inside Dex it also uses what the vault already knows: people and
companies mentioned in a piece link to their pages, open decisions at a gate
can become tasks, and the learn stage can read the writer's published work
from the vault.

The quality bar: nothing is invented, nothing is rewritten in place, nothing
advances without the writer. The anti-pattern: running two stages in one turn
because the next step "seems obvious". It never is; stop at the gate.

## Where Familiar lives

The prompts and the writer's voice files are in the Familiar folder:
`{{FAMILIAR_HOME}}`. If that folder is missing, say so and give the writer the
one line to fix it, then stop:

```
git clone https://github.com/intentionaut/familiar.git {{FAMILIAR_HOME}}
```

The writer's data lives in the vault, so it is searchable, backed up and
never in a public repo:

- **Voice files:** `06-Resources/Familiar/knowledge/` (positioning, voice
  guide, style rules, canonical examples, social schedule, languages). The
  installer seeds it with the templates. Wherever a prompt says `knowledge/`,
  read from and write to this folder, never the Familiar repo's own.
- **Pieces:** `04-Projects/Writing/YYYY-MM-DD-slug/`. Wherever a prompt says
  `pieces/`, use this. Create it on first use.
- **Proposals from `learn`:** `06-Resources/Familiar/proposals/`.

## Stages

The first word of `$ARGUMENTS` picks the stage. If it is missing, ask which,
in one line, with this list:

| Stage | Prompt to follow | Ends at |
|---|---|---|
| `interview <idea>` | `prompts/interview.md` | "Does the thesis sound like what you mean?" |
| `outline` | `prompts/outline.md` | the writer picks a structure |
| `draft` | `prompts/draft.md` | the writer rewrites; asks before dev-edit |
| `dev-edit` | `prompts/dev-edit.md` | a report; the writer accepts or rejects each item |
| `line-edit` | `prompts/line-edit.md` | findings with exact fixes; nothing applied |
| `social` | `prompts/social.md` | two gates, then an explicit "confirm" before anything is scheduled |
| `learn ingest <path>` / `learn diff <piece>` | `prompts/learn.md` | proposals the writer applies per section |
| `case-study <LOG.md \| transcript.jsonl \| session [dir]>` | `prompts/case-study.md` | hands off to `interview` |
| `board` | `scripts/board.py` (a command, no gate) | a page the writer opens |

For every stage:

1. Read `{{FAMILIAR_HOME}}/AGENTS.md`, then the stage's prompt, then every
   knowledge file the prompt lists. Paths in the prompts are relative to the
   Familiar folder, except `pieces/`, which is the vault folder above.
2. Any stage may be re-run on the same piece and adds to what is there. If
   the remaining arguments name a section, heading or paragraph, work on
   that part only. Never overwrite a file that has content without asking:
   replace, add to, or write a numbered variant beside it.
3. Stop where the prompt says to stop. Say in one line what the open
   decision is. Do not start the next stage.

## Commands

`board` is a command, not a stage, so it has no gate:

```
python3 {{FAMILIAR_HOME}}/scripts/board.py --pieces <vault>/04-Projects/Writing --open
```

It writes a static board of every piece, a column per state of the writing,
and a page per piece holding what that piece needs next, the unresolved
brackets and the draft. It reads and changes nothing.

Pass `--pieces` again for any other folder of pieces the writer keeps, so the
board covers everything in flight rather than the vault alone. Offer it when
the writer asks what they have on, or when they come back to a piece that has
been sitting.

`--serve` adds Archive and Delete to each card, for the writer to use. A piece
that has been sent cannot be deleted there. Never archive or delete on their
behalf.

## What Dex adds

- **People and companies.** When notes or a draft name a person or company,
  use `lookup_person` (Work MCP) and the company index, and link the page in
  the piece's `notes.md` under a `## Mentioned` heading. Do not create pages
  from a draft; a draft is not evidence that a relationship exists.
- **Evidence from the vault.** When the interview logs an evidence item as
  "needs finding", search the vault for it before asking the writer (QMD
  `query` if available, otherwise grep across `00-Inbox`, `04-Projects`,
  `05-Areas`). Offer what you found; the writer decides if it counts.
- **Open decisions as tasks.** When a stage ends at a gate and the writer
  says they will come back to it, offer once to create a task with
  `create_task` (pillar inferred per CLAUDE.md, confirm before creating).
  Never create a task without the offer being accepted.
- **Learn from the vault.** `learn ingest` accepts a vault path such as
  `06-Resources/Published/` or a `05-Areas/` folder of past writing.
- **Context log.** Familiar's `SESSION-CONTEXT.md` lives in the piece folder,
  which is Familiar's rule everywhere, and it means Familiar never writes a
  session file to the vault root where Dex keeps its own.

## Honesty rules

- If the voice files in `06-Resources/Familiar/knowledge/` are still the
  unfilled template, say so before drafting and offer `learn ingest` on the
  writer's published work in the vault as the fastest way to fill them. Do
  not draft in a guessed voice.
- If a scheduler call in the social stage fails, report exactly which posts
  landed and which did not. Never retry silently.
- If the Work MCP or QMD is unavailable, say the vault could not be searched
  and continue with what the writer gives you. Missing tools are never an
  empty result.

## Done looks like

Read the file the stage wrote back from disk before saying anything. Then one
line naming the stage that ran, the file it wrote (vault path), and the
decision the writer now owns. If the file is not there or is empty, say that
instead; a stage that wrote nothing did not run.
