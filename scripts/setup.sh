#!/usr/bin/env bash
# One-time environment setup for an editing session. Safe to re-run.
# Usage: bash scripts/setup.sh
set -uo pipefail

echo "== Python tools (Drive download + transcription) =="
pip install -q --root-user-action=ignore gdown faster-whisper 2>&1 | tail -2

echo "== HyperFrames skills + headless Chrome =="
npx -y hyperframes@latest skills 2>&1 | tail -5
npx -y hyperframes@latest browser ensure 2>&1 | tail -3

echo "== Doctor =="
npx -y hyperframes@latest doctor 2>&1 | grep -E "✓|✗" | head -30

echo
echo "Setup finished. Next: fetch the assets folder and the episode folder with scripts/fetch_drive.sh"
