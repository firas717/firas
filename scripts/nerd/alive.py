#!/usr/bin/env python3
"""Bring a pose image to life without cutting it into limbs.

The pose stays ONE image (Firas's rule: no separate limbs). We bend it with a
moving-least-squares rigid warp (Schaefer et al. 2006): a few handles (feet,
hips, chest, head, hands) move a little every frame and the whole picture
follows smoothly, so nothing can come apart at the joints. Small handle moves
read as a real body: breathing, weight shifts, head nods, hand gestures on the
stressed words, a laugh, a tremble, a bobbing walk.

Rig (handles in image pixels) comes from rig.json next to the image when it has
an entry, otherwise it is detected: the faces and hands of this cast are plain
white shapes inside the black outline.

  python3 scripts/nerd/alive.py rig <png> ...           # print detected rigs
  python3 scripts/nerd/alive.py sheet <out.jpg> <png>... # rig overlay for checking
  python3 scripts/nerd/alive.py demo <png> <style> <out.mp4> [seconds]
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

FPS = 60
MOTION_VERSION = 1   # bump when the motion code changes, so cached clips are rebuilt
REPO = Path(__file__).resolve().parents[2]
RIG_FILES = [REPO / "brand/narrator-poses/rig.json"] + sorted(REPO.glob("brand/characters/*/rig.json"))


# ---------------------------------------------------------------------------- image
def load_rgba(path):
    return np.array(Image.open(path).convert("RGBA"))


# ---------------------------------------------------------------------------- rig
def rig_for(path):
    """Rig from <dir>/rig.json if present (keys are file stems), else detected."""
    path = Path(path)
    f = path.parent / "rig.json"
    if f.exists():
        r = json.loads(f.read_text()).get(path.stem)
        if r:
            return r
    return detect_rig(load_rgba(path))


def find_rig(path):
    """Corrected rig from the brand library (by file name), else detected from the image."""
    stem = Path(path).stem
    for f in RIG_FILES:
        r = json.loads(f.read_text()).get(stem)
        if r:
            return r
    return detect_rig(load_rgba(path))


def detect_rig(im):
    a = im[..., 3] > 128
    ys, xs = np.nonzero(a)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    h = y1 - y0
    # white interiors (face, hands): drop the outer white stroke by eroding the silhouette
    inner = cv2.erode(a.astype(np.uint8), np.ones((15, 15), np.uint8)) > 0
    rgb = im[..., :3].astype(int)
    white = inner & (rgb.min(axis=2) > 215) & (rgb.max(axis=2) - rgb.min(axis=2) < 30)
    n, lab, st, cen = cv2.connectedComponentsWithStats(white.astype(np.uint8), 8)
    blobs = [(st[k, cv2.CC_STAT_AREA], cen[k]) for k in range(1, n) if st[k, cv2.CC_STAT_AREA] > 0.0012 * a.sum()]
    blobs.sort(key=lambda b: -b[0])
    head = None
    top = [b for b in blobs if b[1][1] < y0 + 0.35 * h]
    if top:
        head = max(top, key=lambda b: b[0])
    hands = [b for b in blobs if b is not head and b[0] < 0.03 * a.sum()][:2]

    def row_center(y):
        r = np.nonzero(a[int(y)])[0]
        return float((r.min() + r.max()) / 2) if len(r) else float((x0 + x1) / 2)

    hip_y = y0 + 0.55 * h
    chest_y = y0 + 0.33 * h
    rig = {
        "bbox": [int(x0), int(y0), int(x1), int(y1)],
        "feet_y": float(y1 - 0.06 * h),
        "hip": [row_center(hip_y), float(hip_y)],
        "chest": [row_center(chest_y), float(chest_y)],
        "head": [float(head[1][0]), float(head[1][1])] if head else [row_center(y0 + 0.12 * h), float(y0 + 0.12 * h)],
        "hands": [[float(b[1][0]), float(b[1][1])] for b in hands],
    }
    return rig


# ---------------------------------------------------------------------------- MLS rigid warp
def mls_rigid_inverse(src_pts, dst_pts, shape, step=6, alpha=1.6):
    """Backward map for cv2.remap: for every output pixel, where to sample the source.
    MLS from the deformed handles (dst) to the original ones (src), evaluated on a grid."""
    h, w = shape
    gy, gx = np.mgrid[0:h + step:step, 0:w + step:step].astype(np.float64)
    v = np.stack([gx.ravel(), gy.ravel()], 1)                      # (N,2)
    p, q = np.asarray(dst_pts, float), np.asarray(src_pts, float)  # map output -> source
    d2 = ((v[:, None, :] - p[None]) ** 2).sum(2)                   # (N,K)
    wgt = 1.0 / np.maximum(d2, 1e-6) ** alpha
    ws = wgt.sum(1, keepdims=True)
    ps = wgt @ p / ws
    qs = wgt @ q / ws
    ph = p[None] - ps[:, None]
    qh = q[None] - qs[:, None]
    vp = v - ps
    # rigid MLS: f_r(v) = sum_i qh_i A_i,  A_i = w_i [ph; -ph_perp] [vp; -vp_perp]^T
    ph_perp = np.stack([-ph[..., 1], ph[..., 0]], -1)
    vp_perp = np.stack([-vp[:, 1], vp[:, 0]], -1)[:, None]
    a11 = (ph * vp[:, None]).sum(-1)
    a12 = (ph * -vp_perp).sum(-1)
    a21 = (-ph_perp * vp[:, None]).sum(-1)
    a22 = (-ph_perp * -vp_perp).sum(-1)
    fx = (wgt * (qh[..., 0] * a11 + qh[..., 1] * a21)).sum(1)
    fy = (wgt * (qh[..., 0] * a12 + qh[..., 1] * a22)).sum(1)
    fr = np.stack([fx, fy], 1)
    n = np.linalg.norm(fr, axis=1, keepdims=True)
    res = np.linalg.norm(vp, axis=1, keepdims=True) * fr / np.maximum(n, 1e-9) + qs
    mx = res[:, 0].reshape(gy.shape).astype(np.float32)
    my = res[:, 1].reshape(gy.shape).astype(np.float32)
    # upsample the coarse grid exactly: full-res pixel (x, y) sits at grid index (x/step, y/step)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    gu, gv = xx / step, yy / step
    return (cv2.remap(mx, gu, gv, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE),
            cv2.remap(my, gu, gv, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE))


def warp(im, mx, my):
    # premultiply so transparent edges do not bleed dark fringes
    f = im.astype(np.float32)
    f[..., :3] *= f[..., 3:4] / 255.0
    out = cv2.remap(f, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    out = np.clip(out, 0, 255)
    al = np.maximum(out[..., 3:4], 1e-3)
    out[..., :3] = np.where(out[..., 3:4] > 0.5, out[..., :3] * 255.0 / al, 0)
    return np.clip(out, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------- motion
def alpha_fn(tau, peak):
    """Smooth gesture pulse: 0 at tau<=0, rises to 1 at `peak` seconds, decays (alpha function)."""
    tau = np.maximum(tau, 0.0)
    x = tau / peak
    return np.where(tau > 0, x * np.exp(1 - x), 0.0)


def pulses(t, beats, peak=0.16):
    return float(sum(alpha_fn(np.array(t - b), peak) for b in beats))


def rot(pts, pivot, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    d = np.asarray(pts, float) - pivot
    return np.stack([d[:, 0] * c - d[:, 1] * s, d[:, 0] * s + d[:, 1] * c], 1) + pivot


# which way each style moves the body. All amplitudes are fractions of the figure height.
STYLES = {
    "idle": {},
    "talk": {"hands": 0.05, "nod": 1.0},
    "point": {"pump": 0.045, "lean": 0.014, "nod": 0.8},
    "present": {"hands": 0.045, "lean": 0.012, "nod": 1.0},
    "count": {"hands": 0.035, "nod": 1.0},
    "tremble": {"tremble": 0.006, "recoil": 0.045},
    "laugh": {"laugh": 0.014},
    "think": {"tilt": 5.0, "slow": True, "nod": 0.6},
    "search": {"scan": 0.04, "lean": 0.012},
    "shake": {"shake": 7.0},
    "cheer": {"pump": 0.06, "bounce": 0.015},
    "wide": {"shrug": 0.045, "nod": 0.6},
    "hop": {"hop": 0.08, "hands": 0.03},
    "walk": {"walk": 1.0},
    "hold": {"nod": 0.8},
}


class Rig:
    def __init__(self, im, rig):
        self.im = im
        self.r = rig
        x0, y0, x1, y1 = rig["bbox"]
        self.h = float(y1 - y0)
        self.feet_y = rig["feet_y"]
        a = im[..., 3] > 128

        def extent(y):
            row = np.nonzero(a[int(min(max(y, 0), a.shape[0] - 1))])[0]
            return (float(row.min()), float(row.max())) if len(row) else (float(x0), float(x1))
        self.hip = np.array(rig["hip"], float)
        self.chest = np.array(rig["chest"], float)
        self.head = np.array(rig["head"], float)
        self.neck = (self.chest * 0.45 + self.head * 0.55)
        h = self.h
        fl, fr = extent(self.feet_y)
        bl, br = extent(y1 - 2)
        self.g_feet = np.array([[fl, self.feet_y], [(fl + fr) / 2, self.feet_y], [fr, self.feet_y],
                                [bl, y1], [br, y1]], float)
        hl, hr = extent(self.hip[1])
        self.g_hip = np.array([self.hip, [hl + 0.25 * (self.hip[0] - hl), self.hip[1]],
                               [hr - 0.25 * (hr - self.hip[0]), self.hip[1]]], float)
        self.g_chest = np.array([self.chest, [self.chest[0] - 0.09 * h, self.chest[1]],
                                 [self.chest[0] + 0.09 * h, self.chest[1]]], float)
        hx, hy = self.head
        self.g_head = np.array([[hx, hy], [hx - 0.06 * h, hy], [hx + 0.06 * h, hy], [hx, hy - 0.08 * h]], float)
        self.hands = [np.array(p, float) for p in rig.get("hands", [])]
        # a hand touching the head (chin, ear, cap) moves with the head
        self.hand_on_head = [np.linalg.norm(p - self.head) < 0.16 * h for p in self.hands]
        self.src = np.vstack([self.g_feet, self.g_hip, self.g_chest, self.g_head] + [p[None] for p in self.hands])

    def targets(self, t, style, beats, seed=0):
        """Handle positions at time t (seconds since the layer appeared)."""
        S = STYLES[style]
        h = self.h
        ph = (seed * 0.37) % 1 * 2 * math.pi
        slow = 0.6 if S.get("slow") else 1.0
        # base life: breathing, weight shift, head drift
        breath = 0.5 - 0.5 * math.cos(2 * math.pi * t / 3.2 + ph)
        sway = math.sin(2 * math.pi * t / (4.4 / slow) + ph)
        hip_d = np.array([0.008 * h * sway, 0.0])
        chest_d = np.array([0.014 * h * sway, -0.009 * h * breath])
        head_deg = 2.0 * math.sin(2 * math.pi * t / 5.1 + ph * 1.7) - 1.0 * sway
        head_d = chest_d * 1.15
        hand_d = [chest_d.copy() for _ in self.hands]
        lift = np.zeros(2)  # whole figure (hop)
        p = pulses(t, beats)
        dirx = 1.0
        if self.hands:
            far = max(self.hands, key=lambda q: abs(q[0] - self.chest[0]))
            dirx = 1.0 if far[0] >= self.chest[0] else -1.0
        if "nod" in S:
            head_d = head_d + np.array([0, 0.022 * h * p * S["nod"]])
        if "hands" in S:
            for k in range(len(hand_d)):
                pk = pulses(t, beats[k % 2::2] if len(self.hands) > 1 else beats)
                hand_d[k] = hand_d[k] + np.array([0.012 * h * pk * dirx, -S["hands"] * h * pk])
        if "pump" in S and self.hands:
            k = max(range(len(self.hands)), key=lambda i: abs(self.hands[i][0] - self.chest[0]) + abs(self.hands[i][1] - self.chest[1]) * 0.3)
            v = self.hands[k] - self.chest
            v = v / (np.linalg.norm(v) + 1e-6)
            hand_d[k] = hand_d[k] + v * S["pump"] * h * p
        if "lean" in S:
            lean = S["lean"] * h * (0.6 + 0.4 * p)
            chest_d = chest_d + np.array([lean * dirx, 0])
            head_d = head_d + np.array([1.4 * lean * dirx, 0])
        if "tremble" in S:
            tr = S["tremble"] * h
            jig = lambda f, o: math.sin(2 * math.pi * f * t + o) * 0.6 + math.sin(2 * math.pi * f * 1.37 * t + o * 2) * 0.4
            for k in range(len(hand_d)):
                hand_d[k] = hand_d[k] + np.array([tr * jig(9, k), tr * jig(8, k + 1)])
            head_d = head_d + np.array([tr * 0.5 * jig(7, 3), 0])
            rec = S["recoil"] * h * float(alpha_fn(np.array(t - 0.05), 0.18))
            chest_d = chest_d + np.array([-rec * dirx * 0.6, -rec * 0.3])
            head_d = head_d + np.array([-rec * dirx, -rec * 0.4])
        if "laugh" in S:
            env = min(1.0, p * 1.5 + 0.35)
            b = S["laugh"] * h * env * abs(math.sin(2 * math.pi * 3.5 * t))
            chest_d = chest_d + np.array([0, -b])
            head_d = head_d + np.array([0, -1.4 * b])
            head_deg += -3.0 * env
            for k in range(len(hand_d)):
                hand_d[k] = hand_d[k] + np.array([0, -b * 0.8])
        if "tilt" in S:
            head_deg += S["tilt"] * math.sin(2 * math.pi * t / 3.6 + ph)
        if "scan" in S:
            sc = S["scan"] * h * math.sin(2 * math.pi * t / 2.4 + ph)
            head_d = head_d + np.array([sc, 0])
            chest_d = chest_d + np.array([sc * 0.35, 0])
            for k in range(len(hand_d)):
                if np.linalg.norm(self.hands[k] - self.head) < 0.3 * h:
                    hand_d[k] = hand_d[k] + np.array([sc, 0])
        if "shake" in S:
            env = min(1.0, p * 1.2 + 0.25)
            head_deg += S["shake"] * env * math.sin(2 * math.pi * 2.6 * t)
        if "bounce" in S:
            b = S["bounce"] * h * p
            chest_d = chest_d + np.array([0, -b])
            head_d = head_d + np.array([0, -b * 1.2])
        if "shrug" in S:
            s_ = S["shrug"] * h * (0.4 * breath + 0.8 * p)
            for k in range(len(hand_d)):
                hand_d[k] = hand_d[k] + np.array([0, -s_])
            chest_d = chest_d + np.array([0, -s_ * 0.2])
        if "hop" in S:
            tau = t - 0.12
            if 0 < tau < 0.36:
                lift = np.array([0, -S["hop"] * h * math.sin(math.pi * tau / 0.36)])
            squash = 0.012 * h * float(alpha_fn(np.array(t - 0.48), 0.07))
            chest_d = chest_d + np.array([0, squash])
            head_d = head_d + np.array([0, squash * 1.3])
        if "walk" in S:
            step = 2 * math.pi * 1.9 * t
            bob = 0.025 * h * abs(math.sin(step))
            chest_d = chest_d + np.array([0, -bob])
            hip_d = hip_d + np.array([0, -bob * 0.6])
            head_d = head_d + np.array([0, -bob * 1.05])
            head_deg += 2.5 * math.sin(step)
            for k in range(len(hand_d)):
                hand_d[k] = hand_d[k] + np.array([0.04 * h * math.sin(step / 2 + k * math.pi), -bob])

        # head handles: rotate about the neck, then translate
        head_pts = rot(self.g_head, self.neck, head_deg) + head_d
        hands = []
        for k, q in enumerate(self.hands):
            if self.hand_on_head[k]:
                hands.append(rot(q[None], self.neck, head_deg)[0] + head_d + (hand_d[k] - chest_d) * 0.5)
            else:
                hands.append(q + hand_d[k])
        dst = np.vstack([self.g_feet, self.g_hip + hip_d, self.g_chest + chest_d, head_pts]
                        + [p_[None] for p_ in hands])
        return dst + lift


def pad_image(im, m):
    h, w = im.shape[:2]
    out = np.zeros((h + 2 * m, w + 2 * m, 4), np.uint8)
    out[m:m + h, m:m + w] = im
    return out


# ---------------------------------------------------------------------------- groups (several figures in one image)
class GroupRig:
    """Several figures drawn in one picture (a squad running): each bobs on its own beat."""

    def __init__(self, im, rig):
        self.h = float(rig["bbox"][3] - rig["bbox"][1])
        self.figs = rig["figures"]          # [{head:[x,y], foot_x: x}]
        y1 = rig["bbox"][3]
        pts = []
        for f in self.figs:
            hx, hy = f["head"]
            fx = f.get("foot_x", hx)
            pts += [[hx, hy], [hx, hy + 0.18 * self.h], [hx * 0.6 + fx * 0.4, hy + 0.42 * self.h], [fx, y1 - 0.03 * self.h]]
        self.src = np.array(pts, float)

    def targets(self, t, style, beats, seed=0):
        h = self.h
        dst = self.src.copy()
        for k in range(len(self.figs)):
            step = 2 * math.pi * 2.6 * t + k * 2.1
            bob = 0.035 * h * abs(math.sin(step))
            lean = 0.012 * h * math.sin(step * 2)
            sl = slice(4 * k, 4 * k + 4)
            dst[sl, 1] -= bob
            dst[sl.start:sl.start + 2, 0] += lean
        return dst


# ---------------------------------------------------------------------------- styles per pose
def style_for(name, moving=False):
    n = name
    if "soldiers-running" in n:
        return "run"
    if moving and not any(k in n for k in ("crawl", "run-", "walk", "lying", "sit")):
        return "walk"
    table = [
        (("fisherman-pointing-shocked", "worried", "shocked", "recoil", "scared"), "tremble"),
        (("point",), "point"),
        (("count-on-fingers",), "count"),
        (("magnifying", "binoculars", "look-far", "read-map"), "search"),
        (("thumbs-up", "fist-pump", "clap", "celebrate", "jump-joy", "peace"), "cheer"),
        (("stress", "panic-hands", "facepalm", "refuse", "stop-palm", "thumbs-down"), "shake"),
        (("think", "listen"), "think"),
        (("laugh",), "laugh"),
        (("idea", "finger-up", "lightbulb"), "hop"),
        (("arms-wide", "shrug", "hello"), "wide"),
        (("present", "explain", "finger-raise", "mic-stand"), "present"),
        (("reading", "photo-letters", "salute", "warning-sign", "hold-", "read-book", "laptop", "look-phone",
          "write-", "briefcase", "sit", "lying", "stand-pockets", "arms-crossed", "hands-on-hips", "lean-casual"), "hold"),
    ]
    for keys, st in table:
        if any(k in n for k in keys):
            return st
    return "talk"


def pick_beats(words, a, b, gap=0.6):
    """Stressed words inside [a, b] (global times) -> beat times relative to a."""
    out, last = [], -9.0
    for w in words:
        s = w["start"]
        if s < a + 0.25 or s > b - 0.35:
            continue
        txt = w["text"].strip("،.؟?!:")
        if (w["end"] - s >= 0.26 or len(txt) >= 5) and s - last >= gap:
            out.append(round(s - a, 3))
            last = s
    if not out and b - a > 1.2:
        out.append(round(min(0.5, (b - a) / 3), 3))
    return out


# ---------------------------------------------------------------------------- clip = one layer's whole life on screen
def clip_frames(spec):
    """spec: {segments: [{src, t: start(s)}], style, duration, beats, seed, fps, scale_hint}
    All segments share one canvas: poses bottom-aligned and centred like the engine places <img>s."""
    fps = spec.get("fps", FPS)
    segs = spec["segments"]
    ims = [load_rgba(s["src"]) for s in segs]
    rigs = spec.get("rigs") or [rig_for(s["src"]) for s in segs]
    W = max(i.shape[1] for i in ims)
    H = max(i.shape[0] for i in ims)
    m = spec["pad"]
    Wc, Hc = W + 2 * m, H + 2 * m
    Wc += Wc % 2
    Hc += Hc % 2
    prepared = []
    for im, rig, sg in zip(ims, rigs, segs):
        ox, oy = m + (W - im.shape[1]) // 2, m + (H - im.shape[0])
        canvas = np.zeros((Hc, Wc, 4), np.uint8)
        canvas[oy:oy + im.shape[0], ox:ox + im.shape[1]] = im
        R = GroupRig(im, rig) if "figures" in rig else Rig(im, rig)
        st = sg.get("style") or spec["style"]
        prepared.append((canvas, R, R.src + [ox, oy], [ox, oy], st))
    n = max(1, int(round(spec["duration"] * fps)))
    starts = [s["t"] for s in segs]
    for f in range(n):
        t = f / fps
        k = max(i for i, s in enumerate(starts) if s <= t + 1e-6)
        canvas, R, src, off, st = prepared[k]
        beats = [b - starts[k] for b in spec["beats"] if b >= starts[k] - 0.05]
        dst = R.targets(t - starts[k], st, beats, spec.get("seed", 0)) + off
        mx, my = mls_rigid_inverse(src, dst, canvas.shape[:2], step=spec.get("step", 6))
        yield warp(canvas, mx, my)


def canvas_geometry(spec):
    """(canvas_w, canvas_h, pad, max_w, max_h) in source pixels, for placing the <video>."""
    sizes = [Image.open(s["src"]).size for s in spec["segments"]]
    W, H = max(s[0] for s in sizes), max(s[1] for s in sizes)
    m = spec["pad"]
    return W + 2 * m + (W + 2 * m) % 2, H + 2 * m + (H + 2 * m) % 2, m, W, H


def encode_clip(spec, out_path):
    import subprocess
    Wc, Hc, *_ = canvas_geometry(spec)
    tmp = str(out_path) + ".part.webm"
    p = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba",
                          "-s", f"{Wc}x{Hc}", "-r", str(spec.get("fps", FPS)), "-i", "-",
                          "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "16", "-row-mt", "1",
                          "-deadline", "good", "-cpu-used", "4", "-auto-alt-ref", "0", "-threads", "1", tmp],
                         stdin=subprocess.PIPE)
    for fr in clip_frames(spec):
        p.stdin.write(fr.tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError(f"ffmpeg failed for {out_path}")
    Path(tmp).replace(out_path)
    return str(out_path)


def _job(args):
    spec, out = args
    return encode_clip(spec, out)


def render_all(jobs, workers=4):
    """jobs: [(spec, out_path)]; skips clips that already exist (file name is a hash of the spec)."""
    from multiprocessing import Pool
    todo = [(s, o) for s, o in jobs if not Path(o).exists()]
    if not todo:
        return []
    with Pool(workers) as pool:
        return pool.map(_job, todo, chunksize=1)


def spec_hash(spec):
    import hashlib
    return hashlib.sha1(json.dumps(spec, sort_keys=True).encode()).hexdigest()[:12]


# ---------------------------------------------------------------------------- CLI
def _sheet(out, paths):
    tiles = []
    for p in paths:
        im = load_rgba(p)
        r = find_rig(p)
        bg = np.full(im.shape[:2] + (3,), (60, 60, 50), np.uint8)
        a = im[..., 3:4] / 255.0
        c = np.ascontiguousarray((im[..., :3] * a + bg * (1 - a)).astype(np.uint8))
        dots = [(f["head"], (255, 0, 0)) for f in r.get("figures", [])]
        if "figures" not in r:
            dots = [(r["hip"], (0, 200, 255)), (r["chest"], (0, 255, 0)), (r["head"], (255, 0, 0))]
            dots += [(hd, (255, 0, 255)) for hd in r["hands"]]
            cv2.line(c, (0, int(r["feet_y"])), (c.shape[1], int(r["feet_y"])), (255, 255, 0), 3)
        for pt, col in dots:
            cv2.circle(c, (int(pt[0]), int(pt[1])), 14, col, -1)
        s = 420 / c.shape[0]
        c = cv2.resize(c, (int(c.shape[1] * s), 420))
        cv2.putText(c, Path(p).stem[:24], (5, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        tiles.append(c)
    rows, row, wsum = [], [], 0
    for t in tiles:
        if row and wsum + t.shape[1] > 2400:
            rows.append(row)
            row, wsum = [], 0
        row.append(t)
        wsum += t.shape[1]
    rows.append(row)
    W = max(sum(t.shape[1] for t in r) for r in rows)
    Image.fromarray(np.vstack([np.hstack(r + [np.zeros((420, W - sum(t.shape[1] for t in r), 3), np.uint8)]) for r in rows])).save(out, quality=88)
    print("legend: red head, green chest, blue hip, magenta hands, yellow line feet")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "rig":
        for p in sys.argv[2:]:
            print(Path(p).stem, json.dumps(find_rig(p)))
    elif cmd == "sheet":
        _sheet(sys.argv[2], sys.argv[3:])
    elif cmd == "demo":
        p, style, out = sys.argv[2:5]
        dur = float(sys.argv[5]) if len(sys.argv) > 5 else 4.0
        spec = {"v": MOTION_VERSION, "segments": [{"src": p, "t": 0.0}], "rigs": [find_rig(p)], "style": style,
                "duration": dur, "beats": [0.4, 1.2, 2.0, 2.8, 3.5], "seed": 1, "fps": 30,
                "pad": int(0.07 * Image.open(p).size[1]), "step": 6}
        import subprocess
        Wc, Hc, *_ = canvas_geometry(spec)
        ff = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba",
                               "-s", f"{Wc}x{Hc}", "-r", "30", "-i", "-", "-vf", "format=yuv420p", "-c:v", "libx264", "-crf", "18", out],
                              stdin=subprocess.PIPE)
        for fr in clip_frames(spec):
            bg = np.full(fr.shape[:2] + (3,), (42, 43, 32), np.float32)
            a = fr[..., 3:4] / 255.0
            ff.stdin.write((fr[..., :3] * a + bg * (1 - a)).astype(np.uint8).tobytes())
        ff.stdin.close()
        ff.wait()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
