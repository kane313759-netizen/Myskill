#!/usr/bin/env bash
set -euo pipefail
KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if command -v python3 >/dev/null 2>&1; then PY=python3
elif command -v python >/dev/null 2>&1; then PY=python
else echo 'Python 3.8+ is required; nothing installed.' >&2; exit 2
fi
exec "$PY" -B "$KIT_DIR/scripts/kit_lifecycle.py" install --source "$KIT_DIR" --target "${1:-.}"
