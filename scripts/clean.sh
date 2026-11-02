#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" != "--apply" ]; then
  echo "Dry-run only. Nothing removed."
  echo "To remove installed helper files after final-explain: $0 --apply"
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
KIT="$ROOT/.hackathon-kit"
INSTALLED="$KIT/run/INSTALLED_SKILLS.txt"

if [ ! -d "$KIT" ]; then
  echo "No .hackathon-kit found."
  exit 0
fi

STAMP="$(date +%Y%m%d-%H%M%S 2>/dev/null || echo backup)"
BACKUP_ROOT="${TMPDIR:-/tmp}/hackathon-kit-run-backup-$STAMP"
mkdir -p "$BACKUP_ROOT"
if [ -d "$KIT/run" ]; then
  cp -R "$KIT/run/." "$BACKUP_ROOT/"
fi
echo "Run-note backup: $BACKUP_ROOT"

names=()
if [ -f "$INSTALLED" ]; then
  while IFS= read -r name; do
    [ -n "$name" ] || continue
    names+=("$name")
    rm -rf "$ROOT/.agents/skills/$name"
  done < "$INSTALLED"
fi

# Remove only exact local exclude entries created by this installer.
if git -C "$ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  exclude="$(git -C "$ROOT" rev-parse --git-path info/exclude)"
  if [ -f "$exclude" ]; then
    tmp="$(mktemp)"
    cp "$exclude" "$tmp"
    {
      while IFS= read -r line; do
        skip=0
        [ "$line" = ".hackathon-kit/" ] && skip=1
        for name in "${names[@]:-}"; do
          [ "$line" = ".agents/skills/$name/" ] && skip=1
        done
        [ "$skip" -eq 0 ] && printf '%s\n' "$line"
      done < "$tmp"
    } > "$exclude"
    rm -f "$tmp"
  fi
fi

rm -rf "$KIT"
rmdir "$ROOT/.agents/skills" 2>/dev/null || true
rmdir "$ROOT/.agents" 2>/dev/null || true

echo "Removed starter-kit helper files installed by this kit."
echo "Run notes remain backed up locally at: $BACKUP_ROOT"
