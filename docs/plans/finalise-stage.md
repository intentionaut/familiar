# A finalise stage, between line-edit and social

Status: tabled, not started. Raised 2026-08-31.

## The gap

The pipeline goes interview, outline, draft, dev-edit, line-edit, social. Every
stage serves the prose. Nothing serves the page the prose lands on, so the
publishing metadata gets written by hand at the end of a long day, which is when
it gets written worst or not at all.

## What finalise would produce

- **SEO title and meta description**, to a character budget the writer sets.
  Not guessed: measured, and reported with the count.
- **The slug**, checked against the platform's own generator rather than
  assumed. Apostrophes are the usual trap: intentionaut.com carries
  `the-ai-opportunity-you-re-missing`.
- **Social preview**: og:title, og:description, and whether a per-post image
  exists or the site-wide default will be used.
- **Link check**: every URL in the piece resolves, and any link to the piece's
  own future home is flagged as dead until publication.
- **A publishing checklist** for the platform, generated from the piece.

## The rule that makes it non-obvious

The budget is not the platform's budget. It is the platform's budget minus what
the site adds. On intentionaut.com, `pages/writing/[slug].astro` renders
`title + " | Saielle DaSilva"`, so a 60-character target leaves 42 for the
title. Finalise has to know the template, not just the limit.

Same trap in the other direction: for a beehiiv-sourced post the site takes
`description` from `post.subtitle`, so the subtitle is simultaneously the email
subtitle, the on-page lede and the meta description. One field, three jobs, three
different sets of constraints. A finalise stage should say so rather than let the
writer discover it.

## Open

- Does finalise run before or after social? Social needs the resolved URL, and
  finalise is what determines the slug, so probably before.
- Where does the metadata live? Frontmatter is the obvious home, but it is then
  the writer's job to copy it into the platform. Worth checking whether the
  platform has an API that would take it directly.
