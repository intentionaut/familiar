---
name: familiar
description: "Write and edit a newsletter issue about your own work with Familiar: bring in a draft you already wrote and find the spine it has, interview yourself one question at a time, get three structures, a draft in your voice with brackets over anything unsourced, then editor's reports you work through yourself, a week of social posts on your cadence, a publish stage that schedules the ones you approved, and a learn stage that turns your edits into voice rules. Use when the user says 'familiar', 'familiar-custom', 'I already have a draft', 'read my draft', 'help me improve this piece I wrote', 'interview me about', 'draft my newsletter', 'dev edit this piece', 'line edit', 'turn this issue into posts', 'schedule these posts', or 'learn my voice'. Not for a product requirements doc or feature spec; use `product-brief`. Not for a decision record; use `decision-log`. Not for reflecting on how the week felt; use `weekly-reflection`."
---

# Familiar in Dex

This is the **Dex host profile** for Familiar. Familiar is a standalone tool; it
does not need Dex and never assumes it. This file says where things live in a
vault and what extra a vault can offer. Everything else, every stage and every
gate, is defined once in Familiar itself.

**Read `{{FAMILIAR_HOME}}/skills/familiar/SKILL.md` for how the pipeline works,
then `{{FAMILIAR_HOME}}/AGENTS.md` for the rules, then the stage's prompt.** Do
not restate stage behaviour here; if the two ever disagree, Familiar is right.

## Execution mode

Run inline in the current conversation by default, so this work can see what the
user has already discussed, decided, or settled this session. Do not fork merely
because this skill was selected. Only run in the background when the user
explicitly asks for a background run, or the host has already obtained a
specific background-work approval for this run.

## Paths this host declares

- **Familiar home:** `{{FAMILIAR_HOME}}`
- **Config:** `06-Resources/Familiar/knowledge/`: positioning, voice guide,
  style rules, social schedule, links, reflection, models, examples, languages.
  This is the `knowledge/` any prompt refers to.
- **Pieces:** `04-Projects/Writing/YYYY-MM-DD-slug/`. Wherever a prompt says
  the piece folder, it means here.
- **Proposals from `learn`:** `06-Resources/Familiar/proposals/`.

An explicit `$FAMILIAR_CONFIG` or `$FAMILIAR_PIECES` beats these.

## Capabilities this host offers

Use each one only where a prompt asks for that capability. Every one of them is
optional: if the tool is missing or fails, say the lookup could not be done and
carry on. Never treat an absent capability as a blocked stage.

| Capability | In Dex |
|---|---|
| `people` | `lookup_person` (Work MCP) and the company index. Link the person or company page when a piece names them. |
| `search` | The `query` tool (QMD) if available, otherwise grep across `00-Inbox`, `04-Projects`, `05-Areas`. Look for evidence a prompt marks "needs finding" before asking the writer for it. Offer what you found; they decide if it counts. |
| `tasks` | `create_task`, with the pillar inferred per the vault's `CLAUDE.md`. Only for an open decision left at a gate, and only after confirming. |
| `corpus` | `learn ingest` can read past writing from `06-Resources/Published/` or a `05-Areas/` folder of past work. |

"Could not be searched" and "found nothing" are different sentences. Never
substitute one for the other.

## Dex house rules

- Dex names custom skills by their folder, so this installs as
  `familiar-custom` and the commands carry that suffix:
  `/familiar-custom interview <idea>`, `/familiar-custom draft`. The suffix is
  what keeps it safe across Dex updates.
- The board reads the vault's pieces folder:
  `python3 {{FAMILIAR_HOME}}/scripts/board.py --pieces <vault>/04-Projects/Writing --open`
- Context logs go in the piece folder's own `SESSION-CONTEXT.md`, per
  `knowledge/context-log.md`, not in the vault root.

## Honesty

If the config files are still unfilled templates, say so before drafting
anything and offer `learn ingest <path to past writing>` as the fastest way to
fill them. Do not write a piece in a voice Familiar has not been taught.
