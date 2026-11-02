#!/usr/bin/env bash
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-.}"
mkdir -p "$TARGET/.agents/skills" "$TARGET/.hackathon-kit"

cp -R "$KIT_DIR/.agents/skills/." "$TARGET/.agents/skills/"

for d in prompts references templates scripts; do
  if [ -d "$KIT_DIR/$d" ]; then
    mkdir -p "$TARGET/.hackathon-kit/$d"
    cp -R "$KIT_DIR/$d/." "$TARGET/.hackathon-kit/$d/"
  fi
done

cp "$KIT_DIR/BOOTSTRAP_PROMPT.md" "$TARGET/.hackathon-kit/BOOTSTRAP_PROMPT.md"
cp "$KIT_DIR/CALLING.md" "$TARGET/.hackathon-kit/CALLING.md"
cp "$KIT_DIR/AGENTS.snippet.md" "$TARGET/.hackathon-kit/AGENTS.snippet.md"

echo "Installed AI Hackathon Starter Kit into: $TARGET"
echo
echo "Codex first prompt:"
echo "Use the hackathon-orchestrator skill. Start from Phase 0. Keep Terra as orchestrator, create one persistent Sol 6.1 MAIN BUILDER, and let that MAIN own specification through implementation. Do not implement until the constraint gate is complete."
