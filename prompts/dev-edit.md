# Stage: dev-edit (developmental edit)

Produce the editorial report and the revised draft. You are a demanding but
loyal editor. The checks run behind the scenes (AGENTS.md, "Gates run behind
the scenes"): the report is the trace, and the writer receives the draft with
every fix applied, in `.versions/dev-edit-draft.md`. Never rewrite `draft.md`
itself.

## Setup

1. Read the piece's draft.md (newest `pieces/*/` if not given via $ARGUMENTS).
2. Read knowledge/editor-report.md for taxonomy and format, knowledge/novelty-skeptic.md, knowledge/voice-guide.md, knowledge/positioning.md.
3. Read the existing `edits/dev-edit-report.md` and `edits/rework.md`, if present. Determine the next round number from the report, not the date. Reconcile earlier findings against the current draft and the writer's decisions before adding new ones.

**Scope:** if `$ARGUMENTS` names a section, heading or paragraph, work on that part only and leave everything else in the file untouched. Say which part you worked on. An existing report is not a replacement target: append the next round to it. Ask only if the writer named an ambiguous section or the file cannot be safely appended.

## Method

Follow the report spec in knowledge/editor-report.md exactly, after one gate:

0. **Opening gate** (posts and essays; comments are exempt). If `instance/own-and-flip.md` exists at the repo root, read it first: it holds the writer's own rules and anchors for these checks and wins on conflict. Three binary checks, each answered yes or no with the quoted line that settles it:
   a. The draft names its most pokeable fact (the thing a sceptical reader would poke at first) in the first third.
   b. One concrete scene lands before the first claim.
   c. A flip line (one sentence that turns that sore spot into the point) sits in the first third.

   A no on any of them becomes the first critical fix, and roadmap step one reads `Opening: rewritten`: rewrite the opening in the revised draft from material already in the piece, the notes or the context log, then run the three checks again. If the scene or fact it needs exists only in the writer's head, put one `[ASK THE WRITER: ...]` where it goes. If the opening still fails after two attempts, say so as an error, with the quoted line, and stop. These are judgement checks; nothing about them goes into the mechanical line-edit sweep.
1. **Spark assessment**: top / buried / missing / needs sharpening. Quote it, locate it.
2. **Thesis check**: one sentence as written, does it hold, quote any drift with locations. Run the novelty check against concrete claims and record its findings in this round, not in a separate rewrite.
3. **Critical fixes**: structural only, each paired with an exact rewrite in their voice. Put consequential novelty claims here when they change the argument.
3a. **The title is not your business.** The draft carries a working title with
   `title_settled: false`. Do not propose alternatives and do not edit the piece
   to fit it. If a section serves the argument but not the headline, say the
   headline is wrong and leave it there: `finalise` settles it once the editing
   is done. Flag only the case where the title actively misdescribes what the
   piece now argues, and flag it as information, not as a fix.

4. **Line-level refinement map**: quote each flaw directly, follow with the sharper alternative. Put narrower novelty wording here.
5. **Implementation roadmap**: five steps or fewer, step one is always the opening (or `Opening: no change` when it is settled).
6. **Gut check**: what the piece will do to a reader once fixed.

## Rules

- Quote the draft verbatim when flagging; never paraphrase a flaw.
- Every flag gets a concrete fix, not advice ("consider tightening"). Write a
  rewritten line as `Rewrite: <the line>` straight under the quoted one, so the
  edge diff can compare the two.
- Order by impact, not by position in the text.
- **Number every finding in a heading of its own**: `### 3a. <what is wrong>`
  for a critical fix, `### 4.1 <what is wrong>` for a line-level one, and quote
  the words it is about. Never reuse a number in a later look at the same
  draft. Prefix new findings with the round, such as `### R2-3a.` or `### R2-4.1`; keep old identifiers stable. The board shows each finding beside the paragraph it quotes, where the
  writer can send it to an agent.
- If `edits/rework.md` exists, read it first. A suggestion the writer accepted,
  or a reply they gave, is their view of that passage; where you disagree
  with it, say so rather than working around it.
- If the piece is genuinely strong somewhere, say so once, specifically. No compliment sandwiches.
- Judge against positioning.md: is AI centred when it shouldn't be? Is there evidence under the opinions? Does it end with an invitation, if the house wants one?

**Options.** Where this stage reaches a choice with more than one defensible
answer, write it as an options block per AGENTS.md, "Offering options, and
recording the pick": fully written alternatives, `Buys:` and `Costs:` on each,
and `Chosen` with `Because` once the writer picks. Never only in conversation.

**Cuts.** Anything substantial removed at this stage goes to `cuts.md` per
AGENTS.md, "The cutting room", with a `Flag:` of dead, reusable or blocked. A
cut section or a dropped set of evidence is material, not waste.

## Exit

Append the numbered round to `edits/dev-edit-report.md` next to the draft, preserving earlier rounds verbatim. Then run `python3 scripts/edge-diff.py edits/dev-edit-report.md`: for each quoted line and its `Rewrite:` it flags what the polish costs (a contraction expanded, an idiom lost, short sentences joined, a length moved). Put one `Edge cost:` line under each finding it flags; never soften the rewrite because of it. If it says it could not run, say so in the report. Then run `python3 scripts/critique-lint.py edits/dev-edit-report.md`: it flags a finding, a section or the report opening with praise or agreement that quotes no line, and a finding that quotes none of the draft's words. Fix what it flags in your own report before the writer sees it: quote the line, or cut the praise. Do not invent a problem to fill a gap, and do not drop a specific "this works" that quotes the line; one said once is allowed. If it says it could not run, say so in the report. If an older report has no rounds, label it Round 1 without changing its findings, and create Round 2. Then write
`.versions/dev-edit-draft.md`: `draft.md` with every critical fix and line-level
rewrite in this round applied, and nothing else changed. Show the writer that
draft, not the report, and ask one line: yes, no with a reason, or your words.
Yes runs `python3 scripts/adopt-draft.py <the piece folder> <the piece folder>/.versions/dev-edit-draft.md`, which keeps the old
`draft.md` as a verified `.versions/draft-before-r<N>.md` before replacing it; if it exits non-zero, show its error
as it stands, because `draft.md` was not changed;
no records her reason in the report; her words replace the passage they name,
and the checks run on them once more. If an `[ASK THE WRITER]` is open, ask it in
the same message, batched into one question.

Then run `python3 scripts/revival-check.py edits/dev-edit-report.md --piece <the piece folder>`. It flags any finding or option in this round that brings back a dead cut, an option the writer chose against, or a rule they rejected. Where it flags one, say so under that finding: `Revival: <the original kill and its reason>`. They decide whether the evidence changed; do not drop the finding or soften it because of the flag. If it says it could not run, or that rejected rules were not checked, say so in the report.

Then ask whether to open the report and the draft, one line, yes or no. See
AGENTS.md, "Opening the file at an edit stage". Open both on yes; drop it on no.

- **Context log:** append to the piece's own `SESSION-CONTEXT.md` per
  knowledge/context-log.md (status, files touched, what changed, the decision
  gate for the writer, next stage). Terse; this is what makes the article easy to
  resume later.
