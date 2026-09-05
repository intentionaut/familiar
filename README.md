# Familiar

Familiar turns the coding session you just finished into a newsletter issue you
actually wrote.

It reads the transcript, interviews you one question at a time, drafts in your
voice from your own published pieces, and hands back an editor's report instead
of a rewrite. Nothing is invented: anything it cannot source becomes a visible
bracket for you to fill.

Plain markdown prompts, MIT, nothing leaves your machine.

```sh
npx skills add intentionaut/familiar
```

## Your first issue, in about thirty minutes

The hard part of writing about your own work is that the good material is the
part you stopped noticing. You shipped the thing. The reasons were obvious in
June and they are gone by September, and what is left is a repo that tells you
what happened and nothing about why.

So Familiar does not start from a blank prompt. It starts from the work.

1. **Point it at the session you just closed.** Ask your agent to
   `case-study session`, or hand it a build log. It reads the transcript,
   writes a brief, and drafts the questions worth asking you. Transcripts are
   Claude Code's today; on opencode, Codex or Gemini CLI, the build log is the
   way in, and `familiar log entry` scaffolds one.
2. **Answer them.** One question at a time, ten or fifteen minutes, in your own
   words. This is the part nothing else can do for you: everything downstream is
   built from what you said.
3. **Get a draft with its working showing.** In your voice, with a `[NEEDS
   SOURCE]` bracket everywhere a model would have guessed a number, and an
   `[ASK THE WRITER]` bracket everywhere it would have invented a quote.

You need one file filled in before that draft: `knowledge/positioning.md`, which
says what the publication is and who reads it. The voice files can wait until
you care how the prose sounds. Run `familiar status` at any point and it will
tell you what it can see and what it still needs.

## Why it refuses to rewrite

Every stage stops and waits for you. Nothing advances, nothing is applied,
nothing ships until you say so.

The stopping is the design, not a limitation of it. A model left to run from one
end to the other gives you something smooth and slightly wrong, because each
step inherits the last step's small errors and nobody is standing there to catch
them. Familiar puts you in that gap, every time.

Three refusals follow from it.

**It reports; it never rewrites.** The dev edit and the line edit hand you a
report: the quote, the problem, the exact fix. You accept, reject or change each
one. Nothing is applied for you and no file is written over. This is slower than
a clean-up pass, and that is the point. Rewrite tools have two failure modes
people keep reporting: they flag your deliberate choices as tells, and they drop
claims while "only" changing shape. A ranking, a superlative, a hedge that was
actually a considered position, gone. When the change is a proposal you can see,
both failures cost you a glance instead of a paragraph.

**It brackets rather than invents.** A bracket is always better than a
fabrication. That rule came from watching models fill gaps with plausible
detail, and it is the one that matters most.

**It works from things you actually said.** The interview is you answering
questions. The voice files are built from your published writing, not from
adjectives about it. `learn diff` reads what you changed between Familiar's
draft and the issue you sent, and turns that into rules, each one citing the
sentence it came from.

You can walk backwards through all of it. Return to the interview and your notes
grow. Rework one section and the rest is left where it was. A piece sits in its
folder between gates for as long as you need, which some weeks is an hour and
other weeks is a fortnight.

