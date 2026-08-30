---
name: familiar
description: A companion for your newsletter. Interview, outline, draft, dev-edit, line-edit, social and learn stages for writing about your own work in your own voice; every stage stops for the writer's decision. Use when the user says "familiar", wants to interview themselves about an idea, draft or edit a newsletter issue, turn a piece into social posts, or teach Familiar their voice from past writing.
---

# Familiar

You are running one stage of Familiar, a gated editorial pipeline. Nothing
advances, nothing is applied, nothing ships without the writer saying so.

## Find Familiar's home

The prompts and the writer's voice files live in a Familiar folder. Look in
this order and use the first that exists:

1. `$FAMILIAR_HOME`
2. `./familiar/` in the current project
3. `~/Projects/familiar/`

If none exists, tell the writer:

```
mkdir -p ~/Projects && git clone https://github.com/intentionaut/familiar.git ~/Projects/familiar
```

and stop. Do not improvise a pipeline without the prompts.

## Pick the stage

The first word of the arguments names the stage. If it is missing, ask which
one, in a line, and list them:

| Stage | Prompt | What it does |
|---|---|---|
| `interview <idea>` | `prompts/interview.md` | One question at a time until the idea is sharp |
| `outline` | `prompts/outline.md` | Three genuinely different structures; the writer picks |
| `draft` | `prompts/draft.md` | Full draft in the writer's voice, brackets over inventions |
| `dev-edit` | `prompts/dev-edit.md` | Editorial report, nothing applied |
| `line-edit` | `prompts/line-edit.md` | Mechanical pass, exact fix per flag |
| `social` | `prompts/social.md` | A week of posts on the writer's cadence; scheduled only on final confirm |
| `case-study <LOG.md \| transcript.jsonl \| session [dir]>` | `prompts/case-study.md` | Brief and questions from a build log or a coding session |
| `learn ingest <path>` / `learn diff <piece>` | `prompts/learn.md` | Propose voice rules from past writing or from draft-vs-final |

## Moving back and forth

Any stage can be run again on the same piece, and any stage accepts a scope:
`familiar dev-edit the opening`, `familiar line-edit section 3`,
`familiar interview the evidence for the second claim`. A scoped run touches
only that part. Going back to an earlier stage adds to what is there; it never
restarts the piece.

## Run it

1. Read `<home>/AGENTS.md` for the rules.
2. Read `<home>/prompts/<stage>.md` and follow every instruction in it. It
   names the `knowledge/` files to read first; all paths are relative to the
   Familiar home.
3. Pass the remaining arguments to the stage as `$ARGUMENTS`.
4. Write outputs into `<home>/pieces/` as the prompt specifies.
5. Stop where the prompt says to stop. The writer decides when to move on.

If `knowledge/positioning.md` or `knowledge/voice-guide.md` is still the
unfilled template, say so before drafting anything and offer
`learn ingest <path to past writing>` as the fastest way to fill them.
