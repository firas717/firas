#!/usr/bin/env bash
# Install the channel identity fonts found under a directory.
# Note: the container already has fallback fonts that cover Arabic (DejaVu Sans,
# FreeSerif), so a wrong font name renders silently in the wrong font. This script
# lists only the families it installed from <dir>, and fails if it found none.
# HyperFrames also needs each font declared with @font-face from a local file in
# the project (see CLAUDE.md, step 3).
# Usage: bash scripts/install_fonts.sh <dir>
set -euo pipefail

src="${1:?usage: install_fonts.sh <dir>}"
fonts_dir="$HOME/.local/share/fonts/nerd"
mkdir -p "$fonts_dir"

mapfile -d '' files < <(find "$src" -type f \( -iname '*.ttf' -o -iname '*.otf' -o -iname '*.ttc' -o -iname '*.otc' -o -iname '*.woff' -o -iname '*.woff2' \) -print0)
if (( ${#files[@]} == 0 )); then
  echo "✗ no font files under $src" >&2
  exit 1
fi

for f in "${files[@]}"; do
  cp --update=none -- "$f" "$fonts_dir/"
done
fc-cache -f >/dev/null

echo "== Font files found (${#files[@]}) =="
printf '%s\n' "${files[@]}"
echo "== Families installed from $src =="
for f in "${files[@]}"; do
  fc-scan --format '%{family}\n' "$f" 2>/dev/null || echo "✗ not a valid font: $f" >&2
done | sort -u
