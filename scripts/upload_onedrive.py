#!/usr/bin/env python3
"""Upload a large file into a folder of a personal OneDrive share link that allows editing.

Uses the same anonymous "badger" token as fetch_onedrive.py and a resumable upload session
(chunks of 60 MiB), so a 700MB 4K master survives a dropped connection.

Usage:
  python3 scripts/upload_onedrive.py "<edit share link>" "<sub-folder name or .>" <file> [remote name]

The link is an edit link to Firas's OneDrive: pass it on the command line only, never save it
in the repository (the repository is public).
"""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from fetch_onedrive import API, Client

CHUNK = 320 * 1024 * 192  # 60 MiB, a multiple of 320 KiB as the API requires


def request(method, url, data=None, headers=None, timeout=600):
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read()
        return r.status, json.loads(body) if body else {}


def main():
    link, sub, path = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    name = sys.argv[4] if len(sys.argv) > 4 else path.name
    c = Client(link)
    root = c.get_json(f"{API}/shares/{c.sid}/driveitem")
    drive = root["parentReference"]["driveId"]
    parent = root["id"]
    if sub != ".":
        kids = c.get_json(f"{API}/shares/{c.sid}/driveitem/children?$top=500")["value"]
        match = [k for k in kids if k["name"] == sub and "folder" in k]
        if not match:
            sys.exit(f"folder not found in the share: {sub}")
        parent = match[0]["id"]
    auth = {"Authorization": f"Badger {c.token}", "Content-Type": "application/json"}
    url = f"{API}/drives/{drive}/items/{parent}:/{urllib.parse.quote(name)}:/createUploadSession"
    _, sess = request("POST", url, json.dumps({"item": {"@microsoft.graph.conflictBehavior": "rename"}}).encode(), auth)
    upload_url = sess["uploadUrl"]
    size = path.stat().st_size
    pos, t0 = 0, time.time()
    with path.open("rb") as f:
        while pos < size:
            f.seek(pos)
            data = f.read(min(CHUNK, size - pos))
            end = pos + len(data) - 1
            for attempt in range(8):
                try:
                    status, body = request("PUT", upload_url, data, {
                        "Content-Length": str(len(data)), "Content-Range": f"bytes {pos}-{end}/{size}"})
                    break
                except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
                    print(f"  chunk at {pos} failed ({e}); retrying", flush=True)
                    time.sleep(2 ** attempt)
                    # ask the session where it wants to continue
                    try:
                        _, st = request("GET", upload_url)
                        nxt = st.get("nextExpectedRanges", [f"{pos}-"])[0]
                        pos = int(nxt.split("-")[0])
                        f.seek(pos)
                        data = f.read(min(CHUNK, size - pos))
                        end = pos + len(data) - 1
                    except Exception:
                        pass
            else:
                sys.exit("upload failed after retries")
            pos = end + 1
            mb = pos / 1048576
            print(f"  {mb:7.1f} / {size / 1048576:.1f} MiB  ({mb / max(time.time() - t0, 1e-3):.1f} MiB/s)", flush=True)
    if status not in (200, 201) or "id" not in body:
        sys.exit(f"upload did not complete: {status} {body}")
    print(f"uploaded: {body['name']}  {body['size']} bytes  id={body['id']}")


if __name__ == "__main__":
    main()
