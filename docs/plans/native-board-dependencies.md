# What depends on the built-in board

The built-in board is deprecated as of 0.60.0. It works as before and nothing is
removed. This is the list that has to be complete, with each line either ported
or knowingly dropped, before anyone proposes removal. Removal is a public change
(this module publishes to the public repo), so it starts only on the writer's
say and not before.

"Built-in board" here means `scripts/board.py` (the static page, `--serve`, the
per-piece pages) and the things that exist only to serve it. The provider
boundary (`board_provider.py`) and the Notion provider are not being removed.

Status values: **port** (needs a new home first), **drop** (goes with the board,
needs the writer's yes), **keep** (stays, but must stop importing the board),
**check** (answer unknown until looked at).

## Code that imports or runs the board

| Where | What it takes from the board | Status |
| --- | --- | --- |
| `scripts/board.py` | itself: `build`, `serve`, `gather`, `NEXT_COMMAND`, `frontmatter_span` | drop, after the rows below |
| `scripts/board_provider.py` (`LocalProvider.item_for`) | `board.gather`, so the built-in provider and the page cannot disagree | keep the provider interface; the built-in provider goes with the board |
| `scripts/board_sync.py` (`next_text`) | `board.NEXT_COMMAND`, the command named for each state | port: `familiar next` works on the Notion board too, so the table must move out of `board.py` |
| `scripts/published.py` | `from board import frontmatter_span`; other tools run this script to learn what was sent | port: move `frontmatter_span` somewhere that is not the board. The monorepo's CI seam lists `board.py` and `board_provider.py` as triggers because of it |
| `scripts/decisions.py` | `from board import last_context_entry` | port, same move: the context-log reader is not a board feature |
| `scripts/notion_draft.py` (`split_draft`) | `board.frontmatter_span` | port, same move as `published.py` |
| `scripts/board_edit.py` | also imports `frontmatter_span` and `last_context_entry` from the board; the write rules for every edit made from the served board (version kept, conflict refused) | `notion_draft.py`, `notion_surface.py` and `notion_guard.py` also import it, so it is not a drop: split what they share from what only the page uses |
| `scripts/rework.py` | the agent half of draft-comment editing: reads `edits/rework.md`, hands a proposal back | the 0.39.0 draft-comment editor. Port to Notion or drop. This is the one the decision names |
| `scripts/familiar` (`cmd_board`, `cmd_rework`, `board --edit`) | launches `board.py`; `rework` calls `rework.py` | drop with the above; `board`, `board sync` and `next` stay for providers |
| `scripts/build-plugin.py`, `.claude/commands/board.md`, `commands/board.md` | the `/familiar-board` command adapter and its plugin copy | change to the Notion path or drop |
| `scripts/setup.sh` (`COMMANDS="board new-piece harvest"`, the "Installed /familiar-board" line) | installs `/familiar-board` for each agent | change with the command |
| `scripts/pull-final.py`, `commands/board.md` step 1 | the board command first writes `final.md` for sent pieces; the comment in `pull-final.py` explains it with "the board says Ready" | check: `pull-final.py` is useful without the board, but nothing else would run it |
| `tests/test_board.py`, `tests/test_board_provider.py`, `tests/test_board_sync.py`, `tests/test_notion_draft.py`, `tests/test_notion_surface.py`, `tests/test_notion_guard.py`, `tests/test_public_check.py` | exercise the page, the rework loop or `board_edit` | follow the code they test |
| `tests/test_provider_contract.py` | lists `scripts/board.py` as serving localhost and calling nothing out | remove the line with the script |

## Skills, prompts and docs that name it

| Where | What it says | Status |
| --- | --- | --- |
| `README.md` ("See what you have in flight") | how to open the board and the Notion alternative | rewrite |
| `AGENTS.md` (pipeline list, "Commands, and how they differ from stages", File map) | the `board` command, `--serve`, Archive and Delete, rework | rewrite |
| `skills/familiar/SKILL.md` | the `board` and `rework` rows and the Commands paragraph | rewrite |
| `dex/familiar/SKILL.md` | tells the Dex skill to run `board.py --pieces <vault>/04-Projects/Writing --open` | port: the Dex user needs another way to see pieces in flight |
| `CONTRIBUTING.md` | names `/familiar-board` | rewrite |
| `site/index.html` | the `/familiar-board` stage card and "the board knows" copy | rewrite |
| `prompts/draft.md` ("Comments from the board") | how an agent answers comments sent from the served board | port with `rework.py`, or drop |
| `prompts/dev-edit.md`, `prompts/line-edit.md` | finding headings kept stable "so the board can show each finding beside the paragraph" | keep the headings (they help any reader); reword the reason |
| `prompts/harvest.md` | says "the board already surfaces" untriaged items | reword |
| `knowledge/board.md` | the board's colours, fonts and text size | drop with the page |
| `knowledge/board-provider.md` | the provider setting, which stays | keep; remove the deprecation paragraph once the board is gone |
| `docs/plans/cms-and-drafts.md`, `docs/plans/records.md`, `docs/plans/content-strategy-bot.md` | history and plans that cite the board | leave as history; check that no plan still depends on it |
| `CHANGELOG.md`, `site/releases.html` | entries that name the board | history, leave |

## Outside this folder

Other modules and shared docs in the private monorepo this module is extracted
from also name the board (a sibling module's notes about a second board, a
contract that says sent pieces are never read from a board, the seam diagrams,
and the CI trigger list for `board.py` and `board_provider.py`). Those are
listed in the maintainer's working copy of this list, not here, because this
file publishes. None of them import `board.py`; the only runtime reach from
outside is `published.py`, listed above.

## What is not on this list because it does not depend on the board

`familiar next`, `familiar board sync`, `push`, `pull`, the Notion board
database, the Notion editing surface and the schema map all run on the provider
boundary. The rows above say where they still reach into `board.py`.

## Before step 3 starts

1. Every row above is marked ported or dropped, with the writer's yes on each
   drop. The draft-comment editor (`rework.py`, `prompts/draft.md`) is the one
   she named.
2. `grep -rn "import board\b\|from board import" scripts tests` finds nothing
   outside the files being removed.
3. A changelog entry and a migration line exist for the removal, and the
   public extract is rebuilt without the files.
