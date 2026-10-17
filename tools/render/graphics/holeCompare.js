// holeCompare — the escape shaft (Fénix capsule hole) next to a standing man, drawn to scale.
// A tall vertical shaft through layered rock (two wall masses that slide in from the sides),
// a front-view human silhouette inside it, then dimension lines: shaft width (amber) and the
// man's height (muted).
//
// params (all optional):
//   tWalls 0.2          walls slide in from the sides ('snap', 0.55 s); interior + surface glow follow
//   tPerson 0.8         silhouette fades in and rises 24 px ('snap')
//   tDims 1.4           horizontal shaft dimension (arrows run from the centre to the walls), value + label rise,
//                       then the man's height dimension (+0.55 s)
//   tOut null           optional: everything fades out ('exit', 0.3 s)
//   shaftLabel 'قطر الممر', shaftValue '٧١ سم', personValue '١٧٥ سم'
//   shaftCm 71, personCm 175, pxPerCm 3.9      geometry (shaft 277 px wide, man 683 px tall)
//   cx 540, floorY 1158 (soles), dimY 362 (shaft dimension line)
//   glow true           warm surface light at the top of the shaft
//   seed 11             rock texture randomness
// Everything in draw() is a pure function of u.
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
  function valueNoise(r) {             // 1D smooth value noise in [-1,1], lattice spacing 1
    const N = 256, v = [];
    for (let i = 0; i < N; i++) v.push(r() * 2 - 1);
    return (x) => {
      const i = Math.floor(x), f = x - i, s = f * f * (3 - 2 * f);
      const a = v[((i % N) + N) % N], b = v[(((i + 1) % N) + N) % N];
      return a + (b - a) * s;
    };
  }
  function fbm(r, oct) {
    const ns = []; for (let k = 0; k < oct; k++) ns.push(valueNoise(r));
    let norm = 0; for (let k = 0; k < oct; k++) norm += 1 / (1 << k);
    return (x) => { let s = 0; for (let k = 0; k < oct; k++) s += ns[k](x * (1 << k) + k * 17.3) / (1 << k); return s / norm; };
  }
  const f1 = (v) => (+v).toFixed(1);
  const polyD = (pts, close) => 'M' + pts.map(p => f1(p[0]) + ',' + f1(p[1])).join('L') + (close ? 'Z' : '');
  const smooth01 = (x) => { x = Math.max(0, Math.min(1, x)); return x * x * (3 - 2 * x); };
  // Closed Catmull-Rom path; points flagged [x, y, 1] are corners (no tangent smoothing through them).
  function smoothClosed(pts) {
    const n = pts.length;
    let d = 'M' + f1(pts[0][0]) + ',' + f1(pts[0][1]);
    for (let i = 0; i < n; i++) {
      const p0 = pts[(i - 1 + n) % n], p1 = pts[i], p2 = pts[(i + 1) % n], p3 = pts[(i + 2) % n];
      const c1 = p1[2] ? [p1[0], p1[1]] : [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6];
      const c2 = p2[2] ? [p2[0], p2[1]] : [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
      d += `C${f1(c1[0])},${f1(c1[1])} ${f1(c2[0])},${f1(c2[1])} ${f1(p2[0])},${f1(p2[1])}`;
    }
    return d + 'Z';
  }
  // right half (x >= 0, top -> bottom) mirrored into a full closed outline
  function mirrorHalf(R, apex) {
    const L = R.slice().reverse().map(p => [-p[0], p[1], p[2]]);
    const out = R.slice();
    if (apex) out.push(apex);
    return out.concat(apex || R[R.length - 1][0] !== 0 ? L : L.slice(1, L.length - 1));
  }

  // ---------- human figure, front view, centimetres (x from the body axis, y above the floor), 175 cm man ----------
  const HEAD_R = [
    [0, 175], [3.7, 174.5], [6.2, 172.7], [7.5, 169.6], [7.8, 165.8], [7.6, 162.8],
    [8.15, 162.2], [8.55, 160.2], [8.3, 157.4], [7.3, 156.8],                 // ear
    [6.8, 155.4], [5.8, 153.6], [3.6, 152.0], [0, 151.4],                     // jaw, chin
  ];
  const BODY_R = [
    [5.2, 155.0], [5.25, 151.4], [5.9, 149.3],                                // neck
    [9.4, 147.3], [13.4, 145.8], [17.0, 144.3], [19.8, 142.5], [20.8, 139.6], // trapezius, shoulder
    [20.2, 135.0], [17.6, 130.6], [15.6, 126.6],                              // under the arm
    [15.2, 120], [14.4, 112], [13.8, 105], [14.3, 99], [15.8, 93],            // chest, waist
    [16.9, 88], [17.2, 83], [16.7, 76], [15.7, 68], [14.3, 59],               // hip, thigh
    [12.9, 52], [12.5, 47], [12.8, 41], [13.4, 35], [12.7, 27], [11.3, 18],   // knee, calf
    [10.6, 12.5], [10.9, 8.6], [11.6, 5.6], [12.5, 3.2], [13.0, 1.3],               // ankle, foot
    [12.9, 0, 1], [4.4, 0, 1], [4.2, 1.1], [4.5, 3.2],                                // sole
    [4.9, 6.0], [5.2, 9.5], [5.1, 12.5], [4.3, 22], [3.2, 30], [3.5, 38],             // inner ankle, calf
    [4.0, 44], [3.6, 50], [3.0, 56], [2.0, 66], [1.1, 75], [0.45, 80.4],      // inner knee, thigh
  ];
  const ARM_R = [
    [15.0, 144.8], [18.5, 144.1], [21.3, 142.1], [22.7, 138.9], [23.0, 135.0],  // deltoid (bideltoid 46 cm)
    [22.6, 129.0], [22.2, 121.0], [22.0, 113.0], [21.9, 108.0],                 // upper arm, elbow
    [22.3, 102.0], [22.2, 96.0], [21.6, 89.0], [21.0, 84.6],                    // forearm, wrist
    [21.3, 80.6], [21.4, 75.6], [20.9, 70.4], [20.0, 66.7], [18.8, 65.3],       // hand, fingertips
    [17.5, 65.7], [16.5, 68.0], [15.9, 71.5], [15.8, 76.0], [16.3, 80.2],       // fingers, thumb
    [17.0, 84.6], [17.4, 90.0], [17.6, 97.0], [17.4, 103.0], [17.0, 108.0],     // inner forearm, elbow
    [17.1, 114.0], [17.2, 120.0], [16.9, 125.6], [16.2, 129.0],                 // inner upper arm, armpit
    [14.5, 132.0], [13.5, 138.0],
  ];

  function ensureStyle() {
    if (document.getElementById('hcx-style')) return;
    const s = document.createElement('style');
    s.id = 'hcx-style';
    s.textContent = `
      .hcx-root { position:absolute; left:0; top:0; width:1080px; height:1920px; }
      .hcx-root svg { position:absolute; left:0; top:0; overflow:visible; }
      body[data-mode="night"] .hcx-root {
        --hc-r0: var(--surface-alt);
        --hc-r1: color-mix(in srgb, var(--surface-alt) 62%, var(--surface));
        --hc-r2: color-mix(in srgb, var(--surface-alt) 70%, var(--border));
        --hc-r3: color-mix(in srgb, var(--surface-alt) 45%, var(--surface));
        --hc-line: var(--border);
        --hc-peb: color-mix(in srgb, var(--border) 75%, var(--muted));
        --hc-peb2: color-mix(in srgb, var(--surface) 70%, var(--bg));
        --hc-rim: color-mix(in srgb, var(--border) 45%, var(--muted));
        --hc-int: color-mix(in srgb, var(--bg) 80%, #000);
        --hc-person: color-mix(in srgb, var(--muted) 70%, var(--hc-int));
        --hc-amber: var(--accent);
        --hc-amber-line: var(--accent);
        --hc-glow: var(--accent);
        --hc-glow-op: 0.22;
        --hc-amber-glow: rgba(233,161,59,0.40);
        --hc-muted: var(--muted);
        --hc-halo: rgba(8,10,14,0.85);
        --hc-shadow: rgba(0,0,0,0.65);
        --hc-fade: var(--bg);
        --hc-tex-op: 1;
      }
      body[data-mode="day"] .hcx-root {
        --hc-r0: var(--surface-alt);
        --hc-r1: color-mix(in srgb, var(--surface-alt) 86%, var(--surface));
        --hc-r2: color-mix(in srgb, var(--surface-alt) 68%, var(--border));
        --hc-r3: color-mix(in srgb, var(--surface-alt) 86%, var(--border));
        --hc-line: color-mix(in srgb, var(--border) 78%, var(--muted));
        --hc-peb: color-mix(in srgb, var(--border) 60%, var(--muted));
        --hc-peb2: color-mix(in srgb, var(--surface) 55%, var(--surface-alt));
        --hc-rim: color-mix(in srgb, var(--border) 45%, var(--muted));
        --hc-int: color-mix(in srgb, var(--border) 92%, var(--muted));
        --hc-person: color-mix(in srgb, var(--muted) 70%, var(--hc-int));
        --hc-amber: color-mix(in srgb, var(--accent-dim) 55%, var(--text));
        --hc-amber-line: color-mix(in srgb, var(--accent-dim) 78%, var(--text));
        --hc-glow: color-mix(in srgb, var(--accent) 22%, var(--surface));
        --hc-glow-op: 0.75;
        --hc-amber-glow: rgba(184,124,37,0.22);
        --hc-muted: color-mix(in srgb, var(--muted) 78%, var(--text));
        --hc-halo: rgba(236,232,224,0.92);
        --hc-shadow: rgba(70,58,38,0.26);
        --hc-fade: var(--bg);
        --hc-tex-op: 0.6;
      }
      .hcx-tex { opacity: var(--hc-tex-op); }
      .hcx-wall { filter: drop-shadow(0 0 22px var(--hc-shadow)); }
      .hcx-amber { filter: drop-shadow(0 0 10px var(--hc-amber-glow)); }
      .hcx-txt { position:absolute; white-space:nowrap; direction:rtl;
                 text-shadow: 0 0 20px var(--hc-halo), 0 0 6px var(--hc-halo), 0 2px 4px var(--hc-halo); }
      .hcx-label { font:600 50px/64px 'Plex Arabic'; color:var(--text); text-align:center; }
      .hcx-value { font:700 96px/104px 'Readex Pro'; color:var(--hc-amber); text-align:center; }
      .hcx-value .hcx-unit { font-size:56px; margin-inline-start:14px; }
      .hcx-pv { font:600 44px/58px 'Plex Arabic'; color:var(--hc-muted); text-align:right; }
    `;
    document.head.appendChild(s);
  }

  window.GFX.holeCompare = {
    create(el, L, H) {
      ensureStyle();
      const P = L.params || {};
      const p = {
        tWalls: P.tWalls ?? 0.2, tPerson: P.tPerson ?? 0.8, tDims: P.tDims ?? 1.4, tOut: P.tOut ?? null,
        shaftLabel: P.shaftLabel ?? 'قطر الممر', shaftValue: P.shaftValue ?? '٧١ سم', personValue: P.personValue ?? '١٧٥ سم',
        shaftCm: P.shaftCm ?? 71, personCm: P.personCm ?? 175, s: P.pxPerCm ?? 3.9,
        cx: P.cx ?? 540, floorY: P.floorY ?? 1158, dimY: P.dimY ?? 362, glow: P.glow ?? true, seed: P.seed ?? 11,
      };
      const uid = ++UID, id = (k) => `hcx${uid}-${k}`;
      const S = { p };
      L._hc = S;
      const r = rng(p.seed * 7919 + 13);
      const cx = p.cx, s = p.s, floorY = p.floorY, dimY = p.dimY;
      const half = p.shaftCm * s / 2;
      const k = s * p.personCm / 175;                  // px per figure-centimetre
      const headTop = floorY - p.personCm * s;
      const floorTop = floorY + 1;                      // rock floor surface (soles rest on it)
      const CR = 34;                                    // rounded bottom corners of the bore

      const root = H.el('div', 'hcx-root', el);
      S.root = root;
      const svg = H.svg('svg', { width: 1080, height: 1920, viewBox: '0 0 1080 1920' }, root);
      const defs = H.svg('defs', {}, svg);

      // ---------- gradients ----------
      const gV = H.svg('linearGradient', { id: id('glowV'), x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
      H.svg('stop', { offset: 0, style: 'stop-color:var(--hc-glow);stop-opacity:var(--hc-glow-op)' }, gV);
      H.svg('stop', { offset: 0.3, style: 'stop-color:var(--hc-glow);stop-opacity:calc(var(--hc-glow-op) * 0.4)' }, gV);
      H.svg('stop', { offset: 0.65, style: 'stop-color:var(--hc-glow);stop-opacity:calc(var(--hc-glow-op) * 0.1)' }, gV);
      H.svg('stop', { offset: 1, style: 'stop-color:var(--hc-glow);stop-opacity:0' }, gV);
      const gRim = H.svg('linearGradient', { id: id('rim'), gradientUnits: 'userSpaceOnUse', x1: 0, y1: -40, x2: 0, y2: 640 }, defs);
      H.svg('stop', { offset: 0, style: 'stop-color:var(--accent);stop-opacity:0.8' }, gRim);
      H.svg('stop', { offset: 0.4, style: 'stop-color:var(--accent);stop-opacity:0.22' }, gRim);
      H.svg('stop', { offset: 1, style: 'stop-color:var(--accent);stop-opacity:0' }, gRim);
      const gFade = H.svg('linearGradient', { id: id('fade'), x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
      H.svg('stop', { offset: 0, style: 'stop-color:var(--hc-fade);stop-opacity:0' }, gFade);
      H.svg('stop', { offset: 1, style: 'stop-color:var(--hc-fade);stop-opacity:0.6' }, gFade);

      // ---------- rock walls geometry ----------
      function wallEdge(side, seed) {               // side -1 = left wall, +1 = right wall
        const rr = rng(seed), big = fbm(rr, 3), fine = valueNoise(rr);
        const nom = cx + side * half;
        const pts = [];
        let y = -70;
        const yEnd = floorTop - CR;
        while (y < yEnd) {
          const m = smooth01((Math.abs(y - dimY) - 6) / 90);       // calm at the dimension line
          const n = (6.5 * big(y / 105) + 2.4 * fine(y / 19)) * m;
          pts.push([nom + n, y]);
          y += 9 + rr() * 13;
        }
        // rounded bottom corner of the bore, then the floor towards the centre
        const ex = nom, ey = yEnd;
        for (let i = 0; i <= 8; i++) {
          const a = (i / 8) * Math.PI / 2;
          const jitter = (i > 0 && i < 8) ? (rr() - 0.5) * 3 : 0;
          pts.push([ex - side * CR * (1 - Math.cos(a)) - side * jitter * 0.5, ey + CR * Math.sin(a) + jitter]);
        }
        const x0 = ex - side * CR;
        const fl = valueNoise(rr);
        for (let x = x0; side < 0 ? x < cx : x > cx; x -= side * (10 + rr() * 10)) {
          const d = Math.abs(x - cx);
          const amp = smooth01((d - 70) / 60) * 4.5;
          pts.push([x, floorTop + Math.abs(fl(x / 26)) * amp]);
        }
        pts.push([cx - side * 1.5, floorTop]);
        return pts;
      }
      const edgeL = wallEdge(-1, p.seed * 31 + 1), edgeR = wallEdge(1, p.seed * 31 + 2);
      const edgeXAt = (edge, y) => { for (let i = 1; i < edge.length; i++) if (edge[i][1] >= y) { const a = edge[i - 1], b = edge[i]; return a[0] + (b[0] - a[0]) * (y - a[1]) / Math.max(1e-6, b[1] - a[1]); } return edge[edge.length - 1][0]; };
      // the left mass also runs under the right one below the floor, so no gap opens there while they slide in
      const polyL = [[-90, -70]].concat(edgeL, [[cx + 1.5, floorTop + 7], [1170, floorTop + 7], [1170, 1995], [-90, 1995]]);
      const polyR = [[1170, -70]].concat(edgeR, [[cx - 1.5, 1995], [1170, 1995]]);

      // strata boundaries (global coordinates, continuous across the shaft, gently dipping)
      const strata = [];
      {
        let y = -110;
        while (y < 2050) {
          const nz = fbm(r, 2), amp = 4 + r() * 6, slope = -0.045 + (r() - 0.5) * 0.02;
          const line = [];
          for (let x = -100; x <= 1180; x += 24) line.push([x, y + slope * (x - cx) + amp * nz(x / 140)]);
          strata.push(line);
          y += 64 + r() * 120;
        }
      }
      const TONES = ['--hc-r0', '--hc-r1', '--hc-r2', '--hc-r3'];
      const bands = [];
      let lastTone = -1;
      for (let i = 0; i < strata.length - 1; i++) {
        let t = Math.floor(r() * TONES.length); if (t === lastTone) t = (t + 1) % TONES.length; lastTone = t;
        bands.push({ d: polyD(strata[i].concat(strata[i + 1].slice().reverse()), true), tone: TONES[t] });
      }
      const lams = [];
      for (let i = 0; i < strata.length - 1; i++) {
        const nL = Math.floor(r() * 3);
        for (let j = 0; j < nL; j++) {
          const f = 0.25 + r() * 0.5;
          const pts = strata[i].map((q, idx) => [q[0], q[1] + (strata[i + 1][idx][1] - q[1]) * f]);
          const dash = `${f1(30 + r() * 90)} ${f1(14 + r() * 30)} ${f1(10 + r() * 50)} ${f1(18 + r() * 40)}`;
          lams.push({ d: polyD(pts), dash, off: f1(r() * 200) });
        }
      }
      function pebbles(xMin, xMax, n) {
        const out = [];
        for (let i = 0; i < n; i++) {
          const x = xMin + r() * (xMax - xMin), y = -40 + r() * 2000, rad = 2.5 + Math.pow(r(), 2) * 7.5;
          const m = 5 + Math.floor(r() * 3), rot = r() * Math.PI * 2, pts = [];
          for (let j = 0; j < m; j++) { const a = rot + j / m * Math.PI * 2, rr2 = rad * (0.68 + r() * 0.45); pts.push([x + Math.cos(a) * rr2, y + Math.sin(a) * rr2 * 0.8]); }
          out.push({ d: polyD(pts, true), alt: r() < 0.45, op: f1(0.45 + r() * 0.4) });
        }
        return out;
      }
      function cracks(edge, side, n) {
        const out = [];
        for (let i = 0; i < n; i++) {
          let y0;
          do { y0 = 80 + r() * (floorY - 160); } while (Math.abs(y0 - dimY) < 90 || (y0 > 180 && y0 < 300));
          let x = edgeXAt(edge, y0) + side * 1, y = y0;
          const pts = [[x, y]], segs = 3 + Math.floor(r() * 4);
          let ang = (side > 0 ? 0 : Math.PI) + (r() - 0.5) * 0.9;
          for (let j = 0; j < segs; j++) {
            const len = 10 + r() * 20; ang += (r() - 0.5) * 0.9;
            x += Math.cos(ang) * len; y += Math.sin(ang) * len * 0.8; pts.push([x, y]);
          }
          out.push(polyD(pts));
        }
        return out;
      }
      function rubble(side) {
        const out = [];
        const n = 3 + Math.floor(r() * 2);
        for (let i = 0; i < n; i++) {
          const x = cx + side * (half - CR * 0.55 - r() * 46), rad = 4 + r() * 7;
          const yb = floorTop + 1, pts = [];
          const m = 6;
          for (let j = 0; j < m; j++) { const a = Math.PI + j / (m - 1) * Math.PI; const rr2 = rad * (0.75 + r() * 0.4); pts.push([x + Math.cos(a) * rr2 * 1.25, yb + Math.sin(a) * rr2]); }
          out.push(polyD(pts, true));
        }
        return out;
      }

      // ---------- interior (darker bore + surface light) ----------
      const inner = H.svg('g', {}, svg);
      H.svg('rect', { x: cx - half - 30, y: -80, width: 2 * half + 60, height: floorTop + 120, fill: 'var(--hc-int)' }, inner);
      S.inner = inner;
      const glow = H.svg('g', {}, svg);
      if (p.glow) {
        H.svg('rect', { x: cx - half - 30, y: -80, width: 2 * half + 60, height: 80 + 440, fill: `url(#${id('glowV')})` }, glow);
      }
      S.glow = glow;

      // ---------- walls ----------
      const walls = H.svg('g', { class: 'hcx-wall' }, svg);
      function buildWall(poly, edge, side, cls) {
        const g = H.svg('g', {}, walls);
        const body = H.svg('g', {}, g);
        const cp = H.svg('clipPath', { id: id('clip' + cls) }, defs);
        const dPoly = polyD(poly, true);
        H.svg('path', { d: dPoly }, cp);
        H.svg('path', { d: dPoly, fill: 'var(--hc-r0)' }, body);
        const tex = H.svg('g', { 'clip-path': `url(#${id('clip' + cls)})` }, body);
        for (const b of bands) H.svg('path', { d: b.d, fill: `var(${b.tone})` }, tex);
        const tex2 = H.svg('g', { class: 'hcx-tex' }, tex);
        for (const l of lams) H.svg('path', { d: l.d, fill: 'none', stroke: 'var(--hc-line)', 'stroke-width': 1.6, 'stroke-linecap': 'round', 'stroke-dasharray': l.dash, 'stroke-dashoffset': l.off, opacity: 0.55 }, tex2);
        for (const st of strata) H.svg('path', { d: polyD(st), fill: 'none', stroke: 'var(--hc-line)', 'stroke-width': 2, opacity: 0.9 }, tex2);
        const xr = side < 0 ? [-60, cx - 14] : [cx + 14, 1140];
        for (const pb of pebbles(xr[0], xr[1], 70)) H.svg('path', { d: pb.d, fill: pb.alt ? 'var(--hc-peb2)' : 'var(--hc-peb)', opacity: pb.op }, tex2);
        for (const c of cracks(edge, side, 3)) H.svg('path', { d: c, fill: 'none', stroke: 'var(--hc-line)', 'stroke-width': 2, opacity: 0.6, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, tex2);
        // the cut face: crisp rim, warm surface light catching the top of the bore
        const dEdge = polyD(edge);
        H.svg('path', { d: dEdge, fill: 'none', stroke: 'var(--hc-rim)', 'stroke-width': 2, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }, g);
        if (p.glow) H.svg('path', { d: dEdge, fill: 'none', stroke: `url(#${id('rim')})`, 'stroke-width': 2.5, 'stroke-linejoin': 'round', 'stroke-linecap': 'round', class: 'hcx-glowrim' }, g);
        if (side > 0) for (const rb of rubble(side)) H.svg('path', { d: rb, fill: 'var(--hc-r2)', stroke: 'var(--hc-rim)', 'stroke-width': 1.5, 'stroke-linejoin': 'round' }, g);
        return g;
      }
      S.walls = walls;
      S.wallL = buildWall(polyL, edgeL, -1, 'L');
      S.wallR = buildWall(polyR, edgeR, 1, 'R');
      S.rims = Array.from(svg.querySelectorAll('.hcx-glowrim'));

      // lower rock recedes into the background (captions sit there)
      H.svg('rect', { x: -20, y: 1236, width: 1120, height: 700, fill: `url(#${id('fade')})` }, svg);

      // ---------- person ----------
      const toPx = (q) => [cx + q[0] * k, floorY - q[1] * k, q[2]];
      const shapes = [
        smoothClosed(mirrorHalf(BODY_R, [0, 81.2]).map(toPx)),
        smoothClosed(ARM_R.map(toPx)),
        smoothClosed(ARM_R.map(q => [-q[0], q[1], q[2]]).reverse().map(toPx)),
        smoothClosed(mirrorHalf(HEAD_R).map(toPx)),
      ];
      const person = H.svg('g', {}, svg);
      const pStroke = H.svg('g', { fill: 'none', stroke: 'var(--text)', 'stroke-width': 4.4, 'stroke-linejoin': 'round' }, person);
      const pFill = H.svg('g', { fill: 'var(--hc-person)' }, person);
      for (const d of shapes) { H.svg('path', { d }, pStroke); H.svg('path', { d }, pFill); }
      S.person = person;

      // ---------- dimensions ----------
      const dims = H.svg('g', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', fill: 'none' }, svg);
      const hx0 = cx - half, hx1 = cx + half;
      const hg = H.svg('g', { class: 'hcx-amber', stroke: 'var(--hc-amber-line)' }, dims);
      S.hBars = [hx0, hx1].map(x => H.svg('path', { d: `M${f1(x)},${dimY - 22}L${f1(x)},${dimY + 22}`, 'stroke-width': 2.5 }, hg));
      S.hLineL = H.svg('path', { d: `M${cx},${dimY}L${f1(hx0 + 2)},${dimY}`, 'stroke-width': 3 }, hg);
      S.hLineR = H.svg('path', { d: `M${cx},${dimY}L${f1(hx1 - 2)},${dimY}`, 'stroke-width': 3 }, hg);
      S.hLenL = GFXU.prepDash(S.hLineL); S.hLenR = GFXU.prepDash(S.hLineR);
      const chevron = (dir) => `M${f1(dir * 17)},-9L0,0L${f1(dir * 17)},9`;     // tip at (0,0)
      S.hArrL = H.svg('path', { d: chevron(1), 'stroke-width': 3 }, hg);
      S.hArrR = H.svg('path', { d: chevron(-1), 'stroke-width': 3 }, hg);
      S.hx0 = hx0; S.hx1 = hx1;

      // man's height: dashed extension lines + muted dimension line on the left wall
      const dimX = Math.min(cx - half - 50, cx - 23 * k - 110);
      const vg = H.svg('g', { stroke: 'var(--hc-muted)' }, dims);
      if (!p.personValue) vg.style.display = 'none';
      const headSide = cx - 9.2 * k - 10, footSide = cx - 13.2 * k - 10;
      S.vExtT = H.svg('path', { d: `M${f1(headSide)},${f1(headTop)}L${f1(dimX - 14)},${f1(headTop)}`, 'stroke-width': 2, 'stroke-dasharray': '7 7', opacity: 0.85 }, vg);
      S.vExtB = H.svg('path', { d: `M${f1(footSide)},${f1(floorY)}L${f1(dimX - 14)},${f1(floorY)}`, 'stroke-width': 2, 'stroke-dasharray': '7 7', opacity: 0.85 }, vg);
      const vMid = (headTop + floorY) / 2;
      S.vLineT = H.svg('path', { d: `M${f1(dimX)},${f1(vMid)}L${f1(dimX)},${f1(headTop + 2)}`, 'stroke-width': 2.5 }, vg);
      S.vLineB = H.svg('path', { d: `M${f1(dimX)},${f1(vMid)}L${f1(dimX)},${f1(floorY - 2)}`, 'stroke-width': 2.5 }, vg);
      S.vLenT = GFXU.prepDash(S.vLineT); S.vLenB = GFXU.prepDash(S.vLineB);
      const vchev = (dir) => `M-8,${f1(dir * 15)}L0,0L8,${f1(dir * 15)}`;
      S.vArrT = H.svg('path', { d: vchev(1), 'stroke-width': 2.5 }, vg);
      S.vArrB = H.svg('path', { d: vchev(-1), 'stroke-width': 2.5 }, vg);
      Object.assign(S, { dimX, headTop, vMid });
      // extension dash reveal via a mask-free approach: animate the visible length with a clip rect
      const extClip = H.svg('clipPath', { id: id('ext') }, defs);
      S.extRect = H.svg('rect', { x: dimX - 20, y: headTop - 10, width: 0, height: floorY - headTop + 20 }, extClip);
      S.vExtT.setAttribute('clip-path', `url(#${id('ext')})`);
      S.vExtB.setAttribute('clip-path', `url(#${id('ext')})`);
      S.extX0 = Math.max(headSide, footSide); S.extX1 = dimX - 20;

      // ---------- text ----------
      const mk = (cls, txt, css) => { const d = H.el('div', 'hcx-txt ' + cls, root, css); d.textContent = txt; return d; };
      S.value = mk('hcx-value', '', { left: (cx - 300) + 'px', width: '600px', top: (dimY - 118) + 'px' });
      {
        const esc = (t) => String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;');
        const m = /^\s*([0-9٠-٩][0-9٠-٩.,٫٬]*)\s*(.*)$/.exec(p.shaftValue || '');
        S.value.innerHTML = m ? `<span class="hcx-num">${esc(m[1])}</span>${m[2] ? '<span class="hcx-unit">' + esc(m[2]) + '</span>' : ''}` : esc(p.shaftValue);
      }
      S.label = mk('hcx-label', p.shaftLabel, { left: (cx - 300) + 'px', width: '600px', top: (dimY - 118 - 48) + 'px' });
      S.pv = mk('hcx-pv', p.personValue, { left: (dimX - 22 - 400) + 'px', width: '400px', top: (vMid - 29) + 'px' });
    },

    draw(el, u, L, H) {
      const S = L._hc; if (!S) return;
      const p = S.p, ez = H.ez, seg = H.seg;

      // walls slam in from the sides
      const wv = ez('snap', seg(u, p.tWalls, p.tWalls + 0.55));
      const off = (1 - wv) * 640;
      S.wallL.setAttribute('transform', `translate(${f1(-off)},0)`);
      S.wallR.setAttribute('transform', `translate(${f1(off)},0)`);
      S.walls.setAttribute('opacity', ez('standard', seg(u, p.tWalls, p.tWalls + 0.22)).toFixed(3));
      S.inner.setAttribute('opacity', ez('standard', seg(u, p.tWalls + 0.05, p.tWalls + 0.4)).toFixed(3));
      const gv = ez('standard', seg(u, p.tWalls + 0.35, p.tWalls + 1.15));
      S.glow.setAttribute('opacity', gv.toFixed(3));
      for (const rim of S.rims) rim.setAttribute('opacity', gv.toFixed(3));

      // person rises in
      const pu = seg(u, p.tPerson, p.tPerson + 0.4);
      const pop = ez('standard', seg(u, p.tPerson, p.tPerson + 0.35));
      S.person.setAttribute('opacity', pop.toFixed(3));
      S.person.setAttribute('transform', `translate(0,${f1((1 - ez('snap', pu)) * 24)})`);

      // shaft width: arrows run from the centre out to the walls
      const d = u - p.tDims;
      const hv = ez('standard', seg(d, 0.0, 0.5));
      GFXU.dash(S.hLineL, S.hLenL, hv); GFXU.dash(S.hLineR, S.hLenR, hv);
      const show = (u >= p.tDims) ? 1 : 0;
      S.hLineL.style.opacity = S.hLineR.style.opacity = show;
      const aop = ez('standard', seg(d, 0.0, 0.12));
      const xl = H.lerp(540 - 18, S.hx0, hv), xr = H.lerp(540 + 18, S.hx1, hv);
      S.hArrL.setAttribute('transform', `translate(${f1(xl)},${p.dimY})`);
      S.hArrR.setAttribute('transform', `translate(${f1(xr)},${p.dimY})`);
      S.hArrL.style.opacity = S.hArrR.style.opacity = aop;
      const bu = seg(d, 0.42, 0.72);
      const bs = H.lerp(0.3, 1, ez('snap', bu));
      for (const b of S.hBars) {
        const x = b === S.hBars[0] ? S.hx0 : S.hx1;
        b.setAttribute('transform', `translate(${f1(x)},${p.dimY}) scale(1,${bs.toFixed(3)}) translate(${f1(-x)},${-p.dimY})`);
        b.style.opacity = Math.min(1, bu * 3);
      }
      const rise = (div, t0) => {
        const v = seg(d, t0, t0 + 0.25);
        div.style.opacity = Math.min(1, v * 2);
        div.style.transform = `translateY(${f1((1 - ez('snap', v)) * 24)}px)`;
      };
      rise(S.value, 0.22);
      rise(S.label, 0.34);

      // man's height
      const ev = ez('standard', seg(d, 0.55, 0.95));
      S.extRect.setAttribute('x', f1(H.lerp(S.extX0, S.extX1, ev)));
      S.extRect.setAttribute('width', f1(Math.max(0, H.lerp(S.extX0, S.extX1, ev) * -1 + S.extX0 + 4)));
      const vv = ez('standard', seg(d, 0.75, 1.25));
      GFXU.dash(S.vLineT, S.vLenT, vv); GFXU.dash(S.vLineB, S.vLenB, vv);
      S.vLineT.style.opacity = S.vLineB.style.opacity = d >= 0.75 ? 1 : 0;
      const yt = H.lerp(S.vMid - 16, S.headTop, vv), yb = H.lerp(S.vMid + 16, p.floorY, vv);
      S.vArrT.setAttribute('transform', `translate(${f1(S.dimX)},${f1(yt)})`);
      S.vArrB.setAttribute('transform', `translate(${f1(S.dimX)},${f1(yb)})`);
      S.vArrT.style.opacity = S.vArrB.style.opacity = ez('standard', seg(d, 0.75, 0.87));
      rise(S.pv, 1.0);

      // optional exit
      const out = p.tOut == null ? 0 : ez('exit', seg(u, p.tOut, p.tOut + 0.3));
      S.root.style.opacity = (1 - out).toFixed(3);
    },
  };
})();
