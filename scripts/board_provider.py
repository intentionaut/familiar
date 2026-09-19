#!/usr/bin/env python3
"""Where the board's state is read from and written to.

`board` and `next` used to work out every piece's state from the piece folders
and nowhere else. This is the boundary that lets a writer keep that inventory
somewhere else instead, and it changes nothing for a writer who does not: with
no provider set, the built-in board is the provider, and `board.py` is not
touched.

A provider holds *board fields* only: what a piece is called, where it is, what
it needs next, when it last moved, what blocks it. Draft text, notes, source
cards, edit reports and the context log stay in the piece folder and never pass
through a provider.

Two rules every provider follows:

  Writes stop for the writer. A row that changed since it was read raises
  BoardConflict. A provider never picks the newer value, and it never creates a
  second copy to get past a clash.

  Nothing is removed. There is no delete and no archive here. A piece leaves the
  board when the writer moves it, on their side.

The setting lives in the writer's house, in `knowledge/board-provider.md`, and
the shipped template leaves it unset, which means the built-in board.

Usage:
  board_provider.py            which provider is set, and the count by state
"""
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional, Sequence

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import paths  # noqa: E402

SETTINGS_FILE = "board-provider.md"
PROVIDERS = ("local", "notion")

# The only fields a provider reads or writes. Anything else on a row is the
# writer's, and is carried through untouched.
BOARD_FIELDS = ("title", "state", "next_decision", "last_activity", "blockers", "links")


class BoardError(Exception):
    """Something a writer has to act on. Says what happened, then what to do."""

    def __init__(self, what, next_step=""):
        self.what, self.next_step = what, next_step
        super().__init__(f"{what} {next_step}".strip())


class BoardUnavailable(BoardError):
    """The board could not be reached. Never reported as an empty board."""


class BoardConflict(BoardError):
    """The row changed after it was read. The writer decides which value stands."""


class SchemaDrift(BoardError):
    """The board no longer has a field this provider needs."""


class RateLimited(BoardError):
    """The board asked for a pause."""


class ReadOnly(BoardError):
    """This provider derives its state and has nothing to write to."""


class UndeclaredField(BoardError):
    """A write named a field that is not a board field."""


@dataclass(frozen=True)
class BoardItem:
    id: str                       # opaque to callers; see docs/plans/notion-board-provider.md
    title: str
    state: str                    # thinking, writing, editing, ready or sent
    next_decision: str = ""
    last_activity: float = 0.0    # seconds since the epoch
    blockers: Sequence[str] = ()  # counts and labels, never draft text
    links: Sequence[str] = ()
    version: str = ""             # a provider's token for "unchanged since read"
    extra: Mapping = field(default_factory=dict)  # properties this code does not know


class BoardProvider:
    """The contract. A provider implements all of it or says why it cannot."""

    name = ""

    def read_all(self):
        raise NotImplementedError

    def read(self, item_id):
        for item in self.read_all():
            if item.id == item_id:
                return item
        return None

    def create(self, item):
        raise ReadOnly(f"The {self.name} board cannot take a new row.")

    def update(self, item_id, changes, version):
        raise ReadOnly(f"The {self.name} board cannot take a change.")

    @staticmethod
    def check_fields(changes):
        bad = sorted(set(changes) - set(BOARD_FIELDS))
        if bad:
            raise UndeclaredField(
                f"Not a board field: {', '.join(bad)}.",
                f"A change may name {', '.join(BOARD_FIELDS)}.")


class LocalProvider(BoardProvider):
    """The built-in board: state worked out from the piece folders.

    It reads through `board.gather`, the same call the built-in board makes, so
    the two cannot disagree. There is nothing to write back to: the folders are
    the record, and a stage changes them.
    """

    name = "built-in"

    def __init__(self, pieces_dirs, stale_days=7, now=None):
        self.dirs = [Path(d) for d in pieces_dirs]
        self.stale_days = stale_days
        self.now = now

    def read_all(self):
        import datetime
        import board
        now = self.now if self.now is not None else datetime.datetime.now().timestamp()
        items = []
        for d in self.dirs:
            for folder in sorted((f for f in d.iterdir()
                                  if f.is_dir() and not f.name.startswith(".")),
                                 key=lambda f: f.name, reverse=True):
                p = board.gather(folder, now, self.stale_days, "")
                items.append(BoardItem(
                    # Interim: the folder name. The stable-ID decision replaces it.
                    id=p["slug"], title=p["title"], state=p["stage"],
                    next_decision=p["action"], last_activity=p["ts"],
                    blockers=_blockers(p)))
        return items


def _blockers(p):
    """What is in the way, as counts. A bracket's text is the draft's, so it stays out."""
    out = []
    n = len(p["brackets"])
    if n:
        out.append(f"{n} unresolved bracket{'s' if n != 1 else ''}")
    if p["reworking"]:
        out.append(f"{p['reworking']} comment{'s' if p['reworking'] != 1 else ''} open")
    return tuple(out)


def read_setting(knowledge, fname=SETTINGS_FILE):
    """The provider a writer's house names, or None when it names none.

    A bracketed value is the template and counts as unset.
    """
    f = Path(knowledge) / fname
    if not f.is_file():
        return None
    m = re.search(r"^- Provider:[ \t]*(.*?)[ \t]*$", f.read_text(encoding="utf-8"), re.M)
    if not m or not m.group(1) or m.group(1).startswith("["):
        return None
    return m.group(1).strip().lower()


def resolve_provider(pieces_dirs, knowledge=None):
    """The provider the writer's house selects; the built-in board when it selects none."""
    if knowledge is None:
        knowledge, _ = paths.knowledge_dir()
    chosen = read_setting(knowledge)
    if chosen in (None, "local"):
        return LocalProvider(pieces_dirs)
    if chosen == "notion":
        raise BoardError("The Notion board provider is not in this version of Familiar.",
                         f"Set Provider to local in {SETTINGS_FILE}, or update Familiar.")
    raise BoardError(f'"{chosen}" is not a board provider.',
                     f"{SETTINGS_FILE} may name {' or '.join(PROVIDERS)}.")


def counts(items):
    out = {}
    for i in items:
        out[i.state] = out.get(i.state, 0) + 1
    return out


def main(argv=None):
    try:
        provider = resolve_provider(paths.pieces_dirs())
        items = provider.read_all()
    except BoardError as e:
        print(e, file=sys.stderr)
        return 2
    by = counts(items)
    print(f"board: {provider.name}, {len(items)} piece{'s' if len(items) != 1 else ''}")
    for state in ("thinking", "writing", "editing", "ready", "sent"):
        if by.get(state):
            print(f"  {state}: {by[state]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
