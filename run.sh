#!/usr/bin/env sh
# Development launcher (Linux/macOS). On Windows use run.bat.
set -e
cd "$(dirname "$0")"
exec python3 run.py "$@"
