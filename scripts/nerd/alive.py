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
MOTION_VERSION = 4   # bump when the motion code changes, so cached clips are rebuilt
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
def mls_rigid_inverse(src_pts, dst_pts, shape, step=6, alpha=1.0):
    """Backward map for cv2.remap: for every output pixel, where to sample the source.
    MLS from the deformed handles (dst) to the original ones (src), evaluated on a grid."""
    h, w = shape
    # grid samples sit where cv2.resize looks for them: full-res pixel x <-> grid index (x + 0.5) / step - 0.5
    gw, gh = -(-w // step) + 1, -(-h // step) + 1
    gx1 = (np.arange(gw) + 0.5) * step - 0.5
    gy1 = (np.arange(gh) + 0.5) * step - 0.5
    gx, gy = np.meshgrid(gx1, gy1)
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
    # store the displacement (smooth, small) and upsample it in float: no fixed-point remap noise
    dx = (res[:, 0] - v[:, 0]).reshape(gh, gw).astype(np.float32)
    dy = (res[:, 1] - v[:, 1]).reshape(gh, gw).astype(np.float32)
    dx = cv2.resize(dx, (gw * step, gh * step), interpolation=cv2.INTER_CUBIC)[:h, :w]
    dy = cv2.resize(dy, (gw * step, gh * step), interpolation=cv2.INTER_CUBIC)[:h, :w]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return xx + dx, yy + dy


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


# how each style moves the body. Angles in degrees, distances as fractions of the figure height.
# Arms never stretch: a gesturing hand turns around its shoulder, so the arm keeps its length.
STYLES = {
    "idle": {},
    "talk": {"arm": 9, "nod": 1.0},
    "point": {"arm": 6, "main_only": True, "lean": 0.012, "nod": 0.8},
    "present": {"arm": 8, "lean": 0.010, "nod": 1.0},
    "count": {"arm": 5, "nod": 1.0},
    "tremble": {"tremble": 1.6, "recoil": 0.035},
    "laugh": {"laugh": 0.012},
    "think": {"tilt": 4.0, "slow": True, "nod": 0.6},
    "search": {"scan": 0.035, "lean": 0.010},
    "shake": {"shake": 6.0},
    "cheer": {"arm": 10, "main_only": True, "bounce": 0.012},
    "wide": {"shrug": 6.0, "nod": 0.6},
    "hop": {"hop": 0.06, "arm": 5},
    "walk": {"walk": 1.0},
    "hold": {"nod": 0.8},
}


MAX_STRAIN = 0.12   # two neighbouring handles may move apart/together by at most 12% of their distance


def limit_strain(src, dst, pair_dist, fixed=None, iters=40):
    """Keep every pair of neighbouring handles (from different body parts) within MAX_STRAIN of
    their distance: only the pairs that would squeeze or stretch the skin are pulled back toward
    each other (position-based constraints), so the rest of the motion keeps its full size.
    Fixed handles (the feet) never move."""
    disp = (dst - src).astype(float)
    inv = np.ones(len(src)) if fixed is None else (~fixed).astype(float)
    finite = np.isfinite(pair_dist)
    ii, jj = np.nonzero(np.triu(finite, 1))
    if not len(ii):
        return dst
    lim = MAX_STRAIN * pair_dist[ii, jj]
    for _ in range(iters):
        rel = disp[ii] - disp[jj]
        n = np.linalg.norm(rel, axis=1)
        over = n - lim
        bad = over > 1e-3
        if not bad.any():
            break
        w = inv[ii] + inv[jj]
        ok = bad & (w > 0)
        corr = (over[ok] / n[ok] / w[ok])[:, None] * rel[ok]
        np.add.at(disp, ii[ok], -corr * inv[ii[ok]][:, None] * 0.5)
        np.add.at(disp, jj[ok], corr * inv[jj[ok]][:, None] * 0.5)
    # whatever is still over the limit after relaxing: scale the whole frame down (always safe)
    rel = np.linalg.norm(disp[ii] - disp[jj], axis=1)
    ratio = (rel / pair_dist[ii, jj]).max()
    if ratio > MAX_STRAIN:
        disp *= MAX_STRAIN / ratio
    return src + disp


class Rig:
    """Handles of one figure, grouped into rigid parts: feet, hips, chest (+ shoulders), head, hands."""

    def __init__(self, im, rig):
        self.im = im
        self.r = rig
        x0, y0, x1, y1 = rig["bbox"]
        self.h = h = float(y1 - y0)
        self.feet_y = rig["feet_y"]
        a = im[..., 3] > 128

        def extent(y):
            row = np.nonzero(a[int(min(max(y, 0), a.shape[0] - 1))])[0]
            return (float(row.min()), float(row.max())) if len(row) else (float(x0), float(x1))
        self.hip = np.array(rig["hip"], float)
        self.chest = np.array(rig["chest"], float)
        self.head = np.array(rig["head"], float)
        self.neck = self.chest * 0.45 + self.head * 0.55
        fl, fr = extent(self.feet_y)
        bl, br = extent(y1 - 2)
        self.g_feet = np.array([[fl, self.feet_y], [(fl + fr) / 2, self.feet_y], [fr, self.feet_y], [bl, y1], [br, y1]], float)
        hl, hr = extent(self.hip[1])
        self.g_hip = np.array([self.hip, [hl + 0.25 * (self.hip[0] - hl), self.hip[1]],
                               [hr - 0.25 * (hr - self.hip[0]), self.hip[1]]], float)
        self.g_chest = np.array([self.chest, [self.chest[0] - 0.08 * h, self.chest[1]],
                                 [self.chest[0] + 0.08 * h, self.chest[1]]], float)
        hx, hy = self.head
        self.g_head = np.array([[hx, hy], [hx - 0.06 * h, hy], [hx + 0.06 * h, hy], [hx, hy - 0.08 * h]], float)

        hands = [np.array(p, float) for p in rig.get("hands", [])]
        self.hands = hands
        self.kind, self.side, self.shoulder, self.cluster = [], [], [], []
        for q in hands:
            dx = q[0] - self.chest[0]
            side = 1.0 if dx >= 0 else -1.0
            if np.linalg.norm(q - self.head) < 0.16 * h:
                kind = "head"                       # chin, ear, cap: moves with the head
            elif np.linalg.norm(q - self.hip) < 0.12 * h or np.linalg.norm(q - self.chest) < 0.07 * h:
                kind = "rest"                       # pocket, belly
            elif q[1] > self.hip[1] - 0.04 * h and abs(dx) < 0.2 * h:
                kind = "hang"                       # arm hanging by the side
            else:
                kind = "free"
            self.kind.append(kind)
            self.side.append(side)
            self.shoulder.append(np.array([self.chest[0] + side * 0.075 * h, self.chest[1] - 0.05 * h]))
            r_ = 0.025 * h
            self.cluster.append(np.array([q, q + [r_, 0], q + [-r_, 0], q + [0, -r_]]))
        # two hands close together (counting, holding something) move as one
        self.together = len(hands) == 2 and np.linalg.norm(hands[0] - hands[1]) < 0.2 * h
        self.main = max(range(len(hands)), key=lambda i: np.linalg.norm(hands[i] - self.chest)) if hands else None
        sh = [s_ for s_, k in zip(self.shoulder, self.kind) if k in ("free", "hang")]
        self.g_sh = np.array(sh, float).reshape(-1, 2)
        full = np.vstack([self.g_feet, self.g_hip, self.g_chest, self.g_head, self.g_sh] + self.cluster)
        labels = (["feet"] * len(self.g_feet) + ["hip"] * 3 + ["chest"] * 3 + ["head"] * 4 + ["sh"] * len(self.g_sh)
                  + sum([[f"hand{k}"] * 4 for k in range(len(self.cluster))], []))
        # a body handle sitting right next to a hand would pin the skin under it and squeeze it: drop it
        moving = [c for c, k in zip(self.cluster, self.kind) if k in ("free", "hang")]
        keep = np.ones(len(full), bool)
        for i, (pt, lb) in enumerate(zip(full, labels)):
            if lb in ("hip", "chest", "sh") and any(np.linalg.norm(c - pt, axis=1).min() < 0.06 * h for c in moving):
                keep[i] = False
        self.keep = keep
        self.labels = np.array(labels)[keep]
        self.src = full[keep]
        d = np.linalg.norm(self.src[:, None] - self.src[None], axis=2)
        self.pair_dist = np.where(self.labels[:, None] != self.labels[None], d, np.inf)

    def targets(self, t, style, beats, seed=0):
        """Handle positions at time t (seconds since the layer appeared)."""
        S = STYLES[style]
        h = self.h
        ph = (seed * 0.37) % 1 * 2 * math.pi
        slow = 0.6 if S.get("slow") else 1.0
        p = pulses(t, beats)
        facing = self.side[self.main] if self.main is not None else 1.0
        # base life: breathing, weight shift, head drift
        breath = 0.5 - 0.5 * math.cos(2 * math.pi * t / 3.2 + ph)
        sway = math.sin(2 * math.pi * t / (4.4 / slow) + ph)
        hip_d = np.array([0.007 * h * sway, 0.0])
        chest_d = np.array([0.012 * h * sway, -0.008 * h * breath])
        head_deg = 1.5 * math.sin(2 * math.pi * t / 5.1 + ph * 1.7) - 0.8 * sway
        extra_head = np.zeros(2)
        arm = [0.0] * len(self.hands)            # rotation of each hand around its shoulder
        lift = np.zeros(2)

        if "nod" in S:
            extra_head += [0, 0.012 * h * p * S["nod"]]
            head_deg += facing * 2.0 * p * S["nod"]
        if "arm" in S:
            for k in range(len(self.hands)):
                if self.kind[k] != "free" or (S.get("main_only") and k != self.main):
                    continue
                pk = p if (self.together or len(self.hands) < 2 or S.get("main_only")) else pulses(t, beats[k % 2::2])
                arm[k] -= self.side[k] * S["arm"] * pk
        if "lean" in S:
            lean = S["lean"] * h * (0.6 + 0.4 * p)
            chest_d = chest_d + [lean * facing, 0]
            extra_head += [0.5 * lean * facing, 0]
        if "tremble" in S:
            jig = lambda f, o: math.sin(2 * math.pi * f * t + o) * 0.6 + math.sin(2 * math.pi * f * 1.37 * t + o * 2) * 0.4
            for k in range(len(self.hands)):
                arm[k] += S["tremble"] * jig(9, k)
            extra_head += [0.002 * h * jig(7, 3), 0]
            rec = S["recoil"] * h * float(alpha_fn(np.array(t - 0.05), 0.18))
            chest_d = chest_d + [-rec * facing * 0.6, -rec * 0.3]
            extra_head += [-rec * facing * 0.3, -rec * 0.1]
        if "laugh" in S:
            env = min(1.0, p * 1.5 + 0.35)
            b = S["laugh"] * h * env * abs(math.sin(2 * math.pi * 3.5 * t))
            chest_d = chest_d + [0, -b]
            extra_head += [0, -0.25 * b]
            head_deg += -3.0 * env * facing
        if "tilt" in S:
            head_deg += S["tilt"] * math.sin(2 * math.pi * t / 3.6 + ph)
        if "scan" in S:
            sc = S["scan"] * h * math.sin(2 * math.pi * t / 2.4 + ph)
            chest_d = chest_d + [sc * 0.45, 0]
            extra_head += [sc * 0.55, 0]
        if "shake" in S:
            env = min(1.0, p * 1.2 + 0.25)
            head_deg += S["shake"] * env * math.sin(2 * math.pi * 2.6 * t)
        if "bounce" in S:
            b = S["bounce"] * h * p
            chest_d = chest_d + [0, -b]
        if "shrug" in S:
            for k in range(len(self.hands)):
                if self.kind[k] == "free":
                    arm[k] -= self.side[k] * S["shrug"] * (0.4 * breath + 0.8 * min(p, 1.0))
        if "hop" in S:
            tau = t - 0.12
            if 0 < tau < 0.36:
                lift = np.array([0, -S["hop"] * h * math.sin(math.pi * tau / 0.36)])
            squash = 0.008 * h * float(alpha_fn(np.array(t - 0.48), 0.07))
            chest_d = chest_d + [0, squash]
        if "walk" in S:
            step = 2 * math.pi * 1.9 * t
            bob = 0.014 * h * abs(math.sin(step))
            chest_d = chest_d + [0, -bob]
            hip_d = hip_d + [0, -bob * 0.7]
            head_deg += 2.0 * math.sin(step)
            for k in range(len(self.hands)):
                if self.kind[k] in ("hang", "free"):
                    arm[k] += 5.0 * math.sin(step / 2 + k * math.pi)

        head_d = chest_d + extra_head
        head_pts = rot(self.g_head, self.neck, head_deg) + head_d
        sh_pts = self.g_sh + chest_d
        moved = []
        for k, cl in enumerate(self.cluster):
            if self.kind[k] == "head":
                moved.append(rot(cl, self.neck, head_deg) + head_d)
            elif self.kind[k] == "rest":
                near_hip = np.linalg.norm(self.hands[k] - self.hip) < np.linalg.norm(self.hands[k] - self.chest)
                moved.append(cl + (hip_d if near_hip else chest_d))
            else:
                moved.append(rot(cl, self.shoulder[k], arm[k]) + chest_d)
        if self.together and all(k in ("free", "hang") for k in self.kind):
            # same displacement for both hands: nothing squeezes between them
            d = (moved[0] - self.cluster[0]).mean(0)
            moved = [cl + d for cl in self.cluster]
        dst = np.vstack([self.g_feet, self.g_hip + hip_d, self.g_chest + chest_d, head_pts, sh_pts] + moved)[self.keep]
        return limit_strain(self.src, dst, self.pair_dist, fixed=self.labels == "feet") + lift


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
        lab = np.repeat(np.arange(len(self.figs)), 4)
        d = np.linalg.norm(self.src[:, None] - self.src[None], axis=2)
        return limit_strain(self.src, dst, np.where(lab[:, None] != lab[None], d, np.inf))


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


# ---------------------------------------------------------------------------- safety check (Firas: the body must never come apart)
def _components(alpha, min_area=60):
    n, _, st, _ = cv2.connectedComponentsWithStats((alpha > 128).astype(np.uint8), 8)
    return int(sum(1 for k in range(1, n) if st[k, cv2.CC_STAT_AREA] >= min_area))


def check_spec(spec, every=2):
    """Worst case over the clip: extra pieces (tear), area change, clipping at the canvas edge,
    folding or strong local stretch (Jacobian of the warp inside the figure)."""
    fps = spec.get("fps", FPS)
    segs = spec["segments"]
    ims = [load_rgba(s["src"]) for s in segs]
    rigs = spec.get("rigs") or [rig_for(s["src"]) for s in segs]
    Wc, Hc, m, W, H = canvas_geometry(spec)
    base = []
    for im, rig, sg in zip(ims, rigs, segs):
        ox, oy = m + (W - im.shape[1]) // 2, m + (H - im.shape[0])
        canvas = np.zeros((Hc, Wc, 4), np.uint8)
        canvas[oy:oy + im.shape[0], ox:ox + im.shape[1]] = im
        R = GroupRig(im, rig) if "figures" in rig else Rig(im, rig)
        a0 = canvas[..., 3]
        base.append((canvas, R, R.src + [ox, oy], [ox, oy], sg.get("style") or spec["style"],
                     _components(a0), float((a0 > 128).sum())))
    starts = [s["t"] for s in segs]
    worst = {"extra_pieces": 0, "area_min": 1.0, "area_max": 1.0, "edge_px": 0, "jac_min": 9.0, "jac_max": 0.0}
    n = max(1, int(round(spec["duration"] * fps)))
    for f in range(0, n, every):
        t = f / fps
        k = max(i for i, s in enumerate(starts) if s <= t + 1e-6)
        canvas, R, src, off, st, comps0, area0 = base[k]
        beats = [b - starts[k] for b in spec["beats"] if b >= starts[k] - 0.05]
        dst = R.targets(t - starts[k], st, beats, spec.get("seed", 0)) + off
        mx, my = mls_rigid_inverse(src, dst, canvas.shape[:2], step=spec.get("step", 6))
        a = cv2.remap(canvas[..., 3], mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        inside = a > 128
        worst["extra_pieces"] = max(worst["extra_pieces"], _components(a) - comps0)
        r = float(inside.sum()) / area0
        worst["area_min"], worst["area_max"] = min(worst["area_min"], r), max(worst["area_max"], r)
        edge = int((a[0] > 16).sum() + (a[-1] > 16).sum() + (a[:, 0] > 16).sum() + (a[:, -1] > 16).sum())
        worst["edge_px"] = max(worst["edge_px"], edge)
        dxx, dxy = np.gradient(mx, axis=1), np.gradient(mx, axis=0)
        dyx, dyy = np.gradient(my, axis=1), np.gradient(my, axis=0)
        det = (dxx * dyy - dxy * dyx)[inside]
        if det.size:
            worst["jac_min"] = min(worst["jac_min"], float(np.percentile(det, 0.1)))
            worst["jac_max"] = max(worst["jac_max"], float(np.percentile(det, 99.9)))
    worst["ok"] = (worst["extra_pieces"] <= 0 and 0.95 <= worst["area_min"] and worst["area_max"] <= 1.05
                   and worst["edge_px"] == 0 and worst["jac_min"] > 0.75 and worst["jac_max"] < 1.33)
    return worst


def _check_job(job):
    spec, out = job
    return str(out), check_spec(spec, every=2)


def check_all(jobs, workers=4):
    """Run check_spec on every clip; returns [(out_path, worst)] for the clips that fail."""
    from multiprocessing import Pool
    with Pool(workers) as pool:
        res = pool.map(_check_job, jobs, chunksize=1)
    return [(o, w) for o, w in res if not w["ok"]]
