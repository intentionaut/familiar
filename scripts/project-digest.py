#!/usr/bin/env python3
"""Turn a project's git history into a readable digest.

A writer who has never kept a build log still has a history: every commit, dated,
with whatever reasoning made it into the message. This script reads that history
and writes plain markdown the case-study stage can read, the way session-digest
does for a transcript.

Usage:
  scripts/project-digest.py [project-dir] [out.md]
  scripts/project-digest.py --since 2026-06-01 [project-dir] [out.md]
  scripts/project-digest.py --all [projects-root] [out-dir]

--all digests every git repository one level under projects-root (default: the
`Projects live in:` setting in knowledge/build-logs.md, else ~/Projects), one
file per project in out-dir (default: <knowledge>/digests/), and prints one line
per project. It reads; it never asks. Asking whether to pull them all in is the
skill's job, and it asks by default.

Nothing is summarised or interpreted here. The digest is the history, in order,
grouped by day, with the paths each day touched and the days that stand out by
volume. Every item is reconstructed: it records what happened, and the reasoning
only where a commit message carried it.
"""
import pathlib
import re
import subprocess
import sys
from collections import Counter, OrderedDict

SEP = "\x1e"
REC = "\x1f"


def run(args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def project_name(root):
    remote = run(["remote", "get-url", "origin"], root).stdout.strip()
    if remote:
        tail = remote.rstrip("/").split("/")[-1]
        return re.sub(r"\.git$", "", tail)
    return pathlib.Path(root).name


def history(project, since=None):
    """Read a repository's history once and return the facts a digest or an
    engagement line needs: root, name, commits (oldest first), the commits
    whose message carried reasoning, the ones that admit a correction, the
    days, authors, path counts and the README's first paragraph. None if the
    folder is not a repository or has no commits."""
    top = run(["rev-parse", "--show-toplevel"], project)
    if top.returncode != 0:
        return None
    root = top.stdout.strip()

    fmt = "%x1f" + "%x1e".join(["%H", "%ad", "%an", "%s", "%b"])
    log_args = ["log", "--date=short", f"--format={fmt}", "--numstat", "--no-merges"]
    if since:
        log_args.append(f"--since={since}")
    raw = run(log_args, root).stdout
    if not raw.strip():
        return None

    commits = []
    for chunk in raw.split(REC):
        chunk = chunk.strip("\n")
        if not chunk.strip():
            continue
        head, _, stat = chunk.partition("\n")
        parts = head.split(SEP)
        if len(parts) < 4:
            continue
        sha, date, author, subject = parts[:4]
        body = parts[4].strip() if len(parts) > 4 else ""
        paths = []
        for line in stat.splitlines():
            cols = line.split("\t")
            if len(cols) == 3:
                paths.append(cols[2])
        commits.append(dict(sha=sha[:7], date=date, author=author, subject=subject.strip(), body=body, paths=paths))
    commits.reverse()  # oldest first

    by_day = OrderedDict()
    for c in commits:
        by_day.setdefault(c["date"], []).append(c)
    counts = Counter(p for c in commits for p in c["paths"])
    authors = Counter(c["author"] for c in commits)
    with_body = [c for c in commits if c["body"]]
    fix_words = re.compile(r"\b(revert|fix|fixes|fixed|undo|back out|regress|broke|wrong)\b", re.I)
    turns = [c for c in commits if fix_words.search(c["subject"] + " " + c["body"])]
    day_sizes = sorted(((len(v), d) for d, v in by_day.items()), reverse=True)
    median = sorted(len(v) for v in by_day.values())[len(by_day) // 2]
    bursts = [(n, d) for n, d in day_sizes if n >= max(3, 2 * median)]

    readme = ""
    for name in ("README.md", "readme.md", "README"):
        p = pathlib.Path(root) / name
        if p.is_file():
            lines = [l.strip() for l in p.read_text(encoding="utf-8", errors="replace").splitlines()]
            para = []
            for l in lines[1:]:
                if l and not l.startswith("#"):
                    para.append(l)
                elif para:
                    break
            readme = (lines[0] + "\n" + " ".join(para)).strip() if lines else ""
            break

    return dict(root=root, name=project_name(root), commits=commits, by_day=by_day,
                counts=counts, authors=authors, with_body=with_body, turns=turns,
                bursts=bursts, readme=readme,
                first=commits[0]["date"], last=commits[-1]["date"])


def digest_repo(project, since=None):
    """Return (name, digest_markdown, commit_count, first, last) or None if not a repo / empty."""
    h = history(project, since)
    if not h:
        return None
    root, name, commits = h["root"], h["name"], h["commits"]
    by_day, counts, authors = h["by_day"], h["counts"], h["authors"]
    with_body, turns, bursts, readme = h["with_body"], h["turns"], h["bursts"], h["readme"]
    first, last = h["first"], h["last"]
    L = [f"# {name}: what the history says", "",
         f"Reconstructed from `git log` on {root}. {len(commits)} commits, {first} to {last},",
         f"{len(by_day)} days with commits, {len(authors)} author{'s' if len(authors) != 1 else ''}.",
         "Facts only: what changed and when. The reasoning is here only where a",
         "commit message carried it, and the wrong turns are only the ones the",
         "messages admit to. Everything else is a question for the writer.", ""]
    if readme:
        L += ["## What the project says it is", "", readme, ""]
    L += ["## The days that stand out", ""]
    if bursts:
        for n, d in bursts:
            subjects = "; ".join(c["subject"] for c in by_day[d][:6])
            L.append(f"- **{d}**: {n} commits. {subjects}")
    else:
        L.append("- No day stands out by volume; the work was steady.")
    L += ["", "## Where the work went", ""]
    for path, n in counts.most_common(12):
        L.append(f"- `{path}`: {n} commits")
    L += ["", "## Commits that carried reasoning", ""]
    if with_body:
        for c in with_body:
            body = " ".join(c["body"].split())
            L.append(f"- {c['date']} `{c['sha']}` **{c['subject']}**: {body}")
    else:
        L.append("- None. Subjects only; the why was never written down here.")
    L += ["", "## Corrections the messages admit to", ""]
    if turns:
        for c in turns:
            L.append(f"- {c['date']} `{c['sha']}` {c['subject']}")
    else:
        L.append("- None named. That is not the same as none happening.")
    L += ["", "## The history, by day", ""]
    for d, cs in by_day.items():
        L.append(f"### {d}")
        for c in cs:
            L.append(f"- `{c['sha']}` {c['subject']}")
        L.append("")
    return name, "\n".join(L).rstrip() + "\n", len(commits), first, last


def projects_root():
    """The writer's projects folder: build-logs.md's setting, else ~/Projects."""
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        from paths import knowledge_dir
        cfg, _ = knowledge_dir(None)
        text = (pathlib.Path(cfg) / "build-logs.md").read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^- Projects live in:\s*(.+)$", text, re.M)
        if m:
            return pathlib.Path(m.group(1).strip()).expanduser(), pathlib.Path(cfg)
        return pathlib.Path("~/Projects").expanduser(), pathlib.Path(cfg)
    except Exception:
        return pathlib.Path("~/Projects").expanduser(), None


def main():
    argv = sys.argv[1:]
    since = None
    if argv and argv[0] == "--since":
        since = argv[1]
        argv = argv[2:]

    if argv and argv[0] == "--all":
        default_root, cfg = projects_root()
        root = pathlib.Path(argv[1]).expanduser() if len(argv) > 1 else default_root
        out_dir = pathlib.Path(argv[2]) if len(argv) > 2 else (cfg / "digests" if cfg else root / ".familiar-digests")
        if not root.is_dir():
            sys.exit(f"{root} is not a folder")
        repos = sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".") and (p / ".git").exists())
        if not repos:
            sys.exit(f"no git repositories one level under {root}")
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"{len(repos)} projects under {root}; digests in {out_dir}")
        for repo in repos:
            r = digest_repo(repo, since)
            if not r:
                print(f"  {repo.name}: no commits")
                continue
            name, digest, n, first, last = r
            (out_dir / f"{repo.name}.md").write_text(digest, encoding="utf-8")
            print(f"  {repo.name}: {n} commits, {first} to {last}")
        return

    project = pathlib.Path(argv[0] if argv else ".").resolve()
    out = argv[1] if len(argv) > 1 else None
    r = digest_repo(project, since)
    if not r:
        sys.exit(f"{project} is not inside a git repository with commits")
    name, digest, n, _, _ = r
    if out:
        pathlib.Path(out).write_text(digest, encoding="utf-8")
        print(f"wrote {out} ({n} commits from {name})")
    else:
        sys.stdout.write(digest)


if __name__ == "__main__":
    main()
