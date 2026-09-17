#!/usr/bin/env python3
"""Write a build-log entry from a session transcript. Called by the hook.

The hook (hooks/build-log-entry.sh) hands this the PreCompact or SessionEnd
JSON on stdin and gets out of the way. Everything decided here:

  where       the session's own project, else the project it mostly worked in,
              else the cross-project log (scripts/log.py owns the routing)
  what        the part of the transcript not yet recorded, with the writer's
              own words kept whole and subagent reports kept long
  how much    a long session is summarised in chunks rather than having its
              opening thrown away, because the reasoning is usually at the start
  once        one entry per session per event, under a lock, so the same
              session wired in two settings files is still recorded once

Env overrides: FAMILIAR_LOG_FILE, FAMILIAR_LOG_MODEL, FAMILIAR_LOG_EFFORT.
"""
import datetime
import fcntl
import glob
import json
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(os.environ.get("FAMILIAR_ROOT") or
                    pathlib.Path(__file__).resolve().parent.parent)
sys.path.insert(0, str(ROOT / "scripts"))

STATE = pathlib.Path.home() / ".claude" / "familiar-log" / "state"
LIMIT = 120_000          # characters of transcript in one model call
MAX_CHUNKS = 6           # earlier chunks beyond this are read for the writer's words only
AGENT_TOOLS = {"Agent", "Task"}
SECTIONS = """**Shipped**
- One line each. What now exists that didn't before.

**Decisions**
- What was decided, what was rejected, and the reason (only if the reason was given).

**Went wrong**
- Wrong turns, bugs, wasted work. Cause and cost.

**Numbers**
- Anything measurable mentioned in the session.

**Quips**
- What the human said in passing that is worth keeping, one line each, in their
  own words, quoted exactly. A reaction, a half-formed reason, a thing they
  noticed. Never tidy one into a decision, and never write one they did not say.

**Open**
- Unresolved questions, known risks, things waiting on the human."""


def log(msg, session="unknown", event=""):
    now = datetime.datetime.now()
    print(f"[{now:%Y-%m-%d %H:%M:%S}] {session[:8]} {event}: {msg}", flush=True)


def turns_from(lines, agent_chars=4000, result_chars=200):
    """The conversation in those transcript lines, as text.

    A subagent's report is the output of a whole session and is cut to nothing
    by the ordinary tool-result limit, so it gets its own, longer one.
    """
    agent_ids, out = set(), []
    for raw in lines:
        try:
            rec = json.loads(raw)
        except Exception:
            continue
        if rec.get("isMeta") or rec.get("type") not in ("user", "assistant"):
            continue
        content = (rec.get("message", {}) or {}).get("content")
        if isinstance(content, str):
            body = content
        else:
            parts = []
            for block in content or []:
                if not isinstance(block, dict):
                    continue
                t = block.get("type")
                if t == "text":
                    parts.append(block.get("text", ""))
                elif t == "tool_use":
                    name = block.get("name", "")
                    if name in AGENT_TOOLS:
                        agent_ids.add(block.get("id"))
                    inp = block.get("input", {}) or {}
                    hint = inp.get("command") or inp.get("file_path") or inp.get("description") or ""
                    parts.append(f"[tool: {name} {str(hint)[:160]}]")
                elif t == "tool_result":
                    c = block.get("content")
                    s = c if isinstance(c, str) else " ".join(
                        b.get("text", "") for b in (c or []) if isinstance(b, dict))
                    cap = agent_chars if block.get("tool_use_id") in agent_ids else result_chars
                    if block.get("is_error"):
                        parts.append(f"[tool error: {s[:400]}]")
                    elif s:
                        parts.append(f"[tool result: {s[:cap]}]")
            body = "\n".join(p for p in parts if p)
        body = body.strip()
        if not body or body.startswith("<system-reminder>") or body.startswith("<local-command"):
            continue
        out.append(f"### {rec['type'].upper()}\n{body}")
    return out


def paths_touched(lines):
    """Every file path a session's tools named, for routing."""
    found = []
    for raw in lines:
        for m in re.finditer(r'"(?:file_path|notebook_path|path)":\s*"([^"]+)"', raw):
            found.append(m.group(1))
        for m in re.finditer(r'(?:^|[\s"\'=])(/Users/[^\s"\':;]+|~/[^\s"\':;]+)', raw):
            found.append(m.group(1))
    return found


