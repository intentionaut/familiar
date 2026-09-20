#!/usr/bin/env python3
"""A wider, read/write map onto a writer's native Notion schema.

`notion_board.py` owns seven board fields. This is the same mechanism —
a typed property map, a schema check done once, a PATCH built from owned
changed fields only, a stale write refused rather than overwritten — carried
to the rest of a piece's metadata: lifecycle, audience, channel, theme,
priority, owner, next action, decision gate, blocker, source URL, related
project, the two dates, and the publication URL. It never touches
`draft.md`, and it never mentions a Notion property it does not own, so
every property a writer's own workflow adds survives untouched.

Two logical fields carry a piece's place in the pipeline, deliberately kept
separate:

  body_state   Familiar's own five-value stage (thinking, writing, editing,
               ready, sent) — written as-is, the same value written for the
               board's `state` field.
  lifecycle    the writer's own Notion status property, whatever labels
               their workflow already uses. Familiar never assumes an
               overlap between the two vocabularies, so a lifecycle value is
               translated through an explicit table, configured house by
               house. A body_state with no configured lifecycle option is a
               stop, not a guess.

Settings live beside the board provider's, in `knowledge/board-provider.md`:

    - Schema database: <database ID or URL>       (defaults to Notion database)
    - Schema data source: <only when ambiguous>    (defaults to Notion data source)
    - Field lifecycle: Status                      (renames a mapped property)
    - Lifecycle thinking: 01 Idea                  (translation table, one line
    - Lifecycle writing: 02 Drafting                per body_state value)
    - Lifecycle editing: 03 Review
    - Lifecycle ready: 04 Ready
    - Lifecycle sent: 05 Live

The token is never in a file. It comes from FAMILIAR_NOTION_TOKEN, exactly as
for the board provider.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import board_provider as bp  # noqa: E402
import notion_board as nb  # noqa: E402

# Familiar's own five-value pipeline stage. Same vocabulary as the board's
# `state` field; see BOARD_FIELDS in board_provider.py.
BODY_STATES = ("thinking", "writing", "editing", "ready", "sent")

# The logical fields this map owns, their default Notion property name, and
# the Notion type each must be. Nothing outside this dict is ever read or
# written by this module.
FIELDS = {
    "piece_id":        ("Piece ID", "rich_text"),
    "lifecycle":       ("Status", "select"),
    "body_state":      ("Body state", "select"),
    "content_type":    ("Content type", "select"),
    "audience":        ("Audience", "select"),
    "channel":         ("Channel", "select"),
    "theme":           ("Theme", "select"),
    "priority":        ("Priority", "select"),
    "owner":           ("Owner", "rich_text"),
    "next_action":     ("Next action", "rich_text"),
    "decision_gate":   ("Decision gate", "rich_text"),
    "blocker":         ("Blocker", "rich_text"),
    "source_url":      ("Source URL", "url"),
    "related_project": ("Related project", "rich_text"),
    "last_worked":     ("Last worked", "date"),
    "target_date":     ("Target date", "date"),
    "publication_url": ("Publication URL", "url"),
}

TEXT_LIMIT = nb.TEXT_LIMIT


class LifecycleDrift(bp.BoardError):
    """A body_state has no configured Notion lifecycle option, or two do."""


class DuplicatePieceId(bp.BoardConflict):
    """More than one row carries the same stable piece ID."""


def _rich(text):
    return nb._rich(text or "")


def _plain(rich):
    return nb._plain(rich)


class LifecycleMap:
    """Familiar body_state <-> a writer's own Notion status option.

    Built from an explicit table only. A body_state with no entry, or two
    body_states pointing at the same Notion option, is refused at build time
    rather than guessed at write time.
    """

    def __init__(self, table):
        missing = [s for s in BODY_STATES if s not in table]
        if missing:
            raise LifecycleDrift(
                f"No lifecycle option is configured for: {', '.join(missing)}.",
                "Add a Lifecycle line in board-provider.md for each body_state.")
        dupes = {}
        for state, option in table.items():
            dupes.setdefault(option, []).append(state)
        clashes = {o: s for o, s in dupes.items() if len(s) > 1}
        if clashes:
            detail = "; ".join(f'"{o}" for {", ".join(s)}' for o, s in clashes.items())
            raise LifecycleDrift(
                f"More than one body_state maps to the same Notion option: {detail}.",
                "Give each body_state its own Lifecycle line in board-provider.md.")
        self.table = dict(table)
        self.reverse = {v: k for k, v in table.items()}

    def to_notion(self, body_state):
        if body_state not in self.table:
            raise LifecycleDrift(
                f'"{body_state}" is not a configured body_state.',
                f"Body state may be one of: {', '.join(BODY_STATES)}.")
        return self.table[body_state]

    def to_body_state(self, option):
        return self.reverse.get(option, "")


class SchemaProvider:
    """Reads and writes the wider Notion schema map, one owned field at a time."""

    def __init__(self, client, database, data_source=None, names=None, lifecycle=None):
        self.client, self.database, self._ds = client, database, data_source
        self.names = {}
        for f, (default, _) in FIELDS.items():
            self.names[f] = (names or {}).get(f) or default
        self.lifecycle = lifecycle
        self._checked = False

    # -- schema --------------------------------------------------------

    def _source(self):
        found = self.client.request("GET", f"/databases/{self.database}").get("data_sources", [])
        ids = [d["id"] for d in found]
        if self._ds:
            if self._ds.replace("-", "") not in [i.replace("-", "") for i in ids]:
                raise bp.BoardError("That data source is not in this database.",
                                    "Correct Schema data source in board-provider.md, or clear it.")
            return self._ds
        if len(ids) == 1:
            return ids[0]
        names = ", ".join(d.get("name", d["id"]) for d in found) or "none"
        raise bp.BoardError(f"This database has {len(ids)} data sources ({names}).",
                            "Name the one to use as Schema data source in board-provider.md.")

    def _ready(self):
        if self._checked:
            return
        ds = self._source()
        schema = self.client.request("GET", f"/data_sources/{ds}").get("properties", {})
        problems = []
        for f, (_, kind) in FIELDS.items():
            name = self.names[f]
            if name not in schema:
                problems.append(f'"{name}" is missing (a {kind} property)')
            elif schema[name].get("type") != kind:
                problems.append(f'"{name}" is a {schema[name].get("type")} property, and a {kind} one is needed')
        if problems:
            raise bp.SchemaDrift("The schema map no longer matches: " + "; ".join(problems) + ".",
                                 "Fix the property in Notion, or point board-provider.md at the right name.")
        self._ds, self._checked = ds, True

    # -- rows ------------------------------------------------------------

    def _item(self, page):
        props, n = page.get("properties", {}), self.names
        get = lambda f: props.get(n[f], {})
        out = {"piece_id": _plain(get("piece_id").get("rich_text"))}
        for f, (_, kind) in FIELDS.items():
            if f == "piece_id":
                continue
            prop = get(f)
            if kind == "rich_text":
                out[f] = _plain(prop.get("rich_text"))
            elif kind == "select":
                option = (prop.get("select") or {}).get("name", "")
                out[f] = self.lifecycle.to_body_state(option) if f == "lifecycle" else option
            elif kind == "url":
                out[f] = prop.get("url") or ""
            elif kind == "date":
                out[f] = (prop.get("date") or {}).get("start") or ""
        out["version"] = page.get("last_edited_time", "")
        out["page_id"] = page["id"]
        return out

    def _props(self, values):
        out, n = {}, self.names
        for f, v in values.items():
            kind = FIELDS[f][1]
            if kind == "rich_text":
                out[n[f]] = {"rich_text": _rich(v)}
            elif kind == "select":
                option = self.lifecycle.to_notion(v) if f == "lifecycle" else v
                out[n[f]] = {"select": {"name": option} if option else None}
            elif kind == "url":
                out[n[f]] = {"url": v or None}
            elif kind == "date":
                out[n[f]] = {"date": {"start": v} if v else None}
        return out

    def _query(self, body):
        self._ready()
        rows, cursor = [], None
        while True:
            payload = dict(body, page_size=100)
            if cursor:
                payload["start_cursor"] = cursor
            res = self.client.request("POST", f"/data_sources/{self._ds}/query", payload)
            rows += res.get("results", [])
            if not res.get("has_more"):
                return rows
            cursor = res.get("next_cursor")

    def _find(self, piece_id):
        rows = self._query({"filter": {"property": self.names["piece_id"],
                                       "rich_text": {"equals": piece_id}}})
        if len(rows) > 1:
            raise DuplicatePieceId(f"{len(rows)} rows carry the same piece ID.",
                                   "Keep one row, and clear the Piece ID on the others.")
        return rows[0] if rows else None

    def read(self, piece_id):
        page = self._find(piece_id)
        return self._item(page) if page else None

    @staticmethod
    def check_fields(changes):
        bad = sorted(set(changes) - set(FIELDS))
        if bad:
            raise bp.UndeclaredField(
                f"Not a mapped field: {', '.join(bad)}.",
                f"A change may name {', '.join(FIELDS)}.")

    def update(self, piece_id, changes, version):
        """Write only the named, changed, owned fields. Never a full-row replacement."""
        self.check_fields(changes)
        if not piece_id:
            raise bp.BoardError("The stable piece ID is missing.",
                                "Give the piece an ID before it is written to Notion.")
        self._ready()
        page = self._find(piece_id)
        if page is None:
            raise bp.BoardError("There is no row with that piece ID.", "Create the row first.")
        if page.get("last_edited_time", "") != version:
            raise bp.BoardConflict("That row changed in Notion after it was read.",
                                   "Look at it in Notion, then say which value stands.")
        if not changes:
            return self._item(page)
        # Only the named fields are sent, so every other property — owned by
        # this map or not — is left exactly as it is.
        return self._item(self.client.request("PATCH", f"/pages/{page['id']}",
                                              {"properties": self._props(changes)}))


def push(provider, piece_id, values):
    """Bring one row's owned fields up to date. Returns "updated" or "unchanged".

    Reads the row first and writes against the version it read, so a row that
    changed in between raises BoardConflict and is left as it is. A field
    already equal to the value asked for is never sent.
    """
    row = provider.read(piece_id)
    if row is None:
        raise bp.BoardError("There is no row with that piece ID.", "Create the row first.")
    changes = {f: v for f, v in values.items() if row.get(f, "") != v}
    if not changes:
        return "unchanged"
    provider.update(piece_id, changes, row["version"])
    return "updated"


def build(knowledge, env=None, transport=None, **client_kw):
    """The schema provider a writer's house describes, sharing settings with the board."""
    import os
    env = os.environ if env is None else env
    raw_db = nb.read_field(knowledge, "Schema database") or nb.read_field(knowledge, "Notion database")
    db = nb.database_id(raw_db)
    if not db:
        raise bp.BoardError("Notion is selected and no database is set.",
                            "Add Notion database (its ID or URL) to board-provider.md.")
    token = env.get(nb.TOKEN_ENV, "")
    if not token:
        raise bp.BoardError("There is no Notion token.", f"Set {nb.TOKEN_ENV} in your environment.")
    names = {}
    for f in FIELDS:
        v = nb.read_field(knowledge, f"Field {f}")
        if v:
            names[f] = v
    table = {}
    for state in BODY_STATES:
        v = nb.read_field(knowledge, f"Lifecycle {state}")
        if v:
            table[state] = v
    lifecycle = LifecycleMap(table)
    ds = nb.read_field(knowledge, "Schema data source") or nb.read_field(knowledge, "Notion data source")
    return SchemaProvider(nb.NotionClient(token, transport=transport, **client_kw), db,
                          nb.database_id(ds), names, lifecycle)
