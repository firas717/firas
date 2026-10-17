// Deterministic frame engine for 1080x1920 Shorts.
// The page exposes window.renderFrame(t) -> Promise; every visual property is a pure
// function of t (seconds), so any frame can be rendered in any order.
(function () {
  const W = 1080, H = 1920;
  const TL = window.TL;                       // timeline injected by timeline.js
  const stage = document.getElementById('stage');

  // ---------- easing (brand) ----------
  function bezier(x1, y1, x2, y2) {
    const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx;
    const cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
    const sx = t => ((ax * t + bx) * t + cx) * t, sy = t => ((ay * t + by) * t + cy) * t;
    const dx = t => (3 * ax * t + 2 * bx) * t + cx;
    return x => {
      if (x <= 0) return 0; if (x >= 1) return 1;
      let t = x;
      for (let i = 0; i < 8; i++) { const e = sx(t) - x, d = dx(t); if (Math.abs(e) < 1e-6) break; if (Math.abs(d) < 1e-6) break; t -= e / d; }
      if (t < 0 || t > 1) { let lo = 0, hi = 1; t = x; for (let i = 0; i < 30; i++) { const v = sx(t); if (v < x) lo = t; else hi = t; t = (lo + hi) / 2; } }
      return sy(t);
    };
  }
  const EASE = {
    standard: bezier(0.33, 0, 0.10, 1),
    exit: bezier(0.60, 0, 0.85, 0.30),
    snap: bezier(0.22, 1.20, 0.36, 1),
    inout: bezier(0.65, 0, 0.35, 1),
    kb: bezier(0.40, 0.0, 0.60, 1.0),          // gentle in-out for Ken Burns drifts
    linear: x => x,
  };
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, u) => a + (b - a) * u;
  const seg = (t, a, b) => clamp((t - a) / Math.max(1e-6, b - a), 0, 1);
  const ez = (name, u) => (EASE[name] || EASE.standard)(clamp(u, 0, 1));
  const AR_DIGITS = '٠١٢٣٤٥٦٧٨٩';
  const arNum = (n) => String(n).replace(/[0-9]/g, d => AR_DIGITS[+d]);
  const H_ = { W, H, EASE, ez, clamp, lerp, seg, arNum, svgNS: 'http://www.w3.org/2000/svg' };
  window.ENGINE = H_;

  function el(tag, cls, parent, style) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (style) Object.assign(e.style, style);
    (parent || stage).appendChild(e);
    return e;
  }
  H_.el = el;
  function svg(tag, attrs, parent) {
    const e = document.createElementNS(H_.svgNS, tag);
    for (const k in attrs || {}) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  H_.svg = svg;

  // ---------- transitions on a layer: returns {opacity, tx, blur, scale} ----------
  function transitionState(L, t) {
    let op = 1, tx = 0, blur = 0, sc = 1;
    const tin = L.in || { type: 'cut' }, tout = L.out || { type: 'cut' };
    if (tin.type === 'fade' || tin.type === 'dissolve') op *= ez(tin.ease || 'standard', seg(t, L.start, L.start + (tin.dur || 0.4)));
    if (tin.type === 'whip') { const u = seg(t, L.start, L.start + (tin.dur || 0.2)); tx += (1 - ez('standard', u)) * (tin.dir || 1) * W; blur += (1 - u) * 18; }
    if (tin.type === 'pop') { const u = ez('snap', seg(t, L.start, L.start + (tin.dur || 0.3))); sc *= lerp(0.92, 1, u); op *= clamp(u * 1.5, 0, 1); }
    if (tout.type === 'fade' || tout.type === 'dissolve') op *= 1 - ez(tout.ease || 'exit', seg(t, L.end - (tout.dur || 0.4), L.end));
    if (tout.type === 'whip') { const u = seg(t, L.end - (tout.dur || 0.2), L.end); tx -= ez('exit', u) * (tout.dir || 1) * W; blur += u * 18; }
    return { op, tx, blur, sc };
  }

  // ---------- layer types ----------
  const TYPES = {};
  H_.TYPES = TYPES;

  // Background textures / solids with slow drift
  TYPES.bg = {
    create(L) {
      const e = el('div', 'layer bg');
      if (L.color) e.style.background = L.color;
      if (L.src) { const i = el('img', 'bgimg', e); i.src = L.src; L._img = i; }
      return e;
    },
    update(L, t, e) {
      if (L._img) {
        const u = seg(t, L.start, L.end);
        const [x0, y0] = L.from || [0, 0], [x1, y1] = L.to || [0, -120];
        L._img.style.transform = `translate(${lerp(x0, x1, u)}px, ${lerp(y0, y1, u)}px)`;
        L._img.style.opacity = L.opacity == null ? 1 : L.opacity;
      }
    },
  };

  // Photos / video frame sequences: layout full or framed, Ken Burns, grading
  TYPES.media = {
    create(L) {
      const e = el('div', 'layer media ' + (L.layout || 'full'));
      if (L.layout === 'blur') {          // blurred full-frame background only (end cards)
        const bg = el('div', 'blurbg', e);
        const bi = el('img', '', bg); bi.src = L.blurSrc || L.src; L._bgimg = bi;
        el('div', 'scrim', e);
        L._blurOnly = true;
        return e;
      }
      if (L.layout === 'framed') {
        const bg = el('div', 'blurbg', e);
        const bi = el('img', '', bg); bi.src = L.blurSrc || L.src; L._bgimg = bi;
        el('div', 'scrim', e);
        const card = el('div', 'card', e);
        const cw = L.card?.w || 980, ch = Math.round(cw / (L.card?.aspect || (L.iw / L.ih)));
        Object.assign(card.style, { width: cw + 'px', height: ch + 'px', left: (W - cw) / 2 + 'px', top: ((L.card?.cy || 860) - ch / 2) + 'px' });
        L._cw = cw; L._ch = ch; L._card = card;
        const img = el('img', 'mimg', card); L._img = img;
      } else {
        L._cw = W; L._ch = H;
        const img = el('img', 'mimg', e); L._img = img;
      }
      if (L.kind !== 'seq') L._img.src = L.src;
      if (L.grade) e.classList.add('grade-' + L.grade);
      if (L.tint) { const tn = el('div', 'tint', L._card || e); tn.style.background = L.tint; }
      return e;
    },
    update(L, t, e) {
      if (L._blurOnly) {
        const iw = L.iw, ih = L.ih, c2 = Math.max(W / iw, H / ih) * 1.15;
        Object.assign(L._bgimg.style, { width: iw * c2 + 'px', height: ih * c2 + 'px', transform: `translate(${(W - iw * c2) / 2}px, ${(H - ih * c2) / 2}px)` });
        return;
      }
      // cover-fit the source into the box, then Ken Burns scale/offset around a focus point
      const bw = L._cw, bh = L._ch, iw = L.iw, ih = L.ih;
      const cover = Math.max(bw / iw, bh / ih);
      const kb = L.kb || {};
      const u = ez(kb.ease || 'kb', seg(t, L.kbStart ?? L.start, L.kbEnd ?? L.end));
      const [s0, x0, y0] = kb.from || [1, 0, 0], [s1, x1, y1] = kb.to || [1.06, 0, 0];
      const s = cover * lerp(s0, s1, u);
      const [fx, fy] = L.focus || [0.5, 0.5];
      const dw = iw * s, dh = ih * s;
      let left = bw / 2 - fx * dw + lerp(x0, x1, u), top = bh / 2 - fy * dh + lerp(y0, y1, u);
      left = clamp(left, bw - dw, 0); top = clamp(top, bh - dh, 0);   // never show an edge
      if (L.kind === 'seq') {
        const fps = L.seq.fps || 30, n = L.seq.count;
        let k = Math.floor((t - L.start) * fps * (L.seq.speed || 1)) + (L.seq.offset || 0);
        k = clamp(k, 0, n - 1);
        const src = `${L.seq.dir}/${String(k + 1).padStart(5, '0')}.jpg`;
        if (L._img.getAttribute('src') !== src) L._img.src = src;
      }
      Object.assign(L._img.style, { width: dw + 'px', height: dh + 'px', transform: `translate(${left}px, ${top}px)` });
      if (L._bgimg) {
        const c2 = Math.max(W / iw, H / ih) * 1.15;
        Object.assign(L._bgimg.style, { width: iw * c2 + 'px', height: ih * c2 + 'px', transform: `translate(${(W - iw * c2) / 2}px, ${(H - ih * c2) / 2}px)` });
        if (L._card) {
          const tilt = L.card?.tilt || 0;
          L._card.style.transform = `rotate(${tilt}deg)`;
        }
      }
    },
  };

  // Text: kinetic words, titles, labels, dates. html allowed (span.acc for accent colour).
  TYPES.text = {
    create(L) {
      const e = el('div', 'layer textlayer');
      const box = el('div', 'tx ' + (L.style || 'keyword'), e);
      box.innerHTML = L.html || L.text;
      if (L.css) Object.assign(box.style, L.css);
      L._box = box;
      return e;
    },
    update(L, t, e) {
      const a = L.anim || 'up';
      const inD = L.inDur ?? 0.25, outD = L.outDur ?? 0.18;
      const ui = seg(t, L.start, L.start + inD), uo = seg(t, L.end - outD, L.end);
      let op = 1, ty = 0, sc = 1;
      if (a === 'up') { const v = ez('snap', ui); ty = (1 - v) * 24; op = clamp(ui * 2, 0, 1); }
      if (a === 'fade') { op = ez('standard', ui); }
      if (a === 'pop') { const v = ez('snap', ui); sc = lerp(0.85, 1, v); op = clamp(ui * 2, 0, 1); }
      if (a === 'none') { op = 1; }
      op *= 1 - ez('exit', uo); ty -= ez('exit', uo) * 12;
      // optional shrink-to-corner move
      if (L.move) {
        const um = ez(L.move.ease || 'standard', seg(t, L.move.at, L.move.at + (L.move.dur || 0.5)));
        const [mx, my, ms] = L.move.to;
        L._box.style.transform = `translate(${lerp(0, mx, um)}px, ${lerp(0, my, um) + ty}px) scale(${lerp(1, ms, um) * sc})`;
      } else {
        L._box.style.transform = `translateY(${ty}px) scale(${sc})`;
      }
      L._box.style.opacity = op;
    },
  };

  // Count-up number (Eastern Arabic digits by default)
  TYPES.counter = {
    create(L) {
      const e = el('div', 'layer textlayer');
      const box = el('div', 'tx ' + (L.style || 'stat'), e);
      if (L.css) Object.assign(box.style, L.css);
      L._num = el('span', 'num', box);
      if (L.unit) { const u = el('span', 'unit', box); u.innerHTML = L.unit; }
      L._box = box;
      return e;
    },
    update(L, t, e) {
      const u = ez(L.ease || 'standard', seg(t, L.countStart ?? L.start, (L.countStart ?? L.start) + (L.countDur ?? 0.6)));
      const v = Math.round(lerp(L.from ?? 0, L.to, u));
      const txt = (L.prefix || '') + (L.latin ? String(v) : arNum(v)) + (L.suffix || '');
      if (L._num.textContent !== txt) L._num.textContent = txt;
      const ui = seg(t, L.start, L.start + 0.25), uo = seg(t, L.end - 0.18, L.end);
      const v2 = ez('snap', ui);
      L._box.style.transform = `translateY(${(1 - v2) * 24}px)`;
      L._box.style.opacity = clamp(ui * 2, 0, 1) * (1 - ez('exit', uo));
    },
  };

  // Burned captions: one layer, many cues
  TYPES.captions = {
    create(L) {
      const e = el('div', 'layer caplayer');
      L._box = el('div', 'cap', e);
      return e;
    },
    update(L, t, e) {
      const cue = L.cues.find(c => t >= c.s && t < c.e);
      if (!cue) { L._box.style.opacity = 0; L._cur = null; return; }
      if (L._cur !== cue) { L._box.innerHTML = cue.html || cue.text; L._cur = cue; }
      const band = (L.bandRanges || []).some(([a, b]) => t >= a && t < b);
      L._box.classList.toggle('band', band);
      const ui = seg(t, cue.s, cue.s + 0.12), uo = seg(t, cue.e - 0.08, cue.e);
      L._box.style.opacity = Math.min(ez('standard', ui), 1 - uo);
    },
  };

  // Full-screen flashes: wash (white) / dip (black)
  TYPES.flash = {
    create(L) { const e = el('div', 'layer flash'); e.style.background = L.color || '#fff'; return e; },
    update(L, t, e) {
      const mid = (L.start + L.end) / 2;
      const u = t < mid ? seg(t, L.start, mid) : 1 - seg(t, mid, L.end);
      e.style.opacity = ez('inout', u) * (L.max ?? 1);
    },
  };

  // Custom graphics modules registered in graphics/*.js as window.GFX[name] = {create(el, L), draw(el, u, L)}
  TYPES.graphic = {
    create(L) {
      const e = el('div', 'layer gfx');
      const g = (window.GFX || {})[L.name];
      if (!g) { e.textContent = 'missing graphic ' + L.name; return e; }
      L._g = g; g.create(e, L, H_);
      return e;
    },
    update(L, t, e) { if (L._g) L._g.draw(e, t - L.start, L, H_); },
  };

  // Film grain + vignette
  TYPES.grain = {
    create(L) { const e = el('div', 'layer grain'); L._img = el('img', '', e); return e; },
    update(L, t, e) {
      const k = Math.floor(t * (L.fps || 12)) % (L.count || 8);
      const src = `${L.dir}/grain${k}.png`;
      if (L._img.getAttribute('src') !== src) L._img.src = src;
      e.style.opacity = L.opacity ?? 0.06;
    },
  };
  TYPES.overlay = {   // static decorative overlays (vignette, scrims)
    create(L) { const e = el('div', 'layer overlay ' + (L.cls || '')); if (L.css) Object.assign(e.style, L.css); return e; },
    update(L, t, e) { e.style.opacity = L.opacity ?? 1; },
  };

  // ---------- build ----------
  const layers = TL.layers.slice().sort((a, b) => (a.z || 0) - (b.z || 0));
  for (const L of layers) {
    const T = TYPES[L.type];
    L._el = T.create(L);
    L._el.style.zIndex = L.z || 0;
    L._el.style.display = 'none';
  }

  function imagesReady() {
    const imgs = Array.from(stage.querySelectorAll('img')).filter(i => i.offsetParent !== null && i.getAttribute('src'));
    return Promise.all(imgs.map(i => (i.complete && i.naturalWidth) ? Promise.resolve() : i.decode().catch(() => {})));
  }

  window.renderFrame = async function (t) {
    document.body.dataset.mode = (TL.modeSwitch != null && t >= TL.modeSwitch) ? 'day' : 'night';
    for (const L of layers) {
      const active = t >= L.start && t < L.end;
      if (!active) { if (L._el.style.display !== 'none') L._el.style.display = 'none'; continue; }
      if (L._el.style.display === 'none') L._el.style.display = '';
      TYPES[L.type].update(L, t, L._el);
      const st = transitionState(L, t);
      const tr = (st.tx || st.sc !== 1) ? `translateX(${st.tx}px) scale(${st.sc})` : '';
      L._el.style.transform = tr;
      L._el.style.filter = st.blur ? `blur(${st.blur.toFixed(1)}px)` : '';
      L._el.style.opacity = st.op * (L.opacity ?? 1);
    }
    await imagesReady();
    return true;
  };
  window.ENGINE_READY = (async () => { await document.fonts.ready; return true; })();
})();
