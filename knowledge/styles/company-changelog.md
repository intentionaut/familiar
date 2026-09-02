# Style: Company changelog

A public or internal record of what shipped, what changed, and what it means
for users. Short, specific, user-facing. Not a git log.

## Positioning

```
Language: en
Tone: direct, specific, no marketing
Audience: your users (public) or your team (internal)
Cadence: per-release or weekly rollup
```

## Voice

One sentence per change. What it does, why it matters, where to learn more.
No "we are thrilled to announce". No superlatives. If a change is breaking,
say so in the first line. If it is small, say so and skip the paragraph.

## Slot shapes

- **Changelog entry**: 1-3 sentences per item, grouped by type (Added,
  Changed, Fixed, Removed)
- **Social**: one post per significant change, written for the platform
  (technical on Twitter, visual on LinkedIn)
- **No interview**: the source is the release, not your thoughts about it

## What to change

- `positioning.md`: set the product name, the audience, and what counts as
  a changelog-worthy change
- `voice-guide.md`: add the "one sentence per change" rule and the breaking-
  change-first pattern
- `social-schedule.md`: the social stage works but the cadence is per-release

## Adapting the pipeline

1. **Replace `interview` with `bring`**: feed it the release notes, PR
   descriptions, or a diff summary. `familiar bring release-notes.md`
2. **`outline` becomes grouping**: group by type (Added/Changed/Fixed) or
   by feature area.
3. **`draft` becomes formatting**: it writes the entries in changelog format,
   flagging anything that needs a user-facing explanation.
4. **`dev-edit` becomes user-test**: does each entry answer "what changed"
   and "why does it matter"? Flag entries that only answer one.
5. **`line-edit` becomes consistency**: are all entries the same voice? Do
   they all name the feature the same way?
6. **`finalise` becomes release**: the title is the version number, the
   subject line is the headline change.

## Canonical examples

If you have built a changelog with Familiar, add a short example to
`examples/` and reference it here.
