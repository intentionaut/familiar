#!/usr/bin/env python3
"""Turn a Claude Code session transcript into a readable digest.

Claude Code writes every session to ~/.claude/projects/<project>/<id>.jsonl.
That file is the raw material for writing about a coding session, but it is
noisy: tool calls, tool results, system reminders. This script keeps what a
person said and what the assistant said, summarises tool use to one line
each, and writes plain markdown the case-study stage can read.

Usage:
  scripts/session-digest.py <transcript.jsonl> [out.md]
  scripts/session-digest.py --latest [project-dir] [out.md]

--latest picks the most recently modified transcript for the given project
directory (default: the current directory).

Nothing is summarised or interpreted here. The digest is the session, minus
the noise, in order, with timestamps.
"""
import json, os, sys, glob, datetime, pathlib, re

def project_slug(path):
    return str(pathlib.Path(path).resolve()).replace("/", "-")

def latest_transcript(project_dir):
    d = pathlib.Path.home() / ".claude" / "projects" / project_slug(project_dir)
    files = sorted(d.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        sys.exit(f"no transcripts under {d}")
    return files[0]

def text_of(content):
    if isinstance(content, str):
        return content, []
    text, tools = [], []
    for block in content or []:
        if not isinstance(block, dict):
            continue
        t = block.get("type")
        if t == "text":
            text.append(block.get("text", ""))
        elif t == "tool_use":
            inp = block.get("input", {}) or {}
            hint = inp.get("description") or inp.get("command") or inp.get("file_path") or inp.get("pattern") or ""
            tools.append(f"{block.get('name', 'tool')}: {str(hint).strip()[:140]}")
        elif t == "tool_result":
            c = block.get("content")
            s = c if isinstance(c, str) else " ".join(b.get("text", "") for b in (c or []) if isinstance(b, dict))
            if block.get("is_error"):
                tools.append(f"error: {s.strip()[:200]}")
    return "\n".join(x for x in text if x).strip(), tools

def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    if args[0] == "--latest":
        project = args[1] if len(args) > 1 and not args[1].endswith(".md") else "."
        out = next((a for a in args[1:] if a.endswith(".md")), None)
        src = latest_transcript(project)
    else:
        src = pathlib.Path(args[0])
        out = args[1] if len(args) > 1 else None

    lines = src.read_text(encoding="utf-8", errors="replace").splitlines()
    turns, first_ts, last_ts, cwd = [], None, None, None
    for raw in lines:
        try:
            rec = json.loads(raw)
        except Exception:
            continue
        if rec.get("isMeta") or rec.get("type") not in ("user", "assistant"):
            continue
        cwd = cwd or rec.get("cwd")
        ts = rec.get("timestamp")
        if ts:
            first_ts = first_ts or ts
            last_ts = ts
        body, tools = text_of((rec.get("message") or {}).get("content"))
        if body.startswith("<system-reminder>") or body.startswith("<local-command"):
            body = ""
        body = re.sub(r"<system-reminder>.*?</system-reminder>", "", body, flags=re.S).strip()
        if not body and not tools:
            continue
        turns.append((rec["type"], ts, body, tools))

    def when(ts):
        try:
            return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%H:%M")
        except Exception:
            return ""

    head = [
        f"# Session digest: {src.stem[:8]}",
        "",
        f"Transcript: `{src}`",
        f"Project: `{cwd or 'unknown'}`",
        f"From {first_ts or '?'} to {last_ts or '?'}. {len(turns)} turns.",
        "",
        "Raw material, not a record: what was said, in order, with tool use",
        "collapsed to one line each. Reasoning is only here if it was said out loud.",
        "",
        "---",
        "",
    ]
    body = []
    for kind, ts, text, tools in turns:
        who = "Assistant" if kind == "assistant" else ("Writer" if text else "Tool result")
        body.append(f"## {when(ts)} {who}")
        if text:
            body.append("")
            body.append(text)
        if tools:
            body.append("")
            body += [f"- [{t}]" for t in tools]
        body.append("")
    digest = "\n".join(head + body)
    if out:
        pathlib.Path(out).write_text(digest, encoding="utf-8")
        print(f"wrote {out} ({len(turns)} turns from {src.name})")
    else:
        sys.stdout.write(digest)

if __name__ == "__main__":
    main()
