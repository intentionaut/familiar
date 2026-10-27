#!/usr/bin/env python3
"""Propose which live newsletter post each board card is, and write nothing.

A card can say Sent with no web address, or carry a title that has drifted from
the live post. This reads the posts the publication actually sent and the cards
on the board, and prints a table of proposals for the writer to accept or
reject one row at a time. It never changes a card, a final.md or the
publication.

    python3 scripts/beehiiv-reconcile.py                 # cards in the sent state
    python3 scripts/beehiiv-reconcile.py --states sent,ready
    python3 scripts/beehiiv-reconcile.py --publication "My Letter"
    python3 scripts/beehiiv-reconcile.py --cards cards.json   # cards from a file, not the board
    python3 scripts/beehiiv-reconcile.py --json

Needs BEEHIIV_API_KEY in the environment or in a .env in the current folder.
The cards come from the board provider the writer's house selects, or from a
file given with --cards: a list of {"title", "state", "links"} for a board
that is read some other way (for example an export of a Notion board).

How a card is matched, in this order, and the rule used is printed beside it:
  1. address: a link on the card whose last path segment is the post's slug
  2. title: the same words once case, quotes and punctuation are set aside
  3. close: most of the same words (a likely candidate, never a match)
No match is reported as "no live post". Two or more equal candidates are all
listed and none is picked.

Every page of posts is read, sent and archived, not only the first hundred.
With more than one publication on the key, the writer names one.
"""
import argparse
import datetime
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

API = "https://api.beehiiv.com/v2"
CLOSE = 0.6          # share of words in common for rule 3
STATUSES = ("confirmed", "archived")


def key(env=None, cwd=None):
    env = os.environ if env is None else env
    k = env.get("BEEHIIV_API_KEY")
    if k:
        return k
    f = Path(cwd or Path.cwd()) / ".env"
    if f.is_file():
        for line in f.read_text().splitlines():
            if line.startswith("BEEHIIV_API_KEY="):
                return line.split("=", 1)[1].strip().strip("\"'")
    return None


def http_get(url, k):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {k}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def words(title):
    t = html.unescape(title or "").lower()
    t = t.replace("’", "'").replace("‘", "'").replace("'", "")
    return re.sub(r"[^a-z0-9]+", " ", t).split()


def norm(title):
    return " ".join(words(title))


def overlap(a, b):
    x, y = set(words(a)), set(words(b))
    return len(x & y) / len(x | y) if x and y else 0.0


def slug_of(url):
    parts = [p for p in urllib.parse.urlparse(url or "").path.split("/") if p]
    return parts[-1].lower() if parts else ""


def choose_publication(pubs, name=None):
    """The one publication to read, or a reason there is not one."""
    if not pubs:
        raise SystemExit("No publications on that key. Nothing was read.")
    if name:
        hit = [p for p in pubs if (p.get("name") or "").strip().lower() == name.strip().lower()]
        if len(hit) != 1:
            raise SystemExit(f'No single publication is named "{name}". '
                             f'The key sees: {", ".join(p.get("name", "?") for p in pubs)}.')
        return hit[0]
    if len(pubs) > 1:
        raise SystemExit("The key sees more than one publication. Name one with --publication: "
                         + ", ".join(p.get("name", "?") for p in pubs))
    return pubs[0]


def fetch_posts(get, k, pub_id):
    """Every sent and archived post, every page. A read that cannot finish raises."""
    out = []
    for status in STATUSES:
        page = 1
        while True:
            q = urllib.parse.urlencode({"limit": 100, "page": page, "status": status,
                                        "order_by": "publish_date", "direction": "desc"})
            data = get(f"{API}/publications/{pub_id}/posts?{q}", k)
            out += [dict(p, status=p.get("status") or status) for p in data.get("data", [])]
            if page >= int(data.get("total_pages") or 1):
                break
            page += 1
    return out


def when(v):
    try:
        return datetime.datetime.fromtimestamp(int(v), datetime.timezone.utc).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return ""


def propose(card, posts):
    """One card against the live posts. Returns the rule used and every candidate."""
    slugs = {slug_of(u) for u in card["links"] if slug_of(u)}
    by_slug = [p for p in posts if (p.get("slug") or "").lower() in slugs]
    if by_slug:
        return "address", by_slug
    exact = [p for p in posts if norm(p.get("title")) == norm(card["title"])]
    if exact:
        return "title", exact
    close = sorted(((overlap(p.get("title"), card["title"]), p) for p in posts),
                   key=lambda t: -t[0])
    near = [p for s, p in close if s >= CLOSE]
    if near:
        return "close", near
    return "none", []


