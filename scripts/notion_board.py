#!/usr/bin/env python3
"""The Notion board provider.

Reads and writes a writer's Notion board through the provider boundary in
`board_provider.py`. It holds board fields only: title, state, next decision,
last activity, blockers, links, and the piece's ID. It never sends draft text,
never deletes or archives a row, and stops on a stale write instead of choosing
a value.

Settings, in the writer's house (`knowledge/board-provider.md`):

    - Provider: notion
    - Notion database: <database ID or URL>
    - Notion data source: <only when the database has more than one>
    - Property state: Stage          (optional; renames one mapped property)

The token is never in a file. It comes from FAMILIAR_NOTION_TOKEN.

API: version 2025-09-03, where a database holds one or more data sources and
rows are queried and created against a data source. The data source is found
from the database, or named in the settings when there is more than one.
"""
import datetime
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import board_provider as bp  # noqa: E402

API = "https://api.notion.com/v1"
VERSION = "2025-09-03"
TOKEN_ENV = "FAMILIAR_NOTION_TOKEN"

# The mapped properties, their default names, and the Notion type each must be.
PROPERTIES = {
    "title":         ("Name", "title"),
    "state":         ("State", "select"),
    "next_decision": ("Next decision", "rich_text"),
    "last_activity": ("Last activity", "date"),
    "blockers":      ("Blockers", "rich_text"),
    "links":         ("Links", "rich_text"),
    "id":            ("Piece ID", "rich_text"),
}
TEXT_LIMIT = 2000      # characters in one rich-text element
ARRAY_LIMIT = 100      # elements in one rich-text array


def urllib_transport(method, url, headers, body):
    """(status, headers, json) for one request. A network failure is BoardUnavailable."""
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, dict(r.headers), json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            payload = json.loads(e.read() or b"{}")
        except ValueError:
            payload = {}
        return e.code, dict(e.headers), payload
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise bp.BoardUnavailable("Notion could not be reached.",
                                  "Check the connection and run it again.") from e


class NotionClient:
    """One request at a time, paced to Notion's documented average, with backoff."""

    def __init__(self, token, transport=None, sleep=time.sleep, clock=time.monotonic,
                 per_second=3.0, max_attempts=5, rng=random.random):
        self._token, self.transport = token, transport or urllib_transport
        self.sleep, self.clock, self.rng = sleep, clock, rng
        self.gap, self.max_attempts, self._last = 1.0 / per_second, max_attempts, None

    def _pace(self):
        now = self.clock()
        if self._last is not None and now - self._last < self.gap:
            self.sleep(self.gap - (now - self._last))
        self._last = self.clock()

    def request(self, method, path, body=None):
        headers = {"Authorization": f"Bearer {self._token}", "Notion-Version": VERSION,
                   "Content-Type": "application/json"}
        data = json.dumps(body).encode() if body is not None else None
        for attempt in range(1, self.max_attempts + 1):
            self._pace()
            status, hdrs, payload = self.transport(method, API + path, headers, data)
            if status == 200:
                return payload
            if status in (429, 529) or status >= 500:
                if attempt == self.max_attempts:
                    break
                wait = _retry_after(hdrs)
                if wait is None:
                    wait = min(30.0, (2 ** attempt) * 0.5) * (0.5 + self.rng() / 2)
                self.sleep(wait)
                continue
            raise _error(status, payload)
        if status in (429, 529):
            raise bp.RateLimited("Notion asked for a pause and kept asking.",
                                 "Wait a minute and run it again.")
        raise bp.BoardUnavailable("Notion returned an error and kept returning it.",
                                  "Try again shortly, and check status.notion.so.")


def _retry_after(hdrs):
    for k, v in hdrs.items():
        if k.lower() == "retry-after":
            try:
                return max(0.0, float(v))
            except ValueError:
                return None
    return None


