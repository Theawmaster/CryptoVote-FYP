#!/usr/bin/env bash
set -euo pipefail
echo "== pip-audit ==" && pip-audit --strict
echo "== bandit ==" && bandit -r backend models routes utilities -x venv,tests,migrations -lll
echo "== semgrep ==" && semgrep --config p/python --error --exclude venv --exclude tests --exclude migrations
echo "== mypy ==" && mypy utilities backend routes models
echo "✅ Security checks passed."
