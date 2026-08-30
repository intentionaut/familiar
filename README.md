# Familiar

A companion for your newsletter. Familiar sits beside you while you write
about the work you do, asks the questions that pull out what only you know,
and helps you shape it into an issue worth sending. It keeps your voice rules
so the writing sounds like you, not like a model.

It is a set of plain markdown prompts. No app, no account, nothing to install
beyond a folder. Works in Claude Code, opencode, or pasted into a claude.ai
Project.

## What it does

Writing a newsletter about your own work is hard for a specific reason: the
good material is the part you take for granted. Familiar's job is to notice
it, issue after issue.

| Stage | Command | What you get |
|-------|---------|--------------|
| 1 | `/familiar-interview <idea>` | One question at a time until the idea is sharp. Ends with a thesis, the stakes, an evidence list and the lines worth building on |
| 2 | `/familiar-outline` | Three genuinely different shapes for the piece. You pick one |
| 3 | `/familiar-draft` | A full draft in your voice, with `[NEEDS SOURCE]` wherever it would otherwise have invented something |
| 4 | `/familiar-dev-edit` | An editor's report: where the spark is, whether the argument holds, what to fix and in what order. Nothing changed for you |
| 5 | `/familiar-line-edit` | The mechanical pass: AI tells, house spelling, reading ease. An exact fix for every flag |
| 6 | `/familiar-social` | A week of posts on your own cadence: one pool of candidates, you pick per channel, exact send times, and nothing scheduled without a final confirm. Works with a scheduler or hands you a paste-ready list |
| 7 | `/familiar-learn ingest <path>` / `learn diff <piece>` | Teach it your voice. Ingest reads your past issues in bulk and drafts the voice files from evidence; diff compares Familiar's draft with what you actually published and turns your edits into rules. Both propose; you accept per section |
| 0 (optional) | `/familiar-case-study <LOG.md>` | Optional first step. Turns a [Captain's Log](https://github.com/intentionaut/captains-log) build log, or a Claude Code session transcript (`session` for the latest one), into a brief and a set of interview questions grounded in what actually happened |

### See what you have in flight

```sh
scripts/board.py --open
```

A static board, a column per state of the writing, a card per piece with its
title, date, the first thing it says, and the next thing it needs. Click a card
for the whole piece on one page: what it is waiting on, which brackets are
still unresolved, the notes and outline folded away, then the draft.

Pieces in more than one place? Pass `--pieces` once per folder and each card
says where it came from. It is plain HTML on your own machine, it reads your
piece folders, and it changes nothing.

Every stage stops and waits for you. Nothing advances, nothing is applied,
nothing ships until you say so. The gates stop drift, and they let you move
in both directions: run an earlier stage again and it adds to what is there,
or scope any stage to one section (`/familiar-dev-edit the opening`) and the
rest of the file is left alone. The work is always exactly where you left it.

Command names here are the cloned form (`/familiar-interview`). Installed as
the skill, the same stages are `familiar interview`, `familiar outline`, and so
on, without the `/familiar-` prefix.

## Your voice

`knowledge/` is where Familiar keeps what it knows about how you write. Five
files, each a template with questions to answer:

- `positioning.md`: what the publication is, who reads it, what it covers.
- `voice-guide.md`: how you write. Register, sentence habits, the moves that make a piece yours, the things you never do.
- `style-rules.md`: the mechanical checklist the line edit runs. Ships with a full list of AI tells; set your house spelling and dash rule at the top.
- `examples/canonical.md`: short excerpts of your own published writing at full strength, with a note on why each works.
- `social-schedule.md`: your channels, cadence, send times and what shape each slot wants. Only needed if you use the social stage; it refuses to guess a cadence.

Fill in `positioning.md` and `voice-guide.md` before the first issue. The others
can grow as you go. The second time you correct the same thing by hand,
write it into `style-rules.md` and it will not come back.

## How Familiar is different

Most writing skills do one of two things: generate text from a description of
your voice, or clean AI text after the fact. Familiar does neither.

**It works from human material.** The interview is you answering questions,
one at a time, in your own words. The voice files are built from your
published writing, not from adjectives about it. The learn stage reads what
you actually changed between Familiar's draft and the issue you sent, and
turns that into rules. Every rule cites the sentence it came from. The result
is a draft that starts from what you said, not from what a model guesses
someone like you would say.

**It reports; it never rewrites.** The dev edit and the line edit hand you a
report: the quote, the problem, the exact fix. You accept, reject or change
each one. Nothing is applied for you and no file is written over. This is
slower than a clean-up pass, and that is the point. Rewrite tools have two
failure modes people keep reporting: they flag your deliberate choices as
tells, and they drop claims while "only" changing shape. A ranking, a
superlative, a hedge that was actually a considered position, gone. When the
change is a proposal you can see, both failures cost you a glance instead of
a paragraph.

**The tell list is kept honest.** `style-rules.md` carries a full list of AI
writing patterns. Once a week a check compares it with
[humanizer](https://github.com/blader/humanizer), the most actively curated
list of these, and opens an issue with anything new. Additions land one at a
time with a real example, never as a bulk import; a bloated list means false
positives for every writer using it. Humanizer is the right tool when you have
AI text and want it cleaned. Familiar is for when the text starts with you.

## Languages

The mechanical rules were written for English, and some of them are about
English: dashes, spelling, heading case, hyphenated pairs, quotation marks.
Set `Language:` in `positioning.md` and the stages read
`knowledge/languages/<code>.md`, which says which rules to skip or replace
and adds that language's own overused words and tells. The language-agnostic
patterns (padding, hedging, fake candour, announced evidence) still apply.

There is a template and no language files yet. Pull requests from fluent
writers are the way this gets built: see `CONTRIBUTING.md`.

## Use it

```sh
mkdir -p ~/Projects
git clone https://github.com/intentionaut/familiar.git ~/Projects/familiar
~/Projects/familiar/scripts/setup.sh
```

`~/Projects/` is just a suggestion. Any working directory is fine: clone
anywhere, then run `scripts/setup.sh` from there. It derives the folder it
lives in and installs from it.

The script installs the `/familiar-*` commands for Claude Code and opencode so
they work from any folder. Each piece gets its own folder under `pieces/`;
`pieces/README.md` shows the layout the stages write into.

Or install it as a skill:

```sh
npx skills add intentionaut/familiar
```

That gives you one `familiar` skill that takes the stage as its first word
(`familiar interview <idea>`, `familiar learn ingest ~/writing`). It looks for
the Familiar folder at `$FAMILIAR_HOME`, `./familiar/`, or
`~/Projects/familiar` for the prompts and your voice files.

No terminal? Paste `knowledge/*` and `prompts/*` into a claude.ai Project as
knowledge and run the stages by name.

### Inside Dex

If you run [Dex](https://heydex.ai), Familiar installs as a callable skill:

```sh
dex/install.sh ~/path/to/your/vault
```

That gives you `/familiar-custom interview <idea>`, `/familiar-custom draft`, and the rest,
with the vault doing what a vault is for: pieces live in
`04-Projects/Writing/`, people and companies named in a piece link to their
pages, "needs finding" evidence is searched for in your notes before you are
asked, and an open decision at a gate can become a task if you want one. Dex names
custom skills by their folder, and the `-custom` suffix is what keeps it safe
across Dex updates, so the command carries it.

## How it's built

- `prompts/` is the source of truth. One plain markdown file per stage, no tool-specific syntax.
- `.claude/commands/` holds thin adapters that say "read prompts/X.md and follow it". `scripts/setup.sh` installs them globally.
- `knowledge/` is yours. The templates ship tracked in the repo; only
  `knowledge/proposals/` and `knowledge/private/` are ignored. If your voice
  guide ever gets candid, keep the fork private.
- `pieces/` is where the writing happens. Ignored by git, so the repo stays a tool and your drafts stay with you.

## Where it came from

Familiar started as the private newsroom behind
[Intentionaut](https://intentionaut.com), a letter on design, product, data and
AI. The story of how it came to be, and why it refuses to rewrite, is at
[intentionaut.com/open-source/familiar](https://intentionaut.com/open-source/familiar/). The stages are shaped by how good editors actually work: interview first,
propose structures rather than pick one, report rather than rewrite, and run the
boring mechanical pass last. The one rule that matters most came from watching
models fill gaps with invented detail: a bracket is always better than a
fabrication.

## Status

Free, and a prompt pack rather than a product. Issues and pull requests
welcome: language files, one tell at a time with a real example, and styles
for other kinds of publication. `CONTRIBUTING.md` has the three shapes.