def _error(status, payload):
    code = payload.get("code", "")
    if status == 401:
        return bp.BoardUnavailable("Notion refused the token.",
                                   f"Check {TOKEN_ENV}, and that the integration is still active.")
    if status == 403:
        return bp.BoardUnavailable("The integration has no permission for that.",
                                   "Give it access to the board in Notion, with the content and comment capabilities it needs.")
    if status == 404 or code == "object_not_found":
        return bp.BoardUnavailable("Notion cannot see that board.",
                                   "Share the database with the integration, and check the ID in board-provider.md.")
    if code == "conflict_error":
        return bp.BoardConflict("Notion reported a conflicting edit.", "Read the row again and say which value stands.")
    return bp.BoardError(f"Notion refused the request ({code or status}).",
                         "Check the property names and types in board-provider.md against the board.")


_HEX = "0-9a-fA-F"
_ID = re.compile(rf"(?<![{_HEX}])[{_HEX}]{{8}}-?[{_HEX}]{{4}}-?[{_HEX}]{{4}}-?[{_HEX}]{{4}}-?[{_HEX}]{{12}}(?![{_HEX}])")


def database_id(value):
    """The 32-character ID in a database ID or URL, or None.

    A URL's own words come before its ID (`.../Board-<id>`), and a `?v=` view ID
    comes after it, so only the path is read and hyphens are dropped from the
    match, not from the text around it.
    """
    m = _ID.search((value or "").split("?")[0])
    return m.group(0).replace("-", "").lower() if m else None


def _rich(text):
    text = text or ""
    parts = [text[i:i + TEXT_LIMIT] for i in range(0, len(text), TEXT_LIMIT)][:ARRAY_LIMIT]
    return [{"type": "text", "text": {"content": p}} for p in parts]


def _plain(rich):
    return "".join(r.get("plain_text", "") for r in rich or [])


def _iso(seconds):
    return datetime.datetime.fromtimestamp(seconds, datetime.timezone.utc).isoformat()


def _epoch(iso):
    if not iso:
        return 0.0
    return datetime.datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


