#!/bin/sh
# Install Familiar's commit guard. Opt-in: nothing else runs this for you.
#
#   scripts/install-guard.sh            this repository only
#   scripts/install-guard.sh --global   every repository on this machine
#   scripts/install-guard.sh --uninstall
#
# Per-repository is the default on purpose. Going global changes the behaviour
# of every repo you touch, which is a bigger thing to agree to than it looks.
set -e

DIR="$(cd "$(dirname "$0")/.." && pwd)"
GUARD="$DIR/scripts/pre-commit-guard.sh"
MODE="${1:-local}"

if [ "$MODE" = "--uninstall" ]; then
  if [ "$(git config --global core.hooksPath 2>/dev/null)" = "$HOME/.config/git/hooks" ]; then
    git config --global --unset core.hooksPath
    rm -f "$HOME/.config/git/hooks/pre-commit"
    echo "Removed the global guard."
  fi
  [ -f .git/hooks/pre-commit ] && rm -f .git/hooks/pre-commit && echo "Removed this repository's guard."
  exit 0
fi

if [ "$MODE" = "--global" ]; then
  EXISTING="$(git config --global core.hooksPath 2>/dev/null || true)"
  if [ -n "$EXISTING" ] && [ "$EXISTING" != "$HOME/.config/git/hooks" ]; then
    echo "You already have a global hooks path: $EXISTING"
    echo "Not touching it. Copy $GUARD in there yourself, or install per repository instead."
    exit 1
  fi
  mkdir -p "$HOME/.config/git/hooks"
  cp "$GUARD" "$HOME/.config/git/hooks/pre-commit"
  chmod +x "$HOME/.config/git/hooks/pre-commit"
  git config --global core.hooksPath "$HOME/.config/git/hooks"
  WHERE="every repository on this machine"
else
  [ -d .git ] || { echo "Run this from inside a git repository, or pass --global."; exit 1; }
  mkdir -p .git/hooks
  cp "$GUARD" .git/hooks/pre-commit
  chmod +x .git/hooks/pre-commit
  WHERE="this repository"
fi

cat <<MSG

Guard installed for $WHERE.

It runs only where a commit can leave your machine. A repository with no remote
is skipped, so a private vault or a scratch folder stays unblocked.

It refuses a commit that stages:
  - markdown at the repository root outside the usual set (README, LICENSE and
    the rest), which is where working notes tend to land
  - an email address, a phone number, a postcode or a private key, anywhere
  - words about health, money, sexuality or a dispute, outside your published
    content folders

It never edits anything. It names the file and the line and stops.

Two files let you tune it, and both are meant to be committed:
  .mdscope    extra paths where markdown belongs
  .piiallow   patterns that are known-safe in this repository

A genuine false positive:  git commit --no-verify
Remove it:                 scripts/install-guard.sh --uninstall
MSG
