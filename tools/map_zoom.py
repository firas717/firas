#!/usr/bin/env python3
"""Space-to-site zoom on real NASA imagery (GIBS WMTS, public domain), as a 1080x1920 JPEG sequence.

usage: map_zoom.py out_dir [--frames 120]
Levels: Blue Marble NG (z5, z7) -> MODIS Terra true colour 2010-09-16 (z9) -> EO-1 ALI natural colour
image of the San José mine, 2010-09-16 (NASA Earth Observatory), crossfaded at the end.
"""
import io, math, os, sys, json, urllib.request
import numpy as np
from PIL import Image, ImageEnhance

OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
FRAMES = int(sys.argv[sys.argv.index('--frames') + 1]) if '--frames' in sys.argv else 120
CACHE = os.path.join(os.path.dirname(OUT.rstrip('/')), 'gibs_cache'); os.makedirs(CACHE, exist_ok=True)
W, H = 1080, 1920
LAT, LON = -27.157, -70.495            # San José mine (Wikipedia: 27°09′26″S 70°29′44″W)
EO1 = sys.argv[sys.argv.index('--eo1') + 1] if '--eo1' in sys.argv else None

LAYERS = {
    5: ("BlueMarble_NextGeneration", None, "GoogleMapsCompatible_Level8", "jpeg"),
    7: ("BlueMarble_NextGeneration", None, "GoogleMapsCompatible_Level8", "jpeg"),
    9: ("MODIS_Terra_CorrectedReflectance_TrueColor", "2010-09-16", "GoogleMapsCompatible_Level9", "jpg"),
}

def merc_px(lat, lon, z):
    n = 256 * 2 ** z
    x = (lon + 180) / 360 * n
    s = math.sin(math.radians(lat))
    y = (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * n
    return x, y

def tile(z, x, y):
    name, date, tms, ext = LAYERS[z]
    p = os.path.join(CACHE, f"{name}_{date}_{z}_{y}_{x}.{ext}")
    if not os.path.exists(p):
        d = f"/{date}" if date else ""
        url = f"https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/{name}/default{d}/{tms}/{z}/{y}/{x}.{ext}"
        if not date:
            url = f"https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/{name}/default/{tms}/{z}/{y}/{x}.{ext}"
        data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "FirasChannelEditor/1.0"}), timeout=60).read()
        open(p, "wb").write(data)
    return Image.open(p).convert("RGB")

def mosaic(z, half_w, half_h):
    """mosaic at zoom z covering +-half_w/half_h z-pixels around the mine; returns (img, x0, y0)"""
    cx, cy = merc_px(LAT, LON, z)
    x0, y0 = int(cx - half_w), int(cy - half_h)
    x1, y1 = int(cx + half_w), int(cy + half_h)
    tx0, ty0, tx1, ty1 = x0 // 256, y0 // 256, x1 // 256, y1 // 256
    img = Image.new("RGB", ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256))
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            img.paste(tile(z, tx % (2 ** z), ty), ((tx - tx0) * 256, (ty - ty0) * 256))
    return img, tx0 * 256, ty0 * 256

# zoom path, expressed as metres per output pixel (log-linear in time with eased ends)
m_per_px_z = lambda z: 156543.03 * math.cos(math.radians(LAT)) / 2 ** z
S_START, S_END = 5200.0, 8.0            # ~10,000 km tall frame (South America) -> ~15 km tall frame
def scale_at(u):
    e = u * u * (3 - 2 * u)              # smoothstep on log scale
    return math.exp(math.log(S_START) + (math.log(S_END) - math.log(S_START)) * e)

# build mosaics big enough for the frames where each level is used
mos = {}
for z, s_hi in [(5, S_START), (7, m_per_px_z(7) * 1.6), (9, m_per_px_z(9) * 1.6)]:
    k = s_hi / m_per_px_z(z)             # z-pixels per output pixel at the coarsest use
    mos[z] = mosaic(z, W / 2 * k * 1.05 + 256, H / 2 * k * 1.05 + 256)
    print("mosaic", z, mos[z][0].size, flush=True)

eo1 = None
if EO1:
    eo1 = Image.open(EO1).convert("RGB")
    eo1 = ImageEnhance.Contrast(eo1).enhance(1.08)
EO1_M_PER_PX = 10.0 * 3000 / eo1.width if eo1 else None    # ALI pan-sharpened ~10 m/px at native 3000 px

def render_level(z, s):
    img, ox, oy = mos[z]
    k = s / m_per_px_z(z)
    cx, cy = merc_px(LAT, LON, z)
    box = (cx - ox - W / 2 * k, cy - oy - H / 2 * k, cx - ox + W / 2 * k, cy - oy + H / 2 * k)
    return img.transform((W, H), Image.EXTENT, box, Image.BICUBIC)

for f in range(FRAMES):
    u = f / (FRAMES - 1)
    s = scale_at(u)
    # choose the finest level whose native resolution is <= 1.6x the needed scale, crossfade with the coarser one
    levels = [5, 7, 9]
    fine = min([z for z in levels if m_per_px_z(z) <= s * 1.6] or [max(levels)])
    frame = render_level(fine, s)
    coarse = [z for z in levels if z < fine]
    if coarse:
        zc = max(coarse)
        a = min(1.0, max(0.0, (math.log(m_per_px_z(fine) * 1.6) - math.log(s)) / math.log(1.6)))
        if a < 1.0:
            frame = Image.blend(render_level(zc, s), frame, a)
    if eo1 is not None and s < 160:
        # paste the EO-1 scene (10 m/px, mine at MX,MY) centred on the mine, feathered, fading in with zoom
        MX, MY = eo1.width * 0.46, eo1.height * 0.343   # mine complex (grey patch) located visually
        f_ = EO1_M_PER_PX / s                             # EO-1 px -> frame px
        # visible part of EO-1 in its own pixel coordinates
        sx0, sy0 = max(0, MX - W / 2 / f_), max(0, MY - H / 2 / f_)
        sx1, sy1 = min(eo1.width, MX + W / 2 / f_), min(eo1.height, MY + H / 2 / f_)
        dx0, dy0 = W / 2 + (sx0 - MX) * f_, H / 2 + (sy0 - MY) * f_
        dw, dh = max(1, int(round((sx1 - sx0) * f_))), max(1, int(round((sy1 - sy0) * f_)))
        part = eo1.transform((dw, dh), Image.EXTENT, (sx0, sy0, sx1, sy1), Image.BICUBIC)
        # feather only edges that are real image borders (not frame borders)
        mask = np.ones((dh, dw), np.float32); fe = max(2, int(0.22 * min(dw, dh)))
        ramp = np.linspace(0, 1, fe, dtype=np.float32)
        if sx0 <= 0.5: mask[:, :fe] *= ramp[None, :]
        if sx1 >= eo1.width - 0.5: mask[:, -fe:] *= ramp[::-1][None, :]
        if sy0 <= 0.5: mask[:fe, :] *= ramp[:, None]
        if sy1 >= eo1.height - 0.5: mask[-fe:, :] *= ramp[::-1][:, None]
        a = min(1.0, max(0.0, (math.log(160) - math.log(s)) / (math.log(160) - math.log(55))))
        a = a * a * (3 - 2 * a)
        m = Image.fromarray((mask * a * 255).astype(np.uint8))
        frame.paste(part, (int(round(dx0)), int(round(dy0))), m)
    frame.save(os.path.join(OUT, f"{f + 1:05d}.jpg"), quality=92)
print("frames", FRAMES)
