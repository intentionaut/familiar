# Stage: intent-check (optional, before the interview settles an angle)

A focused buyer-intent and AI-discovery check for a candidate piece, not a
search-volume forecast, generic audience survey or content score. Choose a
few sharp reader/query targets rather than covering every related phrase. Invoke when the writer asks `intent-check <piece or idea>` or
asks what people are asking about that candidate. Run after a work-based
observation, research lead or writer-supplied idea and before interview questions
fix an angle; rerun only if the audience or thesis changes materially. Never
run it on every harvest theme, gate the interview, or demand that first-hand
work prove external demand before it is worth writing.

## Setup and evidence

1. Read the candidate's `brief.md` if present, `notes.md` if already started,
   the work/source it names, and the intended audience in `knowledge/positioning.md`.
   Preserve the writer's actual claim and receipts as the anchor. If starting
   from a research lead with no piece folder, first use its existing linked
   brief or start the standard piece folder; do not write into the writer's
   research tool or invent a lead.
2. Read reviewed, linked Sources and exact public questions in the discourse
   the piece joins. Narrow the candidate set to the buyer roles and problems
   the writer actually serves, as declared in positioning or confirmed by the writer;
   do not equate an interested reader with a buyer or invent a funnel stage. Search suggestions show *phrasing*, not search volume or
   intent by themselves. Forums and the public conversations of relevant
   practitioners may show an actual question or contested assumption. Follow
   the source to its original page where possible. Record the author/community,
   date, URL, verbatim span and context; distinguish a writer's answer or
   marketing copy from a reader's question. Respect visibility and source
   restrictions: do not mine private conversations for a public brief without
   permission.
3. Check AI-answer visibility with evidence, not folklore: for each shortlisted
   query, note whether the piece can give an answer-shaped, extractable claim
   with a specific first-hand receipt, explicit scope and a source link a
   reader or assistant can cite. If an actual AI answer or citation is observed,
   record the assistant, prompt, date, exact response and links; one observation
   is not a ranking, recommendation or repeatable traffic measure. Do not
   claim assistant pickup or optimise for a guessed algorithm.
4. Questions found in steps 2 and 3 are candidates for the writer's review,
   each with its receipt. They become evidence when the writer keeps them. A
   proposed query, search hit or research tool's output is not evidence of
   audience demand, and a research tool is not an intent classifier. When
   evidence is missing, name one bounded research question for the writer or
   their research tool. If research is unavailable, mark the gap rather than
   making up examples.
5. Say what you could not look at. A channel behind a login or one that
   refused automated search is listed as `unchecked`, never as empty.
6. Date every observation. One older than two years is marked `dated` and
   can't carry an angle on its own.
7. If the candidate already has an approved draft, check against that draft's
   thesis and leave the draft alone. Angles are then options for framing and
   metadata, not a rewrite.

## Output

Append or update only `## Reader language and intent evidence` in the
candidate's `brief.md`, preserving the rest. On an existing brief, do not
replace its work history, candidate theses or evidence inventory. If this is
an idea without a brief, create a minimal `brief.md` with the writer's idea,
source and the section below, then let the ordinary interview own `notes.md`.
Each observation follows this form:

```markdown
## Reader language and intent evidence
Candidate: <writer's work or idea; source>
Intended reader: <declared segment or unknown>
Discourse checked: <where this question would be asked>
Target spread: <one primary buyer/query target, at most two secondary targets; why others were excluded>

### Observed question 1
Exact words: "<verbatim public question or suggestion>"
Source: <URL, author/community, date, where it appeared>
Observed: <what was actually asked or contested; limits of the evidence>
Inferred job: <a plausible need, explicitly an inference, not a known motive>
Buyer fit: <observed role/problem and why a potential client fit is plausible; mark inference or unknown>
AI-answer fit: <specific answer-shaped claim, firsthand receipt, source link; actual AI observation if any, otherwise untested>
Our receipt: <specific first-hand work that can answer it, or needs finding>
Counterexample / gap: <what this source does not establish, rival reading>

### Angle options
A. <distinct angle grounded in observation and receipt>
Buys: <buyer question and AI-answer use it serves>
Costs: <evidence or focus it leaves out>
B. <different, narrower buyer/query angle; same two lines>
[Optional C, only when there is a third defensible angle]
Chosen: <writer's answer, only after they choose>
Because: <their reason in their words, only after they give it>
Decision gate: Which ONE primary buyer/question should this piece answer,
which adjacent targets should it leave out, or proceed from the writer's
first-hand work despite no visible demand?
Unknowns: <thin evidence, inaccessible conversations, or missing receipt>
```

Offer two or three genuinely different *focused* angles, each supported by
cited reader words, plausible buyer fit and the writer's own evidence where
available. Show which adjacent target each angle excludes and why. A broad
"all product leaders" target is not a substitute for a decision. An angle is
evidenced only when at least two independent observations (different authors
or communities) support it, at least one of them not `dated`. If fewer than
two angles meet that, report `unknown` and leave the writer free to start from
their own work. `Buyer fit: unknown` is the expected answer when no author is
an observed buyer; say so rather than stretching toward one. `AI-answer fit:
untested` is equally normal: without an observed answer, don't fill it. Do not invent a persona, extrapolate a volume or
ranking, or collapse a search suggestion into a person's motive. Present the
choice; do not rewrite the thesis or choose for the writer. If the writer
accepts an angle, the interview may carry its observed question into
`notes.md` as an interview prompt, labelled with its provenance. If they
proceed without visible demand, that is a valid decision too.

`finalise` later handles the settled title, subject and metadata. It should
compare its proposed wording with the finished piece, selected buyer question
and answer-shaped evidence, not retrofit a keyword or claim AI visibility. This stage neither drafts nor publishes.
