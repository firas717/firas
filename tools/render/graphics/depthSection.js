// depthSection — vertical ground cross-section: surface + headframe, strata, depth ruler,
// an amber dashed line descending to the miners' depth, label, optional "?" and Eiffel comparison.
//
// params (all optional):
//   surfaceY 560      y of the ground surface line
//   depthPx 600       pixels from the surface to maxDepthM
//   maxDepthM 700     ruler range in metres (ticks every tickStep)
//   targetM           depth the line descends to (default maxDepthM)
//   tickStep 100      ruler tick spacing (m); minor ticks at half steps
//   x 540             x of the headframe / descending line
//   tIntro [0,0.5]    ruler + headframe reveal (null = shown from u=0)
//   tLine [0.5,3.0]   descent of the dashed line (eased 'standard')
//   tLabel 3.0        label entrance ('up'); label '' or null = no label
//   label '٧٠٠ متر تحت الأرض'   first line = number + next word (number in amber), rest on line 2;
//                                use '|' or '\n' to force the break
//   labelSize 84, label2Size 58
//   question false, tQuestion     pulsing '؟' beside the dot
//   compare false, tCompare       two upside-down Eiffel towers stacked in the ground
//   towerM 330, compareLabel 'برجا إيفل = ٦٦٠ م'
//   seed 7            texture / strata randomness
(function () {
  window.GFX = window.GFX || {};
  let UID = 0;

  // ---------- helpers ----------
  function rng(seed) {
    let a = seed >>> 0;
    return () => {
      a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  const f1 = (v) => v.toFixed(1);
  function crPath(pts) {          // Catmull-Rom spline through pts (after an M to pts[0])
    let d = '';
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)];
      const c1x = p1[0] + (p2[0] - p0[0]) / 6, c1y = p1[1] + (p2[1] - p0[1]) / 6;
      const c2x = p2[0] - (p3[0] - p1[0]) / 6, c2y = p2[1] - (p3[1] - p1[1]) / 6;
      d += `C${f1(c1x)},${f1(c1y)} ${f1(c2x)},${f1(c2y)} ${f1(p2[0])},${f1(p2[1])}`;
    }
    return d;
  }
  const polyD = (pts, close) => 'M' + pts.map(p => f1(p[0]) + ',' + f1(p[1])).join('L') + (close ? 'Z' : '');
  function interpY(pts, x) {      // piecewise-linear y on a control polyline
    for (let i = 0; i < pts.length - 1; i++) {
      if (x >= pts[i][0] && x <= pts[i + 1][0]) {
        const k = (x - pts[i][0]) / (pts[i + 1][0] - pts[i][0]);
        return pts[i][1] + (pts[i + 1][1] - pts[i][1]) * k;
      }
    }
    return pts[pts.length - 1][1];
  }

  // Eiffel Tower half-profile (metres; x from the axis, h = height above the base).
  const ew = (h) => 5 + 57.5 * Math.exp(-h / 88);       // outer edge half-width
  const ARCH_X = 37.5, ARCH_H = 50;
  const archX = (h) => ARCH_X * Math.sqrt(Math.max(0, 1 - Math.pow(h / ARCH_H, 2)));
  function eiffelOuter() {      // outer foot corner -> outer edge -> antenna tip
    const P = [[62.5, 0]];
    const edge = (h0, h1) => { const n = Math.max(2, Math.ceil((h1 - h0) / 5)); for (let i = 1; i <= n; i++) { const h = h0 + (h1 - h0) * i / n; P.push([ew(h), h]); } };
    edge(0, 56);
    P.push([40, 56], [40, 62], [ew(62), 62]);           // first platform
    edge(62, 115);
    P.push([25, 115], [25, 121], [ew(121), 121]);       // second platform
    edge(121, 274);
    P.push([10.5, 274], [10.5, 279], [ew(279), 279]);   // top platform
    edge(279, 297);
    P.push([4.2, 300], [2.4, 308], [1.4, 318], [0.7, 330], [0, 330]);  // lantern + antenna
    return P;
  }
  function eiffelArch() {       // outer foot corner -> inner foot -> decorative arch -> apex
    const P = [[62.5, 0]];
    for (let a = 0; a <= 90; a += 7.5) { const r = a * Math.PI / 180; P.push([ARCH_X * Math.cos(r), ARCH_H * Math.sin(r)]); }
    return P;
  }
  function eiffelLattice() {      // list of segments [[x,h],[x,h]] (both sides)
    const S = [];
    const mir = (a, b) => { S.push([a, b]); S.push([[-a[0], a[1]], [-b[0], b[1]]]); };
    // legs: one X per leg
    mir([62.5, 0], [archX(30), 30]);
    mir([ARCH_X, 0], [ew(30), 30]);
    // platform decks run across the whole tower
    S.push([[-40, 56], [40, 56]], [[-ew(62), 62], [ew(62), 62]]);
    S.push([[-25, 115], [25, 115]], [[-ew(121), 121], [ew(121), 121]]);
    // between first and second platform: open centre + one X per side
    mir([20, 62], [11, 115]);
    mir([ew(62), 62], [11, 115]);
    mir([20, 62], [ew(115), 115]);
    // upper shaft: stacked X braces
    const lv = [121, 158, 200, 240, 274];
    for (let i = 0; i < lv.length - 1; i++) {
      S.push([[ew(lv[i]), lv[i]], [-ew(lv[i + 1]), lv[i + 1]]]);
      S.push([[-ew(lv[i]), lv[i]], [ew(lv[i + 1]), lv[i + 1]]]);
      if (i > 0) S.push([[-ew(lv[i]), lv[i]], [ew(lv[i]), lv[i]]]);
    }
    return S;
  }

  function ensureStyle() {
    if (document.getElementById('dsx-style')) return;
    const s = document.createElement('style');
    s.id = 'dsx-style';
    s.textContent = `
      .dsx-root { position:absolute; left:0; top:0; width:1080px; height:1920px; }
      .dsx-root svg { position:absolute; left:0; top:0; overflow:visible; }
      body[data-mode="night"] .dsx-root {
        --dsx-sky2: color-mix(in srgb, var(--bg) 82%, var(--muted));
        --dsx-mtn: color-mix(in srgb, var(--bg) 62%, var(--surface-alt));
        --dsx-muted: var(--muted);
        --dsx-line: color-mix(in srgb, var(--muted) 72%, var(--border));
        --dsx-amber: var(--accent);
        --dsx-num: var(--accent);
        --dsx-halo: rgba(11,14,19,0.80);
        --dsx-glow: rgba(233,161,59,0.42);
        --dsx-house: var(--surface-alt);
        --dsx-cavity: var(--bg);
        --dsx-tex: var(--text);
        --dsx-cmp: color-mix(in srgb, var(--text) 78%, var(--muted));
        --dsx-fade: var(--bg);
        --g0: color-mix(in srgb, var(--border) 92%, var(--muted));
        --g1: color-mix(in srgb, var(--surface-alt) 55%, var(--border));
        --g2: color-mix(in srgb, var(--border) 62%, var(--surface-alt));
        --g3: var(--surface-alt);
        --g4: color-mix(in srgb, var(--surface-alt) 50%, var(--surface));
        --g5: color-mix(in srgb, var(--surface) 70%, var(--bg));
      }
      body[data-mode="day"] .dsx-root {
        --dsx-sky2: color-mix(in srgb, var(--bg) 86%, var(--muted));
        --dsx-mtn: color-mix(in srgb, var(--border) 85%, var(--muted));
        --dsx-muted: color-mix(in srgb, var(--muted) 72%, var(--text));
        --dsx-line: var(--muted);
        --dsx-amber: var(--accent-dim);
        --dsx-num: color-mix(in srgb, var(--accent-dim) 68%, var(--text));
        --dsx-halo: rgba(243,240,233,0.85);
        --dsx-glow: rgba(184,124,37,0.30);
        --dsx-house: var(--surface-alt);
        --dsx-cavity: var(--surface);
        --dsx-tex: var(--text);
        --dsx-cmp: var(--text);
        --dsx-fade: var(--border);
        --g0: color-mix(in srgb, var(--border) 75%, var(--surface-alt));
        --g1: var(--surface-alt);
        --g2: color-mix(in srgb, var(--surface-alt) 40%, var(--border));
        --g3: color-mix(in srgb, var(--surface-alt) 78%, var(--surface));
        --g4: color-mix(in srgb, var(--surface-alt) 80%, var(--border));
        --g5: color-mix(in srgb, var(--border) 90%, var(--muted));
      }
      body[data-mode="day"] .dsx-root .dsx-stars { display:none; }
      .dsx-fx { filter: drop-shadow(0 0 10px var(--dsx-glow)); }
      .dsx-tick { position:absolute; width:130px; height:50px; font:500 40px/50px 'Plex Arabic'; color:var(--dsx-muted);
                  text-align:right; white-space:nowrap; direction:rtl; }
      .dsx-tick.hi { color:var(--text); font-weight:600; }
      .dsx-label { position:absolute; white-space:nowrap; text-align:right; direction:rtl;
                   text-shadow: 0 0 22px var(--dsx-halo), 0 2px 8px var(--dsx-halo); }
      .dsx-label div { direction:rtl; text-align:right; }
      .dsx-l1 { font:700 84px/1.15 'Readex Pro'; color:var(--text); }
      .dsx-l2 { font:700 58px/1.25 'Readex Pro'; color:var(--text); }
      .dsx-acc { color:var(--dsx-num); }
      .dsx-q { position:absolute; width:200px; text-align:center; font:700 170px/1 'Readex Pro'; color:var(--dsx-muted);
               direction:rtl; text-shadow: 0 0 22px var(--dsx-halo); }
      .dsx-cmp { position:absolute; white-space:nowrap; font:600 46px/1.2 'Plex Arabic'; color:var(--dsx-cmp);
                 direction:rtl; text-align:left; text-shadow: 0 0 18px var(--dsx-halo); }
    `;
    document.head.appendChild(s);
  }

  function splitLabel(label) {
    if (!label) return null;
    const esc = (t) => t.replace(/&/g, '&amp;').replace(/</g, '&lt;');
    const hi = (t) => esc(t).replace(/([0-9٠-٩][0-9٠-٩.,٫٬]*)/g, '<span class="dsx-acc">$1</span>');
    let a, b;
    const forced = label.split(/\s*[|\n]\s*/);
    if (forced.length > 1) { a = forced[0]; b = forced.slice(1).join(' '); }
    else {
      const m = /^(\S*[0-9٠-٩]\S*\s+\S+)\s+(.+)$/.exec(label.trim());
      if (m) { a = m[1]; b = m[2]; } else { a = label; b = ''; }
    }
    return { l1: hi(a), l2: b ? hi(b) : '' };
  }

  window.GFX.depthSection = {
    create(el, L, H) {
      ensureStyle();
      const p = L.params || {};
      const uid = 'dsx' + (++UID);
      const S = {
        surfaceY: p.surfaceY ?? 560, depthPx: p.depthPx ?? 600, maxM: p.maxDepthM ?? 700,
        tickStep: p.tickStep ?? 100, x: p.x ?? 540,
        tIntro: p.tIntro === undefined ? [0, 0.5] : p.tIntro,
        tLine: p.tLine || [0.5, 3.0], lineEase: p.lineEase || 'kb', tLabel: p.tLabel ?? 3.0,
        label: p.label === undefined ? '٧٠٠ متر تحت الأرض' : p.label,
        question: !!p.question, tQuestion: p.tQuestion, compare: !!p.compare, tCompare: p.tCompare,
        towerM: p.towerM ?? 330, compareLabel: p.compareLabel ?? 'برجا إيفل = ٦٦٠ م',
        labelSize: p.labelSize ?? 84, label2Size: p.label2Size ?? 58, seed: p.seed ?? 7,
      };
      S.targetM = p.targetM ?? S.maxM;
      S.s = S.depthPx / S.maxM;                       // px per metre
      S.dotY = S.surfaceY + S.targetM * S.s;
      if (S.tQuestion == null) S.tQuestion = S.tLabel + 0.5;
      if (S.tCompare == null) S.tCompare = S.tLabel + 0.6;
      L._ds = S;
      const W = 1080, HH = 1920, sy = S.surfaceY, X = S.x;
      const R = rng(S.seed * 9973 + 17);

      const root = H.el('div', 'dsx-root', el);
      const mk = (cls) => { const s = H.svg('svg', { width: W, height: HH, viewBox: `0 0 ${W} ${HH}` }, root); if (cls) s.setAttribute('class', cls); return s; };

      // ===== background svg: sky, mountains, ground, texture =====
      const bg = mk();
      const defs = H.svg('defs', {}, bg);
      const sky = H.svg('linearGradient', { id: uid + 'sky', x1: 0, y1: 0, x2: 0, y2: 1, gradientUnits: 'userSpaceOnUse' }, defs);
      sky.setAttribute('y1', 0); sky.setAttribute('y2', sy);
      H.svg('stop', { offset: 0, style: 'stop-color:var(--bg)' }, sky);
      H.svg('stop', { offset: 0.55, style: 'stop-color:var(--bg)' }, sky);
      H.svg('stop', { offset: 1, style: 'stop-color:var(--dsx-sky2)' }, sky);
      const fade = H.svg('linearGradient', { id: uid + 'fade', x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
      H.svg('stop', { offset: 0, style: 'stop-color:var(--dsx-fade);stop-opacity:0' }, fade);
      H.svg('stop', { offset: 1, style: 'stop-color:var(--dsx-fade);stop-opacity:0.55' }, fade);
      H.svg('rect', { x: 0, y: 0, width: W, height: sy + 2, fill: `url(#${uid}sky)` }, bg);

      // stars (night only)
      const stars = H.svg('g', { class: 'dsx-stars' }, bg);
      for (let i = 0; i < 46; i++) {
        const sx = 20 + R() * 1040, syy = 30 + Math.pow(R(), 1.3) * (sy - 230);
        H.svg('circle', { cx: f1(sx), cy: f1(syy), r: f1(0.8 + R() * 1.3), style: `fill:var(--text);opacity:${(0.12 + R() * 0.38).toFixed(2)}` }, stars);
      }
      // distant ridge
      const mpts = [];
      for (let x = -40, i = 0; x <= 1120; x += 46 + R() * 40, i++) {
        const big = Math.sin(x / 190 + 1.3) * 0.5 + 0.5;
        mpts.push([x, sy - (14 + big * 70 + R() * 26)]);
      }
      H.svg('path', { d: 'M-40,' + (sy + 2) + 'L' + mpts.map(q => f1(q[0]) + ',' + f1(q[1])).join('L') + `L1120,${sy + 2}Z`, style: 'fill:var(--dsx-mtn);opacity:0.7' }, bg);

      // strata: band tops as fractions of depthPx below the surface
      const tops = [0, 0.115, 0.31, 0.545, 0.785, 1.17];
      const edges = [];
      tops.forEach((fr, i) => {
        const base = sy + fr * S.depthPx;
        const pts = [];
        const amp = i === 0 ? 0 : 7 + R() * 7, ph = R() * 6.28, fq = 1 / (160 + R() * 120);
        for (let x = -60; x <= 1140; x += 60) {
          pts.push([x, base + (i === 0 ? 0 : Math.sin(x * fq + ph) * amp * 0.8 + (R() - 0.5) * amp * 1.2)]);
        }
        edges.push(pts);
        const d = 'M' + f1(pts[0][0]) + ',' + f1(pts[0][1]) + crPath(pts) + `L1140,${HH + 20}L-60,${HH + 20}Z`;
        H.svg('path', { d, style: `fill:var(--g${i})` }, bg);
      });
      // texture: specks (3 opacity buckets), pebbles, broken lamination lines
      const specks = [[], [], []];
      for (let i = 0; i < 1500; i++) {
        const x = R() * W, y = sy + 6 + R() * (HH - sy);
        const r = 0.7 + Math.pow(R(), 2) * 1.8;
        specks[Math.floor(R() * 3)].push(`M${f1(x - r)},${f1(y)}a${f1(r)},${f1(r)} 0 1,0 ${f1(2 * r)},0a${f1(r)},${f1(r)} 0 1,0 ${f1(-2 * r)},0`);
      }
      [0.07, 0.11, 0.16].forEach((o, k) => H.svg('path', { d: specks[k].join(''), style: `fill:var(--dsx-tex);opacity:${o}` }, bg));
      let pd = '';
      for (let i = 0; i < 110; i++) {
        const cx = R() * W, cy = sy + 14 + R() * (HH - sy), rr = 3 + Math.pow(R(), 1.6) * 9, n = 5 + Math.floor(R() * 3), rot = R() * 6.28;
        const pts = [];
        for (let k = 0; k < n; k++) { const a = rot + k / n * 6.283, q = rr * (0.7 + R() * 0.45); pts.push([cx + Math.cos(a) * q, cy + Math.sin(a) * q * 0.72]); }
        pd += polyD(pts, true);
      }
      H.svg('path', { d: pd, style: 'fill:var(--dsx-tex);fill-opacity:0.035;stroke:var(--dsx-tex);stroke-opacity:0.10;stroke-width:1.2;stroke-linejoin:round' }, bg);
      let ld = '';
      for (let i = 1; i < edges.length; i++) {
        const next = i + 1 < edges.length ? edges[i + 1] : null;
        for (let k = 0; k < 3; k++) {
          const off = 14 + R() * 60 + k * 22;
          const pts = edges[i].map(q => [q[0], q[1] + off + (R() - 0.5) * 4]);
          if (next && pts.some((q, j) => q[1] > next[j][1] - 8)) continue;
          ld += 'M' + f1(pts[0][0]) + ',' + f1(pts[0][1]) + crPath(pts);
        }
      }
      H.svg('path', { d: ld, style: 'fill:none;stroke:var(--dsx-tex);stroke-opacity:0.06;stroke-width:1.5;stroke-dasharray:90 26 40 18 140 30' }, bg);
      H.svg('rect', { x: 0, y: Math.max(sy, S.dotY + 60), width: W, height: HH - Math.max(sy, S.dotY + 60), fill: `url(#${uid}fade)` }, bg);
      // surface line
      H.svg('line', { x1: 0, y1: sy, x2: W, y2: sy, style: 'stroke:var(--dsx-line);stroke-width:2.5' }, bg);

      // ===== mid svg: cavity, towers, ruler, headframe =====
      const mid = mk();
      const cg = H.svg('radialGradient', { id: uid + 'cav' }, H.svg('defs', {}, mid));
      H.svg('stop', { offset: 0, style: 'stop-color:var(--dsx-cavity);stop-opacity:0.95' }, cg);
      H.svg('stop', { offset: 0.6, style: 'stop-color:var(--dsx-cavity);stop-opacity:0.7' }, cg);
      H.svg('stop', { offset: 1, style: 'stop-color:var(--dsx-cavity);stop-opacity:0' }, cg);
      S.cavity = H.svg('ellipse', { cx: X, cy: S.dotY + 4, rx: 70, ry: 30, fill: `url(#${uid}cav)` }, mid);

      // towers (upside down, stacked)
      S.towers = [];
      if (S.compare) {
        const outer = eiffelOuter(), arch = eiffelArch(), lat = eiffelLattice(), ts = S.s, tp = S.towerM * ts;
        const half = arch.slice().reverse().concat(outer.slice(1));   // apex -> arch -> foot -> edge -> tip
        const cx = X + 24 + 62.5 * ts;
        S.towerCx = cx;
        for (let k = 0; k < 2; k++) {
          const y0 = sy + k * tp;
          const P = (q) => [cx + q[0] * ts * (S.towerM / 330), y0 + q[1] * ts * (S.towerM / 330)];
          const right = half.map(P), left = half.map(q => P([-q[0], q[1]]));
          const g = H.svg('g', {}, mid);
          const full = right.concat(left.slice().reverse());
          const st = 'fill:none;stroke:var(--muted);stroke-width:2.5;stroke-linecap:round;stroke-linejoin:round';
          const fill = H.svg('path', { d: polyD(full, true), style: 'fill:var(--muted);opacity:0' }, g);
          const latD = lat.map(sg => { const a = P(sg[0]), b = P(sg[1]); return `M${f1(a[0])},${f1(a[1])}L${f1(b[0])},${f1(b[1])}`; }).join('');
          const latP = H.svg('path', { d: latD, style: 'fill:none;stroke:var(--muted);stroke-width:1.6;stroke-linecap:round;opacity:0' }, g);
          const strokes = [
            { p: H.svg('path', { d: polyD(outer.map(P)), style: st }, g), w: [0, 1] },
            { p: H.svg('path', { d: polyD(outer.map(q => P([-q[0], q[1]]))), style: st }, g), w: [0, 1] },
            { p: H.svg('path', { d: polyD(arch.map(P)), style: st }, g), w: [0, 0.5] },
            { p: H.svg('path', { d: polyD(arch.map(q => P([-q[0], q[1]]))), style: st }, g), w: [0, 0.5] },
          ];
          S.towers.push({ fill, latP, strokes, ready: false });
        }
        S.tipY = sy + 2 * tp;
      }

      // ruler
      const ax = 196;
      S.ax = ax;
      S.axis = H.svg('line', { x1: ax, y1: sy, x2: ax, y2: sy + S.depthPx, style: 'stroke:var(--dsx-line);stroke-width:2.5;stroke-linecap:round' }, mid);
      S.ticks = [];
      const nT = Math.floor(S.maxM / S.tickStep + 1e-6);
      for (let k = 0; k <= nT * 2; k++) {
        const m = k * S.tickStep / 2, y = sy + m * S.s, major = k % 2 === 0;
        const ln = H.svg('line', { x1: ax, y1: f1(y), x2: ax + (major ? 20 : 10), y2: f1(y), style: `stroke:var(--dsx-line);stroke-width:${major ? 2.5 : 2};stroke-linecap:round` }, mid);
        S.ticks.push({ ln, m, y, major });
      }

      // headframe (line art standing on the surface at X)
      const hf = H.svg('g', { transform: `translate(${X},${sy}) scale(-1,1)`, style: 'fill:none;stroke:var(--dsx-line);stroke-width:3;stroke-linecap:round;stroke-linejoin:round' }, mid);
      S.hf = hf;
      const legX = (side, y) => side * (34 - 19 * (-y / 150));
      H.svg('path', { d: 'M106,0V-38L150,-54L194,-38V0Z', style: 'fill:var(--dsx-house)' }, hf);
      H.svg('path', { d: 'M126,0V-20H140V0', style: 'stroke-width:2.5' }, hf);
      H.svg('path', { d: 'M-34,0L-15,-150M34,0L15,-150', style: '' }, hf);
      let br = '';
      const lv = [0, -50, -100, -150];
      for (let i = 0; i < lv.length; i++) {
        if (i > 0) br += `M${f1(legX(-1, lv[i]))},${lv[i]}H${f1(legX(1, lv[i]))}`;
        if (i < lv.length - 1) br += `M${f1(legX(-1, lv[i]))},${lv[i]}L${f1(legX(1, lv[i + 1]))},${lv[i + 1]}M${f1(legX(1, lv[i]))},${lv[i]}L${f1(legX(-1, lv[i + 1]))},${lv[i + 1]}`;
      }
      H.svg('path', { d: br, style: 'stroke-width:1.8' }, hf);
      H.svg('path', { d: 'M14,-146L96,0M24.5,-75L54,-75M30,-28L80,-28', style: 'stroke-width:2.6' }, hf);
      H.svg('path', { d: 'M-26,-150H26', style: 'stroke-width:3.5' }, hf);
      H.svg('circle', { cx: 0, cy: -171, r: 17, style: 'fill:var(--bg)' }, hf);
      H.svg('circle', { cx: 0, cy: -171, r: 3, style: 'fill:var(--dsx-line)' }, hf);
      H.svg('path', { d: 'M0,-185V-157M-12,-171H12', style: 'stroke-width:1.6' }, hf);
      H.svg('path', { d: 'M0,-150V-154', style: 'stroke-width:3' }, hf);
      H.svg('path', { d: 'M15,-176L106,-30', style: 'stroke-width:1.4;opacity:0.7' }, hf);

      // guide (ruler -> head) + marker
      S.guide = H.svg('line', { x1: ax + 24, x2: X - 18, y1: sy, y2: sy, style: 'stroke:var(--dsx-muted);stroke-width:2;stroke-dasharray:2 9;stroke-linecap:round;opacity:0' }, mid);

      // ===== fx svg: dashed amber line, head, dot, ring =====
      const fx = mk('dsx-fx');
      const fdefs = H.svg('defs', {}, fx);
      const rg = H.svg('radialGradient', { id: uid + 'glow' }, fdefs);
      H.svg('stop', { offset: 0, style: 'stop-color:var(--dsx-amber);stop-opacity:0.65' }, rg);
      H.svg('stop', { offset: 1, style: 'stop-color:var(--dsx-amber);stop-opacity:0' }, rg);
      S.line = H.svg('line', { x1: X, y1: sy + 3, x2: X, y2: sy + 3, style: 'stroke:var(--dsx-amber);stroke-width:4;stroke-dasharray:12 13;stroke-linecap:round' }, fx);
      S.head = H.svg('g', { style: 'opacity:0' }, fx);
      H.svg('circle', { cx: 0, cy: 0, r: 26, fill: `url(#${uid}glow)` }, S.head);
      H.svg('circle', { cx: 0, cy: 0, r: 6.5, style: 'fill:var(--dsx-amber)' }, S.head);
      S.marker = H.svg('circle', { cx: ax, cy: sy, r: 6.5, style: 'fill:var(--dsx-amber);opacity:0' }, fx);
      S.ring = H.svg('circle', { cx: X, cy: S.dotY, r: 12, style: 'fill:none;stroke:var(--dsx-amber);stroke-width:2.5;opacity:0' }, fx);
      S.dot = H.svg('g', { style: 'opacity:0' }, fx);
      H.svg('circle', { cx: 0, cy: 0, r: 30, fill: `url(#${uid}glow)` }, S.dot);
      H.svg('circle', { cx: 0, cy: 0, r: 12, style: 'fill:var(--dsx-amber)' }, S.dot);

      // ===== HTML text =====
      S.tickLabels = [];
      for (const t of S.ticks) {
        if (!t.major || t.m === 0) continue;
        const txt = H.arNum(Math.round(t.m)) + ' م';
        const d = H.el('div', 'dsx-tick', root, { left: (ax - 14 - 130) + 'px', top: (t.y - 27) + 'px' });
        d.textContent = txt;
        let hi = null;
        if (Math.abs(t.m - S.targetM) < 1e-6) { hi = H.el('div', 'dsx-tick hi', root, { left: (ax - 14 - 130) + 'px', top: (t.y - 27) + 'px', opacity: 0 }); hi.textContent = txt; }
        S.tickLabels.push({ d, hi, y: t.y });
      }

      const lab = splitLabel(S.label);
      if (lab) {
        const box = H.el('div', 'dsx-label', root);
        const a = H.el('div', 'dsx-l1', box, { fontSize: S.labelSize + 'px' }); a.innerHTML = lab.l1;
        let h = S.labelSize * 1.15;
        if (lab.l2) { const b = H.el('div', 'dsx-l2', box, { fontSize: S.label2Size + 'px' }); b.innerHTML = lab.l2; h += S.label2Size * 1.25; }
        // beside the dot (right side); with towers, clear the lower spire
        let lx = X + 46;
        if (S.compare) lx = Math.max(lx, S.towerCx + 38);
        let top = S.dotY - h / 2 - 8;
        top = Math.min(top, 1228 - h);
        Object.assign(box.style, { left: lx + 'px', top: top + 'px' });
        S.labelEl = box;
      }
      if (S.question) {
        S.qEl = H.el('div', 'dsx-q', root, { left: (X - 118 - 100) + 'px', top: (S.dotY - 170) + 'px' });
        S.qEl.textContent = '؟';
      }
      if (S.compare && S.compareLabel) {
        const tp = S.towerM * S.s;
        const yl = sy + 0.74 * tp;                         // beside the slender upper shaft of tower 1
        const hm = (yl - sy) / S.s * (330 / S.towerM);
        const lx = S.towerCx + ew(hm) * S.s * (S.towerM / 330) + 28;
        S.cmpEl = H.el('div', 'dsx-cmp', root, { left: lx + 'px', top: (yl - 28) + 'px' });
        S.cmpEl.innerHTML = S.compareLabel.replace(/([0-9٠-٩]+)/g, '<span style="font-weight:700">$1</span>');
      }
    },

    draw(el, u, L, H) {
      const S = L._ds; if (!S) return;
      const sy = S.surfaceY;
      // intro: ruler + headframe
      const iv = S.tIntro ? H.seg(u, S.tIntro[0], S.tIntro[1]) : 1;
      const i0 = S.tIntro ? S.tIntro[0] : 0, i1 = S.tIntro ? S.tIntro[1] : 0;
      const axv = H.ez('standard', iv);
      S.axis.setAttribute('y2', H.lerp(sy, sy + S.depthPx, axv).toFixed(1));
      for (const t of S.ticks) {
        const on = S.tIntro ? H.ez('standard', H.seg(u, i0 + (t.y - sy) / S.depthPx * (i1 - i0) * 0.8, i0 + (t.y - sy) / S.depthPx * (i1 - i0) * 0.8 + 0.2)) : 1;
        t.ln.style.opacity = on;
      }
      S.tickLabels.forEach((t, k) => {
        const a = S.tIntro ? i0 + (t.y - sy) / S.depthPx * (i1 - i0) * 0.8 : -1;
        const v = S.tIntro ? H.seg(u, a, a + 0.25) : 1;
        t.d.style.opacity = H.ez('standard', v);
        t.d.style.transform = `translateY(${((1 - H.ez('snap', v)) * 12).toFixed(1)}px)`;
      });
      S.hf.style.opacity = H.ez('standard', iv);

      // descent
      const [l0, l1] = S.tLine;
      const lv = H.ez(S.lineEase, H.seg(u, l0, l1));
      const y = H.lerp(sy + 3, S.dotY, lv);
      const started = u >= l0;
      S.line.setAttribute('y2', (started ? y : sy + 3).toFixed(1));
      S.line.style.opacity = started ? 1 : 0;
      const headOn = H.ez('standard', H.seg(u, l0, l0 + 0.15)) * (1 - H.ez('standard', H.seg(u, l1 - 0.05, l1 + 0.3)));
      S.head.setAttribute('transform', `translate(${S.x},${y.toFixed(1)})`);
      S.head.style.opacity = headOn;
      const gOn = H.ez('standard', H.seg(u, l0, l0 + 0.25));
      S.guide.setAttribute('y1', y.toFixed(1)); S.guide.setAttribute('y2', y.toFixed(1));
      S.guide.style.opacity = gOn * H.lerp(0.65, 0.4, H.ez('standard', H.seg(u, l1, l1 + 0.5)));
      S.marker.setAttribute('cy', y.toFixed(1));
      S.marker.style.opacity = gOn;
      for (const t of S.tickLabels) if (t.hi) t.hi.style.opacity = H.ez('standard', H.seg(u, l1 - 0.1, l1 + 0.3));

      // arrival: cavity, dot, ring
      S.cavity.style.opacity = H.ez('standard', H.seg(u, l1 - 0.3, l1 + 0.3));
      const dv = H.seg(u, l1 - 0.06, l1 + 0.24);
      const dsc = H.lerp(0.4, 1, H.ez('snap', dv));
      S.dot.setAttribute('transform', `translate(${S.x},${S.dotY}) scale(${dsc.toFixed(3)})`);
      S.dot.style.opacity = H.clamp(dv * 3, 0, 1);
      if (u >= l1) {
        const P = 1.8, ph = ((u - l1) % P) / P;
        const e = H.ez('inout', ph);
        S.ring.setAttribute('r', H.lerp(13, 46, e).toFixed(1));
        S.ring.style.opacity = (0.6 * (1 - e)).toFixed(3);
      } else S.ring.style.opacity = 0;

      // label
      if (S.labelEl) {
        const v = H.seg(u, S.tLabel, S.tLabel + 0.25);
        S.labelEl.style.opacity = H.clamp(v * 2, 0, 1);
        S.labelEl.style.transform = `translateY(${((1 - H.ez('snap', v)) * 24).toFixed(1)}px)`;
      }
      // question mark
      if (S.qEl) {
        const tq = S.tQuestion, v = H.seg(u, tq, tq + 0.25);
        let pv = 0;
        if (u > tq + 0.25) { const ph = ((u - tq - 0.25) % 1.7) / 1.7; pv = H.ez('inout', ph < 0.5 ? ph * 2 : 2 - ph * 2); }
        S.qEl.style.opacity = (H.clamp(v * 2, 0, 1) * (0.8 + 0.2 * pv)).toFixed(3);
        S.qEl.style.transform = `translateY(${((1 - H.ez('snap', v)) * 24).toFixed(1)}px) scale(${(1 + 0.06 * pv).toFixed(4)})`;
      }
      // towers
      if (S.towers.length) {
        S.towers.forEach((T, k) => {
          if (!T.ready) { T.strokes.forEach(o => { o.len = window.GFXU.prepDash(o.p); }); T.ready = true; }
          const a = S.tCompare + k * 0.65;
          T.strokes.forEach(o => {
            const v = H.ez('standard', H.seg(u, a + o.w[0] * 0.8, a + o.w[1] * 0.8));
            window.GFXU.dash(o.p, o.len, v);
            o.p.style.opacity = u > a ? 1 : 0;
          });
          T.fill.style.opacity = (0.4 * H.ez('standard', H.seg(u, a + 0.55, a + 1.0))).toFixed(3);
          T.latP.style.opacity = (0.9 * H.ez('standard', H.seg(u, a + 0.5, a + 0.95))).toFixed(3);
        });
        if (S.cmpEl) {
          const tc = S.tCompare + 1.4, v = H.seg(u, tc, tc + 0.25);
          S.cmpEl.style.opacity = H.clamp(v * 2, 0, 1);
          S.cmpEl.style.transform = `translateY(${((1 - H.ez('snap', v)) * 24).toFixed(1)}px)`;
        }
      }
    },
  };
})();
