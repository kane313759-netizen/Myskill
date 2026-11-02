#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
KIT="$ROOT/.hackathon-kit"
fail=0

ok(){ echo "[OK] $*"; }
warn(){ echo "[WARN] $*"; }
bad(){ echo "[FAIL] $*"; fail=1; }

[ -f "$KIT/EXAM_POLICY.md" ] && ok "EXAM_POLICY present" || bad "EXAM_POLICY missing"
[ -f "$KIT/run/STATE.md" ] && ok "STATE present" || bad "STATE missing"
[ -f "$KIT/run/GRADER.md" ] && ok "GRADER present" || bad "GRADER missing"
[ -f "$KIT/run/BASELINE.md" ] && ok "BASELINE present" || bad "BASELINE missing"

if [ -f "$KIT/run/STATE.md" ]; then
  if grep -Eiq 'constraint_gate:[[:space:]]*CLOSED' "$KIT/run/STATE.md"; then
    ok "constraint gate CLOSED"
  else
    warn "constraint gate is not recorded CLOSED"
  fi
fi

PY=""
if command -v python3 >/dev/null 2>&1; then PY=python3
elif command -v python >/dev/null 2>&1; then PY=python
fi

if [ -n "$PY" ]; then
  ok "Python available: $PY"
  if "$PY" -m py_compile "$KIT"/scripts/*.py; then ok "Python helper syntax valid"; else bad "Python helper syntax error"; fi
else
  warn "Python not available; Python helpers cannot run"
fi

nested_git="$(find "$ROOT" -mindepth 2 -type d -name .git -print -quit 2>/dev/null || true)"
if [ -n "$nested_git" ]; then
  warn "nested .git found inside task tree: $nested_git"
else
  ok "no nested .git directory detected inside task tree"
fi

if git -C "$ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  ok "Git worktree detected"
  if git -C "$ROOT" check-ignore -q .hackathon-kit/ 2>/dev/null; then
    ok ".hackathon-kit excluded from git status"
  else
    warn ".hackathon-kit is not excluded from git status"
  fi
  echo
  echo "Tracked/untracked task changes (helper paths may be excluded):"
  git -C "$ROOT" status --short || true
else
  warn "task directory is not a Git worktree"
fi

echo
echo "Submission reminder:"
echo "- official task/submission instructions override this doctor"
echo "- Computer Use and Git Push remain prohibited for this exam"
echo "- if helper files must be absent, run clean.sh --apply only after final-explain"

exit "$fail"
