#!/bin/bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

export PYTHONPATH="$REPO_ROOT/src"
export RAMP_LOCAL_HOST=10.0.0.1
export RAMP_LOCAL_PORT=6000
export RAMP_PEER_HOST=10.0.0.2
export RAMP_PEER_PORT=6001
export RAMP_AUTH_ENABLED=1

python3 applications/chat_sender_app.py
