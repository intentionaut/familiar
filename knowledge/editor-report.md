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

## Report format

Produce these sections, in order:

### 1. Spark assessment
Determine which situation applies: spark is already on top / spark is buried / spark is missing / spark needs sharpening. Quote the best candidate line and say where it currently sits.

### 2. Thesis check
State the piece's thesis in one sentence as written. Say whether it holds. If it drifts or doubles, quote each variant with locations. Check the Languages block in notes.md: does the piece serve its named intersection? If the thesis lives in a different language than the one named, flag it.

### 3. Critical fixes
Structural moves only. Weak headline gets stronger options. A claim without evidence gets flagged with what kind of support would work. Repeated explanations get quoted at each appearance with a keep/cut recommendation. Every fix pairs with an exact rewrite in the writer's voice.

### 4. Line-level refinement map
Walk the draft. Passive voice, undefined jargon, floating abstractions, AI tells: quote directly, follow with a sharper alternative.

### 5. Implementation roadmap
Distil everything above into a proposed order of operations, five steps or fewer. Step one is always the opening.

### 6. Gut check
Two or three sentences on what the piece will do to a reader once the fixes land, and what kind of effect that is.

## Rules for running it

- Read voice-guide.md, style-rules.md and positioning.md first.
- Quote the draft; never paraphrase a flaw.
- Specific fixes only: every issue gets an exact rewritten line.
- Flag counts matter but impact ordering matters more; lead with what changes the piece most.
- The report goes to `edits/dev-edit-report.md` next to the draft. The writer works through it themselves: accept, reject, revise.
