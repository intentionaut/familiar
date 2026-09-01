#!/usr/bin/env bash
# Familiar's commit guard: keep working notes and personal detail out of repos
# that can be pushed.
#
# Writing about your own work means keeping notes about your own work, and those
# notes end up next to the code. This stops the ones that were never meant to
# ship from shipping. It refuses the commit and says which file and which line,
# rather than editing anything.
#
# It only runs where a commit can leave the machine. A repo with no remote, a
# private vault or a scratch folder, is skipped entirely, so personal notes stay
# unblocked where they belong.
#
# Install it with scripts/install-guard.sh. It is opt-in and nothing installs
# it for you.
#
# Per-repo tuning, both optional, both committed so they travel with the repo:
#   .mdscope    extra glob patterns where markdown is allowed
#   .piiallow   extra grep -E patterns that are known-safe in this repo
#
# Deliberate override: git commit --no-verify
set -uo pipefail

git remote | grep -q . || exit 0          # no remote, nothing can leak
staged=$(git diff --cached --name-only --diff-filter=ACMR) || exit 0
[ -z "$staged" ] && exit 0

ROOT_OK="README.md AGENTS.md CLAUDE.md CHANGELOG.md LICENSE.md CONTRIBUTING.md CODE_OF_CONDUCT.md SECURITY.md"
CONTENT_RE='^(src/content/|content/|_posts/|posts/)'
[ -f .mdscope ] && EXTRA_SCOPE=$(paste -sd'|' .mdscope) || EXTRA_SCOPE=''

allowed=""
[ -f .piiallow ] && allowed=$(paste -sd'|' .piiallow)

scope_bad=""; pii_bad=""

is_content() {
  echo "$1" | grep -qE "$CONTENT_RE" && return 0
  [ -n "$EXTRA_SCOPE" ] && echo "$1" | grep -qE "$EXTRA_SCOPE" && return 0
  return 1
}

for f in $staged; do
  [ -f "$f" ] || continue
  # The guard names the things it protects, so it must not scan itself.
  case "$f" in .githooks/*|.gitignore|.piiallow|.mdscope|scripts/pre-commit-guard.sh|scripts/install-guard.sh) continue ;; esac

  # 1. Scope: stray markdown at the repo root is working material, not a deliverable.
  case "$f" in
    */*) ;;
    *.md)
      echo "$ROOT_OK" | tr ' ' '\n' | grep -qx "$f" || \
        scope_bad+="  $f  (root markdown outside the standard set)"$'\n' ;;
  esac

  # 2. Hard PII: blocked everywhere, published content included.
  hard=$(grep -nEI "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|\+44[0-9 ]{9,}|\b0[17][0-9]{8,9}\b|BEGIN [A-Z ]*PRIVATE KEY|\b[A-Z]{1,2}[0-9][0-9A-Z]? ?[0-9][ABD-HJLNP-UW-Z]{2}\b" "$f" 2>/dev/null \
    | grep -vE "noreply@|no-reply@|example\.(com|org)|@types/|@fontsource|@astrojs|@ai-sdk|@anthropic" \
    | { [ -n "$allowed" ] && grep -vE "$allowed" || cat; } | head -3)
  [ -n "$hard" ] && pii_bad+="  $f"$'\n'"$(echo "$hard" | sed 's/^/      /')"$'\n'

  # 3. Sensitive categories: allowed in published content (she writes about this
  #    on purpose), blocked in working docs where it lands by accident.
  is_content "$f" && continue
  soft=$(grep -nEI -i "\b(kink|psychosexual|BDSM|sexuality|gender identity|transitioning|HRT|diagnos(is|ed)|medication|psychiatr|therapist|suicid|self-harm|overdraft|in debt|take-home pay|salary expectation)\b" "$f" 2>/dev/null \
    | { [ -n "$allowed" ] && grep -vE "$allowed" || cat; } | head -3)
  [ -n "$soft" ] && pii_bad+="  $f"$'\n'"$(echo "$soft" | sed 's/^/      /')"$'\n'
done

if [ -n "$scope_bad" ] || [ -n "$pii_bad" ]; then
  echo ""
  echo "  ██  COMMIT BLOCKED — $(git remote get-url origin 2>/dev/null | sed 's#.*[/:]##')"
  echo ""
  [ -n "$scope_bad" ] && { echo "  Markdown out of scope:"; echo "$scope_bad"; }
  [ -n "$pii_bad" ]   && { echo "  Personal or identifying content staged:"; echo "$pii_bad"; }
  cat <<'MSG'
  Working notes belong somewhere private, not in a repo that can be pushed.

  Unstage it:            git restore --staged <file>
  Widen scope for real:  add a glob to .mdscope
  Known-safe pattern:    add a regex to .piiallow
  Genuinely publishable: git commit --no-verify
MSG
  echo ""
  exit 1
fi
exit 0
