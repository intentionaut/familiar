# Themes

What you are trying to be known for. This is the spine `harvest` maps evidence
onto, and it is declared rather than worked out from your logs.

Before this file existed, harvest inferred a set of themes on every run. The
same fortnight of work produced seven themes, then four, then nine, and the
movement came from re-deriving the question rather than from the work changing.
A theme you can rely on is one you wrote down.

## How stages use this file

- `harvest` maps every finding onto a theme `id`. Findings that fit none go to
  `knowledge/proposals/` as candidate themes. It never edits this file.
- `harvest` reports **coverage**: which themes have fresh evidence, and which
  you declared and nothing you built has touched. The second is the useful line.
- `interview` reads the theme a piece serves and its evidence bar.
- `finalise` may read the `## Search` section at the foot, and only when it is
  filled. No other stage reads that section; `tests/test_structure.py` holds
  `draft`, `dev-edit` and `line-edit` to it.

## Rules

**The `id` never changes.** Rename the theme freely; the id is what makes a
theme strengthening across harvests distinguishable from a theme reworded.
Retire an id, never reuse it.

**Every value carries its source**, per AGENTS.md, "Declared before inferred":
`declared`, `inferred (unconfirmed)` with its evidence beside it, or `unknown`.
A stage that wants a value it does not have asks for it or reports it as
unknown. It does not pick a sensible one.

**`unknown` is a legitimate resting state.** A theme with an unknown audience
still works for everything except the one line that needed it. Do not let an
empty field block the file.

**Audience is declared once, in `positioning.md`, not per theme.** Segments are
yours to name: you choose the ids, how many there are, and what each means, and
nothing here assumes a buyer, a peer or a reader of any particular kind. A theme
names the segment ids it is `Written for:` and restates nothing. Repeating an
audience per theme is how a declared file ends up empty: the fill cost is what
kills it.

**A theme written for two or three segments is normal. One written for all of
them is a theme that has not been narrowed.**

**`Job:` is what the theme is for.** It decides three things: how the outcome is
read, which authority rules apply, and how often the theme may run.

- **`thought-leadership`** builds standing with the people who read. Judged by
  replies and shares. Your `voice-guide.md` authority rules apply in full.
- **`business-development`** exists to attract clients. Judged by the
  conversations that follow. Whatever room your `voice-guide.md` gives a
  credential, this is the job that may use it, and no other. **And it is
  capped**, in `positioning.md`, because a letter that runs business
  development too often stops being a letter.

**The cap is the price of the relaxation.** Take one without the other and the
publication turns into a brochure. A stage proposing topics counts how many
business-development pieces have gone out recently and stops offering more once
the cap is reached, whatever the evidence says.

**`Written for:` is who the piece must also work for, never who it addresses.**
A theme written for the people who might hire you becomes a pitch the moment a
stage forgets this. `voice-guide.md`, "Authority: show, don't tell", is the
countermeasure, and the reader addressed is still the one `positioning.md`
names.

**How many themes is not settled.** It follows from your cadence and how long a
theme stays useful, and neither has been worked out. Fewer themes compound
faster at a fortnightly cadence.

## Themes

<!-- Copy the block per theme. Delete the bracketed prompts as you fill them. -->

### T1. [short name, the way you would say it out loud]

- **id:** `[stable-slug-you-will-not-change]`
- **Position:** [one sentence, in your words, that a piece could argue]
  `source: declared`
- **Written for:** [segment ids from positioning.md this theme is meant to
  move. Two or three, not all of them] `source: declared`
- **Job:** [thought-leadership | business-development] `source: declared`
- **Intersection:** [two or more of design, product, data, AI, per positioning.md]
  `source: declared`
- **Status:** [building | owned | retiring]
- **Evidence bar:** [what a piece on this has to stand on to be credible from
  you rather than from anyone]
- **Pieces shipped:** [slug, date. One line each, appended as they send]

## Retired

<!-- Themes no longer being built on. Keep the id here so it is never reused. -->

## Search

Kept apart on purpose. Nothing between `outline` and `line-edit` reads this
section, and a test holds them to it, so a query can never reach a sentence.
`finalise` reads it when it is filled, as the writer's own SEO notes. Leave it
empty if search is not something you work on; the themes above lose nothing.

<!-- One block per theme id, only for themes you want to be found for. -->

- **`[theme-id]`**
  - Target queries: [one per line] `source: [declared | unknown]`
  - Already ranks for: [from Search Console, with the date you last looked]
    `source: [where it came from, with a date | unknown]`
