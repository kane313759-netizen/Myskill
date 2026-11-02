#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if command -v python3 >/dev/null 2>&1; then PY=python3
elif command -v python >/dev/null 2>&1; then PY=python
else echo 'Python 3.8+ is required for safe cleanup.' >&2; exit 2
fi
exec "$PY" -B "$SCRIPT_DIR/kit_lifecycle.py" clean --kit "$SCRIPT_DIR/.." "$@"
