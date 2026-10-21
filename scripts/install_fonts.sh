#!/usr/bin/env bash
# Install every .ttf/.otf found under a directory (the channel identity fonts).
# The container has no Arabic fonts by default, so this must run before preview/render.
# Usage: bash scripts/install_fonts.sh <assets-dir>
set -euo pipefail

src="${1:?usage: install_fonts.sh <assets-dir>}"
fonts_dir="$HOME/.local/share/fonts/nerd"
mkdir -p "$fonts_dir"
find "$src" -type f \( -iname '*.ttf' -o -iname '*.otf' \) -exec cp -n {} "$fonts_dir/" \;
fc-cache -f >/dev/null
echo "== Arabic-capable font families now installed =="
fc-list :lang=ar family | sort -u
