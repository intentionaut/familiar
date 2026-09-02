# Inspirations

Clipped snippets, articles, posts, and quotes that stuck. One file per clip.
The `inspire` command creates them; the `harvest` stage reads them alongside
build logs to find patterns across your work and what you read.

## File format

Each clip is a markdown file named `YYYY-MM-DD-<slug>.md`:

```markdown
# <title>

Source: <URL>
Author: <name>
Clipped: <YYYY-MM-DD>

> <the snippet>

## Why it stuck

<optional - why you clipped this, what it connects to>
```

The "Why it stuck" section is optional. Clips without it are counted in the
harvest report but skipped for pattern extraction.

## How to use

Quick capture:

```sh
familiar inspire "the snippet" --url https://example.com
```

Interactive (via the agent):

```
familiar inspire
```

The agent asks for the text and URL, generates a title from the content, and
writes the file.

## How it connects

- **harvest** reads `inspirations/` and cross-references themes with build logs
- **interview** can look up a clip when the writer mentions something they read
- **case-study** can read clips as supplementary material
