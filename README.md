# Familiar

A companion for your newsletter. Familiar sits beside you while you write
about the work you do, asks the questions that pull out what only you know,
and helps you shape it into an issue worth sending. It keeps your voice rules
so the writing sounds like you, not like a model.

It is plain markdown prompts in a folder you own, so it works in Claude Code,
opencode, or pasted into a claude.ai Project, and it keeps working when any of
those change.

## What it does

Writing about your own work is hard for a specific reason: the good material is
the part you take for granted. You shipped the thing. The reasons were obvious
in June and they are gone by September, and what is left is a repo that tells
you what happened and nothing about why.

Familiar takes you through a series of gates. Each one asks for the part only
you can give, writes your answer down in your words, and then stops. The next
gate works from what the last one got. At the end you have the piece, and the
posts that carry it out into the world, and there is no sentence in either of
them you did not agree to.

The stopping is the whole design. A model left to run from one end to the other
gives you something smooth and slightly wrong, because each step inherits the
last step's small errors and nobody is standing there to catch them. Familiar
puts you in that gap, every time.

You can walk backwards through it. Return to the interview and your notes grow.
Rework one section and the rest is left where it was. A piece sits in its folder
between gates for as long as you need, which some weeks is an hour and other
weeks is a fortnight.

### Where the material comes from

Familiar can sit beside the work itself, before there is a piece.

- **`familiar log`** shows which of your projects keep a build log, and wires
  one up in a command: entries for what shipped, what was decided, what went
  wrong and what it cost, written while you still remember, plus an automatic
  entry when a session ends or compacts. The format is `prompts/log.md`, one
  block you can also just paste into a project's `CLAUDE.md`.
- **`familiar reflect`** asks you two questions about how the work is going and
  records your answers word for word. Opt in and pick a cadence in
  `knowledge/reflection.md`; Familiar offers one at the end of a stage when one
  is due, and drops it the moment you are not in the mood. The answers are the
  rawest voice reference the drafting stages have.

Both feed `case-study`, which turns a log or a session into a brief and
interview questions. The pipeline turns material into an issue; these are where
the material comes from. (They started life as a separate tool, Captain's Log,
whose story is in [`docs/origin.md`](docs/origin.md).)

### See what you have in flight

```sh
scripts/board.py --open
```

A static board, a column per state of the writing, a card per piece with its
title, date, the first thing it says, and the next thing it needs. Click a card
for the whole piece on one page: what it is waiting on, which brackets are
still unresolved, the notes and outline folded away, then the draft.

Pieces in more than one place? Pass `--pieces` once per folder and each card
says where it came from.

Add `--serve` and you can tidy as well as look. Archive moves a piece out of
the way and can be undone; Delete removes the folder. Anything you have already
sent keeps its `final.md` and cannot be deleted from the board, because that
file is the record of a piece that exists in the world and is what the learn
stage reads. The server binds to your own machine, mints a fresh token each
run, and only ever touches pieces it just listed.

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

Familiar starts from things you have actually said and written, and hands back
reports you act on rather than text you have to undo.

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

## Keeping notes out of a public repo

Writing about your own work means keeping notes about it, and those notes end up
next to the code. Familiar ships an optional commit guard that stops the ones
that were never meant to ship from shipping.

```
scripts/install-guard.sh            # this repository
scripts/install-guard.sh --global   # every repository on this machine
```

Opt-in. Nothing installs it for you, and `--uninstall` takes it off.

**It only runs where a commit can leave your machine.** A repository with no
remote is skipped entirely, so a private vault or a scratch folder is never
blocked.

It refuses a commit that stages markdown at the repository root outside the
usual set, an email address, phone number, postcode or private key anywhere, or
words about health, money, sexuality or a dispute outside your published content
folders. It names the file and the line and stops. It never edits anything.

Two committed files tune it: `.mdscope` for extra paths where markdown belongs,
and `.piiallow` for patterns that are known-safe in your repository. A genuine
false positive gets through with `git commit --no-verify`.

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

### Your first hour

Setup ends by telling you what Familiar can see and what it still needs. You can
ask again at any point:

```sh
python3 scripts/doctor.py
```

It reports three states per file, and a missing optional file is fine.

**Familiar needs to know your voice before it drafts anything**, or the draft is
a guess in a stranger's register. Two ways in:

- **You have published before.** `/familiar-learn ingest <folder of your past
  writing>` reads it and drafts your voice files from evidence, with counts
  rather than adjectives. You accept or reject each section. This is the fast
  path and it is much better than writing the files cold.
- **You have not, or you would rather write them.** Open `positioning.md` and
  `voice-guide.md` and answer the bracketed prompts. Short answers are fine, and
  you can start with positioning alone.

Then `/familiar-interview <an idea you have been chewing on>`. It asks one
question at a time, and the first stage usually takes ten or fifteen minutes of
honest answers. There is no way to skip that part, because your answers are the
material: everything downstream is built from what you said.

**What to expect while you work.** Every stage stops and waits. Nothing is
applied to your draft for you, the edit stages hand back a report you work
through yourself, and anything Familiar cannot source is left as a visible
bracket rather than invented. A piece can sit between stages for an hour or a
fortnight; it is a folder of files, so it waits exactly where you left it.

If you keep your voice files somewhere other than the repo, point
`$FAMILIAR_CONFIG` at that folder, or let a host declare it.

The gates, in the order a piece usually meets them. Every one of them can be
run again, and out of order:

```
familiar interview <idea>      find the thesis, one question at a time
familiar outline               three shapes, you pick
familiar draft                 a draft in your voice, brackets over inventions
familiar dev-edit              an editor's report, nothing applied
familiar line-edit             the mechanical pass, an exact fix per flag
familiar repurpose             short: a week of posts. long: seed a companion piece
familiar social                the posts, ending at copy you approved
familiar publish               approved posts into your scheduler
familiar learn ingest <path>   teach it your voice from what you have published
familiar reflect               two questions about how the work is going
familiar case-study <log>      start from a build log or a coding session
familiar board                 what you have in flight, and what each piece needs
```

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

Familiar is what makes [Intentionaut](https://intentionaut.com), a letter on
design, product, data and AI. Every issue goes through it. It is open source
because the problem is not mine alone, and because a tool that shapes how
someone writes should be one they can read. The story of how it came to be, and why it refuses to rewrite, is at
[intentionaut.com/open-source/familiar](https://intentionaut.com/open-source/familiar/). The stages are shaped by how good editors actually work: interview first,
propose structures rather than pick one, report rather than rewrite, and run the
boring mechanical pass last. The one rule that matters most came from watching
models fill gaps with invented detail: a bracket is always better than a
fabrication.

## The letter

Familiar is built in public, and the build stories land first in
[Intentionaut](https://intentionaut.com/subscribe/?utm_source=github-familiar):
what shipped, what went wrong, and what it cost. Roughly fortnightly.

## Status

Free, and a prompt pack rather than a product. Issues and pull requests
welcome: language files, one tell at a time with a real example, and styles
for other kinds of publication. `CONTRIBUTING.md` has the three shapes.
