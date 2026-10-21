#!/usr/bin/env python3
"""List and download a public OneDrive share link (personal OneDrive, no sign-in).

New personal OneDrive links (1drv.ms/f/c/...) refuse unauthenticated API calls, so
this gets the same anonymous "badger" token the OneDrive web viewer uses.

Usage:
  # Full recursive index (no download) -> JSON list of {path, size, id, folder}
  python3 scripts/fetch_onedrive.py index "<share link>" work/assets-index.json

  # Download files whose path starts with any given prefix (or everything with no prefix)
  python3 scripts/fetch_onedrive.py get "<share link>" assets [prefix ...] [--exclude prefix] [--index docs/assets-catalog/index.json]
"""
import argparse
import base64
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

API = "https://my.microsoftpersonalcontent.com/_api/v2.0"
BADGER_APP_ID = "5cbed6ac-a083-4e14-b191-b4ba07653de2"


def share_id(link: str) -> str:
    return "u!" + base64.urlsafe_b64encode(link.encode()).decode().rstrip("=")


def get_token() -> str:
    req = urllib.request.Request(
        "https://api-badgerp.svc.ms/v1.0/token",
        data=json.dumps({"appId": BADGER_APP_ID}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["token"]


class Client:
    def __init__(self, link: str):
        self.sid = share_id(link)
        self.token = get_token()

    def get_json(self, url: str) -> dict:
        for attempt in range(6):
            req = urllib.request.Request(url, headers={
                "Authorization": f"Badger {self.token}", "Prefer": "autoredeem"})
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    return json.load(r)
            except urllib.error.HTTPError as e:
                if e.code == 401:
                    self.token = get_token()
                elif e.code not in (429, 500, 502, 503, 504):
                    raise
                time.sleep(int(e.headers.get("Retry-After", 2 ** attempt)))
            except (urllib.error.URLError, ConnectionError, TimeoutError):
                time.sleep(2 ** attempt)
        raise RuntimeError(f"giving up on {url}")

    def children(self, item_id: str | None):
        if item_id is None:
            url = f"{API}/shares/{self.sid}/driveitem/children?$top=500"
        else:
            drive = self.root["parentReference"]["driveId"]
            url = f"{API}/drives/{drive}/items/{item_id}/children?$top=500"
        while url:
            page = self.get_json(url)
            yield from page.get("value", [])
            url = page.get("@odata.nextLink")

    def walk(self):
        self.root = self.get_json(f"{API}/shares/{self.sid}/driveitem")
        out, stack = [], [(None, "")]
        while stack:
            item_id, prefix = stack.pop()
            for c in self.children(item_id):
                path = f"{prefix}{c['name']}"
                is_folder = "folder" in c
                out.append({"path": path + ("/" if is_folder else ""), "size": c.get("size", 0),
                            "id": c["id"], "folder": is_folder,
                            "mime": c.get("file", {}).get("mimeType", "")})
                if is_folder:
                    stack.append((c["id"], path + "/"))
            print(f"\rindexed {len(out)} items", end="", file=sys.stderr)
        print(file=sys.stderr)
        return sorted(out, key=lambda x: x["path"])

    def download(self, item: dict, dest: Path) -> str:
        target = dest / item["path"]
        if target.exists() and target.stat().st_size == item["size"]:
            return "skip"
        target.parent.mkdir(parents=True, exist_ok=True)
        drive = self.root["parentReference"]["driveId"]
        tmp = target.with_name(target.name + ".part")
        for attempt in range(5):
            try:
                # Download URLs are short-lived, so fetch a fresh one per attempt.
                meta = self.get_json(f"{API}/drives/{drive}/items/{item['id']}?select=id,@content.downloadUrl")
                with urllib.request.urlopen(meta["@content.downloadUrl"], timeout=300) as r, open(tmp, "wb") as f:
                    while chunk := r.read(1 << 20):
                        f.write(chunk)
                tmp.rename(target)
                return "ok"
            except Exception:
                time.sleep(2 ** attempt)
        return "fail"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["index", "get"])
    p.add_argument("link")
    p.add_argument("out")
    p.add_argument("prefixes", nargs="*")
    p.add_argument("--index", help="reuse a saved index instead of re-listing")
    p.add_argument("--exclude", action="append", default=[], help="skip paths starting with this (repeatable)")
    p.add_argument("--jobs", type=int, default=6)
    a = p.parse_args()

    c = Client(a.link)
    if a.index and Path(a.index).exists():
        items = json.loads(Path(a.index).read_text(encoding="utf-8"))
        c.root = c.get_json(f"{API}/shares/{c.sid}/driveitem")
    else:
        items = c.walk()

    if a.cmd == "index":
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(items, ensure_ascii=False, indent=0), encoding="utf-8")
        files = [i for i in items if not i["folder"]]
        print(f"{len(files)} files, {sum(i['size'] for i in files) / 1e9:.2f} GB -> {a.out}")
        return

    files = [i for i in items if not i["folder"]
             and (not a.prefixes or any(i["path"].startswith(px) for px in a.prefixes))
             and not any(i["path"].startswith(ex) for ex in a.exclude)]
    print(f"downloading {len(files)} files, {sum(i['size'] for i in files) / 1e9:.2f} GB -> {a.out}")
    dest = Path(a.out)
    results = {"ok": 0, "skip": 0, "fail": 0}
    failed = []
    with ThreadPoolExecutor(a.jobs) as ex:
        for n, (item, res) in enumerate(zip(files, ex.map(lambda i: c.download(i, dest), files)), 1):
            results[res] += 1
            if res == "fail":
                failed.append(item["path"])
            if n % 25 == 0 or n == len(files):
                print(f"{n}/{len(files)} {results}", flush=True)
    for f in failed:
        print("✗ failed:", f)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
