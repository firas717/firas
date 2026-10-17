#!/usr/bin/env python3
"""Recreate the owner's reference backgrounds at full resolution in brand colours.

Outputs (PNG) into the given folder:
  topo_night.png   - topographic contour lines (amber-dim on night bg), 1400x2400 for slow pans
  topo_day.png     - same field, day palette
  grid_night.png   - square grid, muted lines on night bg with a soft amber glow from the bottom
  paper.png        - crumpled paper (procedural Voronoi facets + fibres), 1600x1200
"""
import sys, os
import numpy as np
from PIL import Image, ImageFilter
from scipy.ndimage import gaussian_filter

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
rng = np.random.default_rng(33)

def hex2rgb(h):
    h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)

NIGHT_BG, SURF, BORDER = hex2rgb('#0B0E13'), hex2rgb('#141922'), hex2rgb('#2A3340')
AMBER, AMBER_DIM, MUTED = hex2rgb('#E9A13B'), hex2rgb('#B87C25'), hex2rgb('#9AA3B0')
DAY_BG, DAY_BORDER = hex2rgb('#F3F0E9'), hex2rgb('#D2CCC0')

def smooth_noise(h, w, scale, octaves=4):
    """fractal value noise via upsampled random grids"""
    acc = np.zeros((h, w), np.float32); amp, tot = 1.0, 0.0
    for o in range(octaves):
        gh, gw = max(2, int(h / scale * 2 ** o)), max(2, int(w / scale * 2 ** o))
        g = rng.random((gh, gw)).astype(np.float32)
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        acc += amp * np.asarray(im, np.float32) / 255; tot += amp; amp *= 0.5
    return acc / tot

def contour_mask(field, levels, width_px):
    """anti-aliased iso-lines: distance to nearest level in units of local gradient"""
    f = field * levels
    frac = np.abs(f - np.round(f))                       # 0 at a level
    gy, gx = np.gradient(f)
    g = np.sqrt(gx ** 2 + gy ** 2) + 1e-6
    d = frac / g                                         # approx pixel distance to the line
    return np.clip(1.0 - (d - width_px / 2), 0, 1)

def topo(w, h, bg, line, path, ss=2):
    W, H = w * ss, h * ss
    field = smooth_noise(H, W, scale=1300 * ss / 2, octaves=2)
    field = gaussian_filter(field, 14 * ss)
    m = contour_mask((field - field.min()) / (np.ptp(field) + 1e-6), levels=16, width_px=2.2 * ss)
    img = bg[None, None, :] * (1 - m[..., None]) + line[None, None, :] * m[..., None]
    Image.fromarray(img.clip(0, 255).astype(np.uint8)).resize((w, h), Image.LANCZOS).save(path)

def grid(w, h, path, cell=96):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    glow = np.clip((y / h - 0.45) / 0.55, 0, 1) ** 1.6     # amber glow rising from the bottom
    base = NIGHT_BG[None, None, :] * (1 - 0.55 * glow[..., None]) + AMBER_DIM[None, None, :] * 0.55 * glow[..., None]
    lx = np.minimum(np.abs((x - w / 2) % cell), cell - np.abs((x - w / 2) % cell))
    ly = np.minimum(np.abs(y % cell), cell - np.abs(y % cell))
    line = np.clip(1.2 - np.minimum(lx, ly), 0, 1) * 0.55
    col = MUTED * 0.55 + BORDER * 0.45
    img = base * (1 - line[..., None]) + col[None, None, :] * line[..., None]
    Image.fromarray(img.clip(0, 255).astype(np.uint8)).save(path)

def paper(w, h, path, ridges=46):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    hgt = np.zeros((h, w), np.float32)
    for _ in range(ridges):
        ang = rng.uniform(0, np.pi); d = np.array([np.cos(ang), np.sin(ang)])
        c = rng.uniform(-0.2, 1.2) * (abs(d[0]) * w + abs(d[1]) * h)
        amp = rng.uniform(0.02, 0.09) * rng.choice([-1, 1])
        hgt += amp * np.abs(x * d[0] + y * d[1] - c)
    for _ in range(140):  # short local creases
        cx, cy, r = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(80, 260)
        ang = rng.uniform(0, np.pi); d = np.array([np.cos(ang), np.sin(ang)])
        env = np.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2 * r * r))
        hgt += rng.uniform(0.05, 0.16) * rng.choice([-1, 1]) * env * np.abs((x - cx) * d[0] + (y - cy) * d[1])
    hgt = gaussian_filter(hgt, 1.4)
    gy, gx = np.gradient(hgt)
    n = np.stack([-gx, -gy, np.ones_like(gx)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    light = np.array([-0.5, -0.6, 0.62]); light /= np.linalg.norm(light)
    shade = n @ light
    shade = (shade - np.median(shade)) / (np.percentile(shade, 98) - np.percentile(shade, 2) + 1e-6)
    fib = smooth_noise(h, w, scale=5, octaves=2)
    blot = smooth_noise(h, w, scale=400, octaves=3)
    base = hex2rgb('#F2EFE9')
    v = (0.93 + 0.15 * shade + 0.03 * (fib - 0.5) - 0.04 * (blot - 0.5))[..., None]
    Image.fromarray((base[None, None, :] * v).clip(0, 255).astype(np.uint8)).save(path)

topo(1400, 2400, NIGHT_BG, NIGHT_BG * 0.45 + MUTED * 0.30 + AMBER_DIM * 0.25, f"{out}/topo_night.png")
topo(1400, 2400, DAY_BG, DAY_BG * 0.45 + DAY_BORDER * 0.35 + AMBER_DIM * 0.2, f"{out}/topo_day.png")
grid(1080, 1920, f"{out}/grid_night.png")
paper(1600, 1200, f"{out}/paper.png")
print("ok")
