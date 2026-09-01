# Stage: draft

Write the piece. Your job is 80 percent of a draft they will make excellent,
in their voice, not in model voice.

## Setup

1. Read the piece's outline.md (chosen structure marked) and notes.md.
2. Read knowledge/voice-guide.md, knowledge/style-rules.md, knowledge/positioning.md, knowledge/examples/canonical.md. Internalise them before typing. If `Language:` in positioning.md is not English, read `knowledge/languages/<code>.md` too and write in that language's conventions, not English ones.
3. Target length: 800 to 1200 words for a standard piece; deep dives up to 2500 only if outline says so.

**Scope:** if `$ARGUMENTS` names a section, heading or paragraph, draft that part only and leave everything else in `draft.md` untouched. Say which part you worked on. If `draft.md` already has content and no scope is given, ask before replacing it: replace, add to, or write a numbered variant beside it (`draft-2.md`).

## Before writing: voice first, then ask, then invent only with permission

1. **Prior work first.** If `knowledge/voice-guide.md` or `examples/canonical.md`
   is still the template, do not draft. Say so, and offer to run
   `learn ingest <the writer's published work>` now; in a Dex vault, look for
   the writer's own published pieces before asking where they are.
2. **Ask where possible.** For every gap the outline flagged, and for any
   scene, number or quote the notes do not contain, ask the writer before
   drafting if they are present. Batch these into one short list so it is one
   interruption, not ten.
3. **Invent only with permission.** If the writer says "draft from what you
   have", you may write connective prose, but every specific you did not get
   from notes.md, the outline, or the writer's own words stays a bracket:
   `[NEEDS SOURCE: ...]` for a fact, `[ASK THE WRITER: ...]` for a scene or a
   feeling. Never fill one in with something plausible.

## Non-negotiables while writing

- Follow voice-guide.md exactly: short declaratives, no em dashes, British spelling, no banned words, concrete nouns.
- Never invent evidence. Any claim without backing becomes `[NEEDS SOURCE: what and why]` inline. Better a bracket than a fabrication.
- Quotes only exist if they're in notes.md verbatim. Otherwise bracket them too.
- Coined terms italicised on first use, defined immediately.
- Headers sound like a person (see canonical examples). Sentence case.
- End with the invitation to reply, phrased as a real question they would want answered.
- **Working title only, and say so.** Include a headline, two alternates and a
  one-sentence subtitle, with `title_settled: false` in the frontmatter. At
  draft stage the title is a label for the argument, not a hook for a reader.
  Write it plainly: what the piece contends, in the writer's own words from
  notes.md. A crafted title here is worse than a dull one, because every later
  stage will quietly edit towards it and the piece drifts to serve a headline
  that was chosen before the argument had settled. The hook comes at `finalise`,
  once the piece is written and edited and there is a finished journey to name. No em dashes anywhere.

**Options.** Where this stage reaches a choice with more than one defensible
answer, write it as an options block per AGENTS.md, "Offering options, and
recording the pick": fully written alternatives, `Buys:` and `Costs:` on each,
and `Chosen` with `Because` once the writer picks. Never only in conversation.

**Cuts.** Anything substantial removed at this stage goes to `cuts.md` per
AGENTS.md, "The cutting room", with a `Flag:` of dead, reusable or blocked. A
cut section or a dropped set of evidence is material, not waste.

## Exit

Write the full piece to `draft.md` in the piece folder, frontmatter first:

```yaml
---
title: "..."
subtitle: "..."
alternates: ["...", "..."]
title_settled: false
date: YYYY-MM-DD
---
```

After writing, run a quick self-check against knowledge/style-rules.md and fix
mechanical violations silently (em dashes, spelling, banned words) before saving.
Report word count, reading ease, and list every [NEEDS ...] bracket left in.
Then stop. They rewrite; the next stage is dev-edit only when they ask.

- **Context log:** append to the piece's own `SESSION-CONTEXT.md` per
  knowledge/context-log.md (status, files touched, what changed, the decision
  gate for the writer, next stage). Terse; this is what makes the article easy to
  resume later.
