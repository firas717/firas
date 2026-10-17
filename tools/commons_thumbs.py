#!/usr/bin/env python3
import json, os, re, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from commons import download
info = json.load(open(sys.argv[1])); outdir = sys.argv[2]
index = {}
for i, (title, v) in enumerate(sorted(info.items())):
    if not v.get("thumb"):
        continue
    ext = ".png" if v["thumb"].lower().endswith(".png") else ".jpg"
    name = f"c{i:03d}{ext}"
    index[name] = title
    try:
        download(v["thumb"], os.path.join(outdir, name))
    except Exception as e:
        print("FAIL", title, e, file=sys.stderr)
json.dump(index, open(os.path.join(outdir, "index.json"), "w"), ensure_ascii=False, indent=1)
print(len(index), "thumbs")