**Already have AI text you want cleaned up?** Use
[humanizer](https://github.com/blader/humanizer). That is the right tool for
that job. Familiar is for when the text starts with you.

## The gates

Everything after the three commands below is a conversation. Tell the agent what
you have, a draft, notes, an idea, a session, and it picks the right stage.
Stage names are things you say, not commands you type.

```
bring <path>        start from a draft or notes you already have
case-study <log>    start from a build log or a coding session
interview <idea>    find the thesis, one question at a time
outline             three shapes, you pick
draft               a draft in your voice, brackets over inventions
dev-edit            an editor's report, nothing applied
line-edit           the mechanical pass, an exact fix per flag
finalise            title, subject line, SEO, once the argument has settled
repurpose           short: a week of posts. long: seed a companion piece
social              the posts, ending at copy you approved
publish             approved posts into your scheduler
learn ingest <path> teach it your voice from what you have published
                    (a folder, a platform export, or a URL)
reflect             two questions about how the work is going
board               what you have in flight, and what each piece needs
```

Each piece lives in its own folder under `pieces/`. Every stage can be run
again, out of order, and scoped to one section: "dev-edit the opening" works.

Three commands exist, because there are three ways a writing session starts:

- `/familiar-new-piece <slug>` when you are beginning something
- `/familiar-board` when you are picking something back up
- `/familiar-harvest` when you are looking for what to write about

## Your voice

`knowledge/` is where Familiar keeps what it knows about how you write. Five
files, each a template with questions to answer:

- `positioning.md`: what the publication is, who reads it, what it covers. Fill
  this one first.
- `voice-guide.md`: how you write. Register, sentence habits, the moves that
  make a piece yours, the things you never do.
- `style-rules.md`: the mechanical checklist the line edit runs. Ships with a
  full list of AI tells; set your house spelling and dash rule at the top.
- `examples/canonical.md`: short excerpts of your own published writing at full
  strength, with a note on why each works.
- `social-schedule.md`: your channels, cadence, send times and what shape each
  slot wants. Only needed if you use the social stage; it refuses to guess a
  cadence.

Two ways to fill them:

- **You have published before.** Ask your agent to `learn ingest <your past
  writing>`. It reads it and drafts your voice files from evidence, with counts
  rather than adjectives. You accept or reject each section. This is the fast
  path and it is much better than writing the files cold.

  A folder of files works, and so does a platform export: **if your archive
  lives in Substack, beehiiv or Ghost, export it, unzip it, and point at the
  folder.** Markdown, plain text and HTML are all readable, so an export needs
  no conversion. A single piece can be a URL instead. There is no way to walk a
  whole publication from its address, which is why the export is the way in.
- **You have not, or you would rather write them.** Answer the bracketed prompts.
  Short answers are fine.

The second time you correct the same thing by hand, write it into
`style-rules.md` and it will not come back.

**The tell list is kept honest.** Once a week a check compares `style-rules.md`
with [humanizer](https://github.com/blader/humanizer), the most actively curated
list of these, and opens an issue with anything new. Additions land one at a
time with a real example, never as a bulk import, because a bloated list means
false positives for every writer using it.

## See what you have in flight

```sh
scripts/board.py --open
```

A static board, a column per state of the writing, a card per piece with its
title, date, the first thing it says, and the next thing it needs. Click a card
for the whole piece on one page: what it is waiting on, which brackets are still
unresolved, the notes and outline folded away, then the draft.

Pieces in more than one place? Pass `--pieces` once per folder and each card says
where it came from.

Add `--serve` and you can tidy as well as look. Archive moves a piece out of the
way and can be undone; Delete removes the folder. Anything you have already sent
keeps its `final.md` and cannot be deleted from the board, because that file is
the record of a piece that exists in the world and is what the learn stage reads.
The server binds to your own machine, mints a fresh token each run, and only ever
touches pieces it just listed.

## Where the material comes from

Familiar can sit beside the work itself, before there is a piece.

- **`familiar log`** shows which of your projects keep a build log, and wires one
  up in a command: entries for what shipped, what was decided, what went wrong
  and what it cost, written while you still remember, plus an automatic entry
  when a session ends or compacts. The format is `prompts/log.md`, one block you
  can also paste into a project's `CLAUDE.md`.
- **`familiar reflect`** asks you two questions about how the work is going and
  records your answers word for word. Opt in and pick a cadence in
  `knowledge/reflection.md`. The answers are the rawest voice reference the
  drafting stages have.

Both feed `case-study`. The pipeline turns material into an issue; these are
where the material comes from. (They started life as a separate tool, Captain's
Log, whose story is in [`docs/origin.md`](docs/origin.md).)

## Install

The skill at the top of this page is the shortest way in. In Claude Code you can
also install it as a plugin, which brings the commands with it:

```
/plugin marketplace add intentionaut/familiar
/plugin install familiar@familiar
```

To get the CLI and the full folder:

```sh
git clone https://github.com/intentionaut/familiar.git ~/Projects/familiar
cd ~/Projects/familiar
python3 scripts/familiar init
```

`init` scaffolds the folders, copies the knowledge templates into
`./knowledge/`, writes a `.familiar` config file, and installs the commands for
the agents you use. `~/Projects/` is only a suggestion; clone anywhere and run
`init` from there.

```sh
familiar init                  set up Familiar in the current directory
familiar new-piece <slug>      scaffold a new piece folder
familiar status                what Familiar can see and what it still needs
                               (and, if knowledge/updates.md says on, whether a
                               newer Familiar exists; off by default, once a day)
familiar skill install         install commands for all agents
familiar skill install codex   install commands for Codex only
```

**It runs anywhere the prompts do.** Nothing in them is tied to one vendor or
one model. Claude Code, opencode, Codex and Gemini CLI each get commands
installed to their standard location, [Dex](https://heydex.ai) installs it as a
callable skill with `dex/install.sh`, and with no terminal at all you can paste
`knowledge/*` and `prompts/*` into a claude.ai Project and run the stages by
name. `knowledge/models.md` says where it is worth spending a better model and
where a cheap one will do, without naming a vendor.

If you keep your voice files somewhere other than the repo, point
`$FAMILIAR_CONFIG` at that folder, or let a host declare it.

### Updating

Three ways in, three ways to stay current. Pick the one you installed with.

Installed with the skills CLI:

```sh
npx skills update familiar
```

Installed as a Claude Code plugin: open `/plugin` and update `familiar` from the
marketplace list. Claude Code owns updates on this path.

A clone:

```sh
cd ~/Projects/familiar && git pull && scripts/setup.sh
```

The second step matters. The installed commands carry the knowledge path from
the moment they were installed, so a pull on its own leaves your agents running
the old ones. `setup.sh` is safe to re-run: it only touches files it wrote, and
it removes commands that no longer exist. `familiar doctor` then reports the
version you are on, and, if `knowledge/updates.md` says on, whether a newer one
exists.

## Keeping notes out of a public repo

Writing about your own work means keeping notes about it, and those notes end up
next to the code. Familiar ships an optional commit guard that stops the ones
that were never meant to ship from shipping.

```sh
scripts/install-guard.sh            # this repository
scripts/install-guard.sh --global   # every repository on this machine
```

Opt-in. Nothing installs it for you, and `--uninstall` takes it off.

**It only runs where a commit can leave your machine.** A repository with no
remote is skipped entirely, so a private vault or a scratch folder is never
blocked.

It refuses a commit that stages markdown at the repository root outside the
usual set, an email address, phone number, postcode or private key anywhere,
or words about health, money, sexuality or a dispute outside your published
content folders. It names the file and the line and stops. It never edits
anything.

Two committed files tune it: `.mdscope` for extra paths where markdown belongs,
and `.piiallow` for patterns that are known-safe in your repository. A genuine
false positive gets through with `git commit --no-verify`.

## Languages

The mechanical rules were written for English, and some of them are about
English: dashes, spelling, heading case, hyphenated pairs, quotation marks. Set
`Language:` in `positioning.md` and the stages read
`knowledge/languages/<code>.md`, which says which rules to skip or replace and
adds that language's own overused words and tells. The language-agnostic patterns
(padding, hedging, fake candour, announced evidence) still apply.

There is a template and no language files yet. Pull requests from fluent writers
are the way this gets built: see `CONTRIBUTING.md`.

## How it's built

- `prompts/` is the source of truth. One plain markdown file per stage, no
  tool-specific syntax.
- `scripts/familiar` is the CLI entry point: `init`, `new-piece`, `status`,
  `skill install`.
- `.claude/commands/` holds thin adapters that say "read prompts/X.md and follow
  it". `scripts/setup.sh` installs them for whichever of Claude Code, opencode,
  Codex and Gemini CLI you already have, substituting real paths on the way.
  `--only <agent>` installs one, `--all` installs everywhere.
- `commands/` is the same set rewritten for a plugin install, where paths cannot
  be substituted because there is no install step to do it. It is generated by
  `scripts/build-plugin.py` and committed, so the plugin needs no build; a test
  regenerates it to stop the two drifting apart. Edit the adapter, not this.
- `knowledge/` is yours. The templates ship tracked in the repo; only
  `knowledge/proposals/` and `knowledge/private/` are ignored. If your voice
  guide ever gets candid, keep the fork private.
- `knowledge/styles/` has templates for different publication types: personal
  essay, research digest, company changelog, internal newsletter.
- `pieces/` is where the writing happens. Ignored by git, so the repo stays a
  tool and your drafts stay with you.
- `.github/ISSUE_TEMPLATE/` has templates for submitting stages, languages,
  styles, and publication styles.

## Where it came from

Familiar is what makes [Intentionaut](https://intentionaut.com), a letter on
design, product, data and AI. Every issue goes through it. It is open source
because the problem is not mine alone, and because a tool that shapes how someone
writes should be one they can read.

The story of how it came to be, and why it refuses to rewrite, is at
[intentionaut.com/open-source/familiar](https://intentionaut.com/open-source/familiar/).
The short version: I finished a product, sat down to write about how it got made,
and found the first three days were unrecoverable. The git history recorded what
happened and nothing about why. I had made every one of those decisions myself
and I could not reconstruct a single one.

The stages are shaped by how good editors actually work: interview first, propose
structures rather than pick one, report rather than rewrite, and run the boring
mechanical pass last.

## The letter

Familiar is built in public, and the build stories land first in
[Intentionaut](https://intentionaut.com/subscribe/?utm_source=github-familiar):
what shipped, what went wrong, and what it cost. Roughly fortnightly.

## Status

Free, and a prompt pack rather than a product. Issues and pull requests welcome:
language files, one tell at a time with a real example, stages for new gates, and
styles for other kinds of publication. `CONTRIBUTING.md` has the four shapes, and
the weekly humanizer issue is a good place to find a first one.
