#!/usr/bin/env bash
# Download a public Google Drive file or folder link into a local directory.
# Archives (zip/rar/7z, including nested ones) are extracted in place.
# Usage: bash scripts/fetch_drive.sh "<drive link>" <dest-dir>
#
# To look inside a folder without downloading it:
#   gdown --folder --json "<drive folder link>"
set -uo pipefail

url="${1:?usage: fetch_drive.sh <drive-link> <dest-dir>}"
dest="${2:?usage: fetch_drive.sh <drive-link> <dest-dir>}"
dest="${dest%/}"
mkdir -p "$dest"

status=0
if [[ "$url" == *"/folders/"* ]]; then
  # No trailing slash: contents land directly in $dest, not $dest/<folder name>/.
  gdown --folder --continue --retries 4 "$url" -O "$dest" || status=$?
else
  gdown --continue --retries 4 "$url" -O "$dest/" || status=$?
fi
(( status )) && echo "⚠ gdown exited with $status; some files may be missing (quota or permissions). Continuing with what arrived."

extract() {
  local a=$1 out=$2
  case "${a,,}" in
    *.zip)
      # Windows zips with Arabic names are often CP1256; fall back to it.
      unzip -q -o "$a" -d "$out" 2>/dev/null || unzip -q -o -O cp1256 "$a" -d "$out" ;;
    *.rar) unrar x -o+ -idq "$a" "$out/" || bsdtar -xf "$a" -C "$out" ;;
    *.7z)  7z x -y -o"$out" "$a" >/dev/null || bsdtar -xf "$a" -C "$out" ;;
  esac
}

# Repeat until no new archives appear, so nested archives are also extracted.
# Archives are kept (not deleted) so a re-run with --continue doesn't re-download them.
for _ in 1 2 3; do
  mapfile -d '' archives < <(find "$dest" -type f \( -iname '*.zip' -o -iname '*.rar' -o -iname '*.7z' \) -print0)
  new=0
  for a in "${archives[@]}"; do
    marker="$a.extracted"
    [[ -e "$marker" ]] && continue
    # Drive splits big folder downloads into Name-001.zip, Name-002.zip...: extract all into one dir.
    out="${a%.*}"; out="${out%-[0-9][0-9][0-9]}"
    mkdir -p "$out"
    if extract "$a" "$out"; then
      touch "$marker"; new=1
      echo "extracted: $a -> $out"
    else
      echo "✗ could not extract: $a"
      status=1
    fi
  done
  (( new )) || break
done

list="$dest/.filelist"
find "$dest" -type f ! -name '.filelist' ! -name '*.extracted' -printf '%P\n' | LC_ALL=C sort > "$list"
echo "== Contents of $dest (first 300; full list in $list) =="
head -300 "$list"
echo "($(wc -l < "$list") files, $(du -sh "$dest" | cut -f1))"
exit "$status"