def human_words(turns):
    """Only what the human said. What a long session cannot afford to lose."""
    return [t for t in turns if t.startswith("### USER")]


def chunk(turns, limit=LIMIT):
    """Turns grouped into model-sized chunks, oldest first."""
    out, cur, size = [], [], 0
    for t in turns:
        if cur and size + len(t) > limit:
            out.append(cur); cur, size = [], 0
        cur.append(t); size += len(t)
    if cur:
        out.append(cur)
    return out


def call_model(prompt, timeout=600):
    model = os.environ.get("FAMILIAR_LOG_MODEL", "sonnet")
    effort = os.environ.get("FAMILIAR_LOG_EFFORT", "medium")
    res = subprocess.run(
        # --setting-sources "" loads no settings, so no hooks: the summariser
        # cannot trigger this hook again.
        ["claude", "-p", "--no-session-persistence", "--setting-sources", "",
         "--model", model, "--effort", effort, "--tools", ""],
        input=prompt, capture_output=True, text=True, timeout=timeout,
        cwd=os.path.expanduser("~"),
        env={**os.environ, "CLAUDE_CODE_ENABLE_AWAY_SUMMARY": "0"},
    )
    if res.returncode != 0:
        raise RuntimeError(f"claude exit {res.returncode}: {res.stderr.strip()[:300]}")
    return res.stdout.strip()


NOTES_PROMPT = """Below is part {i} of {n} of one Claude Code working session, in order.
Take notes for a build log entry that will be written from all the parts.

Facts only, no narrative. Keep: what shipped, what was decided and why, what
went wrong with its cause and cost, any number said out loud, and the human's
own words worth keeping, quoted exactly. Leave out anything you cannot see in
the text. Bullets, no headings, no preamble.

=== TRANSCRIPT PART {i} OF {n} ===
{part}
"""

ENTRY_PROMPT = """You are keeping a build log for a software project. Below is the raw transcript
of one Claude Code working session (or the part of it since the last entry),
followed by the end of the existing log. Write the next log entry.

RULES (these matter more than anything else)
- Record, don't dramatise. Facts, numbers, and what things cost in time or rework.
  No adjectives about the project's trajectory, no praise, no narrative headings.
- Prefer numbers to intensifiers. "Took 3 attempts" beats "was tricky".
- Include the agent's own mistakes and dead ends in Went wrong, with the cause
  and the cost. This is the section most worth reading later.
- Never invent a detail. If the transcript doesn't have it, leave it out.
- Quips are verbatim. Quote the human's own words or leave the section out.
- Plain language. No "leveraged", "streamlined", "robust". No em dashes.
- Do not repeat anything already recorded in the existing log tail.
- This entry is reconstructed from a transcript by a hook, not written during the
  work. It records what happened; the reasoning is only as good as what was said
  out loud. Do not pad reasoning you can't see.
{cross}
FORMAT: output exactly this, starting with the heading line, no preamble, no
code fences, no closing remarks. Omit any section with nothing real in it.

{heading}

{sections}

If genuinely nothing worth recording happened, output only the single word
NOTHING.

=== EXISTING LOG (tail) ===
{tail}
{notes}
=== TRANSCRIPT ===
{convo}
"""

CROSS_RULE = """- This log covers several projects. Group what happened under a bold project
  name inside each section, and say which project every line belongs to.
"""


