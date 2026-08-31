# Changelog

New changes to Familiar. Written for the writer using it, not the developer.

---

## 0.5.0 (2026-08-31)

Familiar now sits beside the work itself. Captain's Log has been folded in.

**What this gives you:**

- **A build log for every project, not just the ones you remembered.**
  `familiar log` scans your projects folder and shows which keep a build log
  and which shipped this week without one. `familiar log add <project>` wires
  the automatic entry, written when a session ends or compacts, and records
  the log's filename so one called anything at all is found. The format stays
  one block you can paste into any project.
- **Reflection, on your cadence.** Two questions about how the work is going,
  answers recorded word for word. Opt in and pick weekly, fortnightly or
  monthly in `knowledge/reflection.md`, edit the question bank there too.
  Familiar offers one at the end of a stage when one is due, once per session,
  and drops it the moment you are not in the mood. Off means off.
- **Threads that notice you changing your mind.** Ideas you are developing get
  worked into every second or third reflection from a new angle, and when an
  answer contradicts an earlier one, Familiar says so and asks. That is where
  a view actually changes, and it is the hardest thing to catch yourself.
- **Your answers stay yours.** Reflections live in a private folder you name,
  never in this repo, and the nudge is a quiet notification that always writes
  a log line so you can tell it ran.
- **Captain's Log is archived.** Its build-log format, hook, reflection ritual
  and design notes all live here now; the old repo points this way. The origin
  story, including the honest paid-versus-free assessment, is kept as written
  in `docs/origin.md`.

## 0.4.2 (2026-08-30)

The board is a real command now, and you can tidy it, not only read it.

**What this gives you:**

- **`/familiar-board`.** It installs with the rest, so the board is one command
  rather than a script you have to remember the path to.
- **Archive and delete, from the board.** Run it with `--serve` and every card
  gets Archive, which moves the piece out of the way and can be undone from the
  toast or the archive drawer, and Delete, which removes the folder after a
  confirmation naming the piece.
- **Anything you have sent is safe.** A piece with a `final.md` shows no delete
  control, and the server refuses one even if asked directly. That file is the
  record of a piece that exists in the world, and it is what the learn stage
  reads to teach itself your voice.
- **The server stays on your machine.** It binds to localhost, mints a fresh
  token each run so no other page in your browser can reach it, and will only
  act on pieces it just listed rather than on any path it is handed.
- **Fixes.** Page files are named safely, so a piece folder with a space or an
  ampersand in its name still opens. An empty `draft.md` no longer counts as a
  draft and gets sent for a developmental edit. Pages for pieces that no longer
  exist are swept on every build. A slug used as a title is no longer Title
  Cased into things like "No Fm".

## 0.4.1 (2026-08-30)

The board says what each piece needs, and covers pieces kept in more than one
place.

**What this gives you:**

- **Columns you recognise.** Thinking, Writing, Editing, Ready, Sent. They
  describe the state of the writing rather than which Familiar stage ran last.
- **Every card says what is next.** When a stage left a note in the context
  log, the card quotes it. When none did, the card works it out from the
  files: run the interview from the questions, ask for three structures,
  resolve four brackets, work through the line edit. No card is blank.
- **Pieces in more than one place.** Pass `--pieces` once per folder, or set
  `FAMILIAR_PIECES` to a colon-separated list, and each card says which folder
  it came from. Useful when a vault and a separate newsletter repo both hold
  work in flight.
- **Titles found where they really are.** A draft with an editor's note above
  its frontmatter now shows its real title rather than falling back to a
  heading from the notes.

## 0.4.0 (2026-08-30)

See everything you have in flight, on one board.

**What this gives you:**

- **A board of every piece.** `scripts/board.py --open` writes a static page
  with a column per stage and a card per piece: title, date, the first thing it
  actually says, how long since you touched it, and how many brackets are still
  unresolved. Pieces that have been sitting are marked.
- **The decision waiting on you, in your own words.** Each card carries the
  decision gate from that piece's context log, quoted rather than summarised.
- **One page per piece, for coming back cold.** Click a card and you get what
  it argues, what is waiting on you, every unresolved `[NEEDS SOURCE]` and
  `[ASK THE WRITER]` listed out, the folder path and the next command, then the
  notes and outline folded away, then the draft. Enough to pick up a piece you
  have not opened in a month.
- **Local, static, and it changes nothing.** Plain HTML on your own machine. It
  reads your piece folders and writes a `.board` folder beside them. Nothing is
  sent anywhere, and no key is needed.

## 0.3.3 (2026-08-30)

Each piece keeps its own context log, so a piece is self contained.

**What this gives you:**

- **The log lives with the piece.** Every stage now appends to
  `SESSION-CONTEXT.md` inside the piece folder rather than one shared file at
  the project root. Moving or archiving a piece takes its history with it, and
  twenty pieces no longer share one stream. If you have an existing root log,
  split it by piece; every entry already names its piece in the heading, so
  nothing has to be guessed. Copy rather than move, and keep the original until
  you have checked.
- **Two wording fixes.** The developmental edit no longer says "revises each
  item herself", and the outline stage says piece where it used to say issue.

## 0.3.2 (2026-08-30)

The draft stage asks before it invents, and in Dex your voice files live in
your vault.

**What this gives you:**

- **Voice first, then ask, then invent only with permission.** Draft will
  not run on template voice files; it offers to learn from your published
  work instead. Gaps the outline flagged are asked about in one short list
  before writing. Anything it still does not have stays a bracket.
- **Your voice stays out of the public repo.** In Dex, the voice files live
  in `06-Resources/Familiar/knowledge/`, seeded from the templates on
  install and never overwritten. Pieces and learn proposals are in the vault
  too.

## 0.3.1 (2026-08-30)

The case-study stage reads your coding sessions, not only a build log.

**What this gives you:**

- **Start a piece from a session.** `case-study session` takes the most
  recent Claude Code session for the project (or a transcript path) and
  turns it into a brief and interview questions, the same as it does for a
  Captain's Log. Wrong turns are found in the moments you changed direction
  or corrected the assistant, and quoted.
- **A readable digest, kept.** `scripts/session-digest.py` writes the
  session into the piece folder as plain markdown: what was said, in order,
  tool use collapsed to a line each. Nothing interpreted. Everything from a
  transcript is marked reconstructed.

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
