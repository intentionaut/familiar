#!/usr/bin/env python3
"""Check a real Notion board against what Familiar expects of it.

  notion_check.py --database <ID or URL>            read only
  notion_check.py --database <ID or URL> --write    also runs a real round trip

Read only, it checks the token, that the database can be reached, and that it
has the seven properties Familiar uses, with the right types. It writes nothing.

With --write it adds ONE test row, titled "Familiar live check <time>", to that
database and runs the real thing against it: a stale write is refused, a draft
with every kind of content is copied to the row's page, comes back, and is
compared with what went in. It says exactly what Notion changed, and it tries
two features the pinned API version may or may not have (level 4 headings, and
a numbered list that starts above 1). It never deletes: the test row is left for
you to remove in Notion.

Point --write at a scratch database, not your real board.

The token is read from FAMILIAR_NOTION_TOKEN and is never printed.
"""
import argparse
import datetime
import difflib
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import board_provider as bp  # noqa: E402
import notion_blocks as blocks  # noqa: E402
import notion_board as nb  # noqa: E402
import notion_draft as nd  # noqa: E402

SAMPLE = """Opening paragraph, with **bold**, *italic*, ~~strike~~, `code` and a [link](https://example.com).

A second paragraph with a soft
wrapped line and a hard break\u0020\u0020
after it. [NEEDS SOURCE: a claim]

## A heading

### A smaller heading

- one
  - nested
- two

1. first
2. second

- [ ] open task
- [x] done task

> A quotation
> over two lines

```python
def f():
    return 1
```

| A | B |
| --- | --- |
| 1 | **2** |

---

![An image](https://example.com/c.png)

Café — “quoted” 🙂 日本語

""" + ("A long paragraph. " * 260).strip()


class Report:
    def __init__(self, out):
        self.out, self.fails = out, 0

    def ok(self, what, detail=""):
        print(f"  ok    {what}" + (f" ({detail})" if detail else ""), file=self.out)

    def bad(self, what, detail=""):
        self.fails += 1
        print(f"  FAIL  {what}" + (f": {detail}" if detail else ""), file=self.out)

    def note(self, what):
        print(f"        {what}", file=self.out)

    def head(self, what):
        print(f"\n{what}", file=self.out)


def run(database, token, write=False, out=sys.stdout, transport=None, **client_kw):
    r = Report(out)
    r.head("Connection")
    if not token:
        r.bad("token", f"{nb.TOKEN_ENV} is not set")
        return r.fails
    r.ok("token", "set; not shown")
    db = nb.database_id(database)
    if not db:
        r.bad("database", "give the database's ID or its URL")
        return r.fails
    client = nb.NotionClient(token, transport=transport, **client_kw)
    provider = nb.NotionProvider(client, db)
    try:
        provider._ready()
    except bp.SchemaDrift as e:
        r.ok("database reachable")
        r.bad("properties", e.what)
        r.note(e.next_step)
        return r.fails
    except bp.BoardError as e:
        r.bad("database", str(e))
        return r.fails
    r.ok("database reachable", "one data source")
    r.ok("properties", "all seven are there, with the right types")
    if not write:
        r.head("Read only")
        r.note("Nothing was written. Run again with --write to try a real round trip.")
        return r.fails

    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    pid = "livecheck-" + stamp.replace(" ", "-").replace(":", "")
    r.head("Board row")
    try:
        made = provider.create(bp.BoardItem(id=pid, title=f"Familiar live check {stamp}", state="thinking",
                                            next_decision="Delete this row: it was made by the live check."))
        r.ok("row created", "left in place for you to delete")
        row = provider.read(pid)
        if row and row.title.startswith("Familiar live check") and row.state == "thinking":
            r.ok("row read back by its piece ID")
        else:
            r.bad("row read back", "the fields that came back are not the ones sent")
        after = provider.update(pid, {"state": "writing"}, row.version)
        r.ok("row updated in place", f"state is now {after.state}")
        try:
            provider.update(pid, {"state": "editing"}, row.version)
            r.bad("stale write", "an update against an old version was accepted")
        except bp.BoardConflict:
            r.ok("stale write refused")
    except bp.BoardError as e:
        r.bad("board row", str(e))
        return r.fails

    r.head("Draft copy")
    page = nd.Page(client, made.extra["page_id"])
    try:
        new = blocks.md_to_blocks(SAMPLE)
        nd.apply(page, nd.plan([], new))
        r.ok("draft copied", f"{len(new)} blocks")
        tree = page.read()
        back = blocks.blocks_to_md(tree)
        want = blocks.canon(SAMPLE)
        if back == want:
            r.ok("what came back matches what went in", "every construct, byte for byte")
        else:
            r.bad("what came back differs from what went in")
            for line in list(difflib.unified_diff(want.split("\n"), back.split("\n"), "sent", "returned", lineterm="", n=0))[:20]:
                r.note(line[:110])
        edited = SAMPLE.replace("Opening paragraph", "Opening, edited")
        ids = [b["id"] for b in tree]
        steps = nd.plan(tree, blocks.md_to_blocks(edited))
        c = nd.summary(steps)
        nd.apply(page, steps)
        after_ids = [b["id"] for b in page.read()]
        if after_ids == ids and c["updated"] == 1:
            r.ok("an edit changed one block in place", "the others, and their comments, were not touched")
        else:
            r.bad("in-place edit", f"{c}; block IDs {'kept' if after_ids == ids else 'changed'}")
    except (bp.BoardError, blocks.Unsupported) as e:
        r.bad("draft copy", str(e))

    r.head("Limits the pinned API version may have lifted (informational)")
    for label, child in (
            ("a level 4 heading", {"object": "block", "type": "heading_4",
                                   "heading_4": {"rich_text": [{"type": "text", "text": {"content": "Level four"}}]}}),
            ("a numbered list that starts above 1", {"object": "block", "type": "numbered_list_item",
                                                     "numbered_list_item": {"list_start_index": 3,
                                                                            "rich_text": [{"type": "text", "text": {"content": "third"}}]}})):
        try:
            client.request("PATCH", f"/blocks/{made.extra['page_id']}/children", {"children": [child]})
            r.note(f"accepted: {label}. The converter still refuses it; it can be lifted.")
        except bp.BoardError as e:
            r.note(f"refused by Notion: {label}. The converter's refusal is right for this version.")
    r.head("Finished")
    if r.fails:
        r.note(f"{r.fails} check(s) failed. Nothing else was changed.")
    else:
        r.note("Every check passed.")
    r.note(f'Delete the row "Familiar live check {stamp}" in Notion when you are done.')
    return r.fails


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--database", help="the database's ID or URL (default: Notion database in board-provider.md)")
    ap.add_argument("--write", action="store_true", help="add one test row and run a real round trip on it")
    args = ap.parse_args(argv)
    database = args.database
    if not database:
        import paths
        knowledge, _ = paths.knowledge_dir()
        database = nb.read_field(knowledge, "Notion database")
    return 1 if run(database, os.environ.get(nb.TOKEN_ENV, ""), args.write) else 0


if __name__ == "__main__":
    sys.exit(main())
