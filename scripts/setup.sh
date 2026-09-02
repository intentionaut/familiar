#!/bin/sh
# Run after cloning. Installs the /familiar-* commands for supported agents
# so they work from any folder. Re-run any time; it overwrites.
#
# Supported agents:
#   Claude Code      ~/.claude/commands/
#   opencode         ~/.config/opencode/command/
#   Codex (OpenAI)   ~/.codex/commands/
#   Gemini CLI       ~/.gemini/commands/
#
# Pass --only <agent> to install for just one:
#   scripts/setup.sh --only claude
#   scripts/setup.sh --only codex
set -e

DIR="$(cd "$(dirname "$0")/.." && pwd)"
ONLY=""
for arg in "$@"; do
  case "$arg" in
    --only) shift ;;
    claude|opencode|codex|gemini) ONLY="$arg" ;;
  esac
done

# Resolve where the writer's knowledge actually lives and bake it into the
# installed commands, so a stage is told rather than left to guess. The
# fallback is this repo's own folder, which is the shipped templates, and the
# adapters say so when that is what they got. See scripts/paths.py.
KDIR="$(python3 "$DIR/scripts/paths.py" --knowledge-only 2>/dev/null || echo "$DIR/knowledge")"

# The three ways into a piece.
COMMANDS="board new-piece harvest"
# reflect is not a way into a piece; it is a standing practice with its own
# scheduled nudge, and it installs unprefixed as /reflect. A nudge that names a
# command the writer does not have is worse than no nudge at all.
ALIAS="reflect"

install_for() {
  local label="$1" dir="$2"
  mkdir -p "$dir"
  for cmd in $COMMANDS; do
    adapter="$DIR/.claude/commands/$cmd.md"
    if [ -f "$adapter" ]; then
      sed -e "s|{{FAMILIAR_HOME}}|$DIR|g" -e "s|{{FAMILIAR_KNOWLEDGE}}|$KDIR|g" "$adapter" > "$dir/familiar-$cmd.md"
    fi
  done

  # The standing practice, installed unprefixed.
  alias_adapter="$DIR/.claude/commands/$ALIAS.md"
  if [ -f "$alias_adapter" ]; then
    sed -e "s|{{FAMILIAR_HOME}}|$DIR|g" -e "s|{{FAMILIAR_KNOWLEDGE}}|$KDIR|g" "$alias_adapter" > "$dir/$ALIAS.md"
  fi

  # Take out commands an earlier version installed that are no longer part of
  # Familiar. A left-behind command is worse than a missing one: it still
  # appears in the agent's list and calls a prompt that is not there any more.
  # Only files this installer wrote are touched.
  removed=""
  for f in "$dir"/familiar-*.md; do
    [ -f "$f" ] || continue
    stem="$(basename "$f" .md)"
    stem="${stem#familiar-}"
    keep=0
    for cmd in $COMMANDS; do
      if [ "$stem" = "$cmd" ]; then keep=1; fi
    done
    if [ "$keep" = "0" ]; then
      rm -f "$f"
      removed="$removed $stem"
    fi
  done

  if [ -n "$removed" ]; then
    echo "  $label: $dir"
    echo "    took out:$removed"
  else
    echo "  $label: $dir"
  fi
}

installed=""

if [ -z "$ONLY" ] || [ "$ONLY" = "claude" ]; then
  install_for "Claude Code" "$HOME/.claude/commands"
  installed="$installed claude"
fi

if [ -z "$ONLY" ] || [ "$ONLY" = "opencode" ]; then
  install_for "opencode" "$HOME/.config/opencode/command"
  installed="$installed opencode"
fi

if [ -z "$ONLY" ] || [ "$ONLY" = "codex" ]; then
  install_for "Codex" "$HOME/.codex/commands"
  installed="$installed codex"
fi

if [ -z "$ONLY" ] || [ "$ONLY" = "gemini" ]; then
  install_for "Gemini CLI" "$HOME/.gemini/commands"
  installed="$installed gemini"
fi

echo
echo "Installed /familiar-board, /familiar-new-piece, /familiar-harvest and /reflect for:$installed"
echo
echo "Three ways in: start a piece, pick one back up, or find something to"
echo "write about. Everything after that is a conversation. Tell the agent"
echo "what you have and it picks the right stage."
echo
# Say what is actually configured and what to do next, rather than assuming.
python3 "$DIR/scripts/doctor.py" || true
