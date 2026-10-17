#!/bin/bash
# usage: fetch_list.sh urls.tsv outdir   (tsv: name<TAB>url) — polite sequential curl
UA="FirasChannelEditor/1.0 (https://github.com/firas717/firas)"
while IFS=$'\t' read -r name url; do
  [ -s "$2/$name" ] && continue
  for t in 1 2 3 4 5; do
    code=$(curl -s -A "$UA" -m 120 -o "$2/$name" -w '%{http_code}' "$url")
    [ "$code" = 200 ] && break
    rm -f "$2/$name"; sleep $((t*5))
  done
  [ "$code" = 200 ] || echo "FAIL $code $name $url"
  sleep 1
done < "$1"
