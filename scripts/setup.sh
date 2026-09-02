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

install_for() {
  local label="$1" dir="$2"
  mkdir -p "$dir"
  for adapter in "$DIR"/.claude/commands/*.md; do
    stage="$(basename "$adapter" .md)"
    sed -e "s|{{FAMILIAR_HOME}}|$DIR|g" -e "s|{{FAMILIAR_KNOWLEDGE}}|$KDIR|g" "$adapter" > "$dir/familiar-$stage.md"
  done
  # /reflect alias
  rm -f "$dir/reflect.md"
  sed -e "s|{{FAMILIAR_HOME}}|$DIR|g" -e "s|{{FAMILIAR_KNOWLEDGE}}|$KDIR|g" "$DIR/.claude/commands/reflect.md" > "$dir/reflect.md"
  echo "  $label: $dir"
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
echo "Installed /familiar-* commands for:$installed"
echo
echo "Familiar stops after every stage and waits for you. It reports rather"
echo "than rewrites: your draft is never edited in place, and anything it"
echo "cannot source is left as a bracket instead of being invented."
echo
# Say what is actually configured and what to do next, rather than assuming.
python3 "$DIR/scripts/doctor.py" || true
