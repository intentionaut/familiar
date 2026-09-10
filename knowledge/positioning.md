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

**This is the one thing here that needs no history**, and it is worth doing on
your first evening. Every other kind of context accumulates: projects read,
sessions logged, pieces sent. You already know who you are writing for, and it
is what sorts everything Familiar finds from here on. `harvest` organises what
it gives you by this.

[your reader]

### Segments

The natural second step, once one reader is not enough. Skip it while one is:
nothing breaks, and stages frame for the reader above. It stops being optional
the moment you have two readers who want different things from the same piece,
because that is the point at which one description cannot serve both.

`knowledge/themes.md` points at these by id, and `harvest` groups what it finds
by them.

Segments are yours: you choose the ids, how many there are, and what each one
means. One line per segment, with the id in backticks, who they are in your own
words, and a `Reads:` line saying where you actually see them and how you know
the number. `Reads:` is evidence about a channel and may be far larger than the
people a theme is written for. Leave any value `unknown` rather than guess, and
give every value a `source:` as the rest of this file does.

**Two more per segment, and they are what make this section do work**: what
that segment wants from a piece, and what a win looks like. Not all of your
readers have the same job. Somebody who forwards your work to a stranger needs
one sentence that stands without you; somebody deciding whether to hire you
needs evidence of judgement under a constraint they can see was real; somebody
building the same kind of thing needs a method with the reasoning under it, not
the method alone.

Write them in your own words, one line each:

    - `id`: who they are. Wants: [what they want from a piece].
      Win: [what a win looks like]. Reads: [where you see them]. source: declared

The win is the useful half, because it is a test rather than a description. A
piece aimed at a segment whose win is a forward has failed if it needs you
explained first, however good it is. Stages apply it that way.

Leave `Wants` and `Win` `unknown` if you have not decided. A stage reads an
unknown as "frame for the one reader above" and says so, rather than inventing
a job for a segment you have not thought about.

## Voice in brief

The long version is `voice-guide.md`. Three or four lines here for stages that
only need the gist:

- [warm / dry / direct / formal]
- [what you never do]
- [what you always do]

## Later, if you keep themes

Nothing below is needed to start, to interview or to draft.

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
