#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
arena_python="${ARENA_PYTHON:-python3.11}"
if ! command -v "$arena_python" >/dev/null 2>&1; then arena_python=python3; fi
if [ ! -x .venv/bin/python ]; then "$arena_python" -m venv .venv; fi
arena_dependency_hash="$(.venv/bin/python -c 'import hashlib; from pathlib import Path; print(hashlib.sha256(Path("requirements.lock").read_bytes()+Path("pyproject.toml").read_bytes()).hexdigest())')"
if [ ! -f .venv/.arena-dependencies ] || [ "$(cat .venv/.arena-dependencies)" != "$arena_dependency_hash" ]; then
  .venv/bin/python -m pip install -r requirements.lock
  .venv/bin/python -m pip install --no-deps -e .
  printf '%s' "$arena_dependency_hash" > .venv/.arena-dependencies
fi
exec .venv/bin/python -m jaeger_arena serve "$@"
