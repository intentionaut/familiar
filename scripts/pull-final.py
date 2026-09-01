#!/usr/bin/env python3
"""Write final.md for pieces that have been sent.

A piece only reads as finished when `final.md` exists: it is the record of what
went out, and it is what `learn diff` reads to turn your own edits into voice
rules. Written by hand it does not get written, so the board says Ready about
something that reached readers days ago.

This fetches what was actually published and writes it, matching posts to piece
folders by title. It never overwrites an existing final.md, and it never invents
a match: a piece with no confident match is reported and left alone.

    python3 scripts/pull-final.py            # write what is missing
    python3 scripts/pull-final.py --dry-run  # say what it would write

Needs BEEHIIV_API_KEY in the environment or in a .env beside the publication's
repo. Publications other than beehiiv can be added as another fetch function;
everything below the fetch is platform agnostic.
"""
import argparse, datetime, html, json, os, re, sys, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import pieces_dirs  # noqa: E402

API = "https://api.beehiiv.com/v2"


def key():
    k = os.environ.get("BEEHIIV_API_KEY")
    if k:
        return k
    for env in (Path.cwd() / ".env", Path.home() / "Projects/intentionaut/.env"):
        if env.is_file():
            for line in env.read_text().splitlines():
                if line.startswith("BEEHIIV_API_KEY="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    return None


def get(url, k):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {k}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def to_markdown(raw):
    raw = re.sub(r"<(script|style)\b.*?</\1>", "", raw, flags=re.S | re.I)
    raw = re.sub(r"<(h[1-6])[^>]*>(.*?)</\1>",
                 lambda m: "\n\n" + "#" * int(m.group(1)[1]) + " " + m.group(2) + "\n\n",
                 raw, flags=re.S | re.I)
    raw = re.sub(r"<li[^>]*>(.*?)</li>", r"\n- \1", raw, flags=re.S | re.I)
    raw = re.sub(r"<blockquote[^>]*>(.*?)</blockquote>",
                 lambda m: "\n\n> " + m.group(1).strip() + "\n\n", raw, flags=re.S | re.I)
    raw = re.sub(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', r"[\2](\1)", raw, flags=re.S | re.I)
    raw = re.sub(r"</p>|<br\s*/?>", "\n\n", raw, flags=re.I)
    raw = html.unescape(re.sub(r"<[^>]+>", "", raw))
    raw = re.sub(r"[ \t]+", " ", raw)
    return re.sub(r"\n{3,}", "\n\n", raw).strip()


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def piece_title(folder):
    for name in ("draft.md", "notes.md"):
        f = folder / name
        if f.is_file():
            m = re.search(r'^title:\s*"?(.+?)"?\s*$', f.read_text(), re.M)
            if m:
                return m.group(1)
    return re.sub(r"^\d{4}-\d{2}-\d{2}-", "", folder.name).replace("-", " ")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    k = key()
    if not k:
        sys.exit("No BEEHIIV_API_KEY found. Nothing was changed.")

    pubs = get(f"{API}/publications", k).get("data", [])
    if not pubs:
        sys.exit("No publications on that key.")
    pub = pubs[0]["id"]
    posts = get(f"{API}/publications/{pub}/posts?limit=100&order_by=created"
                f"&direction=desc", k).get("data", [])
    sent = {norm(p["title"]): p for p in posts if p.get("status") == "confirmed"}

    wrote, skipped, unmatched = [], [], []
    for d in pieces_dirs():
        for folder in sorted(x for x in d.iterdir() if x.is_dir() and not x.name.startswith(".")):
            if not any((folder / n).is_file() for n in ("draft.md", "notes.md")):
                continue
            if (folder / "final.md").is_file():
                skipped.append(folder.name)
                continue
            post = sent.get(norm(piece_title(folder)))
            if not post:
                unmatched.append(folder.name)
                continue
            full = get(f"{API}/publications/{pub}/posts/{post['id']}"
                       f"?expand[]=free_web_content&expand[]=stats", k)["data"]
            body = to_markdown(full["content"]["free"]["web"])
            stats = full.get("stats", {}).get("email", {})
            def when(v):
                """beehiiv gives unix seconds. A date nobody can read is not a record."""
                try:
                    return datetime.datetime.fromtimestamp(
                        int(v), datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                except (TypeError, ValueError):
                    return ""

            published = when(post.get("publish_date"))
            fm = [
                "---",
                f'title: "{post["title"]}"',
                f'date: {published[:10]}',
                f'sent: {published}',
                f'platform: {post.get("platform")}',
                f'recipients: {stats.get("recipients", "")}',
                f'web_url: {post.get("web_url")}',
                'note: "Pulled from the publication after sending. This is the record of'
                ' what exists in the world, and what learn diff reads."',
                "---",
                "",
            ]
            if not args.dry_run:
                (folder / "final.md").write_text("\n".join(fm) + body + "\n")
            wrote.append(f"{folder.name}  <- {post['title']} ({len(body.split())} words)")

    for w in wrote:
        print(("would write " if args.dry_run else "wrote ") + w)
    if unmatched:
        print(f"\nno sent post matched, left alone: {', '.join(unmatched)}")
    print(f"\n{len(wrote)} written, {len(skipped)} already had one, {len(unmatched)} unmatched")


if __name__ == "__main__":
    main()
