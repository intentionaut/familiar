#!/bin/sh
# Install Familiar as a callable Dex skill: /familiar-custom inside a Dex vault.
#
# Usage: dex/install.sh /path/to/your/Dex/vault
#
# Copies dex/familiar/ into <vault>/.claude/skills/familiar-custom/ (the
# -custom suffix is what Dex updates leave alone) and writes this repo's path
# into the skill so it can find the prompts and your voice files. Re-run to
# update; it overwrites the installed copy only.
set -e

VAULT="${1:?usage: dex/install.sh /path/to/your/Dex/vault}"
HOME_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$VAULT/.claude/skills/familiar-custom"

if [ ! -d "$VAULT/.claude/skills" ]; then
  echo "That does not look like a Dex vault (no .claude/skills): $VAULT" >&2
  exit 1
fi

mkdir -p "$DEST/evals" "$VAULT/04-Projects/Writing" "$VAULT/06-Resources/Familiar/proposals"
# Seed the writer's voice files into the vault from the templates, never overwriting.
K="$VAULT/06-Resources/Familiar/knowledge"
mkdir -p "$K/examples" "$K/languages"
for f in positioning.md voice-guide.md style-rules.md editor-report.md social-schedule.md context-log.md models.md examples/canonical.md languages/README.md languages/_template.md; do
  [ -f "$K/$f" ] || cp "$HOME_DIR/knowledge/$f" "$K/$f"
done
sed "s|{{FAMILIAR_HOME}}|$HOME_DIR|g" "$HOME_DIR/dex/familiar/SKILL.md" > "$DEST/SKILL.md"
cp "$HOME_DIR/dex/familiar/evals/trigger-cases.yaml" "$DEST/evals/trigger-cases.yaml"

echo "Installed /familiar into $DEST"
echo "Familiar home: $HOME_DIR"
echo "Voice files: $K (fill in positioning.md and voice-guide.md, or run learn ingest)"
echo "Pieces will be written to $VAULT/04-Projects/Writing/"
echo
echo "Start a new Dex session, then: /familiar-custom interview <an idea>"
echo "(Dex names custom skills by folder; the -custom suffix is what keeps it safe across updates.)"
