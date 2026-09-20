# Board provider

Where the board's state comes from. Unset means the built-in board, which works
out every piece's state from the piece folders and needs nothing from you.

## Settings

- Provider: [local / notion]
- Notion database: [database ID or URL]
- Notion data source: [only when the database has more than one]
- Draft copy: [on / off]

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
