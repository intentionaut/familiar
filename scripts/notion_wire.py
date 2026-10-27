#!/usr/bin/env python3
"""The caller for the Notion editing surface and the wider schema map.

  familiar notion-stage begin  <piece>    read the page, write working.md (no Notion write)
  familiar notion-stage finish <piece>    send the working copy's block changes back
  familiar notion-stage schema <piece>    bring the piece's mapped properties up to date

Notion is an optional provider and every write here goes to a live workspace, so
nothing is written by default. `finish` and `schema` are a dry run: they read,
build the exact requests they would make, print them with a token, and stop.
A write needs both `--apply` and `--confirm <token>`, where the token is the
digest of the requests of the plan as it stands now. A token from an earlier
plan, or none, writes nothing. The writer reads the plan, then passes its token.

The gate is also in the client: `Gated` is a wrapper around the Notion client
that refuses any request that is not a read unless it was built in "send" mode,
which only the confirmed path builds. A plan is recorded by the same wrapper in
"record" mode, so what is printed is what the real code asks the client to send.

Off unless the house opts in: the surface needs `- Editing surface: notion`, and
the schema action needs `- Provider: notion`. Neither reads a token from a file;
the token comes from the environment, as for the board provider, and is never
printed.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import board_edit as be  # noqa: E402
import board_provider as bp  # noqa: E402
import notion_blocks as blocks  # noqa: E402
import notion_draft as nd  # noqa: E402
import notion_guard as ng  # noqa: E402
import notion_surface as ns  # noqa: E402

ACTIONS = ("begin", "finish", "schema")


class WriteRefused(Exception):
    """A write was asked of a client whose gate is shut."""


def is_read(method, path):
    """GET is a read. A POST to a query path is a read: Notion queries by POST."""
    return method == "GET" or (method == "POST" and path.split("?")[0].endswith("/query"))


class Gated:
    """A Notion client that sends reads and treats writes by mode.

    refuse  a write raises WriteRefused; nothing is sent
    record  a write is noted and answered with a stand-in; nothing is sent
    send    a write is noted and sent

    Every non-read request is noted in `sink`, in order, as the plan.
    """

    def __init__(self, inner, mode, sink):
        assert mode in ("refuse", "record", "send")
        self._inner, self._mode, self.sink = inner, mode, sink

    def __getattr__(self, name):
        return getattr(self._inner, name)

    def request(self, method, path, body=None, *, replay_safe):
        if is_read(method, path):
            return self._inner.request(method, path, body, replay_safe=replay_safe)
        if self._mode == "refuse":
            raise WriteRefused(f"{method} {path} refused: the confirm gate is shut.")
        self.sink.append({"method": method, "path": path, "body": body})
        if self._mode == "record":
            n = len(self.sink)
            return {"id": f"dry-run-{n}", "properties": {}, "has_more": False,
                    "results": [{"id": f"dry-run-{n}"}]}
        return self._inner.request(method, path, body, replay_safe=replay_safe)


def token_for(requests):
    """The confirm token: a digest of the exact requests, so a changed plan has a new one."""
    text = json.dumps(requests, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def render(requests, token, action, piece):
    lines = [f"DRY RUN. Nothing was written to Notion. {len(requests)} request(s) would be sent:" if requests
             else "DRY RUN. Nothing was written to Notion. Nothing would be sent."]
    for r in requests:
        lines.append(f"  {r['method']} {r['path']}")
        lines.append("    " + json.dumps(r["body"], sort_keys=True) if r["body"] is not None else "    (no body)")
    if requests:
        lines.append(f"To send them, read them, then run: familiar notion-stage {action} {piece} "
                     f"--apply --confirm {token}")
    return "\n".join(lines)


def _res(status, text, code=0, **kw):
    return dict(status=status, text=text, code=code, requests=kw.pop("requests", []), **kw)


# -- finish ------------------------------------------------------------------

def _plan_finish(folder, client, page_id):
    """(stopped result or None, requests). Reads Notion; writes nothing, locally or there."""
    if (folder / "final.md").exists():
        return _res("stopped", "This piece has been sent. Nothing would be changed.", 1), []
    have = ns.read_working(folder)
    if have is None:
        return _res("stopped", "There is no working copy to send. Begin the stage first.", 1), []
    tags, body = have
    if tags.get("source_page") != page_id:
        return _res("stopped", "The working copy came from a different page. Nothing would be changed.", 1), []
    if tags.get("agreed_digest") != ng.agreed_digest(folder):
        return _res("stopped", "The working copy was made against a version the page and Familiar no longer "
                    "agree on. Begin the stage again.", 1), []
    if nd.read_state(folder).get("interrupted"):
        return _res("stopped", ns._interrupted_message(), 1), []
    try:
        new_blocks = blocks.md_to_blocks(body)
        notion_md, tree, _ = nd._notion_body(nd.Page(client, page_id))
    except blocks.Unsupported as e:
        return _res("stopped", ns._unsupported(e, "The working copy or the page")["message"], 1), []
    local_md = blocks.blocks_to_md(new_blocks)
    outcome = ng.decide(ng.agreed_digest(folder), notion_md, local_md)
    if outcome == ng.CONFLICT:
        return _res("conflict", "Both the page and the working copy changed since they last agreed. "
                    "Nothing would be written. Keep the page or keep the working copy.", 1), []
    if outcome != ng.APPLY_LOCAL:
        return None, []        # nothing to send; a finish may only refresh the working copy
    steps = nd.plan(tree, new_blocks)
    rec = []
    nd.apply(nd.Page(Gated(client, "record", rec), page_id), steps)
    return None, rec


def _locate(dirs, query, knowledge, provider):
    loc = ns.locate(dirs, query, knowledge, provider)
    if isinstance(loc, dict):
        return _res("stopped", loc["message"], 1), None
    return None, loc


# -- the entry point ---------------------------------------------------------

def run(action, dirs, query, knowledge, provider=None, schema=None, env=None, transport=None,
        apply=False, confirm=None, resume=False):
    """A dict: status, text, code, requests, and token for a plan. Never raises on a Notion failure."""
    held = [(o, o.client) for o in (provider, schema) if o is not None]
    try:
        if action == "begin":
            return _begin(dirs, query, knowledge, provider, env, transport)
        if action == "finish":
            return _finish(dirs, query, knowledge, provider, env, transport, apply, confirm, resume)
        if action == "schema":
            return _schema(dirs, query, knowledge, schema, env, transport, apply, confirm)
        return _res("stopped", f"Unknown action: {action}.", 2)
    except bp.BoardError as e:
        return _res("stopped", str(e), 1)
    except WriteRefused as e:
        return _res("refused", str(e), 1)
    finally:
        for o, c in held:                      # a caller's provider comes back as it was given
            o.client = c


def _provider(provider, dirs, knowledge, env, transport):
    return provider or bp.resolve_provider(dirs, knowledge, env=env if env is not None else os.environ,
                                           transport=transport)


def _begin(dirs, query, knowledge, provider, env, transport):
    if not ns.surface_is_notion(knowledge):
        return _res("skipped", "Editing surface is not notion. Nothing was read or written.")
    prov = _provider(provider, dirs, knowledge, env, transport)
    prov.client = Gated(prov.client, "refuse", [])      # begin never writes to Notion
    out = ns.stage_begin(dirs, query, knowledge, prov)
    return _res(out["status"], out["message"], 0 if out["status"] == "ok" else 1, result=out)


def _finish(dirs, query, knowledge, provider, env, transport, apply, confirm, resume):
    if not ns.surface_is_notion(knowledge):
        return _res("skipped", "Editing surface is not notion. Nothing was read or written.")
    prov = _provider(provider, dirs, knowledge, env, transport)
    inner = prov.client
    prov.client = Gated(inner, "refuse", [])
    stop, loc = _locate(dirs, query, knowledge, prov)
    if stop:
        return stop
    folder, page_id, _ = loc
    stop, requests = _plan_finish(Path(folder), prov.client, page_id)
    if stop:
        return stop
    token = token_for(requests)
    plan = render(requests, token, "finish", query)
    if not apply:
        return _res("dry_run", plan, requests=requests, token=token)
    if not requests:
        out = ns.stage_finish(dirs, query, knowledge, prov, resume=resume)   # may only refresh locally
        return _res(out["status"], out["message"], 0 if out["status"] == "ok" else 1, result=out, token=token)
    if confirm != token:
        return _res("refused", "Not confirmed. Nothing was written to Notion.\n" + plan, 1,
                    requests=requests, token=token)
    prov.client = Gated(inner, "send", [])
    out = ns.stage_finish(dirs, query, knowledge, prov, resume=resume)
    ok = out["status"] == "ok"
    return _res("applied" if ok and out["reason"] == "applied" else out["status"], out["message"],
                0 if ok else 1, requests=requests, token=token, result=out)


# -- schema ------------------------------------------------------------------

def _schema(dirs, query, knowledge, schema, env, transport, apply, confirm):
    if bp.read_setting(knowledge) != "notion":
        return _res("skipped", "The board provider is not notion. Nothing was read or written.")
    import board_sync as bs
    import notion_schema
    found = bs.find_pieces(dirs, query)
    if len(found) != 1:
        return _res("stopped", f'"{query}" matches {len(found)} pieces. Name one.', 1)
    folder = found[0]
    piece_id = bp.read_piece_id(folder)
    if not piece_id:
        return _res("stopped", f"{folder.name} has no stable piece ID. Nothing was read or written.", 1)
    item = bp.LocalProvider(dirs).item_for(folder)
    values = {"body_state": item.state, "lifecycle": item.state} if item.state in notion_schema.BODY_STATES else {}
    if not values:
        return _res("stopped", f"{folder.name} has no stage to write. Nothing was sent.", 1)
    sp = schema or notion_schema.build(knowledge, env=env if env is not None else os.environ, transport=transport)
    inner = sp.client
    rec = []
    sp.client = Gated(inner, "record", rec)
    try:
        notion_schema.push(sp, piece_id, values)
    finally:
        sp.client = inner
    token = token_for(rec)
    plan = render(rec, token, "schema", query)
    if not apply:
        return _res("dry_run", plan, requests=rec, token=token)
    if not rec:
        return _res("unchanged", "The row already matches. Nothing was sent.", requests=rec, token=token)
    if confirm != token:
        return _res("refused", "Not confirmed. Nothing was written to Notion.\n" + plan, 1, requests=rec, token=token)
    sent = []
    sp.client = Gated(inner, "send", sent)
    try:
        notion_schema.push(sp, piece_id, values)
    finally:
        sp.client = inner
    if token_for(sent) != token:
        return _res("stopped", "The row moved between the plan and the write; what was sent differs from the plan.",
                    1, requests=sent, token=token)
    return _res("applied", f"{len(sent)} request(s) sent to Notion.", requests=sent, token=token)
