# Prompt: plan draft management and CMS integrations for Familiar

You are planning two additions to Familiar, an open source, gated editorial
pipeline for writing about your own work. Read the repo before you plan
anything; do not design from this description alone.

## What Familiar is

- Repo: `~/Projects/familiar` (github.com/intentionaut/familiar). Read
  `README.md`, `AGENTS.md`, `CHANGELOG.md`, every file in `prompts/`, the
  `knowledge/` templates, `skills/familiar/SKILL.md`, and `dex/familiar/SKILL.md`.
- Seven stages, each a plain markdown prompt with no tool-specific syntax:
  case-study, interview, outline, draft, dev-edit, line-edit, social, learn.
  Every stage ends at a decision the writer makes. Nothing advances, nothing is
  applied, nothing ships without the writer saying so.
- Each piece is a folder: `pieces/YYYY-MM-DD-slug/` holding `notes.md`,
  `outline.md`, `draft.md`, `edits/*.md`, `social.md`, and a per-piece
  `SESSION-CONTEXT.md` that every stage appends to on exit (status, files
  touched, the open decision, next stage). Inside Dex the same folders live at
  `04-Projects/Writing/` in the user's vault.
- Non-negotiables, which any plan must keep: never rewrite the writer's file
  in place (edits are reports); never invent a fact, quote or number (leave a
  bracket); never guess a voice not shown; never overwrite a file with content
  without asking (replace / add to / numbered variant); any stage can be re-run
  on a piece and adds to what is there; any stage can be scoped to one section.
- The writer's voice files (`knowledge/`) and pieces are theirs, never in the
  public repo. Keys and tokens never go in any file the repo tracks.
- House style for everything you write, including the plan: plain language,
  no em dashes, no hype vocabulary, no "not X but Y" framing.

## The two problems

**1. Drafts at a glance.** A writer with several pieces in flight has no way to
see them together. Today the only view is a folder listing and per-piece
`SESSION-CONTEXT.md` files. Wanted: one command (working name `familiar
status`) that shows every piece, the stage each is at, the open decision
waiting on the writer, when it was last touched, and, once integrations exist,
where the current draft lives (local, or a CMS draft with a link). It should
also make resuming a piece one step.

**2. The CMS as the draft store.** Writers already keep drafts in Substack,
beehiiv or Ghost. Familiar should be able to work against the draft in the
CMS instead of a local `draft.md`: pull it, run a stage (dev-edit, line-edit,
a scoped rework, even going back to the interview), and push the result back
as a new draft version, so the writer never has to manage two copies. The
gates stay exactly as they are; the CMS is a place the file lives, not a
reason to skip a decision.

## What to find out first

Do not assume any of these APIs. Check the current documentation and say
what you found, with dates:

- **Ghost**: the Admin API (posts, drafts, mobiledoc/lexical formats, JWT from
  an Admin API key). Likely the most complete.
- **beehiiv**: the public API. Establish whether it can create and update
  draft posts, or only read published ones and manage subscribers. If it
  cannot write drafts, say so and plan around it.
- **Substack**: there is no official public API. Establish what is honestly
  possible (export/import, an unofficial API, email-to-draft, clipboard
  round-trip) and what the risk of each is. Do not plan on something that
  could break next month without saying it could.

Also check how each platform represents a draft (HTML, Markdown, a JSON
document format), because the round-trip from `draft.md` and back has to
preserve the writer's formatting and must not drop anything. Lost content is
the worst failure this feature could have.

## What the plan must contain

1. **A status model.** What "the stage a piece is at" means when the truth is
   spread across files, and how `familiar status` derives it (from
   `SESSION-CONTEXT.md`, from which files exist, or both). Include what the
   command prints, in a fixed-width example, and how it behaves with zero
   pieces, one piece, and twenty.
2. **A draft-location model.** How a piece records where its current draft
   lives (a small frontmatter block or a `draft.json`), how local and remote
   stay honest about which is newer, and what happens on conflict. Propose
   the simplest thing that cannot silently lose a version.
3. **An integration contract.** One interface the three adapters implement
   (auth, list drafts, pull a draft, push a new version, link to the draft in
   the CMS) so stages never know which CMS they are talking to. Say where
   credentials live (system keychain or an env var read at run time, never a
   tracked file) and how a writer connects a platform in under two minutes.
4. **Per-platform adapters**, in the order you would build them given what
   the APIs allow, with the round-trip format for each and the specific
   things that could be lost (footnotes, embeds, images, subtitles, buttons).
5. **How the stages change.** Which prompts need a line added and what the
   line is. Keep the prompts tool-agnostic: the adapter does the fetching, the
   prompt reads a file. The Dex skill (`dex/familiar/SKILL.md`) and the
   skills entry point (`skills/familiar/SKILL.md`) both need the same
   additions.
6. **Phases.** Phase one should be shippable in a weekend by one person and
   still be useful without any CMS (status alone is worth having). Say what
   each phase proves and what would make you stop.
7. **Risks and refusals.** What this feature must never do (publish, schedule,
   change a live post, delete a draft, overwrite a newer remote version) and
   how each is prevented rather than discouraged.
8. **Changelog entries** in Familiar's house style (a headline in plain words,
   then "What this gives you:" bullets), one per phase, so the writing about
   the feature exists before the feature does.

## How to work

- Read first, then plan. Quote the file and line when you rely on something
  in the repo.
- Where two designs are close, pick one and say why in a sentence. Do not
  list options you are not recommending.
- Where something depends on an API you could not verify, mark it
  `[NEEDS SOURCE: ...]` in the plan and keep going. Do not build the plan on
  a guess.
- Deliver the plan as one markdown file at `docs/plans/cms-and-drafts.md` in
  the repo, and finish with the three questions the writer has to answer
  before phase one starts.
