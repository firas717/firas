#!/usr/bin/env bash
# One-time environment setup for an editing session. Safe to re-run.
# Exits non-zero if any required step fails.
# Usage: bash scripts/setup.sh
set -uo pipefail

# Pinned so behavior and skill rules don't drift between episodes.
# Bump deliberately and record the version in videos/LOG.md.
HF="hyperframes@0.8.183"

fail=0
step() {
  local name=$1; shift
  local out
  if out=$("$@" 2>&1); then
    echo "✓ $name"
  else
    echo "✗ $name"
    echo "$out" | tail -15
    fail=1
  fi
}

# av 19 breaks faster-whisper's file decoding (TypeError: metadata_errors).
step "pip: gdown, faster-whisper" \
  pip install -q -U --root-user-action=ignore "gdown>=6.3" faster-whisper "av<19"
step "apt: 7z, unrar, bsdtar" \
  bash -c "apt-get update -qq && apt-get install -y -qq --no-install-recommends p7zip-full unrar libarchive-tools"
step "hyperframes skills" npx -y "$HF" skills
step "hyperframes chrome" npx -y "$HF" browser ensure
step "python imports" python3 -c "import faster_whisper, gdown"

echo "hyperframes version: $(npx -y "$HF" --version 2>/dev/null | tail -1)"
npx -y "$HF" doctor 2>&1 | grep -E "✗" | sed 's/^/  doctor: /' || true

if (( fail )); then
  echo "Setup had failures (see ✗ above)."
  exit 1
fi
echo "Setup OK."
