#!/usr/bin/env python3
"""Build numbered contact sheets so images and videos can be reviewed visually.

Each folder group gets sheets of up to 48 cells (8x6). Every cell shows a thumbnail
(transparent PNGs on a checkerboard; videos as 3 frames) and its number. A JSON map
<out>/sheets.json links "<sheet>#<n>" to the asset path.

Usage: python3 scripts/catalog/sheets.py assets docs/assets-catalog/sheets
"""
import io
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from analyze import AUDIO, IMAGE, SKIP_DIRS, VIDEO  # noqa: E402

CELL, COLS, ROWS = 220, 8, 6
FONT = ImageFont.load_default(size=22)


def checker(w: int, h: int) -> Image.Image:
    bg = Image.new("RGB", (w, h), (90, 90, 90))
    d = ImageDraw.Draw(bg)
    for y in range(0, h, 16):
        for x in range((y // 16) % 2 * 16, w, 32):
            d.rectangle([x, y, x + 15, y + 15], fill=(120, 120, 120))
    return bg


def thumb_image(p: Path) -> Image.Image:
    im = Image.open(p)
    im.seek(0)
    im = im.convert("RGBA")
    im.thumbnail((CELL - 8, CELL - 30))
    bg = checker(*im.size).convert("RGBA")
    bg.alpha_composite(im)
    return bg.convert("RGB")


def thumb_video(p: Path) -> Image.Image:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True)
    dur = float(r.stdout.strip() or 0)
    frames = []
    for t in (dur * 0.15, dur * 0.5, dur * 0.85):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(p), "-frames:v", "1",
                              "-vf", f"scale={CELL - 8}:-2", "-f", "image2pipe", "-vcodec", "png", "-"],
                             capture_output=True).stdout
        if raw:
            frames.append(Image.open(io.BytesIO(raw)).convert("RGBA"))
    if not frames:
        raise ValueError("no frames")
    h = (CELL - 30) // 3
    strip = checker(CELL - 8, h * 3).convert("RGBA")
    for i, f in enumerate(frames):
        f.thumbnail((CELL - 8, h))
        strip.alpha_composite(f, (0, i * h))
    return strip.convert("RGB")


def main() -> None:
    root, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    groups = defaultdict(list)
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.name.endswith(".part"):
            continue
        r = str(p.relative_to(root))
        ext = p.suffix.lower()
        if r.startswith(SKIP_DIRS) or "(Preview)/" in r or ext in AUDIO or ext not in IMAGE | VIDEO:
            continue
        if ext in VIDEO and any(p.with_suffix(e).exists() for e in AUDIO):
            continue  # sound-library preview
        parts = r.split("/")
        key = "/".join(parts[:2]) if len(parts) > 2 else parts[0] if len(parts) > 1 else "_root"
        groups[key].append(p)

    mapping = {}
    for key, items in groups.items():
        slug = key.replace("/", "__").replace(" ", "_")
        per = COLS * ROWS
        for s in range(0, len(items), per):
            chunk = items[s:s + per]
            sheet = Image.new("RGB", (COLS * CELL, ((len(chunk) - 1) // COLS + 1) * CELL), (30, 30, 30))
            d = ImageDraw.Draw(sheet)
            name = f"{slug}__{s // per + 1:02d}.jpg"
            for i, p in enumerate(chunk):
                x, y = (i % COLS) * CELL, (i // COLS) * CELL
                try:
                    t = thumb_video(p) if p.suffix.lower() in VIDEO else thumb_image(p)
                    sheet.paste(t, (x + 4, y + 26))
                except Exception:  # noqa: BLE001
                    d.text((x + 10, y + 100), "unreadable", fill=(255, 80, 80), font=FONT)
                n = s + i + 1
                d.text((x + 6, y + 2), f"{n}{' ▶' if p.suffix.lower() in VIDEO else ''}", fill=(255, 220, 60), font=FONT)
                mapping[f"{name}#{n}"] = str(p.relative_to(root))
            sheet.save(out / name, quality=72)
            print(name, len(chunk), flush=True)
    (out / "sheets.json").write_text(json.dumps(mapping, ensure_ascii=False, indent=0), encoding="utf-8")


if __name__ == "__main__":
    main()
