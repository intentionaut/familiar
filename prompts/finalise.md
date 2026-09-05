# Stage: finalise

The piece is written and edited. This is where it gets its name and its way in.
Three decisions, in order: title and framing, then the subject line, then how it
will be found. They come last on purpose. A title chosen early is a guess; a
title chosen now summarises the whole journey of positioning and crafting.

Runs after `line-edit`, before `repurpose` and `social`. Those stages need a
settled title to point at.

## Setup

1. Read the piece's `draft.md`, `notes.md` and `outline.md`, and the reports in
   `edits/`. Read the whole finished piece before proposing anything.
2. Read knowledge/positioning.md, knowledge/voice-guide.md, knowledge/links.md.
3. If the writer keeps SEO notes of their own, read those and work from them.
   Look first for a filled `## Search` section at the foot of
   `knowledge/themes.md`, and read that section only; nothing else in that
   file is this stage's business. Then look for a file named for search or SEO
   in the knowledge folder, and in a vault, in the publication's own resources. Their practice outranks anything
   generic in this prompt. If there are none, say so once and use section 3.

**Scope:** if `$ARGUMENTS` names one of the three jobs ("finalise the title",
"just the SEO"), do that one and leave the rest. Say which you did.

## 1. Title and framing

The last creative act, not an afterthought.

- Read the finished piece and say in one sentence what it actually argues. Not
  what the outline said it would argue. Pieces move.
- **Propose three titles, drawn from the piece's own strongest lines**, never
  invented from outside it. Quote where each comes from.
- Each carries `Buys:` and `Costs:`, one line each. Open rate, memorability,
  precision and how it reads forwarded to someone else are the axes that matter.
- Name the framing the title implies, and check it against what the piece does.
  A title that flatters the ending over the argument is the common failure. Say
  so when you see it.
- Propose a subtitle in one sentence, and two alternates for the title.

**The trap to name out loud:** the working title from the draft has had the
whole editing pass to become familiar. Familiar is not the same as right. Treat
it as one candidate among the three, with no advantage.

On the writer's pick, set `title_settled: true` in the frontmatter and record
`Chosen` and `Because` in the context log.

## 2. The subject line

A separate decision, and it is not the title.

A title labels the argument for someone who is already reading. A subject line
earns the open from someone who is not. The same words rarely do both.

Propose two, one descriptive and one curiosity-led, each with what it costs.
Say plainly that this is a guess until there is open-rate evidence, and note in
the context log which kind was chosen, so a pattern can be seen across issues.

## 3. How it will be found

Only for pieces that get a web version. Skip it for email-only, and say you did.

Work from the writer's own SEO notes when they exist. When they do not:

- **Slug.** Short, readable, stable. It is a permanent address, so it outlives
  the title and must not be regenerated later.
- **Meta description.** One sentence, written for a person deciding whether to
  click, not stuffed. Around 150 characters.
- **Headings.** The finished piece already has them. Check they read as a
  sensible outline on their own, because that is how a search engine and a
  skimming reader both use them.
- **Internal links.** Two or three to the writer's own related pieces, in the
  body where they are genuinely useful. Name the pieces you mean.
- **One target.** The single thing a person might plausibly search that this
  piece deserves to answer. If there is not one, say so rather than inventing
  it. Most good essays do not have one and are not worse for it.

**Never trade the writing for the ranking.** If a recommendation would change a
sentence the writer chose, it is a proposal for them to reject, not a fix.

**Options.** Where this stage reaches a choice with more than one defensible
answer, write it as an options block per AGENTS.md, "Offering options, and
recording the pick": fully written alternatives, `Buys:` and `Costs:` on each,
and `Chosen` with `Because` once the writer picks. Never only in conversation.

**Cuts.** Anything substantial removed at this stage goes to `cuts.md` per
AGENTS.md, "The cutting room", with a `Flag:` of dead, reusable or blocked. A
cut section or a dropped set of evidence is material, not waste.

## Exit

Write the decisions into `draft.md` frontmatter (`title`, `subtitle`,
`alternates`, `title_settled: true`, `slug`, `description`) and everything
proposed but not taken into the piece as an options block.

Report in one line what is settled and what is still open.

Then stop. `repurpose` and `social` are next, only when the writer asks.

- **Context log:** append to the piece's own `SESSION-CONTEXT.md` per
  knowledge/context-log.md, including `Chosen` and `Because` for the title.
