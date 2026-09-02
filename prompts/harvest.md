# Stage: harvest

Read every build log registered in knowledge/build-logs.md and extract the
shape of your work across projects. Output only the synthesis, not the raw
content. Write the result to knowledge/patterns.md.

This stage runs periodically (weekly, or when the writer feels scattered). It
is not part of the piece pipeline. It feeds the interview stage: when the
writer does not know what to write about, the interview reads patterns.md and
offers ready topics.

## Setup

1. Read knowledge/build-logs.md for the watched project list and the
   cross-project log path (if any).
2. Read knowledge/patterns.md to see what was extracted last time.
3. Read knowledge/positioning.md for the house themes. These are the lens:
   patterns that connect to the house themes are stronger candidates.
4. Check for an `inspirations/` folder next to the knowledge folder. If it
   exists and contains `.md` files, read them all. These are clipped snippets
   from articles, posts, and quotes the writer saved for later.

## Method

Read each registered build log in full. Read the cross-project log if it
exists. Read every file in `inspirations/` if the folder exists. Then extract
three things:

### Recurring themes

Themes that appear across two or more projects. A theme is a technical
concern, a design problem, a recurring decision pattern, or a question the
writer keeps returning to. For each:

- Name the theme in one phrase
- Cite the projects and dates where it appears (e.g. "deployment anxiety:
  cv-coach (2025-06), familiar (2025-08)")
- Note whether the angle changed between projects

Skip themes that appear in only one project. Skip themes that are about the
tooling (e.g. "uses Claude Code") rather than the work.

### Growth signals

Things the writer was learning or struggling with in one project that they
are now applying or teaching in another. For each:

- Name the signal in one phrase
- Cite the learning project and date, then the applying project and date
- Note whether the application is deliberate or accidental

Growth signals are the rawest material for the "how I got here" narrative.

### Inspiration connections

Clipped snippets that connect to themes found in the build logs. For each
annotated clip (one with a "Why it stuck" section):

- Name the connection in one phrase
- Cite the clip (author + date) and the project theme it connects to
- Note whether the clip predates or postdates the project work

Skip clips without a "Why it stuck" section. Count them in the exit report
as "N clips not yet annotated."

### Ready topics

3-5 concrete interview angles for low-energy days. Each one:

- Names the topic in one phrase
- Grounds it in specific evidence (project name, log entry, date)
- Offers a suggested opening interview question
- Notes which house theme it connects to

The opening question should be specific enough to start a real conversation,
not a prompt like "tell me about X." It should reference something that
actually happened.

## Output

Write knowledge/patterns.md in full. This is a snapshot, not append: each
harvest replaces the previous content. Keep the section headers (Recurring
themes, Growth signals, Inspiration connections, Ready topics) so the
interview stage can find them.

Do not repeat the raw log content. Every finding must cite its source (project
name + date), but the finding itself is the synthesis, not a copy of the log
entry.

## Exit

Report what was found:

- How many projects were scanned
- How many clips were read from inspirations/
- How many themes, signals, connections, and ready topics were extracted
- How many clips are not yet annotated
- Whether anything was demoted from a previous harvest (a theme that no
  longer appears in recent logs)

Then suggest: "Run `familiar interview` on any of the ready topics, or tell
me what you want to write about."
