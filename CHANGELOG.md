# Changelog

New changes to Familiar. Written for the writer using it, not the developer.

## How these are written

Hard rules. An entry that breaks one of them does not ship.

1. **Nothing that reports on a person's working.** No dates from a session, no
   piece titles, no description of how someone wrote or how their run went, no
   detail traceable to one person's setup. A release note is not an incident
   report, and the maintainer's own work is not evidence to publish.

   The test is attributability, not origin. A concrete number that illustrates a
   failure mode is good writing and stays, because a stranger reads it as an
   example. The same number stops being an example the moment it carries a date,
   a name, or a sentence about whose run produced it.
2. **Nothing from a conversation.** What was said while building this is
   private, including when it was the reason for the change.
3. **Never disparage the tool, past or present.** Describe what it does now. A
   change that corrects earlier behaviour says what is better in one clause and
   moves on. No adjectives about how bad the old way was, and no jokes at the
   product's expense.
4. **Benefit first, mechanism second.** The reader is deciding whether to
   update, not reviewing the diff.
5. **Plain words.** If a term would send a non-technical reader to a search
   engine, explain it in the clause or cut it.
6. **Three to five bullets, and fewer is usually better.** A release that seems
   to need more is usually two releases, or one bullet repeated. Each bullet
   carries what the reader gets; the bold lead may name the capability or just
   name the area it is in, whichever gets them to the sentence faster. What a
   bullet may not do is explain why the change was a good idea. The reader is
   deciding whether to update, not reviewing the reasoning.
7. **Write the capability, not the correction.** When a change exists because
   something was wrong, this is the one place that must not show. Name what the
   reader now has. A rule that only removes something is half written until it
   says what fills the space.
