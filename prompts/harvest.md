# Stage: harvest

Read every build log registered in knowledge/build-logs.md, and the writer's
own reflections, and extract the shape of your work across projects. Output
only the synthesis, not the raw content. Write the result to
knowledge/patterns.md.

This stage runs periodically (weekly, or when the writer feels scattered). It
is not part of the piece pipeline. It feeds the interview stage: when the
writer does not know what to write about, the interview reads patterns.md and
offers ready topics.

## Setup

1. Read knowledge/build-logs.md for the watched project list and the
   cross-project log path (if any).
2. Read knowledge/patterns.md to see what was extracted last time, including
   the ledger at its foot.
3. Read knowledge/positioning.md for the house themes. These are the lens:
   patterns that connect to the house themes are stronger candidates. Read its
   "Personal context" rules too; they govern what may reach a piece and
   therefore what is worth offering as a topic.
4. Read knowledge/reflection.md for the reflections folder. If reflection is
   on and the folder exists, read every file in it, including `threads.md` if
   there is one.
5. Check for an `inspirations/` folder next to the knowledge folder. If it
   exists and contains `.md` files, read them all. These are clipped snippets
   from articles, posts, and quotes the writer saved for later.

## Method

Read each registered build log in full. Read the cross-project log if it
exists. Read every reflections file. Read every file in `inspirations/` if the
folder exists.

Four rules govern everything below. They exist because the obvious version of
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

Themes that appear across two or more projects, and that survive the
propagation test above. A theme is a technical concern, a design problem, a
recurring decision pattern, or a question the writer keeps returning to. For
each:

- Name the theme in one short phrase, five or six words, scannable in a list.
  The name is the theme. Everything under it is citation, and a theme that
  needs a paragraph to state has not been named yet
- Name it for the judgement it shows, never for the problem that revealed it.
  No caveat clauses in the name: "and the one case it does not cover" is a
  verdict wearing a title
- Cite the projects and dates where it appears (e.g. "deployment anxiety:
  cv-coach (2025-06), familiar (2025-08)"), in two or three lines at most
- Say which citation is the substantial one
- Note whether the angle changed between projects, and say plainly when it did
  not. An unchanged angle across three projects is a habit, and a habit is
  weaker material than a position that moved.
- Say if a log named this itself, and whose framing it is

Skip themes that appear in only one project. Skip themes that are about the
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
project has tested.** The incidents are what it stands on, never what it is
about.

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

A position that only one project has tested is a good candidate, not a topic
yet. Say so and leave it for the next harvest rather than promoting it.

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

Reflections are private and stay private. They may be quoted inside
patterns.md, which lives with the writer's own files, and a topic drawn from
one still answers to positioning's personal-context rules before it can become
a piece.

End the file with a **Ledger**: one dated line per harvest, appended rather
than replaced, naming what was scanned and what changed since the last run
(themes added, themes demoted, position shifts found). The body is a snapshot
and cannot show a theme strengthening or fading; this is the only part of the
file that carries history, so it is never rewritten.

## Exit

Report what was found:

- How many projects were scanned, and which registered logs were thin or
  missing, since that bounds what this harvest could see
- How many reflections files were read, and whether any position shift was
  found
- How many clips were read from inspirations/, if the folder exists
- How many themes, signals, connections, and ready topics were extracted
- How many clips are not yet annotated
- Whether anything was demoted from a previous harvest (a theme that no
  longer appears in recent logs)

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
