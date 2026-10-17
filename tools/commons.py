#!/usr/bin/env python3
"""Polite Wikimedia Commons client: category listing, file metadata, downloads.

Respects Retry-After on HTTP 429 and keeps a JSON cache so repeated runs
do not hit the API again.
"""
import json, os, sys, time, urllib.parse, urllib.request, hashlib

UA = "FirasChannelEditor/1.0 (https://github.com/firas717/firas; documentary editing)"
API = "https://commons.wikimedia.org/w/api.php"
CACHE = os.environ.get("COMMONS_CACHE", os.path.join(os.path.dirname(__file__), ".commons-cache"))
os.makedirs(CACHE, exist_ok=True)


def _get(url, binary=False, tries=12):
    delay = 5
    for i in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
                return data if binary else data.decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                wait = int(e.headers.get("Retry-After") or delay)
                print(f"  429 -> waiting {wait}s", file=sys.stderr)
                time.sleep(wait + 1)
                delay = min(delay * 2, 120)
                continue
            raise
        except Exception as e:
            print(f"  error {e} -> retry in {delay}s", file=sys.stderr)
            time.sleep(delay)
            delay = min(delay * 2, 120)
    raise RuntimeError(f"giving up on {url}")


def api(**params):
    params.setdefault("format", "json")
    params.setdefault("formatversion", "2")
    q = urllib.parse.urlencode(params)
    key = hashlib.md5(q.encode()).hexdigest()
    path = os.path.join(CACHE, key + ".json")
    if os.path.exists(path):
        return json.load(open(path))
    data = json.loads(_get(f"{API}?{q}"))
    json.dump(data, open(path, "w"))
    time.sleep(1.0)
    return data


def category_files(cat, depth=0):
    """All File: titles in a category (optionally one level of subcategories)."""
    out, subcats, cont = [], [], {}
    while True:
        d = api(action="query", list="categorymembers", cmtitle=cat, cmlimit="500",
                cmtype="file|subcat", **cont)
        for m in d["query"]["categorymembers"]:
            if m["ns"] == 6:
                out.append(m["title"])
            elif m["ns"] == 14:
                subcats.append(m["title"])
        if "continue" in d:
            cont = {"cmcontinue": d["continue"]["cmcontinue"]}
        else:
            break
    if depth > 0:
        for s in subcats:
            out += category_files(s, depth - 1)[0]
    return out, subcats


def file_info(titles, thumb_width=None):
    """imageinfo + extmetadata for up to 50 titles per call."""
    res = {}
    for i in range(0, len(titles), 40):
        chunk = titles[i:i + 40]
        params = dict(action="query", titles="|".join(chunk), prop="imageinfo",
                      iiprop="url|size|mime|extmetadata")
        if thumb_width:
            params["iiurlwidth"] = str(thumb_width)
        d = api(**params)
        for p in d["query"]["pages"]:
            if "imageinfo" not in p:
                continue
            ii = p["imageinfo"][0]
            md = ii.get("extmetadata", {})
            g = lambda k: (md.get(k) or {}).get("value", "")
            res[p["title"]] = {
                "title": p["title"], "url": ii["url"], "thumb": ii.get("thumburl"),
                "width": ii["width"], "height": ii["height"], "mime": ii["mime"],
                "page": ii.get("descriptionurl"),
                "license": g("LicenseShortName"), "license_url": g("LicenseUrl"),
                "artist": g("Artist"), "credit": g("Credit"),
                "date": g("DateTimeOriginal") or g("DateTime"),
                "description": g("ImageDescription"),
                "usage_terms": g("UsageTerms"), "restrictions": g("Restrictions"),
            }
    return res


def download(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return dest
    data = _get(url, binary=True)
    with open(dest, "wb") as f:
        f.write(data)
    time.sleep(0.5)
    return dest


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "cat":
        files, subs = category_files(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 0)
        print(json.dumps({"files": files, "subcats": subs}, ensure_ascii=False, indent=1))
    elif cmd == "info":
        titles = json.load(open(sys.argv[2]))
        print(json.dumps(file_info(titles, 800), ensure_ascii=False, indent=1))
    elif cmd == "search":
        d = api(action="query", list="search", srsearch=sys.argv[2], srnamespace="6", srlimit="50")
        print(json.dumps([s["title"] for s in d["query"]["search"]], ensure_ascii=False, indent=1))
