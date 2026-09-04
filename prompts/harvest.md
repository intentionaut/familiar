# Stage: harvest

Read what the writer has recorded about their work, across whatever sources
they keep, and extract its shape. Output only the synthesis, not the raw
content. Write the result to knowledge/patterns.md.

This stage runs periodically (weekly, or when the writer feels scattered). It
is not part of the piece pipeline. It feeds the interview stage: when the
writer does not know what to write about, the interview reads patterns.md and
offers ready topics.

**It has to work on the first week as well as the fiftieth.** Build logs are
the richest source and they are not the only one, and a writer with one project
and no logs at all still has pieces they have sent, reflections they have
recorded and clips they have saved. A harvest that answers "nothing here" to
the person asking what to write about has failed at the one thing it is for.

## Setup

1. Read knowledge/build-logs.md for the watched project list and the
   cross-project log path (if any).
2. Read knowledge/patterns.md to see what was extracted last time, including
   the Ledger and the Turned down list at its foot.
3. Read knowledge/positioning.md for the house themes. These are the lens:
   patterns that connect to the house themes are stronger candidates. Read its
   "Personal context" rules too; they govern what may reach a piece and
   therefore what is worth offering as a topic.
4. Read knowledge/reflection.md for the reflections folder and for
   `Quote reflections in patterns`. If reflection is on and the folder exists,
   read every file in it, including `threads.md` if there is one.
5. Resolve the piece folders the way `scripts/paths.py` does, and read what has
   already been written: every `final.md` (a piece that was sent) and the
   thesis line of every `notes.md`. A topic the writer has already published is
   not a ready topic.
6. Check for an `inspirations/` folder next to the knowledge folder. If it
   exists and contains `.md` files, read them all. These are clipped snippets
   from articles, posts, and quotes the writer saved for later.

### When a source is missing

Every one of these is a normal way to work. None of them is an error, none
gets a warning tone, and the stage runs on what is there.

| Missing | Do this | Say this |
|---|---|---|
| No build logs registered | Harvest the pieces, reflections and clips instead | Name it once in the exit report, with `familiar log add <project>` as the way to add one |
| Reflection off, or no reflections folder | Work from the logs and pieces. Do not offer a topic that needed a reflection to stand up | "Reflection is off, so this harvest is what the work says rather than what you said about it" |
| No `threads.md` | Look for contradictions across reflections yourself | Nothing |
| No `inspirations/` | Skip the section, one line, per its own rules | Nothing in the exit report |
| No pieces yet | Nothing to exclude. Every topic is new | Nothing |
| No previous patterns.md | First harvest. Nothing to demote, nothing to keep continuous | "First harvest" in the Ledger |

Never report a missing source as an empty finding, and never make a writer feel
behind for not having one.

## Method

### What to read, when there is more than fits

Read every reflections file, every file in `inspirations/`, and the
cross-project log in full: they are small and they are where the angles are.
Build logs are the ones that grow without limit, and a single project's log
reaches a size no context window holds while still being a normal, healthy
log.

So, in this order, and stop when the budget is spent rather than when the logs
run out:

1. Every log's most recent entries, always, however many logs there are.
2. Any entry a log marks as reconstructed, because those mark the boundary
   where the record changes character.
3. Backwards through the rest, newest first, largest logs last, so one big
   project cannot consume the whole read.

**Coverage is reported, never assumed.** Say in the exit how many logs were
read in full and how many by their recent entries. A finding drawn from a
partial read is still a finding; a partial read presented as a complete one is
how a shallow harvest passes for a thorough one.

### The instance, which is what a finding is counted in

A theme needs two or more **independent instances**. A project is the usual
one, and it is not the only one. Two moments in a single project's log are
independent when a real change sits between them: a position taken and then
reversed, an approach tried and replaced, a question answered differently in
March and in September. Two entries about the same week are one instance
described twice.

This is what lets the stage work for a writer with one project, which is every
writer at the start. A fortnight of one log can hold a reversal, and a reversal
is worth more than the same opinion held in four repos.

