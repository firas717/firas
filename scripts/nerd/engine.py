#!/usr/bin/env python3
"""Al-Nerd composition engine: builds a HyperFrames index.html from a shot list.

The fixed channel frame (title band, scene-title band, scene card, caption box, part band,
watermark, progress bar, end card) follows brand/docs/01 and CLAUDE.md. Each episode only
describes its shots: a time window, a scene title, and layers (photos, poses/characters,
text, rings, arrows, icons, map overlays). Every animation goes on one paused GSAP timeline
at global time, so the result is seekable and deterministic.

Coordinates of layers are in scene-card space: 1080 x 680, origin top-left.
"""
import html
import json
import math
from pathlib import Path

from PIL import Image

import alive

W, H = 1080, 1920
CARD_Y, CARD_W, CARD_H = 500, 1080, 680
FPS = 30

TOPICS = {  # accent, drawn-scene background (brand/docs/01)
    "tech": ("#2FB6E8", "#0C1B26"), "science": ("#7FB72B", "#F4F1E6"), "history": ("#C08A1E", "#E8D9B8"),
    "war": ("#E25822", "#2A2B20"), "crime": ("#D23030", "#1C1F22"), "mystery": ("#8B5CF6", "#15121F"),
    "nature": ("#17A47C", "#10211C"), "news": ("#4C8BE0", "#161A20"),
}

NARRATOR_SCALE = 0.48   # standing narrator pose (~920px) -> ~440px, 65% of the scene card
CHAR_SCALE = 0.41       # secondary characters are drawn taller than the narrator
STILL = ("dead-officer",)  # bodies stay still; every other pose/character is brought to life (alive.py)


def esc(s):
    return html.escape(str(s), quote=True)


