#!/usr/bin/env python3
"""Cut narrator poses out of Gemini sprite sheets on a magenta background.

For each sheet: key out magenta (including the darker purple ground shadows Gemini
adds), split the sheet into one image per character with connected components, add a
white outer stroke (the channel identity composites the narrator with one), and save
transparent PNGs plus a numbered preview sheet for naming.

All poses share one scale: a standing pose comes out ~900px tall, and a crouching or
lying pose keeps its true size relative to that. The scale of each sheet is derived
from the size of the character's white face (Gemini draws every pose on a sheet at
the same scale), so poses from different sheets also match each other.

Usage:
  python3 scripts/poses/extract_poses.py <out_dir> <sheet.jpg> [<sheet.jpg> ...]
Then rename the numbered files (NNN.png) to pose names, e.g. point-left.png.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

FACE_AREA_REF = 9700  # face area (px) of a pose scaled so a standing pose is ~900px tall
STROKE = 7            # white outer stroke width (px)
MIN_AREA = 0.004      # components smaller than this share of the sheet are props/marks


def face_area(rgb: np.ndarray, alpha: np.ndarray, member: np.ndarray) -> int:
    """Area of the largest solid-white region (the blank face) inside one pose."""
    white = (rgb.min(axis=2) > 225) & (alpha > 0.5) & member
    labels, n = ndimage.label(white)
    return int(np.bincount(labels.ravel())[1:].max()) if n else 0


def key_magenta(rgb: np.ndarray) -> np.ndarray:
    """Alpha in [0,1]: 0 where the pixel is magenta/purple (background or its shadow)."""
    r, g, b = (rgb[..., i].astype(np.float32) for i in range(3))
    magenta = np.minimum(r, b) - g          # high for magenta and dark purple, ~0 for greys/navy/white
    alpha = np.clip(1.0 - (magenta - 35.0) / 50.0, 0.0, 1.0)
    return alpha


def despill(rgb: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    """Pull leftover magenta tint out of edge pixels."""
    out = rgb.astype(np.float32)
    r, g, b = out[..., 0], out[..., 1], out[..., 2]
    cap = g + 20.0
    edge = alpha < 0.999
    out[..., 0] = np.where(edge, np.minimum(r, np.maximum(cap, g)), r)
    out[..., 2] = np.where(edge, np.minimum(b, np.maximum(cap, g)), b)
    return np.clip(out, 0, 255).astype(np.uint8)


def components(alpha: np.ndarray, sheet_area: int):
    solid = alpha > 0.5
    # Join hands/props/motion marks to their body: dilate before labelling.
    grown = ndimage.binary_dilation(solid, iterations=max(6, int(alpha.shape[1] * 0.012)))
    labels, n = ndimage.label(grown)
    boxes = ndimage.find_objects(labels)
    out = []
    min_area = sheet_area * MIN_AREA
    for i, sl in enumerate(boxes, 1):
        if sl is None:
            continue
        member = labels[sl] == i
        mask = member & solid[sl]
        if mask.sum() < min_area:
            continue
        # Dilation can bridge poses stacked in one column: split at fully empty row bands.
        rows = mask.any(axis=1)
        cuts, run = [], 0
        for y, filled in enumerate(rows):
            run = 0 if filled else run + 1
            if run == 8:
                cuts.append(y)
        parts, start = [], 0
        for c in cuts + [len(rows)]:
            if mask[start:c].sum() > 0:
                parts.append([start, c])
            start = c
        # Small parts (motion marks above a head) rejoin the part below them.
        merged = []
        for p in parts:
            if merged and mask[merged[-1][0]:merged[-1][1]].sum() < min_area:
                merged[-1][1] = p[1]
            elif mask[p[0]:p[1]].sum() < min_area and merged is not None and parts.index(p) + 1 < len(parts):
                nxt = parts[parts.index(p) + 1]
                nxt[0] = p[0]
            else:
                merged.append(p)
        for a, b in merged:
            sub = (slice(sl[0].start + a, sl[0].start + b), sl[1])
            sub_member = np.zeros_like(member)
            sub_member[a:b] = member[a:b]
            if (sub_member & solid[sl]).sum() >= min_area:
                out.append((sub, sub_member[a:b]))
    # Reading order: rows top to bottom, then left to right.
    out.sort(key=lambda t: (round(t[0][0].start / (alpha.shape[0] / 8)), t[0][1].start))
    return out


def add_stroke(img: Image.Image, px: int) -> Image.Image:
    pad = px + 4
    canvas = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad), (0, 0, 0, 0))
    canvas.alpha_composite(img, (pad, pad))
    a = canvas.getchannel("A").point(lambda v: 255 if v > 40 else 0)
    grown = a.filter(ImageFilter.MaxFilter(2 * px + 1)).filter(ImageFilter.GaussianBlur(0.8))
    stroke = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
    stroke.putalpha(grown)
    stroke.alpha_composite(canvas)
    return stroke


def main() -> None:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    previews = []
    for sheet_path in sys.argv[2:]:
        rgb = np.array(Image.open(sheet_path).convert("RGB"))
        alpha = key_magenta(rgb)
        comps = components(alpha, rgb.shape[0] * rgb.shape[1])
        faces = [face_area(rgb[sl], alpha[sl], member) for sl, member in comps]
        # Median is robust to poses whose face is hidden (camera, back view, facepalm).
        scale = (FACE_AREA_REF / max(np.median(faces), 1)) ** 0.5
        rgb = despill(rgb, alpha)
        rgba = np.dstack([rgb, (alpha * 255).astype(np.uint8)])
        for sl, member in comps:
            crop = rgba[sl].copy()
            crop[..., 3] = np.where(member, crop[..., 3], 0)
            img = Image.fromarray(crop, "RGBA")
            img = img.crop(img.getbbox())
            img = img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.LANCZOS)
            img = add_stroke(img, STROKE)
            n += 1
            img.save(out / f"{n:03d}.png", optimize=True)
            previews.append((n, img, Path(sheet_path).name))
        print(f"{sheet_path}: total {n}", flush=True)

    # Numbered preview sheets (on dark grey, like the channel background).
    cell, cols = 230, 8
    font = ImageFont.load_default(size=26)
    for s in range(0, len(previews), 48):
        chunk = previews[s:s + 48]
        sheet = Image.new("RGB", (cols * cell, ((len(chunk) - 1) // cols + 1) * cell), (28, 31, 34))
        d = ImageDraw.Draw(sheet)
        for i, (num, img, _) in enumerate(chunk):
            t = img.copy()
            t.thumbnail((cell - 10, cell - 34))
            x, y = (i % cols) * cell, (i // cols) * cell
            sheet.paste(t, (x + (cell - t.width) // 2, y + 30), t)
            d.text((x + 6, y + 2), str(num), fill=(255, 210, 60), font=font)
        sheet.save(out / f"_preview_{s // 48 + 1}.jpg", quality=80)


if __name__ == "__main__":
    main()