### Rules

Five rules govern everything below. They exist because the obvious version of
this stage produces a page of true, useless statements.

**Do not hand a log its own conclusion back.** A good build log already names
its own rules. Restating one, with the citation appended, reads as synthesis
and is transcription. Where a log has already named the thing, say so in a
clause and spend the finding on what follows from it. The value of reading
every log at once is what no single log could see.

**A propagation is not a pattern.** Projects with one author share rules,
hooks, components and a CLAUDE.md. When something recurs because it was
deliberately carried from one project to the next, that is a growth signal, and
it is reported there and nowhere else. Never count it twice.

**Weight by evidence, not by appearances.** Logs differ in size by two orders
of magnitude. Name which project carries the substantial instance and which
are corroborations. Two projects is not enough when the second is a passing
mention: that is one instance with a witness.

**The logs say what happened. The reflections say what the writer thinks.**
Only one of those can carry an angle. A finding built entirely from build logs
is about software; check it against the reflections before it becomes a topic.

**Write the capability, not the correction.** A build log is mostly a record of
what went wrong, because that is the part worth keeping and the part its own
format asks for. Harvesting it by weight therefore produces a charge sheet, and
a writer handed a list of their own errors will not start a piece from it. A
failure in a log is evidence of a judgement the writer now holds. Name the
judgement. The failure is the citation underneath it, in a clause, and it never
supplies the name of a theme.

Do not editorialise the writer's decisions and do not praise them. No verdicts
on whether something was wise, mature, expensive or overdue. The reader of this
file is the person who made every call in it. AGENTS.md, "Stating a finding",
carries the rules and the test; this stage breaks them more easily than any
other, because a cross-project read is where an unstated standard is easiest to
invent. A system built for one kind of product not covering another is scope. A
question a project left open is a question, not a debt.

A theme that only exists because something broke is usually a theme that has
not been found yet. Look again for the capability it produced, and if there is
none, drop it.

Then extract four things.

### Recurring themes

Themes that appear across two or more independent instances, and that survive
the propagation test above. A theme is a technical concern, a design problem, a
recurring decision pattern, or a question the writer keeps returning to. For
each:

- Name the theme in one short phrase, five or six words, scannable in a list.
  The name is the theme. Everything under it is citation, and a theme that
  needs a paragraph to state has not been named yet
- Name it for the judgement it shows, never for the problem that revealed it.
  No caveat clauses in the name: "and the one case it does not cover" is a
  verdict wearing a title
