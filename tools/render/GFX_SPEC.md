# Motion-graphics modules — spec for builders

Channel: Arabic faceless documentary channel. This episode: the 2010 Copiapó (Chile) mine rescue,
rendered as a **vertical YouTube Short, 1080×1920, 30 fps**. Graphics are HTML/SVG drawn in headless
Chromium, one frame at a time.

## API (must follow exactly)

Create `tools/render/graphics/<name>.js`:

```js
window.GFX.<name> = {
  create(el, L, H) { /* build DOM/SVG once inside el (a 1080x1920 absolutely positioned div) */ },
  draw(el, u, L, H) { /* update everything for local time u (seconds since layer start) */ },
};
```

* `L.params` holds your parameters (documented per module below); `L.end - L.start` is the layer duration.
* `H` helpers (from `engine.js`): `H.ez(name,u)` easing with names `standard` (cubic-bezier .33,0,.10,1),
  `snap` (.22,1.20,.36,1 overshoot), `exit` (.60,0,.85,.30), `inout`; `H.seg(t,a,b)` → 0..1 clamp;
  `H.lerp`, `H.clamp`, `H.arNum(n)` → Eastern Arabic digits; `H.el(tag, cls, parent, style)`; `H.svg(tag, attrs, parent)`.
  `window.GFXU.prepDash(path)` / `GFXU.dash(path, len, v)` for stroke reveal.
* **Deterministic**: `draw` must be a pure function of `u` (no Date, no Math.random at draw time, no CSS
  transitions/animations, no requestAnimationFrame). Seeded pseudo-random in `create` is fine.
* Never linear easing for motion. Nothing may move without easing.
* Keep it self-contained (inline SVG; no network). Images only via `file://` paths given in params.

## Brand rules (binding)

* Colours: use CSS variables so night/day mode works: `var(--bg) var(--surface) var(--surface-alt) var(--text)
  var(--muted) var(--border) var(--accent)` (amber #E9A13B) `var(--accent-dim)` (#B87C25) `var(--alert)` (#C8402E,
  only for danger/collapse). Night: bg #0B0E13, text #F2EFE9. Day: bg #F3F0E9, text #12161C.
  Amber is the only accent colour; it should cover ≤10% of the screen.
* Fonts (already loaded by the page): `'Readex Pro'` weight 700 for titles/keywords (add
  `font-variation-settings:'wght' 800` for heavy); `'Plex Arabic'` weights 500/600/700 for labels and numbers.
  Arabic numbers use **Eastern Arabic digits** (٠١٢٣٤٥٦٧٨٩) via `H.arNum` or literal strings.
* Arabic is RTL: put `direction: rtl` on text elements (the page sets `body *{direction:rtl}` already;
  SVG `<text>` needs `direction="rtl"` and usually `text-anchor="middle"`). No letter-spacing, no uppercase,
  no letter-by-letter animation (animate whole words/lines).
* Sizes (Shorts scale): titles 154–196 px, keywords 100–134 px, labels 48–60 px, small annotations ≥ 38 px.
  Lines 2–4 px, rounded caps. Soft glows allowed (`filter: drop-shadow(0 0 12px rgba(233,161,59,.35))`).
* Text contrast ≥ 4.5:1 against what is behind it.
* **Safe areas** (YouTube Shorts UI covers parts of the frame): keep all text and key elements inside
  x 76…1004 and y 200…1230. Captions are burned at y ≈ 1260–1450, so **leave y > 1240 free of text**;
  decorative backgrounds may extend everywhere. Keep x > 960 free of small text below y 1000 (side buttons).
* Style reference: calm, premium documentary (Vox / Al Daheeh / Masaha). Clean flat shapes, thin lines,
  subtle depth, generous spacing. No clip-art, no emoji, no gradients that look cheap, no neon.
* Motion vocabulary: enter by moving 24 px up over 0.25 s with `snap`; exit 0.18 s with `exit`;
  strokes draw with `standard` over 0.4–1.2 s; pulses use `inout` and are subtle.

## How to test your module (do this, look at the PNGs, iterate until it looks professional)

```bash
mkdir -p /home/user/firas/tools/render/test/<name> && cd /home/user/firas/tools/render/test/<name>
# write timeline.js with: a bg layer + your graphic layer (+ optionally a captions layer to check overlap)
node /home/user/firas/tools/render/render.js timeline.js stills --gfx <name> --stills 0.2,0.8,1.5,3,5
```

`timeline.js` format:
```js
window.TL = {"duration": 6, "fps": 30, "modeSwitch": null, "layers": [
  {"type":"bg","start":0,"end":6,"z":0,"color":"#0B0E13"},
  {"type":"graphic","name":"<name>","start":0,"end":6,"z":3,"params":{...}},
  {"type":"captions","start":0,"end":6,"z":8,"cues":[{"s":0,"e":6,"text":"سطر ترجمة تجريبي يملأ مكان الترجمة"}]}
]};
```
Set `"modeSwitch": 0` to test day mode. Read the PNGs in `stills/` with the Read tool to check them.
Check: no overlaps, nothing clipped, Arabic shaped and RTL, numbers Eastern, everything inside safe areas,
animation states sensible at every sampled time (before/after each beat), looks premium.

Only write files inside `tools/render/graphics/<name>.js` and `tools/render/test/<name>/`.