8. **No relief from a burden they never carried.** A bullet that names what a
   feature spares the reader ("no report to open", "no extra step", "without
   leaving the terminal") only works when the reader lived through the thing
   being spared. Where they never had it, the sentence is describing a design
   conversation they were not in, and it leaves them wondering what they missed.
   The test is whether the absence was ever present in a version they used. If
   it was not, say where the work happens rather than where it does not.
9. **A quiet release is a real release.** Not everything that ships is news. A
   version whose changes the reader will never notice is written as "Bug fixes
   and updates." and nothing else, and that entry is finished, not lazy.
   Spending five bullets on housekeeping teaches people to skim the ones that
   matter. Where something did move that a reader would want to know about, say
   that one thing in a sentence under the line and leave the rest out.

---

## 0.19.0 (2026-09-04)

Content safeguards in Familiar

**What this gives you:**

- **Write about client work without holding your breath.** Name the things that
  must never leave your desk once, and Familiar will not schedule anything that
  contains one. You stop carrying the list in your head while you draft.
- **A safeguard you will not switch off.** Names and money stop a publish;
  anything that is usually fine gets a quiet note and leaves the judgement to
  you. It stays out of the way until it matters.
- **Silent until you want it.** Nothing changes for anyone who does not use it.

**If you are upgrading:** create `knowledge/never-publish.md` in your own
knowledge folder and fill it in. Keep it with your other knowledge files, never
in a public repo.

## 0.18.0 (2026-09-04)

Harvest reads what you said about the work, not only what you did.

**What this gives you:**

- **Your reflections are part of the harvest.** It reads them alongside the
  build logs, so the topics it offers come back in your own words, and it
  names the places where an answer you gave contradicts an earlier one.
- **Every topic arrives ready to talk from.** The position, the two projects
  that answer it differently, one sentence you already wrote that could survive
  into the draft, and the one thing still missing. It picks one and says why,
  because on a low day the choosing is the cost.
- **Harvest shows you what it found.** It offers the themes and the topics at
  the end of the run, so the findings reach you without opening a file.
- **`patterns.md` keeps a ledger.** One dated line per harvest, naming what was
  added and what was demoted, so a theme can be watched strengthening or fading
  across runs.
- **`familiar log add` does the whole job.** It registers the project, creates
  the log and wires the hooks that write an entry when a session ends or
  compacts, whichever command you reach for.

## 0.17.0 (2026-09-02)

Three ways in, and a new piece starts by asking rather than by waiting.

**What this gives you:**

- **Three commands, one per way a session starts.** `/familiar-new-piece` when
  you are beginning something, `/familiar-board` when you are picking something
  back up, `/familiar-harvest` when you are looking for what to write about.
  Everything after that is a conversation: tell the agent what you have, a
  draft, notes, an idea, and it picks the stage.
- **`/familiar-new-piece <slug>` goes straight into the interview.** It makes
  the folder, the notes file and the context log, then starts asking. The piece
  begins where you are, rather than at a scaffold waiting to be picked up.
- **`familiar status` leads with what is working.** Your voice files, the
  pieces in flight, your social schedule and whether reflection is on. It names
  a file that is still a template when that is what stands between you and a
  draft.

---

## 0.16.0 (2026-09-02)

Writing you already have gets a way in, and every post gets a pass before it
ships.

**What this gives you:**

- **Bring a draft you already wrote.** `familiar bring <path>` walks a piece you
  already have section by section, saying what each part is doing rather than
  what it says, then names the argument it actually makes against the one you
  meant. Where a draft promises three things and delivers one, that is the first
  thing it tells you. Your file is copied in and never edited.
- **Draft editing flexibility.** Challenged runs the pipeline from the interview
  on. Tidied carries your words straight across to the line edit, sentence for
  sentence. You choose at the gate.
- **Social post editing.** `familiar social-edit` reads a post for whether it
  says one thing, whether it makes sense to someone who has not read the piece,
  and whether it ends on a thought or trails off into a link, all against your
  own house rules. When a post is really two posts, it writes out the viewpoints
  the material supports in full and asks what you actually think.

---

## 0.15.0 (2026-09-01)

Bug fixes and updates.

---

## 0.14.1 (2026-09-01)

Bug fixes and updates.

---

## 0.14.0 (2026-09-01)

Bug fixes and updates.

---

## 0.13.0 (2026-09-01)

Familiar now knows where your files are, and says so.

**What this gives you:**

- **Your writing rules get read, instead of the blank ones that ship with the
  tool.** Familiar comes with a `knowledge` folder full of templates, and most
  people keep their real, filled-in versions somewhere else. Nothing told the
  stages that, so a stage could quietly read the blanks, fall back to defaults
  for things like spelling, and hand you an edit against rules that were not
  yours. Now the location is written down, so every stage reads the same files
  you filled in.
- **One place to say where things live.** A `.familiar` file next to the tool,
  or the environment variables you may already have set. Both are read by
  everything now, rather than by one script that happened to know.
- **Every command carries the answer.** When you install, the resolved location
  is written into the commands themselves, so a stage is told where your files
  are rather than working it out. If it ever lands on the templates, it now says
  so out loud instead of proceeding.
- **The board stops needing to be told.** `board.py` with no arguments finds
  every folder your pieces live in, including more than one.
- **`python3 scripts/paths.py`** prints what resolved and whether it found your
  files or the shipped templates. Worth thirty seconds when an edit feels wrong.

---

## 0.12.0 (2026-09-01)

The interview notices when you are running out of road, and does more of the
work instead of less.

**What this gives you:**

- **It offers you a choice when writing an answer gets expensive.** Answers get
  shorter as an interview goes on. That is not you losing interest, it is
  composing costing more, and it costs most when you are tired, which is often
  exactly when you sat down to write. When an answer comes back much shorter
  than the last two, or general where a specific was asked for, the next
  question arrives as two to four options instead. One letter is a complete
  answer.
- **The options come from what you already said.** Never from somewhere else,
  and there is always an "or something else", so a pick can never quietly
  narrow your piece down to whatever the tool happened to think of.
- **It goes back to open questions when your answers lengthen again.** This is a
  fallback and not a mode. The picks carry the stretch where composing is
  expensive, and the open questions are where an interview surprises you, which
  is most of what it is for.

---

## 0.11.0 (2026-09-01)

The things you cut stop disappearing.

**What this gives you:**

- **A cutting room for every piece.** Material gets cut for good reasons and it
  is still good material. A statistic dropped because your argument moved is
  still true. A section cut because it is really its own piece is a piece nobody
  has written down. Anything substantial that comes out of a piece is now
  recorded in `cuts.md` with one line on why.
- **Three flags, and they do the work.** `dead` means wrong and settled, so a
  later stage will not propose the same thing again. `reusable` means right, but
  not here. `blocked` means right and wanted, waiting on a source or a
  permission or a decision you have not made yet.
- **The board shows you what is waiting to be revived.** A piece with reusable
  cuts carries a count on its card, and its own page lists them with the reason
  each was cut. The idea you had to drop stops being something you have to
  remember and becomes something the board tells you about.
- **Nothing is ever deleted from it.** When a cut does become a piece, its flag
  changes and it names where it went, so the trail stays readable.

---

## 0.10.0 (2026-09-01)

Familiar can now learn from the choices you make, not only the edits you make.

**What this gives you:**

- **A third way of learning your voice: `learn decisions`.** Until now Familiar
  learned by comparing its draft against what you actually published. That only
  ever catches what you changed. It cannot catch what you chose, because
  choosing happens before there is any text to compare. This reads the reasons
  you gave when you picked between options and turns the ones that recur into
  proposed rules.
- **Three occurrences before anything becomes a rule.** One pick is a
  preference. Two is a coincidence. Below three it is listed as something to
  watch, with the picks attached, and said plainly not to be a rule yet.
- **The most useful thing it can find is a contradiction.** If a reason you gave
  goes against what your voice guide says, it comes back to you named as a
  contradiction. Either the guide is out of date or you have changed, and only
  you can say which.
- **Reviews get offered instead of remembered.** Turn on `voice-review.md` and
  Familiar will mention, once, at the end of a stage, that enough decisions have
  built up to be worth a look. Off by default. The cadence is a floor rather
  than an alarm, and a missed review costs nothing because the evidence keeps.
- **It proposes, never applies.** Same gate as everything else here. You accept,
  reject or rewrite each rule, and the proposal file stays as the record either
  way.

---

## 0.9.0 (2026-09-01)

The choices you make while writing are written down, with your reason beside
them.

**What this gives you:**

- **Options arrive as finished text.** Where a stage has more than one good
  answer, each one is written out in full in the piece, with a line on what it
  buys and a line on what it costs. You read them and pick, in seconds.
- **Two to four of them.** One is a recommendation wearing a disguise. Five is a
  shrug.
- **Your reason is kept next to your choice.** One line, in your own words. It
  is never written for you, and if you did not give one it says so.
- **The ones you turned down stay in the file.** A later stage can see that a
  thing was considered and rejected, rather than proposing it again.
- **`voice-review.md`**, for reading all of that back later. Off until you turn
  it on, and the cadence is a floor rather than an alarm. What it turns on
  arrives in the next release.

---

## 0.8.0 (2026-09-01)

Naming a piece is now its own step, at the end, where it belongs. And the piece
gets a way to be found before anyone starts making posts about it.

**What this gives you:**

- **The title comes last, because that is when you know what you wrote.** There
  is a new step, `finalise`, that runs once the writing and editing are done. It
  reads the finished piece, tells you in one sentence what it actually argues,
  which is not always what you set out to argue, and offers three titles drawn
  from the piece's own strongest lines. Each one comes with what it buys you and
  what it costs. The working title from the draft is treated as one candidate
  among three with no head start, because by then it has had the whole edit to
  become familiar, and familiar is not the same as right.
- **Your subject line is a different decision from your title.** A title labels
  the argument for somebody already reading. A subject line has to earn the open
  from somebody who is not. The same words rarely do both jobs, so `finalise`
  asks for them separately and records which kind you picked, so you can see a
  pattern across issues instead of guessing every time.
- **Being findable is part of finishing.** Slug, description, headings, links to
  your own related pieces, and the one thing a person might search that this
  piece deserves to answer. If you keep your own notes on search, it works from
  those rather than telling you what it thinks. And it will never trade a
  sentence you chose for a better ranking: anything that would change your
  writing arrives as a suggestion you can refuse.
- **Posts cannot be made for a piece that has no name yet.** Repurposing and
  social both stop and point you at `finalise` if the title is still provisional.
  Scheduled posts that point at a title you later changed are a quiet mess, and
  this is the cheapest possible way to not have it.
- **Refining 0.7.0.** That release settled the title during the developmental
  edit. It now waits until the line edit is done too, so the title is chosen
  against the finished piece. The developmental edit leaves it alone and says
  so.

---

## 0.7.0 (2026-09-01)

Two changes that came out of using it. Your piece stops drifting towards a title
you picked too early, and the edit reports open somewhere you can actually read
them.

**What this gives you:**

- **A title can no longer steer the piece.** Familiar used to write a
  finished-sounding headline at draft stage, before the argument had settled.
  That headline then pulled every later edit towards it, and the piece ended up
  serving a direction the writing was not going. The drift is hard to spot,
  because each individual edit looks like an improvement. Drafts now get a plain
  working title that labels the argument and is meant to be dull. The real title
  gets chosen at the developmental edit, once there is a finished argument to
  name, with options drawn from the piece's own strongest lines. Until you
  settle it, no stage is allowed to edit the piece to fit its headline. If a
  section fits the argument but not the title, the title is the thing that is
  wrong.
- **The edit reports offer to open themselves.** A developmental or line edit
  hands you a report you work through by hand, usually with the draft open next
  to it. That is not a thing you can do in a terminal. Familiar now asks once,
  at the end of an edit, whether to open the report and the draft together. Yes
  or no. Say no and it drops it and does not ask again.

---

## 0.6.0 (2026-08-31)

Familiar goes all the way to scheduled now, and it works the same whether or not
you run it inside anything else.

**What this gives you:**

- **Publishing, as its own step.** `/familiar-publish` takes the posts you
  already approved and schedules them. It is separate from `/familiar-social`
  on purpose: you can schedule a day later, or a week later, without anyone
  reopening copy you already said yes to. It reads only what you chose; posts
  you held back cannot be scheduled by accident.
- **A post that fits still fits once the link is on it.** Links are built,
  tagged and counted before anything is scheduled, in that order. A post that
  fits at 291 characters is 337 once its tracking parameters are on the end,
  and that is the thing this stops. Over the limit, Familiar stops and tells
  you by how much. It never trims your words to make room; the only cut
  it will offer is to the tracking parameters, which you did not write.
- **A scheduler is optional.** Buffer works out of the box if you connect it.
  Turn it off, or never turn it on, and you get a clean table of every post
  with its channel, time and finished text, ready to paste.
- **It tells you what the scheduler cannot do.** A link that belongs in a
  pinned first comment comes back as a short checklist with times, because
  schedulers create posts and not comments. The link stays where you put it.
- **Familiar no longer assumes where it is running.** Every stage works on its
  own, with no vault and no other tools, and every one of them installs. If you
  do run it inside Dex, Dex adds what it can and says so in one short profile.

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
  and design notes all live here now, and the old repo points this way. Nothing
  it did has been dropped.

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

The first public version. Six gated stages for writing about your own work,
with the voice files shipped as templates you fill in from your own writing.

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
