#!/bin/bash
# Nudge when a reflection is overdue.
#
# The backstop, not the main path. Familiar offers a reflection at the end of a
# stage when one is due; this catches the weeks you do not open it at all.
#
# Reads knowledge/reflection.md for whether reflection is on, the cadence, and
# where the answers live. Notifies and always writes to a log, because a
# notification alone fails silently under Do Not Disturb or when permission was
# never granted, and a scheduler you cannot tell has run is worse than none.
#
# Usage: scripts/reflection-nudge.sh [--dry-run]
set -uo pipefail

DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$HOME/.claude/familiar-reflect.log"
DRY=0
[ "${1:-}" = "--dry-run" ] && DRY=1
stamp=$(date "+%Y-%m-%d %H:%M")
say() { echo "$stamp  $*" >> "$LOG"; [ "$DRY" = 1 ] && echo "$*"; }

# Settings can live in the repo or, inside a Dex vault, in the vault.
SETTINGS="$DIR/knowledge/reflection.md"
for alt in "$HOME/Documents/Dex/06-Resources/Familiar/knowledge/reflection.md"; do
  [ -f "$alt" ] && SETTINGS="$alt"
done
[ -f "$SETTINGS" ] || { say "no reflection.md found; nothing to do"; exit 0; }

field() { sed -n "s/^- $1: *//p" "$SETTINGS" | head -1 | sed 's/ *$//'; }
ON=$(field "Reflection")
CADENCE=$(field "Cadence")
FOLDER=$(field "Reflections live in")

case "$ON" in
  on|On|ON) ;;
  "["*)     say "settings still the template; not nudging until they are filled in"; exit 0 ;;
  *)        say "reflection is off"; exit 0 ;;
esac

case "$CADENCE" in
  weekly)      DAYS=7 ;;
  fortnightly) DAYS=14 ;;
  monthly)     DAYS=30 ;;
  *)           say "cadence not set to weekly, fortnightly or monthly; not nudging"; exit 0 ;;
esac

FOLDER="${FOLDER/#\~/$HOME}"
[ -d "$FOLDER" ] || { say "reflections folder not found: $FOLDER"; exit 0; }

due=()
for file in "$FOLDER"/*.md; do
  [ -f "$file" ] || continue
  name=$(basename "$file" .md)
  case "$name" in threads|README|readme) continue ;; esac

  last=$(grep -oE '^## [0-9]{4}-[0-9]{2}-[0-9]{2}' "$file" 2>/dev/null | tail -1 | sed 's/^## //')
  if [ -z "$last" ]; then
    due+=("$name (nothing recorded yet)")
    continue
  fi
  last_s=$(date -j -f "%Y-%m-%d" "$last" "+%s" 2>/dev/null) || continue
  days=$(( ( $(date "+%s") - last_s ) / 86400 ))
  [ "$days" -ge "$DAYS" ] && due+=("$name (${days}d)")
done

if [ ${#due[@]} -eq 0 ]; then
  say "ran; nothing due (${CADENCE})"
  exit 0
fi

list=$(printf '%s, ' "${due[@]}"); list=${list%, }
say "due: $list"
[ "$DRY" = 1 ] && exit 0

osascript -e "display notification \"$list\" with title \"Familiar\" subtitle \"Worth a reflection: run /reflect\" sound name \"Glass\"" 2>>"$LOG" || true
