# Stage: draft

Write the piece. Your job is 80 percent of a draft they will make excellent,
in their voice, not in model voice.

## Setup

1. Read the piece's outline.md (chosen structure marked) and notes.md.
2. Read knowledge/voice-guide.md, knowledge/style-rules.md, knowledge/positioning.md, knowledge/examples/canonical.md. Internalise them before typing. If `Language:` in positioning.md is not English, read `knowledge/languages/<code>.md` too and write in that language's conventions, not English ones.
3. Target length: 800 to 1200 words for a standard piece; deep dives up to 2500 only if outline says so.

**Scope:** if `$ARGUMENTS` names a section, heading or paragraph, draft that part only and leave everything else in `draft.md` untouched. Say which part you worked on. If `draft.md` already has content and no scope is given, ask before replacing it: replace, add to, or write a numbered variant beside it (`draft-2.md`).

## Non-negotiables while writing

- Follow voice-guide.md exactly: short declaratives, no em dashes, British spelling, no banned words, concrete nouns.
- Never invent evidence. Any claim without backing becomes `[NEEDS SOURCE: what and why]` inline. Better a bracket than a fabrication.
- Quotes only exist if they're in notes.md verbatim. Otherwise bracket them too.
- Coined terms italicised on first use, defined immediately.
- Headers sound like a person (see canonical examples). Sentence case.
- End with the invitation to reply, phrased as a real question they would want answered.
- Include headline plus two alternates at the top of the file, and a one-sentence subtitle. No em dashes anywhere.

## Exit

Write the full piece to `draft.md` in the piece folder, frontmatter first:

```yaml
---
title: "..."
subtitle: "..."
alternates: ["...", "..."]
date: YYYY-MM-DD
---
```

After writing, run a quick self-check against knowledge/style-rules.md and fix
mechanical violations silently (em dashes, spelling, banned words) before saving.
Report word count, reading ease, and list every [NEEDS ...] bracket left in.
Then stop. They rewrite; the next stage is dev-edit only when they ask.

- **Context log:** append to the project root `SESSION-CONTEXT.md` per
  knowledge/context-log.md (status, files touched, what changed, the decision
  gate for the writer, next stage). Terse; this is what makes the article easy to
  resume later.
