#!/usr/bin/env bash
# Vendor sweep: find vendored / generated directories that are committed to git,
# so they can be excluded from Codacy (and usually untracked) BEFORE tuning anything else.
# Run from a repository root. Read-only: prints findings and suggestions, changes nothing.
#
#   bash vendor_sweep.sh [min_files]     (default min_files = 20)
set -euo pipefail

MIN="${1:-20}"
git rev-parse --show-toplevel >/dev/null 2>&1 || { echo "not inside a git repository" >&2; exit 2; }

# Directory names that almost always hold third-party or generated code.
NAMES='venv|\.venv|env|site-packages|node_modules|vendor|third_party|dist|build|__pycache__|\.tox|\.eggs|target|Pods'

TMP_FILE="$(mktemp -t vendor_sweep.XXXXXX)"
trap 'rm -f "${TMP_FILE}"' EXIT

total="$(git ls-files | wc -l | tr -d ' ')"
echo "tracked files: ${total}"
echo

# Count tracked files per matching directory (shallowest match wins so nested copies are listed once each).
git ls-files \
  | awk -v names="^(${NAMES})$" -F/ '
      { path=""; for (i=1; i<NF; i++) { path = path (i>1 ? "/" : "") $i
          if ($i ~ names) { count[path]++; break } } }
      END { for (p in count) printf "%d\t%s\n", count[p], p }' \
  | sort -rn > "${TMP_FILE}" || true

if [ ! -s "${TMP_FILE}" ]; then
  echo "No vendored or generated directories are tracked. Nothing to exclude."
  exit 0
fi

echo "Tracked vendored/generated directories (min ${MIN} files):"
found=0
while IFS=$'\t' read -r n p; do
  [ "$n" -ge "$MIN" ] || continue
  found=1
  pct=$(( 100 * n / total ))
  printf '  %6d files (%d%% of repo)  %s/\n' "$n" "$pct" "$p"
done < "${TMP_FILE}"

if [ "$found" -eq 0 ]; then
  echo "  (none reach ${MIN} files)"
  exit 0
fi

echo
echo "Suggested .codacy.yml exclude_paths (must land on the DEFAULT branch to take effect):"
while IFS=$'\t' read -r n p; do
  [ "$n" -ge "$MIN" ] || continue
  echo "  - \"${p}/**\""
done < "${TMP_FILE}"

echo
echo "Suggested cleanup (needs the owner's approval; do not run automatically):"
while IFS=$'\t' read -r n p; do
  [ "$n" -ge "$MIN" ] || continue
  echo "  git rm -r --cached \"${p}\"   # untrack, keeps the files on disk"
done < "${TMP_FILE}"
echo "  and add the same directory names to .gitignore"