- Cite where it appears, with dates (e.g. "deployment anxiety: cv-coach
  (2025-06), familiar (2025-08)"), in two or three lines at most
- Say which citation is the substantial one
- Note whether the angle changed between instances, and say plainly when it did
  not. An unchanged angle across three projects is a habit, and a habit is
  weaker material than a position that moved.
- Say if a log named this itself, and whose framing it is

**Keep a theme's name across harvests.** The previous patterns.md was read in
setup. Where a theme's citations overlap what is already there, reuse the name
it already has, even where a fresh phrasing would be marginally better. A
writer coming back weekly has to be able to tell a theme strengthening from the
same theme worded differently, and only one of those is information. Rename
when the evidence itself has changed, and say so in the Ledger.

Skip themes that rest on a single instance. Skip themes that are about the
tooling (e.g. "uses Claude Code") rather than the work. Skip themes that would
be true of any competent engineer's week: the test is whether the finding needs
this writer, these projects and this fortnight to be worth stating.

### Growth signals

Things the writer was learning or struggling with in one project that they
are now applying or teaching in another, and positions that moved. For each:

- Name the signal in one phrase
- Cite the learning project and date, then the applying project and date
- Note whether the application is deliberate or accidental

This section owns every deliberate propagation, including rules copied between
repos, a hook installed everywhere after it proved itself, and a component
extracted in one project and reached for in the next.

A **position shift** is the strongest signal available and it lives here.
Reflections and `threads.md` are where one is visible: an answer that
contradicts an earlier answer in the same thread, a definition that moved, a
constraint that changed shape. Cite both sides in the writer's own words, with
their dates, and say what sits between them in the logs.

Growth signals are the rawest material for the "how I got here" narrative.

### Inspiration connections

Clipped snippets that connect to themes found in the build logs. For each
annotated clip (one with a "Why it stuck" section):

- Name the connection in one phrase
- Cite the clip (author + date) and the project theme it connects to
- Note whether the clip predates or postdates the project work

Skip clips without a "Why it stuck" section. Count them in the exit report
as "N clips not yet annotated."

If there is no `inspirations/` folder, write one line saying the folder does
not exist yet and how to start it. Do not report a zero as though it were a
finding, and do not repeat that line in the exit report.

### Ready topics

3-5 concrete interview angles for low-energy days. A topic is an angle, not a
subject: a claim, a reader, and a reason it is worth saying now. "What I
learned about X" is a subject and will produce an interview that goes nowhere.

A topic is pitched between two failures, and both are easy to write.

**Too broad** is a maxim any engineer could have published: "test your
assumptions", "config is not enforcement". It cites the writer's work and does
not need it.

**Too specific** is one incident: the afternoon a credit balance ran out, the
constant that was deleted the next day. That is an anecdote, and an anecdote
fills three paragraphs and then asks the writer to find the point themselves,
which is the work this stage exists to have already done.

A topic sits in the middle: **a position the writer holds, which more than one
instance has tested.** The incidents are what it stands on, never what it is
about. Two projects is the usual shape and one project across a real change is
the other, per "The instance" above.

Open the section with a **one-line index**: the five names and nothing else, so
the writer can choose before reading. Then **pick one and say why**. On a low
day the choosing is the cost, and a stage that returns five equal options has
handed the work back.

Each topic carries these, in this order, one line each unless stated:

- **The name**, a phrase
- **A metadata line**: who it is for, the house intersection, and whether the
  evidence supports a letter or a deep dive
- **The position**, one sentence. Use the writer's own words wherever the
  reflections give them. A position stated in the stage's voice has to be
  agreed with before it can be written from, which is a step nobody needs
- **The tension**, one or two lines, and this is the part that makes a topic
  writable. Name the two instances that disagree. A position every project
  supports produces a report; a position two of the writer's own projects
  answer differently produces an argument, and the argument is the piece
- **The evidence**, two or three bullets: project, date, and the specific fact
- **A line you already have**: one sentence from a reflection or a log, quoted
  exactly, that could survive into the draft. This is the strongest prime
  available, because it is the writer's own good sentence handed back
- **The opening question**, answerable out loud in a sentence
- **What you would need**: the one thing that is not yet on file, or "nothing,
  it is all here". This is what decides whether a topic is possible today

A position tested only once is a good candidate rather than a topic. Say so
and leave it for the next harvest rather than promoting it.

**Do not offer back what has already been written or turned down.** The pieces
were read in setup and the Turned down list is at the foot of patterns.md.
A position a sent piece already carries is finished: name it in one line under
the index, as written, with the date it went out, so the writer can see the
stage knows. A topic on the Turned down list does not appear at all. Neither is
a finding, and neither gets a paragraph.

**Say what a topic could not carry.** Run `scripts/never-publish.py` over each
topic's evidence and quoted line. A block match means the topic as evidenced
cannot go out, so mark it, name which piece of evidence is the problem, and
leave the topic in place: the position is often still writable from other
evidence, and that is the writer's call. This costs one command and turns a
refusal at the publish gate, three stages later, into a note at the moment of
choosing.

The opening question **asks for judgement the writer holds today**, never for
recall of what they thought weeks ago. Reconstructing a past mental state is
exactly what the logs exist because nobody can do, and a question that demands
it produces an invented answer or a shrug. Ask what they would do again, what
they still believe, what they would tell someone about to make the same call.
It should be specific enough to start a real conversation, not a prompt like
"tell me about X", and it should reference something that actually happened.

Prefer a topic only this writer could produce. A maxim about software that any
engineer could have written is not a topic, whatever it cites.

## Output

Write knowledge/patterns.md in full. This is a snapshot, not append: each
harvest replaces the previous content. Keep the section headers (Recurring
themes, Growth signals, Inspiration connections, Ready topics) so the
interview stage can find them.

Do not repeat the raw log content. Every finding must cite its source (project
name + date), but the finding itself is the synthesis, not a copy of the log
entry.

**Quoting a reflection moves private material into the knowledge folder.**
Reflections are the one thing Familiar keeps outside the repo, and a quoted
line lands in a file that may sit in a synced folder, a private repo, or a
vault that commits itself. So patterns.md carries the note at its head about
where to keep it, the same note never-publish.md carries, and
`knowledge/reflection.md` decides how much travels:

- `Quote reflections in patterns: words` (the default when the line is absent)
  quotes the sentence, which is what makes a topic writable from a cold start.
- `citation only` cites the file and date and paraphrases nothing. Weaker
  topics, and the right answer for a writer whose knowledge folder is shared.

A topic drawn from a reflection still answers to positioning's personal-context
rules before it can become a piece.

End the file with two appended sections, both of which survive the snapshot.

**Ledger**: one dated line per harvest, naming what was scanned, what coverage
was reached, and what changed since the last run (themes added, themes demoted,
themes renamed and why, position shifts found). The body cannot show a theme
strengthening or fading, so this is the only part of the file that carries
history, and it is never rewritten.

**Turned down**: one line per topic the writer has said no to, with the date and
their reason in their words if they gave one. Read in setup, and never offered
again. This is `cuts.md`'s `dead` flag applied to the stage that proposes
rather than the piece that cuts: a rejected idea recorded is a rejection that
holds, and without it every harvest re-offers what was already refused. Never
delete a line from it. If a turned-down topic later becomes a piece after all,
say so on the line rather than removing it.

## Exit

Report what was found:

- How many projects were scanned, how many logs were read in full and how many
  by their recent entries, and which registered logs were thin or missing. That
  is what bounds the harvest, and it is never left to be assumed
- How many reflections files were read, and whether any position shift was
  found
- How many clips were read from inspirations/, if the folder exists
- How many themes, signals, connections, and ready topics were extracted
- How many clips are not yet annotated
- What was already written, in one line: how many positions a sent piece
  already carries, so a returning writer sees the stage is reading their work
  and not only their logs
- Whether anything was demoted or renamed since the last harvest, and whether
  any topic is marked as unpublishable on current evidence
- Any source that is missing, once, in the words the table in Setup gives

The counts say the harvest ran. They do not say what it found, and a writer
who has to open a file to learn that is being handed homework at the end of a
stage that exists to lower the cost of starting. So **offer the findings, in
one line, and stop**:

> Show you the themes and the ready topics? (y/n)

On yes, print both, in the conversation, in this order and nothing else:

- **Every recurring theme**, one line each: the theme in its own phrase, then
  its project-and-date citations. Not the paragraph from the file: the line
  the writer needs in order to say "that one".
- **Every ready topic**, as its phrase, its tension, its opening question, and
  the house theme it connects to. The tension and the question are the whole
  point of the topic, so neither is ever summarised away. Say which one the
  file picked, and why, in the same line it is printed on.

Growth signals and inspiration connections stay in the file unless asked for.
They are the reasoning behind the topics rather than a thing to pick from, and
a list nobody is choosing from turns the answer back into homework. One
exception: a position shift is named in the exit report, in one line, because
it is the finding most likely to be the piece.

On no, drop it and do not raise it again in that session. Ask once, at the
exit, after the counts and before the suggestion below. Never ask mid-harvest,
and never ask a second time in one session.

Then suggest: "Run `familiar interview` on any of the ready topics, or tell
me what you want to write about."
