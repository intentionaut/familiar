# Board provider

Where the board's state comes from. Unset means the built-in board, which works
out every piece's state from the piece folders and needs nothing from you.

## Settings

- Provider: [local / notion]
- Notion database: [database ID or URL]
- Notion data source: [only when the database has more than one]
- Draft copy: [on / off]
- Editing surface: [notion / off]

## What a provider holds

Board fields only: a piece's title, its state, what it needs next, when it last
moved, what is in its way, and links to its files. Draft text, notes, source
cards, edit reports and the context log stay in the piece folder, and a
provider's board fields never carry them. Copying a draft to your own workspace
is a separate, opt-in setting, off until you turn it on.

A provider never deletes or archives anything, and it never picks between two
values that disagree. When a row has changed since Familiar read it, Familiar
stops and asks you which value stands.

Keep connection details for a provider in your own house, never in this file's
shipped template. Tokens belong in the environment.

## Notion

The board is a Notion database with these properties. Names are the defaults;
to use another name, add a line such as `- Property state: Stage`.

| Field | Default name | Notion type |
| --- | --- | --- |
| title | Name | title |
| state | State | select |
| next_decision | Next decision | rich text |
| last_activity | Last activity | date |
| blockers | Blockers | rich text |
| links | Links | rich text |
| piece_id | Piece ID | rich text |

After a stage, `familiar board sync <piece>` brings that piece's row up to date.
A failed sync prints one line and never stops the stage.

Share the database with your Notion integration, and put its token in
`FAMILIAR_NOTION_TOKEN` in your environment. Properties other than these are
left as they are.

## The wider schema map

Beyond the seven board fields, `scripts/notion_schema.py` maps a wider set of
per-piece fields onto the rest of your Notion schema: content type, audience,
channel, theme, priority, owner, next action, decision gate, blocker, source
URL, related project, last-worked date, target date and publication URL, the
same way. It reads the schema once, writes only the fields that changed, and
leaves everything else on the row alone. It shares the database and token
above; to point it at a different database, add `- Schema database:` and
`- Schema data source:`. To rename a mapped property, add a line such as
`- Field owner: Assignee`.

Two fields carry a piece's place in the pipeline. `body_state` writes
Familiar's own five stages (thinking, writing, editing, ready, sent) as-is.
`lifecycle` writes your own Notion status property, translated through an
explicit table you configure, one line per stage, naming the option it maps
to:

    - Lifecycle thinking: [your option for "thinking"]
    - Lifecycle writing: [your option for "writing"]
    - Lifecycle editing: [your option for "editing"]
    - Lifecycle ready: [your option for "ready"]
    - Lifecycle sent: [your option for "sent"]

Every stage needs a line, and no two stages may name the same option. A
stage with no configured option is refused, never guessed, and Familiar never
creates, renames or deletes a Notion property to make one fit.

## Draft copy

Off unless you turn it on. When on, `familiar push <piece>` copies `draft.md` to
the piece's Notion page, and `familiar pull <piece>` brings the page's text back.

- Only one side changes the text at a time. A push or a pull goes ahead when
  exactly one side has changed since the two last agreed. When both have,
  nothing changes and you are asked which stands.
- Before `draft.md` is replaced its text is kept in `.versions/`. Before the page
  is replaced its text is kept there too.
- Front matter stays in `draft.md`. A pull replaces the body only.
- A sent piece's draft is never written. Its copy in Notion is a record.
- Formatting with no markdown form (underline, colour) is dropped on a pull, and
  the pull says how much. A block with no draft form (a toggle, a callout, a
  column) stops the pull and is named.

## Editing surface

Off unless you write `- Editing surface: notion`. When on, the Notion page body
is your working draft. Before a writing stage Familiar reads the page and writes
a working copy, `working.md`, in the piece folder, tagged with the page ID and
the digest both sides last agreed on. When the stage ends, its changes go back
to the page as an exact set of block edits, and only if the page is still what
the stage read. `draft.md` is not touched.

- Two changed bodies are never merged. If the page and the working copy both
  changed, nothing is written and you are asked which stands.
- Only what the converter carries is used. A toggle, callout, column or other
  block with no draft form stops the stage, and the first one is named.
- If an earlier write did not finish, the stage stops and says so. Finishing it
  would overwrite any edit you made in Notion since, so look at the page first.
- A sent piece is never changed.

## Checking a board before you rely on it

```sh
python3 scripts/notion_check.py --database <ID or URL>            # read only
python3 scripts/notion_check.py --database <ID or URL> --write    # one test row, a real round trip
```

The first checks the token, the connection and the seven properties, and writes
nothing. The second adds one test row and runs a real copy, edit and return on it,
then says what Notion changed. Point `--write` at a scratch database. It never
deletes; remove the test row yourself.
