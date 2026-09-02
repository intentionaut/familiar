# Stage: bring (a draft or notes you already have)

Writing that exists before Familiar sees it. A draft in a folder, an export from
a CMS, a pile of notes that has been sitting for a year. This stage reads it,
names the argument it found, audits what it claims, and asks the questions the
prose cannot answer.

It does not write the piece. It does not touch the file the writer handed over.
The words are already theirs, and this stage exists to show them what they have.

| Choice | What it means | Where it goes |
|---|---|---|
| **draft** | One piece of prose with a shape already, however wrong | the draft branch below |
| **notes** | Several files, or one that is not prose yet. No shape | the notes branch below |

## The choice (gate 0)

`$ARGUMENTS` may name it: `bring draft <path>` or `bring notes <path>`. It may
also just be a path. A single markdown or text file is a draft; a folder, or
several paths, is notes. Take the obvious reading and say which you took.

If it is genuinely unclear, a long file of headings and fragments being the
usual case, ask in one line and stop:

> Is this a draft with a shape already, or material you have not shaped yet?
> A draft gets a spine and a claims audit. Material gets an inventory and
> candidate spines.

Do not proceed on an assumption. Mapping a pile as though it were an argument
invents the argument.

## Setup

1. Read knowledge/positioning.md and knowledge/voice-guide.md. You need the
   scope in positioning.md to say what this piece is about in the house's own
   terms, and the voice to phrase questions that draw specifics.
2. Read knowledge/style-rules.md. You are not editing against it here. You are
   reading so the claims audit can tell a house convention from a real problem.
3. Create `pieces/YYYY-MM-DD-short-slug/` (today's date; slug from the source's
   own title or filename). If the folder exists and holds a piece already, ask
   before adding to it.
4. Copy the source in **verbatim**, byte for byte:
   - draft branch: `source.md`
   - notes branch: `sources/<original filename>` per file
   Never edit these again. They are the record of what the writer had before
   Familiar read it, and every later stage can diff against them.

**Scope:** if `$ARGUMENTS` names a section or heading of the source, map that
part only and say which part you worked on. If `spine.md` already has content
and no scope is given, ask before replacing it: replace, add to, or write a
numbered variant beside it.

## Method

Read the whole thing before writing anything. A spine found from the first three
paragraphs is the opening restated, not the argument.

### Write `spine.md`

```
# Spine: <the source's own title>

## Source
Path, word count, date last modified, and this line: reconstructed from prose.
It records what the draft says, and the reasoning only where the draft says it
out loud.

## What this draft is doing
Section by section, what each one is doing rather than what it says. Quote the
sentence that carries it. A section that is doing two things gets both, and
that is usually a finding.

## The argument as found
One sentence. Quote it where the draft states it. Where the draft implies an
argument without ever making it, write the sentence you think it is reaching
for and mark it [ASK THE WRITER: is this the argument you meant?].

## Candidate spines
Two or three, one line each. The shape it has now is always one of them, named
honestly. The others are shapes the same material would support.

## Where it wanders
Sections that do not serve any candidate spine. What each one is about, and
which of the three flags it takes. These go to cuts.md as well, never deleted.

## Claims audit
Every factual claim, one per line, marked:
  have          sourced in the draft, with the source named
  claimed       asserted as fact with nothing behind it
  needs finding the writer will have to go and get this
A number, a date, a named company, a "studies show", a market size, an
attributed quote. This is the section that earns the stage.

## What only the writer has
The questions the prose cannot answer: why this, why now, what changed their
mind, what they know that never made it onto the page.
```

On the notes branch there is no `## The argument as found`, because there is
not one yet. `## What this draft is doing` becomes `## What is in here`: an
inventory, one line per file, saying what each holds and what it is for.

### Write `brief.md` and `interview-questions.md`

Same shape prompts/case-study.md writes, so the interview reads them without
learning anything new. The intersection and candidate theses come from the
spine; the evidence inventory is the claims audit, carried across with its
statuses intact. Aim for 8 to 12 questions, each grounded in a specific passage,
each one the prose genuinely cannot answer.

## Rules

- **Never edit the source.** Not to fix a typo, not to normalise a heading, not
  to strip frontmatter. `source.md` is frozen at the moment it arrives.
- **Never write `draft.md`.** This stage produces a map, not a piece. The draft
  stage carries the words across when the writer asks for it.
- **The title is not settled**, whatever the source calls itself. A brought
  draft arrives with a title someone chose before the argument was tested, and
  every later stage would edit towards it. Record it in the spine and leave it
  there until finalise.
- **Every quote is verbatim or it is a bracket.** `[NEEDS SOURCE: ...]` for a
  fact, `[ASK THE WRITER: ...]` for a scene or a feeling. Never smooth a
  half-finished sentence into a whole one and quote it back.
- **The honest stop.** If the only spine you can find is "here is what the piece
  said", say so and stop. Some drafts were abandoned for a reason, and naming
  that reason is a better result than a map of nothing.

**Options.** Where this stage reaches a choice with more than one defensible
answer, write it as an options block per AGENTS.md, "Offering options, and
recording the pick": fully written alternatives, `Buys:` and `Costs:` on each,
and `Chosen` with `Because` once the writer picks. Never only in conversation.

**Cuts.** Anything substantial removed at this stage goes to `cuts.md` per
AGENTS.md, "The cutting room", with a `Flag:` of dead, reusable or blocked. A
cut section or a dropped set of evidence is material, not waste.

## Exit

Save `spine.md`, `brief.md` and `interview-questions.md`. Report the word count
of the source, how many claims came out `claimed` or `needs finding`, and how
many sections wander.

Then two questions, and stop.

1. > Is the argument I found the one you meant?

2. > Do you want this challenged, or tidied?
   >
   > Challenged runs the interview, so the piece gets a thesis and a structure
   > you chose, and a developmental edit that has something to check it against.
   > Tidied carries your words straight across and goes to the line edit. It is
   > faster, and there is no developmental edit on that road, because a
   > developmental edit with no thesis behind it is theatre.

Record the answer as `Register:` in the context log. Do not run the next stage.
Hand off: on challenged, tell the orchestrator to run /interview on this piece
folder with interview-questions.md as the question seed and brief.md and
spine.md as context. On tidied, tell it to run /draft, which will find
`source.md` and carry it across, and then prompts/line-edit.md.

If knowledge/voice-guide.md is still the template, offer this once, in one line,
and drop it if they say no: the source is the writer's own prose, so
`learn ingest source.md` is the fastest way to fill the voice files, and this is
the one moment there is definitely prose to learn from.

- **Context log:** append to the piece's own `SESSION-CONTEXT.md` per
  knowledge/context-log.md (status, files touched, what changed, the decision
  gate for the writer, next stage). Record `Register:` and the source path.
  Terse; this is what makes the article easy to resume later.
