# Command: inspire

Clip a snippet, article, post, or quote into Familiar. This is a capture
command, not a pipeline stage. It writes a file that other stages read.

## File format

Each clip is a markdown file in `inspirations/` named `YYYY-MM-DD-<slug>.md`:

```markdown
# <title>

Source: <URL>
Author: <name>
Clipped: <YYYY-MM-DD>

> <the snippet>

## Why it stuck

<optional - why you clipped this, what it connects to>
```

## Setup

1. Read knowledge/positioning.md to know the house themes. These help when
   suggesting a title or noting connections.
2. Resolve the inspirations folder: look for `inspirations/` next to the
   `knowledge/` folder, or create it if it does not exist.

## Method

If $ARGUMENTS contains text:

- Use it as the snippet.
- If --url is provided, use it as the source. If not, ask for it.
- Generate a title from the content: the author's name and a short phrase
  describing the gist (e.g. "Julian Della Mattia on AI and decisions").
- Generate a slug from the title: lowercase, hyphens for spaces, strip
  non-alnum, max 5 words.
- Write the file to `inspirations/YYYY-MM-DD-<slug>.md` with today's date.
- Do NOT ask "Why it stuck" unless the writer offers it. Speed is the point.

If $ARGUMENTS is empty:

- Ask: "What did you see?" (accept paste or URL)
- Ask: "What's the URL?"
- If the writer adds a note about why it stuck, include it. If not, skip
  the "Why it stuck" section entirely.
- Write the file.

## Exit

Report the file path and the title. If the writer did not add a note, say
they can add one later by editing the file. Do not suggest next stages: this
is a capture, not a gate.
