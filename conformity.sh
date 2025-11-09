#!/bin/bash
# Launch Conformity with clean Python environment

unset PYTHONPATH
cd "$(dirname "$0")"
exec ./venv/bin/python3 run.py "$@"
