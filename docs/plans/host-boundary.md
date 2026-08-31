# Plan: the host boundary

**Status:** proposed, 31 August 2026.
**Instruction it comes from:** Familiar should do more and its host should do
less. Familiar ships a skill that Dex plugs into. Dex stays supported, and it is
never required.

## The rule

**Familiar runs standalone.** Every stage completes with no host, no vault and
no MCP. A host is additive: it can make a stage better informed, and it can
never be the reason a stage works.

Dex is the first host and it stays a first-class one. This plan does not remove
the Dex integration. It removes the assumption that the Dex integration is where
the good version lives.

## What is wrong today

`skills/familiar/SKILL.md` is 88 lines. `dex/familiar/SKILL.md` is 144. The
second is a fork of the first with vault paths written through it, and it is
bigger because it carries real behaviour the generic skill does not have.

Two problems follow.

1. **The generic path is the poor relation.** The stage table, the gate
   discipline and the honesty rules are duplicated in both files, so a fix to
   one is a fix to one. That is the newsroom disease in miniature, and it will
   drift the same way.
2. **Location is baked into logic.** The Dex skill names
   `06-Resources/Familiar/knowledge/` and `04-Projects/Writing/` in the places
   where it should be naming "the config" and "the pieces". A second host cannot
   be added without a third fork.

## The shape

### One canonical skill, hosts that add

`skills/familiar/SKILL.md` becomes the single source for everything that is true
regardless of where Familiar runs: the stage table, what each stage writes, the
gates, config and piece resolution, the honesty rules.

`dex/familiar/SKILL.md` stays a real skill and keeps its own front matter,
triggers and execution notes, because Dex needs those to route to it. What it
stops doing is restating stage semantics. It declares three things and defers
for the rest:

- **Paths.** Where config, pieces and proposals live in a vault.
- **Capabilities.** What this host can do that a bare shell cannot.
- **House rules.** The `-custom` naming requirement, and Dex's own conventions.

### Capabilities, declared and optional

Today the Dex skill instructs the model to call `lookup_person`, `query` and
`create_task`. Those move behind a declaration, and the prompts ask for a
capability rather than for Dex:

| Capability | What a host that has it can do |
|---|---|
| `people` | Resolve a name to a page, and link it |
| `search` | Search the writer's own notes for evidence |
| `tasks` | Turn an open decision at a gate into a tracked task |
| `corpus` | Point `learn ingest` at the writer's past published work |

A prompt says "if the host offers `search`, look for the evidence before asking
the writer for it; otherwise ask." With no host, every one of these is absent
and every stage still finishes. That sentence is the whole boundary.

### Familiar owns resolution

Config location stops being something the installer decides and becomes
something Familiar resolves, in order:

1. `$FAMILIAR_CONFIG`
2. the path the host declares
3. `./knowledge/`
4. `~/.familiar/knowledge/`

Pieces resolve the same way through `$FAMILIAR_PIECES`, the host, then
`<home>/pieces/`. A Dex vault becomes one resolvable location rather than the
location, which is exactly what "plugs in" should mean.

### What moves off the host

- **Stage semantics.** Stated once, in the canonical skill.
- **The tracking-parameter convention.** It currently lives only in the writer's
  vault as a link map. The convention is a Familiar concept and ships as
  `knowledge/links.md`; the writer's own values stay their config.

What legitimately stays in a vault: the filled config values, the pieces, and
the writer's published work. Those are the writer's, not the tool's.

## How it is verified

The claim "Familiar runs standalone" is worth nothing unless it is checked.
Add a smoke check that runs each stage's setup with no host, no `$FAMILIAR_CONFIG`
and template config, and asserts that every stage resolves its inputs and
reaches its first gate. Non-Dex is the default path in the README, and Dex is a
section within it, which is already how the README is arranged.

## Not doing

- A plugin API, a manifest format, or dynamic host discovery. There are two
  hosts: none, and Dex. A markdown table of capabilities is the right size.
- Removing the Dex integration, or making it a second-class citizen. It stays.
