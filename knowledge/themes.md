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

**What a theme is for.** A theme carries positioning for future work, and it
implies the tone and the audience a piece takes. It does not set cadence. How
often anything publishes is a publishing rule in `positioning.md`; that rule may
read a theme's `Job:`, but the theme does not own it, and no stage treats a
theme as a slot in a rota.

**`Job:` implies tone and which authority rules apply.**

- **`thought-leadership`** builds standing with the people who read. Judged by
  replies and shares. Your `voice-guide.md` authority rules apply in full.
- **`business-development`** exists to attract clients. Judged by the
  conversations that follow. Whatever room your `voice-guide.md` gives a
  credential, this is the job that may use it, and no other. **And it is
  capped** by a publishing rule in `positioning.md`, because a letter that runs
  business development too often stops being a letter. The cap belongs to the
  publication, not to the theme.

**The cap is the price of the relaxation.** Take one without the other and the
publication turns into a brochure. A stage proposing topics counts how many
business-development pieces have gone out recently and stops offering more once
the cap is reached, whatever the evidence says.

**`Written for:` is who the piece must also work for, never who it addresses.**
A theme written for the people who might hire you becomes a pitch the moment a
stage forgets this. `voice-guide.md`, "Authority: show, don't tell", is the
countermeasure, and the reader addressed is still the one `positioning.md`
names.

**How many themes is not settled, and it does not follow from your cadence.** A
theme is a position you hold, not a slot you fill, so nine themes at a
fortnightly letter is not "a piece per theme every four months". Declare the
positions you actually hold and let the number be what it is.

## Themes

### T1. The four languages

- **id:** `four-languages`
- **Position:** Product leadership that is fluent in product, data, design,
  and AI. The work moves between all four; it never camps in one.
  `source: declared, 14 September 2026, from the intentionaut site`
- **Written for:** `unknown`
- **Job:** `unknown`
- **Intersection:** product, data, design, AI `source: declared`
- **Status:** building
- **Evidence bar:** `unknown`
- **Pieces shipped:** none yet

Coverage on this theme is read per language: a run of pieces in one language
and silence in the other three is a gap for `harvest` to surface, the same way
an untouched theme is.

### T2. Hiring

- **id:** `hiring`
- **Position:** `unknown` (declared as a topic on
  14 September 2026, one of the leadership themes for an age of change; the
  position is yours to state)
- **Written for:** `unknown`
- **Job:** `unknown`
- **Intersection:** `unknown`
- **Status:** building
- **Evidence bar:** `unknown`
- **Pieces shipped:** none yet

### T3. Org design

- **id:** `org-design`
- **Position:** `unknown` (declared as a topic on
  14 September 2026, one of the leadership themes for an age of change; the
  position is yours to state)
- **Written for:** `unknown`
- **Job:** `unknown`
- **Intersection:** `unknown`
- **Status:** building
- **Evidence bar:** `unknown`
- **Pieces shipped:** none yet

### T4. Acceleration

- **id:** `acceleration`
- **Position:** `unknown` (declared as a topic on
  14 September 2026, one of the leadership themes for an age of change; the
  position is yours to state)
- **Written for:** `unknown`
- **Job:** `unknown`
- **Intersection:** `unknown`
- **Status:** building
- **Evidence bar:** `unknown`
- **Pieces shipped:** none yet

### T5. Accountability

- **id:** `accountability`
- **Position:** `unknown` (declared as a topic on
  14 September 2026, one of the leadership themes for an age of change; the
  position is yours to state)
- **Written for:** `unknown`
- **Job:** `unknown`
- **Intersection:** `unknown`
- **Status:** building
- **Evidence bar:** `unknown`
- **Pieces shipped:** none yet

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

