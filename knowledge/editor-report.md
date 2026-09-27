# Editor report spec

The developmental edit returns a structured report, not a rewritten draft.
It surfaces the decisions, the writer makes them.
Friction is deliberate. Never apply changes automatically.

## Issue taxonomy

The recurring problems drafts wrestle with:

1. **Buried spark**: the line that makes the piece alive is hidden in paragraph six. Find it, name its location, propose the move.
2. **Thesis drift**: the piece argues two things, or the argument shifts halfway. Quote both versions of the thesis, pick or merge.
3. **Abstract without concrete**: a claim with no scene, number, deployment, or named example under it.
4. **Missing stakes**: why should this reader care by Wednesday morning? What happens if they ignore it?
5. **Unsourced claims**: statistics, quotes, or "studies show" with nothing behind them.
6. **Listicle creep**: structure collapsed into parallel bullets when the argument wanted a spine.
7. **Voice drift**: AI tells, marketing speak, metronome rhythm (see style-rules.md).
8. **No invitation**: ends flat instead of turning to the reader.
9. **Intersection missing or abandoned**: notes.md names an intersection (e.g. design × data) but the draft centres a different language, or drifts into AI-only territory. Quote the named intersection from notes.md, then quote where the draft actually lands. If the piece genuinely changed direction, the intersection in notes.md needs updating, not the draft.

10. **Novelty overclaim or useful reframe**: apply `knowledge/novelty-skeptic.md` to claims that imply an invention, a first or a new mechanism, and to reframes that might extend the discussion. Name what was known and what this piece actually adds. Do not present a source-search miss as proof of novelty.

## Repeated developmental edits

Run 1 through n as numbered rounds in the same `edits/dev-edit-report.md`.
Read the full previous report, current draft, `notes.md` and any writer decisions
in `edits/rework.md` before each pass. A new round begins with its date and
scope, the draft version/identifier if available, and a reconciliation table:
previous finding ID, current status (`resolved`, `still open`, `writer rejected`,
`changed scope`, or `cannot verify`), and a one-line citation to the current
passage or writer verdict. A changed sentence alone is not proof that the
underlying issue is fixed. Do not re-flag a resolved or rejected issue; do not
silently erase it. If the same issue remains, refer to the old ID rather than
minting a duplicate. New findings get permanent round-prefixed IDs (`R2-3a`,
`R2-4.1`, etc.) in their own headings. Old reports without round headers count
as Round 1; keep their finding IDs and content intact, then add Round 2. Never
replace or silently consolidate an earlier round. If the current file is not
safe to append to, write a numbered variant and link it to the history.

- A round starts with `## Round N · YYYY-MM-DD`. An older report gets
  `## Round 1 · <its date>` added under its title and nothing else changed.
- Older findings with no ID (bold lines, prose) are cited in the
  reconciliation by section and first words. Never retrofit IDs onto them.
- Options offered inside a finding use `####` headings or bold lines. A `##`
  or `###` heading ends the finding, and the board would cut its body off.

## Report format

For each new round, produce these sections, in order (after its reconciliation):

### 1. Spark assessment
Determine which situation applies: spark is already on top / spark is buried / spark is missing / spark needs sharpening. Quote the best candidate line and say where it currently sits.

### 2. Thesis check
Apply the novelty check to concrete claims using `knowledge/novelty-skeptic.md`; place any numbered findings in section 3 or 4 by impact. State the piece's thesis in one sentence as written. Say whether it holds. If it drifts or doubles, quote each variant with locations. Check the Languages block in notes.md: does the piece serve its named intersection? If the thesis lives in a different language than the one named, flag it.

### 3. Critical fixes
Structural moves only. A working title is not settled here; flag a title that misdescribes the argument as information for finalise, not a fix. A claim without evidence gets flagged with what kind of support would work. Repeated explanations get quoted at each appearance with a keep/cut recommendation. Every fix pairs with an exact rewrite in the writer's voice.

### 4. Line-level refinement map
Walk the draft. Passive voice, undefined jargon, floating abstractions, AI tells: quote directly, follow with a sharper alternative.

### 5. Implementation roadmap
Distil everything above into a proposed order of operations, five steps or fewer. Step one is always the opening, or `Opening: no change` when it is settled.

### 6. Gut check
Two or three sentences on what the piece will do to a reader once the fixes land, and what kind of effect that is.

## Rules for running it

- Read voice-guide.md, style-rules.md and positioning.md first.
- Quote the draft; never paraphrase a flaw.
- Specific fixes only: every issue gets an exact rewritten line.
- Flag counts matter but impact ordering matters more; lead with what changes the piece most.
- Number every new finding in a heading of its own (`### R2-3a.`, `### R2-4.1` for round 2), quote the words it is about, and never reuse a number in a later look. Round 1 may retain legacy IDs. The board shows each finding beside the paragraph it quotes, where the writer can send it to an agent.
- The cumulative report goes to `edits/dev-edit-report.md` next to the draft; append a new round instead of replacing history. The writer works through it themselves: accept, reject, revise.
