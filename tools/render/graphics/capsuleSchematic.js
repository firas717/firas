// capsuleSchematic — the Fénix 2 rescue capsule as a front-view technical schematic, with its height,
// its diameter and a 175 cm man on the same ground line for scale.
//
// Look (from the archive photos): conical cap with a steel ring for the winch cable, white upper body
// with guide wheels, two window slots and the Chilean flag (blue canton + white star, red band),
// a blue collar, a dark-blue mesh cage over the lower ~35 %, a blue bottom band with guide wheels,
// rounded base.
//
// params (all optional):
//   tDraw [0,1.2]        outline draws (stroke reveal, var(--text), 3 px): ground, cable + ring, silhouette,
//                        wheels, then interior lines and the mesh sweep top -> bottom
//   tFill 1.0            real colours fade in (0.55 s, 'standard'); the ink detail lines cross-fade away
//   tDims 1.6            height dimension (left, amber) + heightLabel, diameter dimension (under the base)
//                        + diameterLabel, then the man (muted) + humanLabel; all done by tDims + 1.2
//   tOut null            optional: everything fades out ('exit', 0.3 s)
//   heightLabel 'نحو ٤ أمتار'   Readex 700 70 px beside the dimension midpoint; digits are amber
//   diameterLabel '٥٤ سم'       Readex 700 58 px under the diameter dimension; digits are amber
//   humanLabel '١٧٥ سم'         small muted label above the man's head (null = none)
//   name null            optional title at the top (Readex 700 110 px, top edge y 200); when set the whole
//                        drawing shrinks about the ground line (sceneScale 0.86) to make room
//   tName                title entrance (default tDraw[0])
//   cable                thin cable rising from the ring, fading upwards (default: on unless a name is set)
//   cx 560, groundY 1134, dimX 400, humanX 780      layout (capsule 880 px tall = 3.98 m, 2.21 px/cm)
//   sceneScale           override the automatic scale (1, or 0.86 with a name)
// Everything in draw() is a pure function of u.
(function () {
  window.GFX = window.GFX || {};
  let UID = 0;

  const f1 = (v) => (+v).toFixed(1);
  const polyD = (pts, close) => 'M' + pts.map(p => f1(p[0]) + ',' + f1(p[1])).join('L') + (close ? 'Z' : '');

  // real object colours, slightly desaturated (identical in night and day mode)
  const C = {
    white: '#EDEAE3', white2: '#DAD6CD', collar: '#CCC7BD', red: '#C8402E', blue: '#24477F', blueD: '#1C3866',
    cageIn: '#142038', lattice: '#5D7DB5', tyre: '#2F343C', tyreHi: '#4C535D', hub: '#AEB4BC', steel: '#A7ACB3', steelD: '#80868E',
    recess: '#2B313A', window: '#20262F', seam: 'rgba(18,22,28,0.30)', seamOnBlue: 'rgba(5,10,22,0.55)',
  };

  // ---------- human figure, front view, centimetres (x from the body axis, y above the floor), 175 cm ----------
  const HEAD_R = [
    [0, 175], [3.7, 174.5], [6.2, 172.7], [7.5, 169.6], [7.8, 165.8], [7.6, 162.8],
    [8.15, 162.2], [8.55, 160.2], [8.3, 157.4], [7.3, 156.8],
    [6.8, 155.4], [5.8, 153.6], [3.6, 152.0], [0, 151.4],
  ];
  const BODY_R = [
    [5.2, 155.0], [5.25, 151.4], [5.9, 149.3],
    [9.4, 147.3], [13.4, 145.8], [17.0, 144.3], [19.8, 142.5], [20.8, 139.6],
    [20.2, 135.0], [17.6, 130.6], [15.6, 126.6],
    [15.2, 120], [14.4, 112], [13.8, 105], [14.3, 99], [15.8, 93],
    [16.9, 88], [17.2, 83], [16.7, 76], [15.7, 68], [14.3, 59],
    [12.9, 52], [12.5, 47], [12.7, 41], [13.1, 35], [12.5, 27], [11.3, 18],
    [10.4, 11.5], [10.6, 8.2], [11.5, 5.2], [12.5, 2.8], [12.8, 0.9, 1],
    [12.2, 0, 1], [4.6, 0, 1], [4.0, 1.3],
    [4.4, 4.6], [5.2, 8.6], [5.3, 12.5], [4.5, 22], [3.5, 31], [3.6, 38],
    [4.0, 44], [3.6, 50], [3.0, 56], [2.0, 66], [1.1, 75], [0.45, 80.4],
  ];
  const ARM_R = [
    [15.0, 144.8], [18.5, 144.1], [21.3, 142.1], [22.7, 138.9], [23.0, 135.0],
    [22.6, 129.0], [22.2, 121.0], [22.0, 113.0], [21.9, 108.0],
    [22.3, 102.0], [22.2, 96.0], [21.6, 89.0], [21.0, 84.6],
    [21.5, 80.6], [21.7, 75.6], [21.1, 70.2], [20.0, 66.4], [18.7, 65.1],
    [17.4, 65.6], [16.4, 68.0], [15.8, 71.5], [15.7, 76.0], [16.3, 80.2],
    [17.0, 84.6], [17.4, 90.0], [17.6, 97.0], [17.4, 103.0], [17.0, 108.0],
    [17.1, 114.0], [17.2, 120.0], [16.9, 125.6], [16.2, 129.0],
    [14.5, 132.0], [13.5, 138.0],
  ];
  function smoothClosed(pts) {        // closed Catmull-Rom; points flagged [x, y, 1] are corners
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
  function mirrorHalf(R, apex) {
    const Lh = R.slice().reverse().map(p => [-p[0], p[1], p[2]]);
    const out = R.slice();
    if (apex) out.push(apex);
    return out.concat(apex || R[R.length - 1][0] !== 0 ? Lh : Lh.slice(1, Lh.length - 1));
  }

  // digits -> Eastern Arabic, digit runs wrapped in an amber span and glued to the following word
  function richLabel(txt, arNum) {
    const esc = String(txt).replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
    return arNum(esc).replace(/([٠-٩]+(?:[٫٬.,][٠-٩]+)*)( ?)/g,
      (m, num, sp) => `<span class="csx-num">${num}</span>${sp ? ' ' : ''}`);
  }

  function ensureStyle() {
    if (document.getElementById('csx-style')) return;
    const s = document.createElement('style');
    s.id = 'csx-style';
    s.textContent = `
      .csx-root { position:absolute; left:0; top:0; width:1080px; height:1920px; }
      .csx-root svg { position:absolute; left:0; top:0; overflow:visible; }
      body[data-mode="night"] .csx-root {
        --cs-amber: var(--accent);
        --cs-amber-line: var(--accent);
        --cs-amber-glow: rgba(233,161,59,0.38);
        --cs-ext: color-mix(in srgb, var(--muted) 85%, var(--bg));
        --cs-ground: color-mix(in srgb, var(--muted) 55%, var(--bg));
        --cs-human: var(--muted);
        --cs-human-fill: color-mix(in srgb, var(--muted) 40%, var(--bg));
        --cs-halo: rgba(8,10,14,0.85);
        --cs-contact: rgba(0,0,0,0.55);
        --cs-lift: rgba(0,0,0,0.0);
      }
      body[data-mode="day"] .csx-root {
        --cs-amber: color-mix(in srgb, var(--accent-dim) 70%, var(--text));
        --cs-amber-line: color-mix(in srgb, var(--accent-dim) 82%, var(--text));
        --cs-amber-glow: rgba(184,124,37,0.20);
        --cs-ext: color-mix(in srgb, var(--muted) 90%, var(--bg));
        --cs-ground: color-mix(in srgb, var(--muted) 60%, var(--bg));
        --cs-human: var(--muted);
        --cs-human-fill: color-mix(in srgb, var(--muted) 36%, var(--bg));
        --cs-halo: rgba(243,240,233,0.92);
        --cs-contact: rgba(70,58,38,0.22);
        --cs-lift: rgba(70,58,38,0.16);
      }
      .csx-amber { filter: drop-shadow(0 0 9px var(--cs-amber-glow)); }
      .csx-body  { filter: drop-shadow(0 18px 26px var(--cs-lift)); }
      .csx-txt { position:absolute; direction:rtl;
                 text-shadow: 0 0 20px var(--cs-halo), 0 0 6px var(--cs-halo), 0 2px 4px var(--cs-halo); }
      .csx-txt .csx-num { color: var(--cs-amber); }
      .csx-h  { font:700 70px/84px 'Readex Pro'; color:var(--text); text-align:right; white-space:normal; }
      .csx-d  { font:700 54px/60px 'Readex Pro'; color:var(--text); text-align:center; white-space:nowrap; }
      .csx-hu { font:600 42px/52px 'Plex Arabic'; color:var(--muted); text-align:center; white-space:nowrap; }
      .csx-title { font:700 110px/132px 'Readex Pro'; font-variation-settings:'wght' 760; color:var(--text);
                   text-align:center; white-space:nowrap; }
    `;
    document.head.appendChild(s);
  }

  window.GFX.capsuleSchematic = {
    create(el, L, H) {
      ensureStyle();
      const P = L.params || {};
      const p = {
        tDraw: P.tDraw ?? [0, 1.2], tFill: P.tFill ?? 1.0, tDims: P.tDims ?? 1.6, tOut: P.tOut ?? null,
        heightLabel: P.heightLabel ?? 'نحو ٤ أمتار', diameterLabel: P.diameterLabel ?? '٥٤ سم',
        humanLabel: P.humanLabel === undefined ? '١٧٥ سم' : P.humanLabel,
        name: P.name ?? null, cable: P.cable ?? !P.name,
        cx: P.cx ?? 560, G: P.groundY ?? 1134, dimX: P.dimX ?? 400, humanX: P.humanX ?? 780,
      };
      p.tName = P.tName ?? p.tDraw[0];
      p.f = P.sceneScale ?? (p.name ? 0.86 : 1);
      const uid = ++UID, id = (k) => `csx${uid}-${k}`;
      const S = { p };
      L._cs = S;

      const cx = p.cx, G = p.G, f = p.f;
      // geometry helpers: dx = px from the capsule axis, h = px above the ground (at scale 1)
      const X = (dx) => cx + dx * f, Y = (h) => G - h * f;
      const pt = (dx, h) => [X(dx), Y(h)];
      const rectD = (dx0, dx1, h0, h1) => polyD([pt(dx0, h0), pt(dx1, h0), pt(dx1, h1), pt(dx0, h1)], true);
      const rrectD = (dx0, dx1, h0, h1, r) => {                // rounded rect, h0 = top
        const x0 = X(dx0), x1 = X(dx1), y0 = Y(h0), y1 = Y(h1), rr = r * f;
        return `M${f1(x0 + rr)},${f1(y0)}L${f1(x1 - rr)},${f1(y0)}A${f1(rr)},${f1(rr)} 0 0 1 ${f1(x1)},${f1(y0 + rr)}` +
          `L${f1(x1)},${f1(y1 - rr)}A${f1(rr)},${f1(rr)} 0 0 1 ${f1(x1 - rr)},${f1(y1)}L${f1(x0 + rr)},${f1(y1)}` +
          `A${f1(rr)},${f1(rr)} 0 0 1 ${f1(x0)},${f1(y1 - rr)}L${f1(x0)},${f1(y0 + rr)}A${f1(rr)},${f1(rr)} 0 0 1 ${f1(x0 + rr)},${f1(y0)}Z`;
      };
      const circD = (dx, h, r) => {                              // circle starting at its bottom, clockwise
        const x = X(dx), y = Y(h), rr = r * f;
        return `M${f1(x)},${f1(y + rr)}A${f1(rr)},${f1(rr)} 0 1 1 ${f1(x)},${f1(y - rr)}A${f1(rr)},${f1(rr)} 0 1 1 ${f1(x)},${f1(y + rr)}`;
      };
      const lineD = (a, b) => `M${f1(a[0])},${f1(a[1])}L${f1(b[0])},${f1(b[1])}`;

      // ---------- capsule profile (scale 1: 880 px tall, 118 px body = 54 cm) ----------
      const HW = 59;                    // body half width
      const g = {
        top: 880, ringC: 865, ringR: 15, ringr: 8.5,
        neckTop: 853, neckBot: 837, neckW: 6,
        coneTop: 838, coneTopW: 13, coneBase: 766,
        col0: 766, col1: 754, colW: 63,
        blue0: 338, blue1: 320, bandW: 62,
        cage0: 320, cage1: 72, cageIn: 53,
        bot0: 72, bot1: 44, baseR: 26,
        hoop0: 198, hoop1: 191,
        wheelUp: 714, wheelLo: 58, wheelR: 11, wheelDx: 61,
      };
      S.g = g;
      // right half of the silhouette, top centre -> bottom centre (mirrored for the left)
      const halfPts = (sd) => [
        [0, g.neckTop], [g.neckW, g.neckTop], [g.neckW, g.coneTop], [g.coneTopW, g.coneTop], [HW, g.coneBase],
        [g.colW, g.col0], [g.colW, g.col1], [HW, g.col1],
        [HW, g.blue0], [g.bandW, g.blue0], [g.bandW, g.blue1], [HW, g.blue1],
        [HW, g.bot0], [g.bandW, g.bot0], [g.bandW, g.bot1], [HW, g.bot1],
      ].map(q => pt(sd * q[0], q[1]));
      function halfD(sd) {
        const pts = halfPts(sd);
        let d = polyD(pts);
        // base: straight down to the corner, quarter arc, flat bottom to the centre
        const r = g.baseR;
        d += `L${f1(X(sd * HW))},${f1(Y(r))}`;
        d += `A${f1(r * f)},${f1(r * f)} 0 0 ${sd > 0 ? 1 : 0} ${f1(X(sd * (HW - r)))},${f1(Y(0))}`;
        d += `L${f1(X(0))},${f1(Y(0))}`;
        return d;
      }
      const dR = halfD(1), dL = halfD(-1);
      // closed silhouette (for fills, clip and shading): right half then the left half reversed
      const silPts = [];
      {
        const R = halfPts(1), Lp = halfPts(-1).reverse();
        const r = g.baseR, N = 8;
        const arc = (sd) => { const a = []; for (let i = 0; i <= N; i++) { const t = (i / N) * Math.PI / 2; a.push(pt(sd * (HW - r + r * Math.cos(t)), r - r * Math.sin(t))); } return a; };
        silPts.push(...R, ...arc(1), ...arc(-1).reverse(), ...Lp);
      }
      const silD = polyD(silPts, true);

      const root = H.el('div', 'csx-root', el);
      S.root = root;
      const svg = H.svg('svg', { width: 1080, height: 1920, viewBox: '0 0 1080 1920' }, root);
      const defs = H.svg('defs', {}, svg);

      // gradients
      const gCable = H.svg('linearGradient', { id: id('cable'), gradientUnits: 'userSpaceOnUse', x1: 0, y1: Y(g.top), x2: 0, y2: p.name ? Y(g.top) - 150 : 0 }, defs);
      H.svg('stop', { offset: 0, style: 'stop-color:var(--muted);stop-opacity:0.9' }, gCable);
      H.svg('stop', { offset: 1, style: 'stop-color:var(--muted);stop-opacity:0' }, gCable);
      const gGround = H.svg('linearGradient', { id: id('ground'), gradientUnits: 'userSpaceOnUse', x1: X(-270), y1: 0, x2: X(370), y2: 0 }, defs);
      [[0, 0], [0.14, 1], [0.86, 1], [1, 0]].forEach(([o, a]) => H.svg('stop', { offset: o, style: `stop-color:var(--cs-ground);stop-opacity:${a}` }, gGround));
      const gShade = H.svg('linearGradient', { id: id('shade'), gradientUnits: 'userSpaceOnUse', x1: X(-g.colW), y1: 0, x2: X(g.colW), y2: 0 }, defs);
      [[0, '#000', 0.34], [0.12, '#000', 0.16], [0.30, '#fff', 0.0], [0.38, '#fff', 0.16], [0.46, '#fff', 0.0],
       [0.70, '#000', 0.06], [0.90, '#000', 0.24], [1, '#000', 0.40]]
        .forEach(([o, c, a]) => H.svg('stop', { offset: o, 'stop-color': c, 'stop-opacity': a }, gShade));
      const gContact = H.svg('radialGradient', { id: id('contact'), cx: 0.5, cy: 0.5, r: 0.5 }, defs);
      H.svg('stop', { offset: 0, style: 'stop-color:var(--cs-contact);stop-opacity:1' }, gContact);
      H.svg('stop', { offset: 1, style: 'stop-color:var(--cs-contact);stop-opacity:0' }, gContact);
      const clipSil = H.svg('clipPath', { id: id('sil') }, defs);
      H.svg('path', { d: silD }, clipSil);
      const clipCage = H.svg('clipPath', { id: id('cage') }, defs);
      H.svg('path', { d: rectD(-g.cageIn, g.cageIn, g.cage0, g.cage1) }, clipCage);
      const clipSweep = H.svg('clipPath', { id: id('sweep') }, defs);
      S.sweepRect = H.svg('rect', { x: X(-70), y: Y(g.cage0) - 2, width: 140 * f, height: 0 }, clipSweep);
      S.sweepY0 = Y(g.cage0) - 2; S.sweepH = (g.cage0 - g.cage1) * f + 4;

      // ---------- ground + contact shadow ----------
      S.groundA = H.svg('path', { d: `M${f1(X(50))},${f1(G)}L${f1(X(-270))},${f1(G)}`, stroke: `url(#${id('ground')})`, 'stroke-width': 2.5, 'stroke-linecap': 'round', fill: 'none' }, svg);
      S.groundB = H.svg('path', { d: `M${f1(X(50))},${f1(G)}L${f1(X(370))},${f1(G)}`, stroke: `url(#${id('ground')})`, 'stroke-width': 2.5, 'stroke-linecap': 'round', fill: 'none' }, svg);
      S.lenGA = GFXU.prepDash(S.groundA); S.lenGB = GFXU.prepDash(S.groundB);
      S.contact = H.svg('ellipse', { cx: X(0), cy: G + 1, rx: 96 * f, ry: 9 * f, fill: `url(#${id('contact')})` }, svg);

      // ---------- cable ----------
      if (p.cable) {
        const yTop = p.name ? Y(g.top) - 150 : -10;
        S.cable = H.svg('path', { d: `M${f1(X(0))},${f1(Y(g.top) + 2)}L${f1(X(0))},${f1(yTop)}`, stroke: `url(#${id('cable')})`, 'stroke-width': 2.5, fill: 'none', 'stroke-linecap': 'round' }, svg);
        S.lenCable = GFXU.prepDash(S.cable);
      }

      // ---------- fills (real colours) ----------
      const fills = H.svg('g', { class: 'csx-body' }, svg);
      S.fills = fills;
      const fp = (d, fill, extra) => H.svg('path', Object.assign({ d, fill }, extra || {}), fills);
      const bodyG = H.svg('g', { 'clip-path': `url(#${id('sil')})` }, fills);
      const bp = (d, fill, extra) => H.svg('path', Object.assign({ d, fill }, extra || {}), bodyG);
      bp(silD, C.white);
      bp(polyD([pt(-g.neckW, g.neckTop + 4), pt(g.neckW, g.neckTop + 4), pt(g.neckW, g.coneTop), pt(-g.neckW, g.coneTop)], true), C.steel);
      bp(polyD([pt(-g.coneTopW, g.coneTop), pt(g.coneTopW, g.coneTop), pt(HW, g.coneBase), pt(-HW, g.coneBase)], true), C.white2);
      bp(rectD(-g.colW, g.colW, g.col0, g.col1), C.collar);
      bp(rectD(-g.bandW, g.bandW, g.blue0, g.blue1), C.blue);
      bp(rectD(-HW, HW, g.cage0, g.cage1), C.cageIn);
      // mesh (clipped to the cage interior)
      const mesh = H.svg('g', { 'clip-path': `url(#${id('cage')})` }, bodyG);
      const meshLines = [];
      {
        const yT = Y(g.cage0), yB = Y(g.cage1), Hh = yB - yT, run = Hh / 1.7, sp = 19 * f;
        const xL = X(-g.cageIn), xR = X(g.cageIn);
        for (let c = xL - run; c <= xR + 1; c += sp) meshLines.push(lineD([c, yT], [c + run, yB]));
        for (let c = xL; c <= xR + run + 1; c += sp) meshLines.push(lineD([c, yT], [c - run, yB]));
      }
      // inner depth of the cage: darker towards the sides
      for (const d of meshLines) H.svg('path', { d, stroke: C.lattice, 'stroke-width': 1.7, fill: 'none', 'stroke-linecap': 'round' }, mesh);
      bp(rectD(-HW, -g.cageIn, g.cage0, g.cage1), C.blue);
      bp(rectD(g.cageIn, HW, g.cage0, g.cage1), C.blue);
      bp(rectD(-HW, HW, g.hoop0, g.hoop1), C.blue);
      bp(rectD(-g.bandW, g.bandW, g.bot0, g.bot1), C.blue);
      bp(rectD(-HW, HW, g.bot1, -2), C.blueD);
      // flag: blue canton with a white star, red band
      const fl = { c0: 538, c1: 498, r1: 458, cw: 40 };
      bp(rectD(-HW, -HW + fl.cw, fl.c0, fl.c1), C.blue);
      bp(rectD(-HW, HW, fl.c1, fl.r1), C.red);
      {
        const sx = -HW + fl.cw / 2, sh = (fl.c0 + fl.c1) / 2, R = 12.5, r = 5.0, pts = [];
        for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? r : R; pts.push([X(sx) + Math.cos(a) * rr * f, Y(sh) + Math.sin(a) * rr * f]); }
        bp(polyD(pts, true), C.white);
      }
      // windows + front wheel housing
      bp(rrectD(-21, -11, 664, 602, 5), C.window);
      bp(rrectD(11, 21, 664, 602, 5), C.window);
      bp(rrectD(-10, 10, 734, 694, 4), C.recess);
      bp(rrectD(-4.5, 4.5, 729, 699, 4.5), C.tyreHi);
      // coloured detail lines (panel joints, band edges)
      const det = H.svg('g', { fill: 'none', 'stroke-width': 2, 'stroke-linecap': 'round' }, bodyG);
      for (const hh of [g.coneBase, g.col1, 678, 399]) H.svg('path', { d: lineD(pt(-g.colW, hh), pt(g.colW, hh)), stroke: C.seam }, det);
      for (const hh of [g.blue0, g.blue1, g.hoop0, g.hoop1, g.bot0, g.bot1]) H.svg('path', { d: lineD(pt(-g.colW, hh), pt(g.colW, hh)), stroke: C.seamOnBlue }, det);
      for (const sd of [-1, 1]) H.svg('path', { d: lineD(pt(sd * g.cageIn, g.cage0), pt(sd * g.cageIn, g.cage1)), stroke: C.seamOnBlue }, det);
      for (const sd of [-1, 1]) H.svg('path', { d: lineD(pt(sd * 6, g.coneTop - 1), pt(sd * 24, g.coneBase + 1)), stroke: C.seam, 'stroke-width': 1.6 }, det);
      // cylinder shading over everything inside the silhouette
      bp(silD, `url(#${id('shade')})`);
      // ring (steel annulus)
      fp(circD(0, g.ringC, g.ringR) + circD(0, g.ringC, g.ringr), C.steel, { 'fill-rule': 'evenodd' });

      // ---------- ink detail lines (schematic stage, cross-fade away when the colours arrive) ----------
      const ink = H.svg('g', { fill: 'none', stroke: 'var(--text)', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, svg);
      S.ink = ink;
      const inkMesh = H.svg('g', { 'clip-path': `url(#${id('sweep')})` }, ink);
      const inkMeshIn = H.svg('g', { 'clip-path': `url(#${id('cage')})`, opacity: 0.5, 'stroke-width': 1.4 }, inkMesh);
      for (const d of meshLines) H.svg('path', { d }, inkMeshIn);
      S.inkDet = [];
      const addInk = (d, h, w) => { const e = H.svg('path', { d }, ink); if (w) e.setAttribute('stroke-width', w); S.inkDet.push({ e, len: GFXU.prepDash(e), h }); };
      for (const hh of [g.coneBase, g.col1, g.blue0, g.blue1, g.hoop0, g.hoop1, g.bot0, g.bot1]) {
        const w = (hh === g.coneBase || hh === g.col1) ? g.colW : (hh === g.hoop0 || hh === g.hoop1 ? HW : g.bandW);
        addInk(lineD(pt(-w, hh), pt(w, hh)), hh);
      }
      for (const hh of [678, 399]) addInk(lineD(pt(-HW, hh), pt(HW, hh)), hh, 1.5);
      for (const sd of [-1, 1]) addInk(lineD(pt(sd * g.cageIn, g.cage0), pt(sd * g.cageIn, g.cage1)), g.cage0 - 20);
      for (const sd of [-1, 1]) addInk(lineD(pt(sd * 6, g.coneTop - 1), pt(sd * 24, g.coneBase + 1)), g.coneTop - 10, 1.5);
      addInk(rrectD(-21, -11, 664, 602, 5), 640);
      addInk(rrectD(11, 21, 664, 602, 5), 640);
      addInk(rrectD(-10, 10, 734, 694, 4), 720);
      addInk(polyD([pt(-HW, fl.c1), pt(-HW + fl.cw, fl.c1), pt(-HW + fl.cw, fl.c0), pt(-HW, fl.c0)]), fl.c0);
      addInk(lineD(pt(-HW, fl.r1), pt(HW, fl.r1)), fl.r1);
      addInk(lineD(pt(-HW + fl.cw, fl.c1), pt(HW, fl.c1)), fl.c1);
      {
        const sx = -HW + fl.cw / 2, sh = (fl.c0 + fl.c1) / 2, R = 12.5, r = 5.0, pts = [];
        for (let i = 0; i <= 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? r : R; pts.push([X(sx) + Math.cos(a) * rr * f, Y(sh) + Math.sin(a) * rr * f]); }
        addInk(polyD(pts), sh, 1.5);
      }

      // ---------- ink silhouette (stays) ----------
      const outl = H.svg('g', { fill: 'none', stroke: 'var(--text)', 'stroke-width': 3, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, svg);
      S.silR = H.svg('path', { d: dR }, outl); S.lenR = GFXU.prepDash(S.silR);
      S.silL = H.svg('path', { d: dL }, outl); S.lenL = GFXU.prepDash(S.silL);
      S.ringO = H.svg('path', { d: circD(0, g.ringC, g.ringR) }, outl); S.lenRO = GFXU.prepDash(S.ringO);
      S.ringI = H.svg('path', { d: circD(0, g.ringC, g.ringr), 'stroke-width': 2.5 }, outl); S.lenRI = GFXU.prepDash(S.ringI);
      // guide wheels on short spring arms: own group above the outline (fills fade, strokes draw)
      const wg = H.svg('g', { stroke: 'var(--text)', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, svg);
      S.wheels = [];
      for (const sd of [-1, 1]) for (const hw of [g.wheelUp, g.wheelLo]) {
        const br = H.svg('path', { d: rrectD(sd > 0 ? 52 : -64, sd > 0 ? 64 : -52, hw + 6, hw - 6, 2), 'stroke-width': 2, fill: C.steelD }, wg);
        const wh = H.svg('path', { d: circD(sd * g.wheelDx, hw, g.wheelR), 'stroke-width': 2.5, fill: C.tyre }, wg);
        const hb = H.svg('path', { d: circD(sd * g.wheelDx, hw, 3.6), stroke: 'none', fill: C.hub }, wg);
        S.wheels.push({ br, lb: GFXU.prepDash(br), wh, lw: GFXU.prepDash(wh), hb, h: hw });
      }

      // ---------- dimensions ----------
      const dims = H.svg('g', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', fill: 'none' }, svg);
      const dimX = X(p.dimX - cx), yTop = Y(g.top), yBot = Y(0), yMid = (yTop + yBot) / 2;
      Object.assign(S, { dimX, yTop, yBot, yMid });
      const ext = H.svg('g', { stroke: 'var(--cs-ext)', 'stroke-width': 2, 'stroke-dasharray': '7 7' }, dims);
      S.extTop = H.svg('path', { d: '' }, ext);
      S.extTopX0 = X(-g.ringR - 7); S.extTopX1 = dimX - 16;
      const ag = H.svg('g', { class: 'csx-amber', stroke: 'var(--cs-amber-line)' }, dims);
      // single paths revealed from the middle outwards (no double-alpha seam at the centre)
      S.vLine = H.svg('path', { d: `M${f1(dimX)},${f1(yTop + 2)}L${f1(dimX)},${f1(yBot - 2)}`, 'stroke-width': 3 }, ag);
      S.lenV = S.vLine.getTotalLength();
      const vchev = (dir) => `M-9,${dir * 17}L0,0L9,${dir * 17}`;
      S.aT = H.svg('path', { d: vchev(1), 'stroke-width': 3 }, ag);
      S.aB = H.svg('path', { d: vchev(-1), 'stroke-width': 3 }, ag);
      S.tickT = H.svg('path', { d: `M${f1(dimX - 16)},${f1(yTop)}L${f1(dimX + 16)},${f1(yTop)}`, 'stroke-width': 2.5 }, ag);
      S.tickB = H.svg('path', { d: `M${f1(dimX - 16)},${f1(yBot)}L${f1(dimX + 16)},${f1(yBot)}`, 'stroke-width': 2.5 }, ag);
      // diameter, under the base
      const wY = G + 22, wx0 = X(-HW), wx1 = X(HW);
      Object.assign(S, { wY, wx0, wx1 });
      S.extW = [wx0, wx1].map(x => H.svg('path', { d: '' }, ext));
      S.extWY0 = Y(g.baseR) + 10; S.extWY1 = wY + 9;
      S.wLine = H.svg('path', { d: `M${f1(wx0 + 2)},${f1(wY)}L${f1(wx1 - 2)},${f1(wY)}`, 'stroke-width': 3 }, ag);
      S.lenW = S.wLine.getTotalLength();
      const hchev = (dir) => `M${dir * 15},-8L0,0L${dir * 15},8`;
      S.aWL = H.svg('path', { d: hchev(1), 'stroke-width': 3 }, ag);
      S.aWR = H.svg('path', { d: hchev(-1), 'stroke-width': 3 }, ag);

      // ---------- human for scale ----------
      const k = 2.211 * f;                          // px per cm (capsule: 880 px = 398 cm)
      const hx = X(p.humanX - cx);
      const toPx = (q) => [hx + q[0] * k, G - q[1] * k, q[2]];
      const shapes = [
        smoothClosed(mirrorHalf(BODY_R, [0, 81.2]).map(toPx)),
        smoothClosed(ARM_R.map(toPx)),
        smoothClosed(ARM_R.map(q => [-q[0], q[1], q[2]]).reverse().map(toPx)),
        smoothClosed(mirrorHalf(HEAD_R).map(toPx)),
      ];
      const person = H.svg('g', {}, svg);
      H.svg('ellipse', { cx: hx, cy: G + 1, rx: 44 * f, ry: 6 * f, fill: `url(#${id('contact')})`, opacity: 0.8 }, person);
      const pS = H.svg('g', { fill: 'none', stroke: 'var(--cs-human)', 'stroke-width': 3, 'stroke-linejoin': 'round' }, person);
      const pF = H.svg('g', { fill: 'var(--cs-human-fill)' }, person);
      for (const d of shapes) { H.svg('path', { d }, pS); H.svg('path', { d }, pF); }
      S.person = person;
      S.headTop = G - 175 * k;

      // ---------- text ----------
      const mk = (cls, html, css) => { const d = H.el('div', 'csx-txt ' + cls, root, css); d.innerHTML = html; return d; };
      const hRight = dimX - 30, hW = Math.max(160, hRight - 76);
      S.hl = mk('csx-h', richLabel(p.heightLabel, H.arNum), { left: f1(hRight - hW) + 'px', width: f1(hW) + 'px', top: f1(yMid) + 'px' });
      S.dl = mk('csx-d', richLabel(p.diameterLabel, H.arNum), { left: f1(X(0) - 300) + 'px', width: '600px', top: f1(wY - 2) + 'px' });
      if (p.humanLabel) S.hu = mk('csx-hu', H.arNum(p.humanLabel), { left: f1(hx - 200) + 'px', width: '400px', top: f1(S.headTop - 62) + 'px' });
      if (p.name) S.title = mk('csx-title', H.arNum(p.name), { left: '76px', width: '928px', top: '200px' });
    },

    draw(el, u, L, H) {
      const S = L._cs; if (!S) return;
      const p = S.p, ez = H.ez, seg = H.seg, lerp = H.lerp;
      const [d0, d1] = p.tDraw, D = Math.max(0.05, d1 - d0);
      const sv = (a, b) => ez('standard', seg(u, d0 + a * D, d0 + b * D));
      const dashOn = (e, len, v) => { GFXU.dash(e, len, v); e.style.opacity = v > 0 ? 1 : 0; };
      const midOut = (e, len, v) => {
        e.style.strokeDasharray = `${f1(v * len)} ${f1(len + 2)}`;
        e.style.strokeDashoffset = f1(-(1 - v) * len / 2);
        e.style.opacity = v > 0 ? 1 : 0;
      };

      // one-time fit of the title to the safe width (fonts are loaded once draw runs)
      if (S.title && !S.fitted) {
        const w = S.title.scrollWidth;
        if (w > 928) S.title.style.fontSize = f1(110 * 928 / w) + 'px';
        S.fitted = true;
      }

      // ---- outline stage ----
      const vg = sv(0, 0.55);
      dashOn(S.groundA, S.lenGA, vg); dashOn(S.groundB, S.lenGB, vg);
      if (S.cable) dashOn(S.cable, S.lenCable, sv(0.05, 0.6));
      dashOn(S.ringO, S.lenRO, sv(0.0, 0.35));
      dashOn(S.ringI, S.lenRI, sv(0.08, 0.4));
      const vs = sv(0.12, 0.85);
      dashOn(S.silR, S.lenR, vs); dashOn(S.silL, S.lenL, vs);
      const fv = ez('standard', seg(u, p.tFill, p.tFill + 0.55));
      for (const w of S.wheels) {
        const a = 0.25 + 0.45 * (1 - w.h / 880);
        dashOn(w.br, w.lb, sv(a, a + 0.25)); dashOn(w.wh, w.lw, sv(a + 0.05, a + 0.3));
        w.br.style.fillOpacity = w.wh.style.fillOpacity = fv.toFixed(3);
        w.hb.style.opacity = fv.toFixed(3);
      }
      for (const q of S.inkDet) {
        const a = 0.3 + 0.45 * (1 - q.h / 880);
        dashOn(q.e, q.len, sv(a, Math.min(1, a + 0.28)));
      }
      const msv = sv(0.55, 1.0);
      S.sweepRect.setAttribute('height', f1(S.sweepH * msv));

      // ---- colour stage ----
      S.fills.setAttribute('opacity', fv.toFixed(3));
      S.ink.setAttribute('opacity', (1 - fv).toFixed(3));
      S.contact.setAttribute('opacity', fv.toFixed(3));

      // ---- dimensions ----
      const d = u - p.tDims;
      const rise = (div, t0) => {
        if (!div) return;
        const v = seg(d, t0, t0 + 0.25);
        div.style.opacity = Math.min(1, v * 2).toFixed(3);
        return (1 - ez('snap', v)) * 24;
      };
      // top extension line runs from the ring to the dimension line
      const ev = ez('standard', seg(d, 0, 0.3));
      const ex = lerp(S.extTopX0, S.extTopX1, ev);
      S.extTop.setAttribute('d', ev > 0 ? `M${f1(S.extTopX0)},${f1(S.yTop)}L${f1(ex)},${f1(S.yTop)}` : '');
      // vertical dimension grows from the midpoint outwards
      const vv = ez('standard', seg(d, 0.1, 0.62));
      midOut(S.vLine, S.lenV, vv);
      const yt = lerp(S.yMid - 18, S.yTop, vv), yb = lerp(S.yMid + 18, S.yBot, vv);
      S.aT.setAttribute('transform', `translate(${f1(S.dimX)},${f1(yt)})`);
      S.aB.setAttribute('transform', `translate(${f1(S.dimX)},${f1(yb)})`);
      const aop = ez('standard', seg(d, 0.1, 0.22)).toFixed(3);
      S.aT.style.opacity = S.aB.style.opacity = aop;
      const tk = seg(d, 0.55, 0.8);
      const ts = lerp(0.2, 1, ez('snap', tk));
      for (const [e, y] of [[S.tickT, S.yTop], [S.tickB, S.yBot]]) {
        e.setAttribute('transform', `translate(${f1(S.dimX)},${f1(y)}) scale(${ts.toFixed(3)},1) translate(${f1(-S.dimX)},${f1(-y)})`);
        e.style.opacity = Math.min(1, tk * 3).toFixed(3);
      }
      const tyH = rise(S.hl, 0.38);
      S.hl.style.transform = `translateY(calc(-50% + ${f1(tyH)}px))`;
      // diameter under the base
      const wev = ez('standard', seg(d, 0.42, 0.7));
      S.extW.forEach((e, i) => {
        const x = i ? S.wx1 : S.wx0;
        e.setAttribute('d', wev > 0 ? `M${f1(x)},${f1(S.extWY0)}L${f1(x)},${f1(lerp(S.extWY0, S.extWY1, wev))}` : '');
      });
      const wv = ez('standard', seg(d, 0.55, 0.95));
      midOut(S.wLine, S.lenW, wv);
      const cxm = (S.wx0 + S.wx1) / 2;
      S.aWL.setAttribute('transform', `translate(${f1(lerp(cxm - 16, S.wx0, wv))},${f1(S.wY)})`);
      S.aWR.setAttribute('transform', `translate(${f1(lerp(cxm + 16, S.wx1, wv))},${f1(S.wY)})`);
      S.aWL.style.opacity = S.aWR.style.opacity = ez('standard', seg(d, 0.55, 0.67)).toFixed(3);
      const tyD = rise(S.dl, 0.78);
      S.dl.style.transform = `translateY(${f1(tyD)}px)`;
      // the man for scale
      const pu = seg(d, 0.6, 1.0);
      S.person.setAttribute('opacity', ez('standard', seg(d, 0.6, 0.95)).toFixed(3));
      S.person.setAttribute('transform', `translate(0,${f1((1 - ez('snap', pu)) * 24)})`);
      if (S.hu) { const ty = rise(S.hu, 0.95); S.hu.style.transform = `translateY(${f1(ty)}px)`; }

      // ---- title ----
      if (S.title) {
        const v = seg(u, p.tName, p.tName + 0.25);
        S.title.style.opacity = Math.min(1, v * 2).toFixed(3);
        S.title.style.transform = `translateY(${f1((1 - ez('snap', v)) * 24)}px)`;
      }

      // ---- optional exit ----
      const out = p.tOut == null ? 0 : ez('exit', seg(u, p.tOut, p.tOut + 0.3));
      S.root.style.opacity = (1 - out).toFixed(3);
    },
  };
})();
