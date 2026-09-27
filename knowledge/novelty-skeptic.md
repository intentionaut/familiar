# Novelty skeptic

An editorial check inside Familiar, not another agent, a publishing gate or a
claim that any work is original. Run twice: at the post-interview thesis gate
before outline (`prompts/interview.md`) and on the concrete draft during each
`dev-edit` round (`prompts/dev-edit.md`). Test the claim, not the writer's
competence. Assume a gap in exposure before assuming innovation.

## Evidence boundary

Read the piece's `notes.md`, draft, positioning and linked evidence. First name
the actual discourse the piece joins, its audience and the level of claim
(product leadership, organisational practice, technical mechanism, or another
field), rather than treating a matching word as a matching idea. Compare a
claimed novelty to sources the writer has reviewed and linked to the piece,
with exact source URLs, dates, authors and passages. If the writer uses a
research tool, it can supply searches, citations and claim flags; Familiar
alone makes the editorial decision. Never treat a claim flag, an unreviewed
search result or a missing hit as a verdict. If the antecedent or search
coverage is inadequate, name one targeted research question for the writer or
their research tool and leave the claim provisional. Check both named terms and older nearby practices, including people outside
the writer's usual field. Technical prior art may constrain a technical-first
claim but does not by itself refute a contribution to product or organisational
discourse. Only treat an antecedent as answering the claim when it addresses
the same proposition at the same level; otherwise note it as an adjacent echo.
Say which discourse was searched, what the search covered, what it did not,
and whether evidence is first-hand. An antecedent named from general knowledge,
with no source checked, is marked `unverified` and never given an invented
URL. A classification that rests on it is provisional until the source is
checked.

## Classify each implied novelty

Check explicit words like "new", "first", "no one", "invented", and a coined
mechanism, as well as an unstated originality claim in the argument. Choose:

1. **Existing practice / likely exposure gap** (default when an antecedent
   fits): name the closest established proposition or practice *in the discourse
   the piece joins*, who used it and the exact source; state the writer's situated application without claiming
   invention.
2. **Useful reframe**: name the antecedent, then the precise shift in use,
   setting, audience or participation that extends its discussion. Do not
   smuggle an invention claim into a reframe. This is a positive outcome.
3. **Candidate genuine novelty**: identify the smallest bounded difference
   against the closest known antecedents in that discourse, search terms, sources, disciplines
   and time range checked, and remaining blind spots. Provisional, not a
   certificate of being first; the writer decides whether to stake it.
4. **Insufficient evidence** (default when antecedent or search is weak):
   bracket the unsupported claim and name one targeted research question.

Never classify "genuine novelty" just because the writer found an idea
surprising or a search came up empty. A claim can move classification after
more evidence. Avoid a global originality verdict about the whole piece.

## Output at each gate

At interview, put a concise classification and closest source (or search gap)
under `notes.md` Open questions. Leave the writer's thesis alone and ask for
their verdict before carrying a novelty assertion into an outline.

At `dev-edit`, use numbered findings in the cumulative
`edits/dev-edit-report.md`, with round-prefixed IDs after Round 1. Each has:

```markdown
### R2-3a. Novelty claim: <short label>
Quoted claim: "<verbatim draft passage>" (<section/paragraph>)
Discourse compared: <the conversation and audience the claim is entering>
Closest antecedent: <person/practice at the same level, exact URL and what the source supports;
  or "not established" with searches checked>
Classification: Existing practice / Useful reframe / Candidate genuine novelty / Insufficient evidence
Contribution this piece can defend: <bounded difference or situated use>
Proposed replacement: "<a complete line in the writer's voice, or [NEEDS SOURCE: ...]>"
Open question: <one research or writer decision; name search limits>
Decision gate: Keep as reframe / Research more / Make a bounded novelty claim / Cut
Status: Open (the writer accepts, rejects or revises; no auto-edit)
```

Only offer options the evidence supports; a candidate novelty cannot be
promoted just by choosing a menu entry. Quote and locate the actual claim, not
a paraphrase. If a prior round resolved a claim, mark it resolved in the next
round's reconciliation rather than opening the same finding again. If the
writer rejects a finding, retain that verdict. Never silently edit the draft,
the writer's sources, or the report's earlier rounds. Familiar neither publishes
nor judges the writer's worth.
