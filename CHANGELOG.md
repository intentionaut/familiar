# Changelog

New changes to Familiar. Written for the writer using it, not the developer.

---

## 0.3.0 (2026-08-30)

Familiar runs inside Dex as a skill.

**What this gives you:**

- **`/familiar-custom` in your vault.** `dex/install.sh <vault>` installs it as
  a protected custom skill (Dex names them by folder, and the suffix is the
  protection). Every stage works the same; pieces are written to
  `04-Projects/Writing/` so they are searchable and backed up with the rest.
- **The vault helps.** People and companies named in a piece link to their
  pages, evidence marked "needs finding" is looked for in your notes first,
  and an open decision at a gate can become a task, only if you say yes.
- **Scored against Dex's own rubric.** The skill passes the mechanical
  checks and all four safety gates: distinguishable from its neighbours,
  no destructive step without confirmation, nothing leaves the machine
  without a gate, and it reads its output back before claiming done.

## 0.2.1 (2026-08-30)

Moving back and forth between stages is now the default, and any stage can
work on one section.

**What this gives you:**

- **Go back without starting over.** Run the interview again on a piece that
  already has notes and it reads them, tells you the current thesis, and adds
  to them. The same holds for every stage.
- **Rework one section.** Name a section, heading or paragraph and the stage
  works on that part only: `dev-edit the opening`, `line-edit section 3`.
- **Nothing is overwritten silently.** If a file already has content, the
  stage asks whether to replace it, add to it, or write a numbered variant
  beside it.
- **Resume at your pace.** On return it says in one line where the piece is
  and what the open decision was, and leaves the next move to you.

## 0.2.0 (2026-08-30)

Familiar learns your voice from what you publish, knows which of its rules
are only about English, and keeps its list of AI tells honest against the
most active list out there.

**What this gives you:**

- **A learn stage.** Point it at a folder of past issues and it drafts your
  voice files from evidence, with counts rather than adjectives. After each
  issue, hand it your final next to its draft and the edits you made twice
  become rules. Both propose; you apply section by section.
- **A social stage on your own cadence.** Fill in channels, days and times
  once. It builds one pool of candidates, you pick per channel, it proposes
  exact send times, and nothing is scheduled without a final confirm. With no
  scheduler connected it hands you a paste-ready list instead.
- **Languages.** The rules that are really about English (dashes, spelling,
  heading case) are marked and skipped when your house language is something
  else. A per-language file adds that language's own tells. There are none
  yet; pull requests from fluent writers are the way this fills in.
- **An honest tell list.** Once a week Familiar compares its own list against
  humanizer and opens an issue with anything new. Additions land one at a
  time with a real example. First adopted: "quietly" as a metaphor for small
  or unnoticed.
- **Install as a skill.** `npx skills add intentionaut/familiar` gives you one
  `familiar` command that takes the stage as its first word.

## 0.1.0 (2026-08-30)

The first public version. Familiar is the newsroom behind Intentionaut with
the personal parts taken out and the voice files turned into templates with
questions in them.

**What this gives you:**

- **Six gated stages.** Case study, interview, outline, draft, developmental
  edit, line edit. Each stops and waits for you.
- **Reports, never rewrites.** Edits come back as the quote, the problem and
  the exact fix. Nothing is applied for you.
- **A bracket instead of a fabrication.** Wherever a draft would have
  invented a number or a quote, it leaves `[NEEDS SOURCE]`.
- **Your voice, as files.** Positioning, voice guide, style rules and
  canonical examples, each a template to fill in.
- **Works anywhere plain markdown works.** Claude Code, opencode, or pasted
  into a claude.ai Project.
