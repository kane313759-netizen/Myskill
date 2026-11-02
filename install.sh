#!/usr/bin/env bash
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-.}"
mkdir -p "$TARGET/.agents/skills" "$TARGET/.hackathon-kit/run"

INSTALLED_FILE="$TARGET/.hackathon-kit/run/INSTALLED_SKILLS.txt"
touch "$INSTALLED_FILE"

# Install skills without overwriting pre-existing project/user skills.
for src in "$KIT_DIR"/.agents/skills/*; do
  [ -d "$src" ] || continue
  name="$(basename "$src")"
  dst="$TARGET/.agents/skills/$name"
  if [ -e "$dst" ]; then
    echo "SKIP existing skill: $name" >&2
    continue
  fi
  cp -R "$src" "$dst"
  grep -qxF "$name" "$INSTALLED_FILE" 2>/dev/null || echo "$name" >> "$INSTALLED_FILE"
done

# Support files. Runtime notes live separately under .hackathon-kit/run/ and are never overwritten here.
for d in prompts references templates scripts; do
  if [ -d "$KIT_DIR/$d" ]; then
    mkdir -p "$TARGET/.hackathon-kit/$d"
    cp -R "$KIT_DIR/$d/." "$TARGET/.hackathon-kit/$d/"
  fi
done

for f in EXAM_POLICY.md BOOTSTRAP_PROMPT.md CALLING.md AGENTS.snippet.md; do
  cp "$KIT_DIR/$f" "$TARGET/.hackathon-kit/$f"
done

# Initialize run notes only when missing.
for f in STATE BASELINE GRADER IMMUTABLES SPEC_DRAFT SYSTEM_MAP CONSTRAINTS DECISIONS VERIFY HANDOFF; do
  src="$TARGET/.hackathon-kit/templates/$f.md"
  dst="$TARGET/.hackathon-kit/run/$f.md"
  if [ -f "$src" ] && [ ! -e "$dst" ]; then
    cp "$src" "$dst"
  fi
done

if [ ! -e "$TARGET/.hackathon-kit/run/LAST_10_MINUTES.md" ]; then
  cat > "$TARGET/.hackathon-kit/run/LAST_10_MINUTES.md" <<'EOF'
# LAST 10 MINUTES

## Solved

## Changed

## Remaining risks

## Follow-up explanation points
EOF
fi

# Hide helper files from local git status without modifying .gitignore.
if git -C "$TARGET" rev-parse --git-dir >/dev/null 2>&1; then
  exclude="$(git -C "$TARGET" rev-parse --git-path info/exclude)"
  mkdir -p "$(dirname "$exclude")"
  touch "$exclude"
  grep -qxF ".hackathon-kit/" "$exclude" 2>/dev/null || echo ".hackathon-kit/" >> "$exclude"
  while IFS= read -r name; do
    [ -n "$name" ] || continue
    pattern=".agents/skills/$name/"
    grep -qxF "$pattern" "$exclude" 2>/dev/null || echo "$pattern" >> "$exclude"
  done < "$INSTALLED_FILE"
fi

echo "Installed AI Hackathon Starter Kit into: $TARGET"
echo "Run notes: $TARGET/.hackathon-kit/run/"
echo
echo "Codex first prompt:"
echo "Use the hackathon-orchestrator skill. Read .hackathon-kit/EXAM_POLICY.md first. Start from grader intake and baseline. Do not implement product logic until CP1 Spec Freeze closes the constraint gate."
