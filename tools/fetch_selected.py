#!/usr/bin/env python3
"""Download the chosen Commons photos at a usable resolution (standard thumbnail steps; originals are
rate-limited) and write a credits table.

usage: fetch_selected.py info.json index.json ids.txt out_dir credits.json
"""
import json, os, re, subprocess, sys, time, urllib.parse

info = json.load(open(sys.argv[1])); idx = json.load(open(sys.argv[2]))
ids = [l.strip() for l in open(sys.argv[3]) if l.strip()]
out = sys.argv[4]; os.makedirs(out, exist_ok=True)
credits_path = sys.argv[5]
credits = json.load(open(credits_path)) if os.path.exists(credits_path) else {}
UA = "FirasChannelEditor/1.0 (https://github.com/firas717/firas)"
strip = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()

def get(url, dest):
    for t in range(4):
        r = subprocess.run(["curl", "-s", "-A", UA, "-m", "180", "-o", dest, "-w", "%{http_code}", url], capture_output=True, text=True)
        if r.stdout == "200" and os.path.getsize(dest) > 5000:
            return True
        time.sleep(4 + 6 * t)
    if os.path.exists(dest): os.remove(dest)
    return False

name_of = {k[:-4]: v for k, v in idx.items()}
for cid in ids:
    title = name_of[cid]; v = info[title]
    url = v["url"].split("?")[0]
    head, tail = url.split("/wikipedia/commons/")
    fn = tail.split("/")[-1]
    dest = os.path.join(out, cid + ".jpg")
    if not os.path.exists(dest):
        cands = []
        for step in (3840, 1920, 1280, 960):
            if v["width"] > step:
                cands.append(f"{head}/wikipedia/commons/thumb/{tail}/{step}px-{fn}")
        cands.append(url)
        ok = False
        for c in cands:
            if get(c, dest):
                ok = True; break
        print(("ok  " if ok else "FAIL"), cid, title[5:60], flush=True)
        time.sleep(1.0)
    credits[cid] = {"file": title, "page": v.get("page"), "license": v["license"], "license_url": v.get("license_url"),
                    "artist": strip(v["artist"]), "credit": strip(v["credit"])[:200], "date": strip(v["date"])[:30]}
json.dump(credits, open(credits_path, "w"), ensure_ascii=False, indent=1)
