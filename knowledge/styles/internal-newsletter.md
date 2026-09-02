# Style: Internal newsletter

A regular update for your team: what shipped, what is coming, what needs
attention. Written for people who already know the context. No onboarding.

## Positioning

```
Language: en
Tone: direct, brief, no ceremony
Audience: your team (engineering, product, or cross-functional)
Cadence: weekly
```

## Voice

Assume the reader knows the background. No "as you know" padding. Lead with
what changed and what they need to do. If nothing needs doing, say so in one
line and move on. Bad internal newsletters waste time; good ones save it.

## Slot shapes

- **Update**: 3-5 items, each 1-3 sentences, grouped by what needs attention
  vs. what is FYI
- **Social**: usually none; internal newsletters do not go on social
- **No repurpose**: the audience is fixed

## What to change

- `positioning.md`: team name, what the team owns, what counts as news
- `voice-guide.md`: add the "assume context" rule and the attention/FYI
  grouping
- `social-schedule.md`: leave empty or set to `scheduler: none`

## Adapting the pipeline

1. **`interview` stays**: ask "what shipped, what changed, what needs
   attention?" One question at a time works for internal updates too.
2. **`outline` becomes triage**: group items into Needs Attention and FYI.
3. **`draft` becomes compression**: cut every sentence that does not tell
   the reader something new or ask them to do something.
4. **`dev-edit` becomes the time test**: if this takes more than 2 minutes
   to read, it is too long. Flag anything that could be a link instead of
   a paragraph.
5. **`line-edit` stays**: the mechanical pass still matters for internal
   credibility.
6. **Skip `repurpose`, `social`, `publish`**: internal newsletters do not
   need these. The pipeline should stop after `finalise`.

## Canonical examples

If you have built an internal newsletter with Familiar, add a short example
to `examples/` and reference it here.
