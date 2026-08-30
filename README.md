# Familiar

A companion for your craft. Familiar sits beside you while you write about the
work you do, asks the questions that pull out what only you know, and helps
you shape it into something worth sending. It keeps your book of rules so the
writing sounds like you, not like a model.

It is a set of plain markdown prompts. No app, no account, nothing to install
beyond a folder. Works in Claude Code, opencode, or pasted into a claude.ai
Project.

## What it does

Writing about your own work is hard for a specific reason: the good material
is the part you take for granted. Familiar's job is to notice it.

| Stage | Command | What you get |
|-------|---------|--------------|
| 1 | `/familiar-interview <idea>` | One question at a time until the idea is sharp. Ends with a thesis, the stakes, an evidence list and the lines worth building on |
| 2 | `/familiar-outline` | Three genuinely different shapes for the piece. You pick one |
| 3 | `/familiar-draft` | A full draft in your voice, with `[NEEDS SOURCE]` wherever it would otherwise have invented something |
| 4 | `/familiar-dev-edit` | An editor's report: where the spark is, whether the argument holds, what to fix and in what order. Nothing changed for you |
| 5 | `/familiar-line-edit` | The mechanical pass: AI tells, house spelling, reading ease. An exact fix for every flag |
| 6 | `/familiar-social` | A week of posts on your own cadence: one pool of candidates, you pick per channel, exact send times, and nothing scheduled without a final confirm. Works with a scheduler or hands you a paste-ready list |
| 0 | `/familiar-case-study <LOG.md>` | Optional first step. Turns a [Captain's Log](https://github.com/intentionaut/captains-log) build log into a brief and a set of interview questions grounded in what actually happened |

Every stage stops and waits for you. Nothing advances, nothing is applied,
nothing ships until you say so. The friction is the point: the decisions stay
yours, and the writing stays yours.

## Your book

`knowledge/` is where Familiar keeps what it knows about how you write. Five
files, each a template with questions to answer:

- `positioning.md`: what the publication is, who reads it, what it covers.
- `voice-guide.md`: how you write. Register, sentence habits, the moves that make a piece yours, the things you never do.
- `style-rules.md`: the mechanical checklist the line edit runs. Ships with a full list of AI tells; set your house spelling and dash rule at the top.
- `examples/canonical.md`: short excerpts of your own published writing at full strength, with a note on why each works.
- `social-schedule.md`: your channels, cadence, send times and what shape each slot wants. Only needed if you use the social stage; it refuses to guess a cadence.

Fill in `positioning.md` and `voice-guide.md` before the first piece. The others
can grow as you go. The second time you correct the same thing by hand,
write it into `style-rules.md` and it will not come back.

## Use it

```sh
git clone https://github.com/intentionaut/familiar.git ~/Projects/familiar
~/Projects/familiar/scripts/setup.sh
```

The script installs the `/familiar-*` commands for Claude Code and opencode so
they work from any folder. Each piece gets its own folder under `pieces/`.

No terminal? Paste `knowledge/*` and `prompts/*` into a claude.ai Project as
knowledge and run the stages by name.

## How it's built

- `prompts/` is the source of truth. One plain markdown file per stage, no tool-specific syntax.
- `.claude/commands/` holds thin adapters that say "read prompts/X.md and follow it". `scripts/setup.sh` installs them globally.
- `knowledge/` is yours. It is gitignored from nothing, so if you fork this and your voice guide is candid, keep the fork private.
- `pieces/` is where the writing happens. Ignored by git, so the repo stays a tool and your drafts stay with you.

## Where it came from

Familiar started as the private newsroom behind
[Intentionaut](https://intentionaut.com), a letter on design, product, data and
AI. The stages are shaped by how good editors actually work: interview first,
propose structures rather than pick one, report rather than rewrite, and run the
boring mechanical pass last. The one rule that matters most came from watching
models fill gaps with invented detail: a bracket is always better than a
fabrication.

## Status

Free, and a prompt pack rather than a product. Issues and pull requests
welcome, especially additions to the AI-tell list in `style-rules.md`.
