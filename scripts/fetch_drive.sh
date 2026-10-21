#!/usr/bin/env bash
# Download a public Google Drive file or folder link into a local directory.
# Zip/rar/7z archives are extracted automatically.
# Usage: bash scripts/fetch_drive.sh "<drive link>" <dest-dir>
set -euo pipefail

url="${1:?usage: fetch_drive.sh <drive-link> <dest-dir>}"
dest="${2:?usage: fetch_drive.sh <drive-link> <dest-dir>}"
mkdir -p "$dest"

if [[ "$url" == *"/folders/"* ]]; then
  gdown --folder --continue --retries 4 "$url" -O "$dest/"
else
  gdown --continue --retries 4 "$url" -O "$dest/"
fi

# Extract any archives that came down, then remove the archive.
find "$dest" -maxdepth 3 -type f \( -iname '*.zip' -o -iname '*.rar' -o -iname '*.7z' \) -print0 |
  while IFS= read -r -d '' a; do
    out="${a%.*}"
    mkdir -p "$out"
    case "${a,,}" in
      *.zip) unzip -q -o "$a" -d "$out" ;;
      *) 7z x -y -o"$out" "$a" >/dev/null ;;
    esac
    rm -f "$a"
    echo "extracted: $a -> $out"
  done

echo "== Contents of $dest =="
find "$dest" -type f | sed "s|^$dest/||" | sort | head -300
echo "($(find "$dest" -type f | wc -l) files, $(du -sh "$dest" | cut -f1))"