class Video:
    def __init__(self, project_dir, duration, topic, title, voice_end, alive=True):
        self.dir = Path(project_dir)
        self.alive = alive        # living poses: each pose layer becomes a warped video clip
        self.alive_jobs = []
        self.words = []
        self.duration = duration
        self.voice_end = voice_end
        self.accent, self.scene_bg = TOPICS[topic]
        self.title = title
        self.shots = []
        self.captions = []
        self.keywords = []
        self.audio_src = None
        self._n = 0
        self.js = []          # timeline statements
        self.css_extra = []
        self.map_svg = None
        self.map_proj = None

    # ---------- helpers ----------
    def uid(self, p="e"):
        self._n += 1
        return f"{p}{self._n}"

    def size(self, rel):
        with Image.open(self.dir / rel) as im:
            return im.size

    def at(self, t):
        return f"{t:.3f}"

    # ---------- public API ----------
    def audio(self, src):
        self.audio_src = src

    def set_words(self, words):
        """Word timings: the living poses gesture on the stressed words."""
        self.words = words

    def set_captions(self, caps, keywords=()):
        self.captions = caps
        self.keywords = list(keywords)

    def use_map(self, svg_rel):
        self.map_svg = (self.dir / svg_rel).read_text()
        meta = json.loads((self.dir / (svg_rel + ".json")).read_text())
        lon0, lon1, lat0, lat1 = meta["bounds"]
        w, h = meta["size"]

        def merc(lat):
            return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
        ytop, ybot = merc(lat1), merc(lat0)
        s = min(w / math.radians(lon1 - lon0), h / (ytop - ybot))
        ox = (w - s * math.radians(lon1 - lon0)) / 2
        oy = (h - s * (ytop - ybot)) / 2
        self.map_proj = lambda lon, lat: (ox + s * math.radians(lon - lon0), oy + s * (ytop - merc(lat)))

    def shot(self, t0, t1, label, layers, bg="scene", chapter=False):
        self.shots.append(dict(t0=t0, t1=t1, label=label, layers=layers, bg=bg, chapter=chapter))

    # ---------- layer renderers (return html, add js) ----------
    def r_photo(self, L, t0, t1):
        i = self.uid("ph")
        src, kb, pos = L["src"], L.get("kb", "in"), L.get("pos", "50% 50%")
        dim = L.get("dim", 0.18)
        if L.get("frame") == "archive":
            x, y, w, h = L.get("box", (300, 70, 480, 360))
            rot = L.get("rot", -3)
            blur = src.replace(".jpg", "-blur.jpg")
            blur = blur if (self.dir / blur).exists() else src
            out = (f'<div class="ph-blur"><img src="{esc(blur)}" style="object-position:{pos}"></div>'
                   f'<div class="ph-vig"></div>'
                   f'<div id="{i}" class="ph-frame" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;'
                   f'transform:rotate({rot}deg)"><img src="{esc(src)}" style="object-position:{pos}"></div>')
            self.js.append(f'tl.fromTo("#{i}",{{y:40,opacity:0}},{{y:0,opacity:1,duration:0.35,ease:"power3.out"}},{self.at(t0 + L.get("at", 0))});')
            self.js.append(f'tl.fromTo("#{i} img",{{scale:1}},{{scale:1.05,duration:{t1 - t0:.3f},ease:"none"}},{self.at(t0)});')
            return out
        out = (f'<div class="ph"><img id="{i}" src="{esc(src)}" style="object-position:{pos};{L.get("css", "")}"></div>'
               f'<div class="ph-dim" style="opacity:{dim}"></div><div class="ph-vig"></div>')
        d = t1 - t0
        if kb == "in":
            self.js.append(f'tl.fromTo("#{i}",{{scale:1.0}},{{scale:1.06,duration:{d:.3f},ease:"none"}},{self.at(t0)});')
        elif kb == "out":
            self.js.append(f'tl.fromTo("#{i}",{{scale:1.07}},{{scale:1.01,duration:{d:.3f},ease:"none"}},{self.at(t0)});')
        elif kb in ("left", "right"):
            dx = -30 if kb == "left" else 30
            self.js.append(f'tl.fromTo("#{i}",{{scale:1.08,x:{-dx}}},{{scale:1.08,x:{dx},duration:{d:.3f},ease:"none"}},{self.at(t0)});')
        return out

    def r_pic(self, L, t0, t1, scale_default):
        """A pose/character PNG, optionally swapping poses or cycling walk frames."""
        i = self.uid("pc")
        srcs = [L["src"]] + [s for _, s in L.get("swap", [])] + L.get("frames", [])[1:]
        sc = L.get("scale", scale_default)
        w, h = self.size(L["src"])
        w, h = w * sc, h * sc
        cx, by = L.get("x", 220), L.get("y", 660)
        imgs = []
        for k, s in enumerate(dict.fromkeys(srcs)):
            sw, sh = self.size(s)
            iw, ih = sw * sc, sh * sc
            imgs.append(f'<img data-k="{k}" src="{esc(s)}" style="left:{(w - iw) / 2:.0f}px;width:{iw:.0f}px;height:{ih:.0f}px;'
                        f'opacity:{1 if k == 0 else 0}">')
        uniq = list(dict.fromkeys(srcs))
        live = self._alive_clip(L, t0, t1, sc, (w / sc, h / sc))
        if live:
            imgs = [live]
        flip = ' style="transform:scaleX(-1)"' if L.get("flip") else ""
        out = (f'<div id="{i}" class="pic" style="left:{cx - w / 2:.0f}px;top:{by - h:.0f}px;width:{w:.0f}px;'
               f'height:{h:.0f}px;z-index:{L.get("z", 3)};opacity:{L.get("opacity", 1)}"><div class="flip"{flip}>{"".join(imgs)}</div></div>')
        a = t0 + L.get("at", 0)
        enter = L.get("enter", "fade")
        frm = {"left": "{x:-260,opacity:0}", "right": "{x:260,opacity:0}", "up": "{y:120,opacity:0}",
               "pop": "{scale:0.6,opacity:0}", "fade": "{opacity:0}", "drop": "{y:-200,opacity:0}", "none": None}[enter]
        if frm:
            to = {"left": "x:0,opacity:1", "right": "x:0,opacity:1", "up": "y:0,opacity:1", "pop": "scale:1,opacity:1",
                  "fade": "opacity:1", "drop": "y:0,opacity:1"}[enter]
            ease = "back.out(1.6)" if enter == "pop" else "power3.out"
            self.js.append(f'tl.fromTo("#{i}",{frm},{{{to},duration:0.35,ease:"{ease}"}},{self.at(a)});')
        # pose swaps at given times (hard cut + small bounce); a living clip already contains the cut
        for t_sw, s in L.get("swap", []):
            k = uniq.index(s)
            ts = t0 + t_sw
            if not live:
                self.js.append(f'tl.set("#{i} img",{{opacity:0}},{self.at(ts)});tl.set("#{i} img[data-k=\\"{k}\\"]",{{opacity:1}},{self.at(ts)});')
            self.js.append(f'tl.fromTo("#{i}",{{scale:0.96}},{{scale:1,duration:0.2,ease:"back.out(2)"}},{self.at(ts)});')
        # walk/run/crawl cycle
        if L.get("frames"):
            fr = [uniq.index(s) for s in L["frames"]]
            fps = L.get("fps", 7)
            t, n = a, 0
            while t < t1 - 0.02:
                k = fr[n % len(fr)]
                self.js.append(f'tl.set("#{i} img",{{opacity:0}},{self.at(t)});tl.set("#{i} img[data-k=\\"{k}\\"]",{{opacity:1}},{self.at(t)});')
                t += 1 / fps
                n += 1
        mv = L.get("move")
        if mv:
            # absolute target (enter tweens end at x/y 0); start after the enter tween to keep one writer at a time
            dx, dy = mv.get("dx", 0), mv.get("dy", 0)
            ms = max(t0 + mv.get("at", 0), a + (0.36 if frm else 0))
            dur = min(mv.get("dur", t1 - ms), t1 - ms - 0.02)
            self.js.append(f'tl.to("#{i}",{{x:{dx},y:{dy},duration:{dur:.3f},ease:"{mv.get("ease", "none")}"}},{self.at(ms)});')
        if L.get("bob"):
            n = max(1, int((t1 - a) / 0.6))
            self.js.append(f'tl.to("#{i} img",{{y:-6,duration:0.3,ease:"sine.inOut",yoyo:true,repeat:{n * 2 - 1}}},{self.at(a)});')
        if L.get("breathe", True) and not L.get("frames") and not L.get("bob") and not live:
            self.js.append(f'tl.fromTo("#{i} img",{{scaleY:1}},{{scaleY:1.015,transformOrigin:"50% 100%",duration:{max(0.4, (t1 - a) / 2):.3f},ease:"sine.inOut",yoyo:true,repeat:1}},{self.at(a)});')
        if L.get("shake_at") is not None:
            ts = t0 + L["shake_at"]
            self.js.append(f'tl.fromTo("#{i} .flip",{{x:-8}},{{x:8,duration:0.05,yoyo:true,repeat:5,ease:"none"}},{self.at(ts)});tl.set("#{i} .flip",{{x:0}},{self.at(ts + 0.32)});')
        if L.get("fade_to") is not None:
            self.js.append(f'tl.to("#{i}",{{opacity:{L["fade_to"]},duration:0.6}},{self.at(t0 + L.get("fade_at", 0.5))});')
        return out

    def _alive_clip(self, L, t0, t1, sc, size0):
        """<video> markup for a living pose, and queue the clip that alive.py will render."""
        if not self.alive or L.get("alive") is False or L.get("frames"):
            return None
        if any(k in Path(L["src"]).stem for k in STILL):
            return None
        a = t0 + L.get("at", 0)
        dur = t1 - a
        srcs = [L["src"]] + [s for _, s in L.get("swap", [])]
        segs = [{"src": str(self.dir / L["src"]), "t": 0.0}]
        segs += [{"src": str(self.dir / s), "t": round(t_sw - L.get("at", 0), 3)} for t_sw, s in L.get("swap", [])]
        stem = Path(L["src"]).stem
        heights = [self.size(s)[1] for s in srcs]
        spec = {"v": alive.MOTION_VERSION, "segments": segs, "rigs": [alive.find_rig(g["src"]) for g in segs],
                "style": L.get("act") or alive.style_for(stem, moving=bool(L.get("move"))),
                "duration": round(dur, 3), "beats": alive.pick_beats(self.words, a, t1), "seed": self._n,
                "fps": alive.FPS, "pad": int(0.07 * max(heights)), "step": 6}
        rel = f"assets/alive/{stem}-{alive.spec_hash(spec)}.webm"
        self.alive_jobs.append((spec, self.dir / rel))
        Wc, Hc, m, Wm, Hm = alive.canvas_geometry(spec)
        w0, h0 = size0
        left = -(m + (Wm - w0) // 2) * sc
        bottom = -(Hc - m - Hm) * sc
        vid = self.uid("av")
        return (f'<video id="{vid}" class="clip" data-start="{a:.3f}" data-duration="{dur:.3f}" src="{esc(rel)}" muted playsinline '
                f'style="left:{left:.1f}px;bottom:{bottom:.1f}px;width:{Wc * sc:.1f}px;height:{Hc * sc:.1f}px"></video>')

    def r_text(self, L, t0, t1):
        i = self.uid("tx")
        style = L.get("style", "big")
        x, y = L.get("x", 540), L.get("y", 340)
        rot = L.get("rot", 0)
        cls = {"year": "t-year", "stamp": "t-stamp", "big": "t-big", "label": "t-label", "tag": "t-tag",
               "note": "t-note", "strike": "t-big"}[style]
        size = L.get("size")
        st = f"font-size:{size}px;" if size else ""
        if style == "stamp":
            st += f"color:{L.get('color', self.accent)};border-color:{L.get('color', self.accent)};"
        elif L.get("color"):
            st += f"color:{L['color']};"
        out = (f'<div class="t-anchor" style="left:{x}px;top:{y}px;transform:rotate({rot}deg)">'
               f'<div id="{i}" class="{cls}" style="{st}">{esc(L["text"])}</div></div>')
        a = t0 + L.get("at", 0)
        enter = L.get("enter", "pop")
        if enter == "slam":
            self.js.append(f'tl.fromTo("#{i}",{{scale:2.2,opacity:0}},{{scale:1,opacity:1,duration:0.22,ease:"power4.in"}},{self.at(a)});')
            self.js.append(f'tl.fromTo("#{i}",{{x:-6}},{{x:0,duration:0.08,repeat:3,yoyo:true}},{self.at(a + 0.22)});')
        elif enter == "pop":
            self.js.append(f'tl.fromTo("#{i}",{{scale:0.5,opacity:0}},{{scale:1,opacity:1,duration:0.3,ease:"back.out(1.8)"}},{self.at(a)});')
        elif enter == "up":
            self.js.append(f'tl.fromTo("#{i}",{{y:40,opacity:0}},{{y:0,opacity:1,duration:0.3,ease:"power3.out"}},{self.at(a)});')
        else:
            self.js.append(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.25}},{self.at(a)});')
        if style == "strike":
            s = self.uid("sk")
            out = out.replace("</div></div>", f'<i id="{s}" class="strike" style="background:{self.accent}"></i></div></div>', 1)
            self.js.append(f'tl.fromTo("#{s}",{{scaleX:0}},{{scaleX:1,duration:0.3,ease:"power2.out"}},{self.at(t0 + L.get("strike_at", 0.6))});')
        return out

    def _svg_draw(self, d, t, dur, color, width, dashed=False, head=False, glow=True):
        i = self.uid("sv")
        dash = 'stroke-dasharray="2 18"' if dashed else ""
        mk = f'marker-end="url(#ah-{i})"' if head else ""
        marker = (f'<defs><marker id="ah-{i}" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">'
                  f'<path d="M0,0 L10,5 L0,10 z" fill="{color}"/></marker></defs>') if head else ""
        filt = 'filter="drop-shadow(0 0 6px rgba(0,0,0,.6))"' if glow else ""
        out = (f'<svg class="ov" viewBox="0 0 {CARD_W} {CARD_H}">{marker}<path id="{i}" d="{d}" fill="none" stroke="{color}" '
               f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round" {dash} {mk} {filt}/></svg>')
        if dashed:
            self.js.append(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.15}},{self.at(t)});')
            self.js.append(f'tl.fromTo("#{i}",{{attr:{{"stroke-dashoffset":200}}}},{{attr:{{"stroke-dashoffset":0}},duration:{dur:.3f},ease:"none"}},{self.at(t)});')
        else:
            # hidden until drawn: the round linecap otherwise shows a dot at the start point
            self.js.append(f'(function(){{var p=document.getElementById("{i}");var l=p.getTotalLength();'
                           f'tl.fromTo(p,{{opacity:0}},{{opacity:1,duration:0.01}},{self.at(t)});'
                           f'tl.fromTo(p,{{strokeDasharray:l,strokeDashoffset:l}},{{strokeDashoffset:0,duration:{dur:.3f},ease:"power2.inOut"}},{self.at(t)});}})();')
        return out

    def r_ring(self, L, t0, t1):
        x, y, w, h = L["x"], L["y"], L["w"], L["h"]
        cx, cy, rx, ry = x + w / 2, y + h / 2, w / 2, h / 2
        # hand-drawn ellipse: slightly more than one turn with a wobble
        pts = []
        for k in range(0, 76):
            a = -math.pi / 2 + k / 72 * 2 * math.pi * 1.06
            wob = 1 + 0.04 * math.sin(k * 0.7)
            pts.append((cx + rx * wob * math.cos(a), cy + ry * wob * math.sin(a)))
        d = "M" + "L".join(f"{px:.1f},{py:.1f}" for px, py in pts)
        return self._svg_draw(d, t0 + L.get("at", 0), L.get("dur", 0.5), L.get("color", self.accent), L.get("width", 8))

    def r_arrow(self, L, t0, t1):
        (x1, y1), (x2, y2) = L["from"], L["to"]
        bend = L.get("bend", 0.25)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        nx, ny = -(y2 - y1), (x2 - x1)
        cx, cy = mx + nx * bend, my + ny * bend
        d = f"M{x1:.1f},{y1:.1f} Q{cx:.1f},{cy:.1f} {x2:.1f},{y2:.1f}"
        return self._svg_draw(d, t0 + L.get("at", 0), L.get("dur", 0.6), L.get("color", self.accent), L.get("width", 7),
                              dashed=L.get("dashed", False), head=True)

    def r_route(self, L, t0, t1):
        pts = [self.map_proj(lon, lat) for lon, lat in L["path"]]
        if len(pts) == 2:
            (x1, y1), (x2, y2) = pts
            bend = L.get("bend", 0.2)
            nx, ny = -(y2 - y1), (x2 - x1)
            cx, cy = (x1 + x2) / 2 + nx * bend, (y1 + y2) / 2 + ny * bend
            d = f"M{x1:.1f},{y1:.1f} Q{cx:.1f},{cy:.1f} {x2:.1f},{y2:.1f}"
        else:
            d = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        return self._svg_draw(d, t0 + L.get("at", 0), L.get("dur", 0.8), L.get("color", self.accent), L.get("width", 6),
                              dashed=L.get("dashed", False), head=L.get("head", True))

    def r_highlight(self, L, t0, t1):
        import re
        ids = L["ids"]
        paths = re.findall(r'<path class="land" data-id="([^"]+)" d="([^"]+)"/>', self.map_svg)
        sel = [d for pid, d in paths if pid in ids]
        i = self.uid("hl")
        color = L.get("color", self.accent)
        out = (f'<svg class="ov" viewBox="0 0 {CARD_W} {CARD_H}"><g id="{i}" fill="{color}" fill-opacity="0.85" '
               f'stroke="#FFFFFF" stroke-width="2.5">' + "".join(f'<path d="{d}"/>' for d in sel) + "</g></svg>")
        a = t0 + L.get("at", 0)
        self.js.append(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.3}},{self.at(a)});')
        if L.get("pulse", True):
            self.js.append(f'tl.to("#{i}",{{attr:{{"fill-opacity":0.55}},duration:0.45,yoyo:true,repeat:{max(1, int((t1 - a) / 0.45) - 1)},ease:"sine.inOut"}},{self.at(a + 0.3)});')
        if L.get("cross"):
            xs = [float(v) for d in sel for v in re.findall(r"([0-9.]+),", d)]
            ys = [float(v) for d in sel for v in re.findall(r",([0-9.]+)", d)]
            bx, by = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
            out += self.r_text({"text": "✕", "style": "big", "x": bx, "y": by, "size": 130, "color": "#FFFFFF",
                                "enter": "slam", "at": L["cross"]}, t0, t1)
        return out

    def r_pin(self, L, t0, t1):
        x, y = self.map_proj(L["lon"], L["lat"])
        i = self.uid("pn")
        side = L.get("side", "left")
        out = (f'<div id="{i}" class="pin" style="left:{x:.0f}px;top:{y:.0f}px">'
               f'<i style="background:{L.get("color", self.accent)}"></i>'
               f'<b class="pin-l {side}">{esc(L["label"])}</b></div>') if L.get("label") else (
               f'<div id="{i}" class="pin" style="left:{x:.0f}px;top:{y:.0f}px"><i style="background:{L.get("color", self.accent)}"></i></div>')
        self.js.append(f'tl.fromTo("#{i}",{{scale:0,opacity:0}},{{scale:1,opacity:1,duration:0.3,ease:"back.out(2)"}},{self.at(t0 + L.get("at", 0))});')
        return out

    def r_icon(self, L, t0, t1):
        i = self.uid("ic")
        svg = ICONS[L["name"]](self, L)
        s = L.get("s", 200)
        x, y = L["x"], L["y"]
        out = (f'<div class="icn" style="left:{x - s / 2:.0f}px;top:{y - s / 2:.0f}px;width:{s}px;height:{s}px;'
               f'transform:rotate({L.get("rot", 0)}deg)"><div id="{i}" class="icn-in">{svg}</div></div>')
        a = t0 + L.get("at", 0)
        enter = L.get("enter", "pop")
        if enter == "pop":
            self.js.append(f'tl.fromTo("#{i}",{{scale:0.4,opacity:0}},{{scale:1,opacity:1,duration:0.32,ease:"back.out(1.8)"}},{self.at(a)});')
        elif enter == "drop":
            self.js.append(f'tl.fromTo("#{i}",{{y:-220,opacity:0}},{{y:0,opacity:1,duration:0.35,ease:"bounce.out"}},{self.at(a)});')
        elif enter == "slide":
            self.js.append(f'tl.fromTo("#{i}",{{x:300,opacity:0}},{{x:0,opacity:1,duration:0.35,ease:"power3.out"}},{self.at(a)});')
        else:
            self.js.append(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.25}},{self.at(a)});')
        mv = L.get("move")
        if mv:
            self.js.append(f'tl.to("#{i}",{{x:{mv.get("dx", 0)},y:{mv.get("dy", 0)},rotation:{mv.get("rot", 0)},duration:{mv.get("dur", 1):.3f},ease:"{mv.get("ease", "power1.in")}"}},{self.at(t0 + mv.get("at", 0))});')
        if L.get("float"):
            self.js.append(f'tl.to("#{i}",{{y:-10,duration:0.8,yoyo:true,repeat:{max(1, int((t1 - a) / 0.8))},ease:"sine.inOut"}},{self.at(a + 0.3)});')
        return out

    def r_html(self, L, t0, t1):
        i = self.uid("hx")
        out = f'<div id="{i}" class="hx" style="{L.get("style", "")}">{L["html"]}</div>'
        self.js.append(f'tl.fromTo("#{i}",{L.get("from", "{opacity:0}")},{L.get("to", "{opacity:1,duration:0.3}")},{self.at(t0 + L.get("at", 0))});')
        for extra in L.get("js", []):
            self.js.append(extra.replace("#SELF", f"#{i}").replace("T0", self.at(t0)))
        return out

    def r_sea(self, L, t0, t1):
        i = self.uid("sea")
        top = L.get("top", 430)
        waves = "".join(
            f'<path class="wv" d="M-200,{20 + k * 26} ' + " ".join(f"Q{-150 + 100 * j},{8 + k * 26} {-100 + 100 * j},{20 + k * 26} T{0 + 100 * j},{20 + k * 26}" for j in range(0, 14, 2)) + '"/>'
            for k in range(0, 9))
        out = (f'<div class="sea" style="top:{top}px"><svg id="{i}" width="1480" height="{CARD_H - top + 20}" viewBox="0 0 1480 {CARD_H - top + 20}">'
               f'<rect width="1480" height="{CARD_H - top + 20}" fill="#1d2a2c"/>{waves}</svg></div>')
        self.js.append(f'tl.fromTo("#{i}",{{x:0}},{{x:-200,duration:{t1 - t0:.3f},ease:"none"}},{self.at(t0)});')
        return out

    def render_layer(self, L, t0, t1):
        k = L["type"]
        if k == "photo":
            return self.r_photo(L, t0, t1)
        if k == "narr":
            L = dict(L)
            L["src"] = f"assets/poses/{L.pop('pose')}.png"
            L["swap"] = [(t, f"assets/poses/{p}.png") for t, p in L.get("swap", [])]
            if L.get("frames"):
                L["frames"] = [f"assets/poses/{p}.png" for p in L["frames"]]
            return self.r_pic(L, t0, t1, NARRATOR_SCALE)
        if k == "char":
            L = dict(L)
            L["src"] = f"assets/chars/{L.pop('name')}.png"
            return self.r_pic(L, t0, t1, CHAR_SCALE)
        return getattr(self, "r_" + k)(L, t0, t1)

    # ---------- document assembly ----------
    def build(self, out="index.html"):
        A, SB = self.accent, self.scene_bg
        shots_html = []
        for n, s in enumerate(self.shots):
            t0, t1 = s["t0"], s["t1"]
            bgcls = {"scene": "bg-scene", "dark": "bg-dark", "none": "", "paper": "bg-paper", "map": "bg-map"}[s["bg"]]
            inner = "".join(self.render_layer(L, t0, t1) for L in s["layers"])
            maplayer = ""
            shots_html.append(f'<div id="shot{n}" class="clip shot {bgcls}" data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" '
                              f'data-track-index="1">{maplayer}{inner}</div>')
            if s["chapter"] and n > 0:
                self.js.append(f'tl.to("#dip",{{opacity:1,duration:0.1,ease:"none"}},{self.at(t0 - 0.1)});'
                               f'tl.to("#dip",{{opacity:0,duration:0.1,ease:"none"}},{self.at(t0)});')
        # scene-title band segments
        labels, cur = [], None
        for s in self.shots:
            if cur and cur["label"] == s["label"] and abs(cur["t1"] - s["t0"]) < 0.05:
                cur["t1"] = s["t1"]
            else:
                cur = dict(label=s["label"], t0=s["t0"], t1=s["t1"])
                labels.append(cur)
        label_html = "".join(
            f'<div class="clip stitle" data-start="{l["t0"]:.3f}" data-duration="{l["t1"] - l["t0"]:.3f}" data-track-index="2">'
            f'<i class="dot"></i><span>{esc(l["label"])}</span></div>' for l in labels if l["label"])
        # captions
        cap_html = []
        for k, c in enumerate(self.captions):
            t0 = c["start"]
            t1 = self.captions[k + 1]["start"] if k + 1 < len(self.captions) else min(c["end"] + 0.6, self.voice_end + 0.3)
            text = esc(c["text"])
            for kt, kw in self.keywords:  # (time inside the caption, word): colour that one occurrence only
                if t0 - 0.01 <= kt < t1:
                    text = text.replace(esc(kw), f'<em style="color:{A}">{esc(kw)}</em>', 1)
            cid = f"cap{k}"
            cap_html.append(f'<div class="clip cap" data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" data-track-index="3">'
                            f'<div id="{cid}" class="cap-box" dir="rtl">{text}</div></div>')
            self.js.append(f'tl.fromTo("#{cid}",{{opacity:0,y:10}},{{opacity:1,y:0,duration:0.14,ease:"power2.out"}},{self.at(t0)});')
        # progress bar + grain jitter
        self.js.append(f'tl.fromTo("#prog",{{scaleX:0}},{{scaleX:1,duration:{self.voice_end:.3f},ease:"none"}},0);')
        seed = 12345
        t = 0.0
        while t < self.duration:
            seed = (seed * 1103515245 + 12345) % 2 ** 31
            gx, gy = seed % 120 - 60, (seed // 120) % 80 - 40
            self.js.append(f'tl.set("#grain",{{x:{gx},y:{gy}}},{t:.3f});')
            t += 2 / FPS
        end_t0 = self.voice_end + 0.05
        audio = (f'<audio id="mix" src="{esc(self.audio_src)}" data-start="0" data-duration="{self.duration:.3f}" '
                 f'data-track-index="5" data-volume="1"></audio>') if self.audio_src else ""
        doc = TEMPLATE.format(
            css=CSS.replace("%ACCENT%", A).replace("%SCENEBG%", SB) + "\n".join(self.css_extra),
            duration=f"{self.duration:.3f}", title=esc(self.title).replace("\n", "<br>"),
            shots="\n".join(shots_html), labels=label_html, caps="\n".join(cap_html), audio=audio,
            end_start=f"{end_t0:.3f}", end_dur=f"{self.duration - end_t0:.3f}",
            js="\n".join(self.js), mapsvg=self.map_svg or "")
        (self.dir / out).write_text(doc)
        if self.alive_jobs:
            (self.dir / "assets/alive").mkdir(parents=True, exist_ok=True)
            made = alive.render_all(self.alive_jobs)
            print(f"living poses: {len(self.alive_jobs)} clips ({len(made)} rendered, {len(self.alive_jobs) - len(made)} cached)")
        return doc


# ---------- icons (flat, black outline, white sticker stroke) ----------
def _wrap(inner, vb="0 0 200 200"):
    return (f'<svg viewBox="{vb}" width="100%" height="100%" style="overflow:visible;'
            f'filter:drop-shadow(0 0 0 #fff) drop-shadow(3px 0 0 #fff) drop-shadow(-3px 0 0 #fff) drop-shadow(0 3px 0 #fff) drop-shadow(0 -3px 0 #fff) drop-shadow(0 8px 10px rgba(0,0,0,.45))">{inner}</svg>')


K = 'stroke="#1B1D1E" stroke-width="6" stroke-linejoin="round" stroke-linecap="round"'

ICONS = {
    "letter": lambda v, L: _wrap(f'<rect x="20" y="50" width="160" height="105" rx="8" fill="#F2EADA" {K}/>'
                                 f'<path d="M22 54 L100 112 L178 54" fill="none" {K}/>'
                                 f'<path d="M100 98 c-10-14-28-4-18 8 l18 16 l18-16 c10-12-8-22-18-8z" fill="{v.accent}" stroke="#1B1D1E" stroke-width="3"/>'),
    "ticket": lambda v, L: _wrap(f'<path d="M15 60 h170 v25 a15 15 0 0 0 0 30 v25 h-170 v-25 a15 15 0 0 0 0-30z" fill="#E9C46A" {K}/>'
                                 f'<path d="M140 62 v76" stroke="#1B1D1E" stroke-width="4" stroke-dasharray="6 6"/>'
                                 f'<text x="78" y="110" font-size="26" font-weight="700" text-anchor="middle" fill="#1B1D1E" font-family="Plex">مسرح</text>'),
    "receipt": lambda v, L: _wrap(f'<path d="M45 20 h110 v160 l-14-10 -14 10 -14-10 -14 10 -14-10 -14 10 -14-10 -12 10z" fill="#FFFDF7" {K}/>'
                                  + "".join(f'<path d="M62 {50 + k * 22} h{76 - (k % 2) * 26}" stroke="#7a7a7a" stroke-width="5" stroke-linecap="round"/>' for k in range(5))
                                  + f'<circle cx="128" cy="150" r="14" fill="none" stroke="{v.accent}" stroke-width="5"/>'),
    "ring": lambda v, L: _wrap(f'<circle cx="100" cy="120" r="52" fill="none" stroke="#D8A44A" stroke-width="16"/>'
                               f'<circle cx="100" cy="120" r="52" fill="none" stroke="#1B1D1E" stroke-width="3"/>'
                               f'<path d="M78 58 l22-34 l22 34 l-22 18z" fill="#BDE8FF" {K}/>'),
    "doc": lambda v, L: _wrap(f'<rect x="35" y="15" width="130" height="170" rx="6" fill="#F2EADA" {K}/>'
                              + "".join(f'<path d="M55 {60 + k * 20} h{90 - (k % 3) * 18}" stroke="#8a8270" stroke-width="5" stroke-linecap="round"/>' for k in range(6))
                              + f'<rect x="52" y="26" width="96" height="24" rx="3" fill="none" stroke="{v.accent}" stroke-width="4"/>'
                              f'<text x="100" y="45" font-size="17" font-weight="700" text-anchor="middle" fill="{v.accent}" font-family="Plex">سري للغاية</text>'),
    "briefcase": lambda v, L: _wrap(f'<rect x="20" y="62" width="160" height="110" rx="12" fill="#2b2b2b" {K}/>'
                                    f'<path d="M72 62 v-20 a8 8 0 0 1 8-8 h40 a8 8 0 0 1 8 8 v20" fill="none" {K}/>'
                                    f'<path d="M20 102 h160" stroke="#1B1D1E" stroke-width="5"/>'
                                    f'<rect x="88" y="94" width="24" height="18" rx="3" fill="#D8A44A" stroke="#1B1D1E" stroke-width="4"/>'),
    "telegram": lambda v, L: _wrap(f'<rect x="20" y="30" width="160" height="140" rx="4" fill="#F2EADA" {K}/>'
                                   f'<rect x="20" y="30" width="160" height="34" fill="{v.accent}" {K}/>'
                                   f'<text x="100" y="56" font-size="22" font-weight="700" text-anchor="middle" fill="#fff" font-family="Plex">برقية عاجلة</text>'
                                   + "".join(f'<path d="M38 {88 + k * 20} h{124 - (k % 2) * 34}" stroke="#8a8270" stroke-width="5" stroke-linecap="round"/>' for k in range(4))),
    "plane": lambda v, L: _wrap(f'<path d="M20 100 L150 90 Q185 92 185 100 Q185 108 150 110 L20 100z" fill="#7b8a70" {K}/>'
                                f'<path d="M95 94 L60 40 L82 40 L125 92z M95 106 L60 160 L82 160 L125 108z M28 100 L14 76 L28 76 L44 98z" fill="#5f6b55" {K}/>'),
    "qmark": lambda v, L: _wrap('<text x="100" y="160" font-size="190" font-weight="700" text-anchor="middle" fill="#A9E34B" stroke="#1B1D1E" stroke-width="5" font-family="Plex">؟</text>'),
    "excl": lambda v, L: _wrap('<text x="100" y="165" font-size="190" font-weight="700" text-anchor="middle" fill="#A9E34B" stroke="#1B1D1E" stroke-width="5" font-family="Plex">!</text>'),
    "check": lambda v, L: _wrap(f'<circle cx="100" cy="100" r="80" fill="#2f9e44" {K}/><path d="M60 102 l28 28 l54-60" fill="none" stroke="#fff" stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>'),
    "cross": lambda v, L: _wrap(f'<circle cx="100" cy="100" r="80" fill="{v.accent}" {K}/><path d="M65 65 l70 70 M135 65 l-70 70" stroke="#fff" stroke-width="18" stroke-linecap="round"/>'),
    "radio": lambda v, L: _wrap(f'<rect x="45" y="90" width="110" height="80" rx="10" fill="#5f6b55" {K}/><circle cx="80" cy="130" r="20" fill="#2b2b2b" {K}/>'
                                f'<path d="M120 115 h20 M120 135 h20 M120 155 h20" stroke="#1B1D1E" stroke-width="5"/><path d="M130 90 L150 30" {K}/>'
                                + "".join(f'<path d="M{150 - r} {30 - r * .3} A{r} {r} 0 0 1 {150 + r} {30 - r * .3}" fill="none" stroke="#A9E34B" stroke-width="6" stroke-linecap="round"/>' for r in (18, 34, 50))),
    "eye": lambda v, L: _wrap(f'<path d="M15 100 Q100 25 185 100 Q100 175 15 100z" fill="#F2EADA" {K}/><circle cx="100" cy="100" r="32" fill="{v.accent}" {K}/><circle cx="100" cy="100" r="12" fill="#1B1D1E"/>'),
    "calendar": lambda v, L: _wrap(f'<rect x="25" y="35" width="150" height="145" rx="10" fill="#FFFDF7" {K}/><rect x="25" y="35" width="150" height="42" rx="10" fill="{v.accent}" {K}/>'
                                   f'<text x="100" y="66" font-size="26" font-weight="700" text-anchor="middle" fill="#fff" font-family="Plex">{esc(L.get("month", ""))}</text>'
                                   f'<text x="100" y="150" font-size="58" font-weight="700" text-anchor="middle" fill="#1B1D1E" font-family="Plex">{esc(L.get("year", ""))}</text>'),
    "polaroid": lambda v, L: _wrap(f'<rect x="20" y="10" width="160" height="185" rx="4" fill="#FFFDF7" {K}/>'
                                   f'<image href="{esc(L["src"])}" x="32" y="22" width="136" height="130" preserveAspectRatio="xMidYMid slice"/>'),
    "idcard": lambda v, L: _wrap(f'<rect x="10" y="40" width="180" height="120" rx="12" fill="#FFC21A" {K}/>'
                                 f'<path d="M30 70 l14-24 l14 24z" fill="#1B1D1E"/><text x="44" y="68" font-size="16" font-weight="700" text-anchor="middle" fill="#FFC21A" font-family="Plex">!</text>'
                                 f'<text x="112" y="88" font-size="19" font-weight="700" text-anchor="middle" fill="#1B1D1E" font-family="Plex">{esc(L.get("l1", ""))}</text>'
                                 f'<text x="100" y="128" font-size="25" font-weight="700" text-anchor="middle" fill="#1B1D1E" font-family="Plex">{esc(L.get("l2", ""))}</text>'),
    "wave": lambda v, L: _wrap('<path d="M10 120 q30-40 60 0 t60 0 t60 0" fill="none" stroke="#9ec7d0" stroke-width="10" stroke-linecap="round"/>'),
}

CSS = r"""
@font-face{font-family:Plex;src:url("assets/fonts/IBMPlexSansArabic-Regular.ttf") format("truetype");font-weight:400}
@font-face{font-family:Plex;src:url("assets/fonts/IBMPlexSansArabic-SemiBold.ttf") format("truetype");font-weight:600}
@font-face{font-family:Plex;src:url("assets/fonts/IBMPlexSansArabic-Bold.ttf") format("truetype");font-weight:700}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#191917}
#root{position:relative;width:100%;height:100%;overflow:hidden;background:#191917;font-family:Plex,sans-serif;color:#fff}
.band{position:absolute;left:0;width:1080px;background:#0E0E0E}
#topband{top:200px;height:230px;display:flex;align-items:center;justify-content:center;text-align:center}
#qtitle{font-weight:700;font-size:74px;line-height:1.3;background:linear-gradient(#FFC21A,#F08A1C);-webkit-background-clip:text;background-clip:text;color:transparent;padding:0 60px}
#labelband{top:430px;height:70px}
#labellayer{position:absolute;top:430px;left:0;width:1080px;height:70px}
.stitle{position:absolute;inset:0;display:flex;align-items:center;justify-content:flex-start;direction:rtl;padding-right:72px;gap:18px;font-weight:600;font-size:46px;color:#fff}
.stitle .dot{width:18px;height:18px;border-radius:50%;background:#A9E34B;display:block}
#stage{position:absolute;top:500px;left:0;width:1080px;height:680px;overflow:hidden;background:%SCENEBG%}
.shot{position:absolute;inset:0;overflow:hidden}
.bg-scene{background:%SCENEBG% url("assets/img/scene-bg.png") center/cover no-repeat}
.bg-dark{background:#0E0E0E url("assets/img/dark-bg.png") center/cover no-repeat}
.bg-paper{background:#E8DFCC}
.bg-map{background:transparent}
.map-base{position:absolute;inset:0}
.map-svg{position:absolute;inset:0;width:1080px;height:680px}
.map-svg .land{fill:#3a3d2f;stroke:#5c6048;stroke-width:1.2}
.ph{position:absolute;inset:0;overflow:hidden}
.ph img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;filter:grayscale(1) contrast(1.08)}
.ph-dim{position:absolute;inset:0;background:#000}
.ph-vig{position:absolute;inset:0;background:url("assets/img/vignette.png") center/cover no-repeat}
.ph-blur{position:absolute;inset:-40px;overflow:hidden}
.ph-blur img{width:100%;height:100%;object-fit:cover}
.ph-frame{position:absolute;background:#F2EADA;padding:14px 14px 40px;box-shadow:0 18px 40px rgba(0,0,0,.6)}
.ph-frame img{width:100%;height:100%;object-fit:cover;filter:grayscale(1) contrast(1.1);display:block}
.pic{position:absolute}
.pic .flip{position:absolute;inset:0}
.pic img{position:absolute;bottom:0}
.pic video{position:absolute;display:block}
.ov{position:absolute;inset:0;width:1080px;height:680px;overflow:visible;pointer-events:none}
.t-anchor{position:absolute;width:0;height:0;display:flex;align-items:center;justify-content:center}
.t-anchor>div{position:absolute;white-space:nowrap;direction:rtl}
.t-year{font-weight:700;font-size:170px;line-height:1;background:linear-gradient(#FFC21A,#F08A1C);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 8px 0 rgba(0,0,0,.5))}
.t-big{font-weight:700;font-size:96px;color:#fff;text-shadow:0 6px 0 rgba(0,0,0,.55)}
.t-stamp{font-weight:700;font-size:78px;border:8px solid;border-radius:14px;padding:0 26px;line-height:1.35;background:rgba(14,14,14,.25)}
.t-label{font-weight:600;font-size:40px;color:#1B1D1E;background:#F2EADA;padding:6px 22px;border-radius:10px;box-shadow:0 6px 0 rgba(0,0,0,.4)}
.t-tag{font-weight:700;font-size:44px;color:#1B1D1E;background:#FFC21A;padding:8px 26px;border-radius:12px;border:5px solid #1B1D1E;box-shadow:0 0 0 6px #fff,0 10px 20px rgba(0,0,0,.5)}
.t-note{font-weight:600;font-size:36px;color:#F2EADA;text-shadow:0 3px 0 #000}
.strike{position:absolute;left:-6%;right:-6%;top:52%;height:12px;border-radius:6px;transform-origin:100% 50%}
.t-anchor>div{position:absolute}
.icn{position:absolute}
.icn-in{width:100%;height:100%}
.pin{position:absolute;width:0;height:0}
.pin i{position:absolute;left:-13px;top:-13px;width:26px;height:26px;border-radius:50%;border:4px solid #fff;box-shadow:0 0 0 4px rgba(0,0,0,.4)}
.pin-l{position:absolute;top:-26px;white-space:nowrap;font-weight:700;font-size:34px;color:#fff;text-shadow:0 3px 0 #000,0 0 10px #000;direction:rtl}
.pin-l.left{right:22px}.pin-l.right{left:22px}.pin-l.up{top:-78px;left:-60px}.pin-l.down{top:18px;left:-50px}
.sea{position:absolute;left:0;width:1080px;bottom:0;overflow:hidden}
.wv{fill:none;stroke:#3f5a5e;stroke-width:5;stroke-linecap:round}
.hx{position:absolute}
#grain{position:absolute;left:-60px;top:-40px;width:1200px;height:760px;background-image:url("assets/img/grain.png");opacity:.07;mix-blend-mode:screen;pointer-events:none}
#dip{position:absolute;inset:0;background:#000;opacity:0;pointer-events:none}
#capzone{top:1180px;height:240px;background:#191917}
#caplayer{position:absolute;top:1180px;left:0;width:1080px;height:240px}
.cap{position:absolute;inset:0;display:flex;align-items:center;justify-content:center}
.cap-box{max-width:930px;background:rgba(14,14,14,.88);border-radius:14px;padding:20px 30px;font-weight:600;font-size:62px;line-height:1.35;text-align:center;color:#fff}
.cap-box em{font-style:normal}
#partband{top:1420px;height:140px}
#bottom{top:1560px;height:360px}
#wm{position:absolute;left:72px;top:1600px;width:84px;height:84px;opacity:.85}
#prog{position:absolute;right:0;top:1908px;width:1080px;height:6px;background:%ACCENT%;transform-origin:100% 50%}
#endcard{position:absolute;inset:0;background:#0E0E0E;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px}
#endcard img{width:240px;height:240px}
#endname{font-weight:700;font-size:84px;line-height:1.1;background:linear-gradient(#FFC21A,#F08A1C);-webkit-background-clip:text;background-clip:text;color:transparent}
#endtag{font-weight:400;font-size:34px;color:#F2EADA}
"""

TEMPLATE = """<!doctype html>
<html lang="ar" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="assets/vendor/gsap.min.js"></script>
<style>{css}</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{duration}" data-width="1080" data-height="1920" data-fps="30">
  <div class="band" id="topband"><div id="qtitle" dir="rtl">{title}</div></div>
  <div class="band" id="labelband"></div>
  <div id="labellayer">{labels}</div>
  <div id="stage">
    <div class="map-base" style="background:#1d2a2c">{mapsvg}</div>
    {shots}
    <div id="grain"></div>
    <div id="dip"></div>
  </div>
  <div class="band" id="capzone"></div>
  <div id="caplayer">{caps}</div>
  <div class="band" id="partband"></div>
  <div class="band" id="bottom"></div>
  <img id="wm" src="assets/img/logo.png" alt="" />
  <div id="prog"></div>
  <div id="endcard" class="clip" data-start="{end_start}" data-duration="{end_dur}" data-track-index="4">
    <img id="endlogo" src="assets/img/logo.png" alt="" />
    <div id="endname">النيرد</div>
    <div id="endtag">قصص · تاريخ · تقنية · وجرائم</div>
  </div>
  {audio}
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{js}
tl.fromTo("#endlogo",{{scale:0.7,opacity:0}},{{scale:1,opacity:1,duration:0.4,ease:"back.out(1.6)"}},{end_start});
window.__timelines["main"] = tl;
</script>
</body>
</html>
"""