def build_prompt(turns, tail, heading, cross, call=call_model, session="", event=""):
    """The entry prompt, summarising earlier chunks rather than dropping them."""
    parts = chunk(turns)
    notes = ""
    if len(parts) > 1:
        earlier, last = parts[:-1], parts[-1]
        if len(earlier) > MAX_CHUNKS:
            # Past this much transcript, the oldest parts are read for the
            # human's own words only. Their turns are where the reasoning is,
            # and they are a fraction of the size.
            oldest = [turn for part in earlier[:-MAX_CHUNKS] for turn in human_words(part)]
            earlier = ([oldest] if oldest else []) + earlier[-MAX_CHUNKS:]
        summaries = []
        for i, part in enumerate(earlier, 1):
            text = "\n\n".join(part)
            try:
                summaries.append(call(NOTES_PROMPT.format(i=i, n=len(parts), part=text[:LIMIT])))
            except Exception as e:
                log(f"notes for part {i} failed: {e}", session, event)
                summaries.append("\n\n".join(human_words(part))[:20_000])
        notes = "\n=== NOTES FROM EARLIER PARTS OF THIS SESSION ===\n" + "\n\n".join(summaries) + "\n"
        convo = "\n\n".join(last)
    else:
        convo = "\n\n".join(parts[0]) if parts else ""
    return ENTRY_PROMPT.format(cross=CROSS_RULE if cross else "", heading=heading,
                               sections=SECTIONS, tail=tail, notes=notes, convo=convo)


def resolve(cwd, lines):
    """(log path, reason). scripts/log.py owns every rule about where a log is."""
    forced = os.environ.get("FAMILIAR_LOG_FILE")
    if forced:
        return pathlib.Path(forced), "FAMILIAR_LOG_FILE"
    import log as flog  # scripts/log.py
    root, watched, _reg = flog.read_settings()
    path, reason = flog.route(cwd, paths_touched(lines), root, watched, flog.cross_project_log())
    if path:
        return path, reason
    for pat in ("*-LOG.md", "*-PROGRESS.md", "LOG.md"):
        hits = sorted(glob.glob(os.path.join(cwd, pat)))
        if hits:
            return pathlib.Path(hits[0]), "a log file in the folder"
    return None, reason


def main():
    hook = json.loads(sys.stdin.read())
    cwd = hook.get("cwd") or os.getcwd()
    transcript = hook.get("transcript_path", "")
    session = hook.get("session_id", "unknown")
    event = hook.get("hook_event_name", "")
    now = datetime.datetime.now()
    STATE.mkdir(parents=True, exist_ok=True)

    if not transcript or not os.path.exists(transcript):
        # Said in full on purpose: this was the commonest outcome and the log
        # never said which of "no path given" and "path gone" had happened.
        log(f"no transcript to read (path given: {transcript or 'none'}). "
            "A session that ended before anything was said has none.", session, event)
        return 0

    lock = open(STATE / f"{session}.lock", "a+")
    fcntl.flock(lock, fcntl.LOCK_EX)
    try:
        lines = open(transcript, encoding="utf-8", errors="replace").read().splitlines()
        offset_file = STATE / f"{session}.offset"
        try:
            start = int(offset_file.read_text().strip())
        except Exception:
            start = 0
        new = lines[start:]
        if not new:
            log("nothing new since the last entry", session, event)
            return 0

        log_file, reason = resolve(cwd, lines)
        if not log_file or not log_file.exists():
            log(f"no build log for this session: {reason}", session, event)
            return 0

        turns = turns_from(new)
        convo_len = sum(len(t) for t in turns)
        if convo_len < 400:
            log(f"too little conversation to record ({convo_len} chars)", session, event)
            return 0

        cross = reason.startswith("cross-project")
        kind = "compacted, auto" if event == "PreCompact" else "auto"
        heading = f"## {now:%Y-%m-%d} ({kind})"
        existing = log_file.read_text(encoding="utf-8")
        prompt = build_prompt(turns, existing[-4000:], heading, cross,
                              session=session, event=event)
        try:
            entry = call_model(prompt)
        except Exception as e:
            log(f"{e}", session, event)
            return 0
        if not entry or entry.upper().startswith("NOTHING"):
            log("model judged nothing worth recording", session, event)
            offset_file.write_text(str(len(lines)))
            return 0
        if not entry.startswith("## "):
            entry = heading + "\n\n" + entry

        with open(log_file, "a+", encoding="utf-8") as f:
            f.seek(0, 2)
            if f.tell() and not existing.endswith("\n"):
                f.write("\n")
            f.write("\n" + entry.rstrip() + "\n")
        offset_file.write_text(str(len(lines)))
        log(f"appended {len(entry)} chars to {log_file} ({reason})", session, event)
        return 0
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()


if __name__ == "__main__":
    sys.exit(main())
