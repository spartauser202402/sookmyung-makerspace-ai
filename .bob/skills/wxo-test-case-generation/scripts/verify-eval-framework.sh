#!/usr/bin/env bash
# SHARED FILE: keep in sync with skills/wxo-validate-test-case/scripts/verify-eval-framework.sh
# Verify the evaluation framework without changing the environment.
# Usage: bash verify-eval-framework.sh [python-executable]
# Exit 0 when agentops is available; exit 1 otherwise.

set -euo pipefail

if [ "$#" -gt 1 ]; then
  echo "Usage: $0 [python-executable]" >&2
  exit 1
fi

if [ "$#" -eq 1 ]; then
  eval_python="$1"
elif command -v python >/dev/null 2>&1; then
  eval_python=python
else
  eval_python=python3
fi

if ! command -v "$eval_python" >/dev/null 2>&1; then
  echo "Error: Python executable not found: $eval_python. Activate the intended project environment and try again." >&2
  exit 1
fi

echo "Checking Python environment..."
if "$eval_python" -c 'import sys; print("Python: " + sys.executable, flush=True); import agentops'; then
  echo "agentops is installed and available."
else
  echo "Error: agentops could not be imported. Activate the intended project environment and install ibm-watsonx-orchestrate-evaluation-framework using the project package manager, then rerun this check." >&2
  exit 1
fi
