# Positioning

Source of truth for what this publication is. Every stage reads it first.
Replace the bracketed prompts with your answers. Short is fine.

## The basics

- Name: [the publication's name]
- Author: [you]
- Where it lives: [platform or URL]
- Cadence: [weekly, fortnightly, whenever it is ready]. Every stage takes the
  ship date from the piece's `draft.md` frontmatter `date:`, never from an
  assumed weekday.
- One-liner: [what it is, for whom, in one sentence you would say out loud]

## House rules

These are the mechanical choices the line edit enforces. Set them once.

- Language: [en, or an ISO code such as de, pt-BR, he. Anything but English
  makes the stages read `knowledge/languages/<code>.md` and skip the
  English-only rules]
- Spelling: [British / American / other]
- Em dashes: [never / sparingly / fine]
- Reading ease target: [e.g. Flesch 60+, grade level about 8]
- Pieces end with: [an invitation to reply / a question / nothing in particular]
- Anything else that is non-negotiable: [e.g. sentence-case headings, no exclamation marks]

## Scope

The themes this publication covers, and the ones it does not:

- [theme 1]
- [theme 2]
- [theme 3]

If one theme tends to crowd out the others, say so here. The interview will use
this list to name which theme a piece serves and where themes cross.

## Audience

Write to one reader, not an audience. Describe that person in two or three
lines: what they do, what they already know, what they are tired of reading.

[your reader]

## Voice in brief

The long version is `voice-guide.md`. Three or four lines here for stages that
only need the gist:

- [warm / dry / direct / formal]
- [what you never do]
- [what you always do]

## Later, if you keep themes

Nothing below is needed to start, to interview or to draft. It matters once
`knowledge/themes.md` points at segments by id, and not before.

### Segments

Optional, and only worth filling if you keep `knowledge/themes.md`, which points
at these by id. Delete this section otherwise; nothing else reads it.

Segments are yours: you choose the ids, how many there are, and what each one
means. One line per segment, with the id in backticks, who they are in your own
words, and a `Reads:` line saying where you actually see them and how you know
the number. `Reads:` is evidence about a channel and may be far larger than the
people a theme is written for. Leave any value `unknown` rather than guess, and
give every value a `source:` as the rest of this file does.

### How often business development may run

Only matters if a theme in `themes.md` has `Job: business-development`. Those
themes may use whatever room your voice guide gives a credential, and in
exchange they are capped: write the cap here as pieces per period, in your own
terms (one issue in four, two a quarter). It is an editorial constant you
declare, provisionally, with a review date, and never a number derived from
data. Reader engagement may decide which business-development theme takes the
next slot; it never decides how many slots there are. Until you set one, the
cap is `unknown`, and no stage treats business development as unlimited: a
stage proposing topics counts the recent business-development pieces and says
so before offering another.