class NotionProvider(bp.BoardProvider):
    name = "notion"

    def __init__(self, client, database, data_source=None, names=None):
        self.client, self.database, self._ds, self.names = client, database, data_source, {}
        for f, (default, _) in PROPERTIES.items():
            self.names[f] = (names or {}).get(f) or default
        self._checked = False

    # -- finding the board -------------------------------------------------

    def _source(self):
        found = self.client.request("GET", f"/databases/{self.database}").get("data_sources", [])
        ids = [d["id"] for d in found]
        if self._ds:
            if self._ds.replace("-", "") not in [i.replace("-", "") for i in ids]:
                raise bp.BoardError("That data source is not in this database.",
                                    "Correct Notion data source in board-provider.md, or clear it.")
            return self._ds
        if len(ids) == 1:
            return ids[0]
        names = ", ".join(d.get("name", d["id"]) for d in found) or "none"
        raise bp.BoardError(f"This database has {len(ids)} data sources ({names}).",
                            "Name the one to use as Notion data source in board-provider.md.")

    def _ready(self):
        if self._checked:
            return
        ds = self._source()
        schema = self.client.request("GET", f"/data_sources/{ds}").get("properties", {})
        problems = []
        for f, (_, kind) in PROPERTIES.items():
            name = self.names[f]
            if name not in schema:
                problems.append(f'"{name}" is missing (a {kind} property)')
            elif schema[name].get("type") != kind:
                problems.append(f'"{name}" is a {schema[name].get("type")} property, and a {kind} one is needed')
        if problems:
            raise bp.SchemaDrift("The board no longer matches: " + "; ".join(problems) + ".",
                                 "Fix the property in Notion, or point board-provider.md at the right name.")
        self._ds, self._checked = ds, True

    # -- rows --------------------------------------------------------------

    def _item(self, page):
        props, n = page.get("properties", {}), self.names
        get = lambda f: props.get(n[f], {})
        pid = _plain(get("id").get("rich_text"))
        blockers = _plain(get("blockers").get("rich_text"))
        links = _plain(get("links").get("rich_text"))
        return bp.BoardItem(
            id=pid or f"page:{page['id']}",
            title=_plain(get("title").get("title")),
            state=(get("state").get("select") or {}).get("name", ""),
            next_decision=_plain(get("next_decision").get("rich_text")),
            last_activity=_epoch((get("last_activity").get("date") or {}).get("start")),
            blockers=tuple(b for b in blockers.split("; ") if b),
            links=tuple(l for l in links.split("\n") if l),
            version=page.get("last_edited_time", ""),
            extra={"page_id": page["id"], "url": page.get("url", "")})

    def _props(self, values):
        out, n = {}, self.names
        for f, v in values.items():
            if f == "title":
                out[n[f]] = {"title": _rich(v)}
            elif f == "state":
                out[n[f]] = {"select": {"name": v} if v else None}
            elif f == "last_activity":
                out[n[f]] = {"date": {"start": _iso(v)} if v else None}
            elif f == "blockers":
                out[n[f]] = {"rich_text": _rich("; ".join(v))}
            elif f == "links":
                out[n[f]] = {"rich_text": _rich("\n".join(v))}
            else:                                    # next_decision, id
                out[n[f]] = {"rich_text": _rich(v)}
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

    def read_all(self):
        return [self._item(p) for p in self._query({})]

    def _find(self, item_id):
        rows = self._query({"filter": {"property": self.names["id"],
                                       "rich_text": {"equals": item_id}}})
        if len(rows) > 1:
            raise bp.BoardConflict(f"{len(rows)} rows carry the same piece ID.",
                                   "Keep one row, and clear the Piece ID on the others.")
        return rows[0] if rows else None

    def read(self, item_id):
        page = self._find(item_id)
        return self._item(page) if page else None

    def create(self, item):
        if self._find(item.id):
            raise bp.BoardConflict("A row already carries that piece ID.",
                                   "Read it instead, or clear the Piece ID on the old row.")
        values = {"title": item.title, "state": item.state, "next_decision": item.next_decision,
                  "last_activity": item.last_activity, "blockers": item.blockers,
                  "links": item.links, "id": item.id}
        page = self.client.request("POST", "/pages", {
            "parent": {"type": "data_source_id", "data_source_id": self._ds},
            "properties": self._props(values)})
        return self._item(page)

    def update(self, item_id, changes, version):
        self.check_fields(changes)
        self._ready()
        page = self._find(item_id)
        if page is None:
            raise bp.BoardError("There is no row with that piece ID.", "Create the row first.")
        if page.get("last_edited_time", "") != version:
            raise bp.BoardConflict("That row changed in Notion after it was read.",
                                   "Look at it in Notion, then say which value stands.")
        # Only the named fields are sent, so every other property is left as it is.
        return self._item(self.client.request("PATCH", f"/pages/{page['id']}",
                                              {"properties": self._props(changes)}))


def read_field(knowledge, label):
    """A `- <label>: value` line from board-provider.md; None when unset or still the template."""
    f = Path(knowledge) / bp.SETTINGS_FILE
    if not f.is_file():
        return None
    m = re.search(rf"^- {re.escape(label)}:[ \t]*(.*?)[ \t]*$", f.read_text(encoding="utf-8"), re.M)
    if not m or not m.group(1) or m.group(1).startswith("["):
        return None
    return m.group(1).strip()


def build(knowledge, env=None, transport=None, **client_kw):
    """The Notion provider a writer's house describes."""
    env = os.environ if env is None else env
    db = database_id(read_field(knowledge, "Notion database"))
    if not db:
        raise bp.BoardError("Notion is selected and no database is set.",
                            "Add Notion database (its ID or URL) to board-provider.md.")
    token = env.get(TOKEN_ENV, "")
    if not token:
        raise bp.BoardError("There is no Notion token.", f"Set {TOKEN_ENV} in your environment.")
    names = {}
    for f in PROPERTIES:
        v = read_field(knowledge, f"Property {f if f != 'id' else 'piece_id'}")
        if v:
            names[f] = v
    ds = read_field(knowledge, "Notion data source")
    return NotionProvider(NotionClient(token, transport=transport, **client_kw), db,
                          database_id(ds), names)