def rows(cards, posts):
    out = []
    for c in cards:
        rule, cand = propose(c, posts)
        base = {"card": c["title"], "state": c["state"], "card_links": list(c["links"]),
                "rule": rule, "candidates": [
                    {"title": p.get("title"), "web_url": p.get("web_url"),
                     "published": when(p.get("publish_date")), "status": p.get("status")}
                    for p in cand]}
        if rule in ("address", "title") and len(cand) == 1:
            p = cand[0]
            base["confidence"] = "high" if rule == "address" else "medium"
            base["proposal"] = {"title": p.get("title"), "web_url": p.get("web_url"),
                                "title_differs": norm(p.get("title")) != norm(c["title"]),
                                "url_missing": not any(slug_of(u) == (p.get("slug") or "").lower()
                                                       for u in c["links"]),
                                "url_differs": any(slug_of(u) == (p.get("slug") or "").lower()
                                                   and u.rstrip("/") != (p.get("web_url") or "").rstrip("/")
                                                   for u in c["links"])}
        elif rule == "none":
            base["confidence"] = "none"
        else:
            base["confidence"] = "pick one" if len(cand) > 1 else "low"
        out.append(base)
    return out


def table(rs):
    lines = ["card | proposed title | proposed web address | rule | confidence",
             "-----|----------------|----------------------|------|-----------"]
    for r in rs:
        p = r.get("proposal")
        if p:
            title = p["title"] + (" (card title differs)" if p["title_differs"] else "")
            note = (" (card has a different address for it)" if p["url_differs"]
                    else "" if p["url_missing"] else " (already on the card)")
            url = p["web_url"] + note
        elif r["rule"] == "none":
            title, url = "no live post", ""
        else:
            title = "; ".join(c["title"] for c in r["candidates"])
            url = "; ".join(c["web_url"] or "" for c in r["candidates"])
        lines.append(f'{r["card"]} | {title} | {url} | {r["rule"]} | {r["confidence"]}')
    return "\n".join(lines)


def cards_from_board(states):
    import board_provider
    import paths
    provider = board_provider.resolve_provider(paths.pieces_dirs())
    items = provider.read_all()
    keep = {s.strip() for s in states.split(",") if s.strip()}
    return [{"title": i.title, "state": i.state, "links": list(i.links or ())}
            for i in items if i.state in keep]


def cards_from_file(path, states):
    keep = {s.strip() for s in states.split(",") if s.strip()}
    out = []
    for c in json.loads(Path(path).read_text(encoding="utf-8")):
        if not isinstance(c, dict) or not isinstance(c.get("title"), str):
            raise ValueError(f"{path}: every card needs a title")
        if c.get("state") in keep:
            out.append({"title": c["title"], "state": c["state"], "links": list(c.get("links") or ())})
    return out


def main(argv=None, get=http_get, cards=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--states", default="sent", help="board states to read, comma separated")
    ap.add_argument("--publication", help="publication name when the key sees more than one")
    ap.add_argument("--cards", help="a JSON file of cards instead of the board provider")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    k = key()
    if not k:
        print("No BEEHIIV_API_KEY found. Nothing was read.", file=sys.stderr)
        return 2
    try:
        pub = choose_publication(get(f"{API}/publications", k).get("data", []), a.publication)
        posts = fetch_posts(get, k, pub["id"])
        cs = cards if cards is not None else (cards_from_file(a.cards, a.states) if a.cards
                                              else cards_from_board(a.states))
    except SystemExit as e:
        print(e, file=sys.stderr)
        return 2
    except Exception as e:   # a read that did not finish is unknown, never an empty result
        print(f"Could not read: {e}. Nothing was changed.", file=sys.stderr)
        return 2
    rs = rows(cs, posts)
    if a.json:
        print(json.dumps({"publication": pub.get("name"), "posts_read": len(posts), "rows": rs}, indent=2))
    else:
        print(f'{len(posts)} live posts read from "{pub.get("name")}", {len(cs)} cards compared.\n')
        print(table(rs))
        print("\nNothing was changed. Accept or reject each row yourself.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
