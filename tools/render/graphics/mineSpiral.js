// mineSpiral — side view of the San José mine: a helical ramp spiralling down through the hill,
// the collapse around turn 5 cuts the only way out, the 33 are trapped in the refuge at the bottom.
// params: { tDraw:[0,1.4], tCollapse:2.0, tCut:3.0, tTrapped:3.6,
//           labels:{ portal:'المدخل', collapse:'الانهيار', refuge:'الملجأ', trapped:'٣٣ عاملًا محاصرون' } }
// Everything in draw() is a pure function of u.
(function () {
  const PI = Math.PI, TAU = 2 * PI;
  let UID = 0;

  // ---------- geometry (1080x1920 Shorts canvas) ----------
  const HX = { cx: 540, rx: 220, ry: 36, y0: 420, y1: 1054, turns: 7 };
  const PITCH = (HX.y1 - HX.y0) / HX.turns;
  const TH_END = HX.turns * TAU;
  const CUT_TH = 9 * PI;          // right edge, middle of turn 5
  const X_TH = 8 * PI;            // red X on the route out (left edge, start of turn 5)
  const helixPt = th => [HX.cx - HX.rx * Math.cos(th), HX.y0 + PITCH * th / TAU + HX.ry * Math.sin(th)];
  const HILL = [[-30, 384], [100, 377], [210, 357], [320, 324], [420, 295], [520, 274], [610, 266],
                [700, 273], [800, 296], [900, 327], [1000, 352], [1110, 367]];
  const PORTAL_X = 226;
  const REFUGE = { x: 540, y: 1112, w: 150, h: 44 };
  const ZONE = { x: helixPt(CUT_TH)[0], y: helixPt(CUT_TH)[1], rx: 66, ry: 50 };

  function rng(seed) { let s = seed >>> 0; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }
  const f1 = v => (+v).toFixed(1);
  const dOf = pts => 'M' + pts.map(p => f1(p[0]) + ' ' + f1(p[1])).join(' L');
  function polyLen(pts) { let l = 0; for (let i = 1; i < pts.length; i++) l += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); return l; }
  function cubic(p0, p1, p2, p3, n) {
    const out = [];
    for (let i = 0; i <= n; i++) {
      const t = i / n, a = (1 - t) ** 3, b = 3 * (1 - t) ** 2 * t, c = 3 * (1 - t) * t * t, d = t ** 3;
      out.push([a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]]);
    }
    return out;
  }
  // Catmull-Rom through points -> dense polyline
  function spline(pts, n) {
    let out = [];
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)];
      const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6];
      const c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
      const s = cubic(p1, c1, c2, p2, n);
      out = out.concat(i ? s.slice(1) : s);
    }
    return out;
  }
  function yAt(poly, x) {
    for (let i = 1; i < poly.length; i++) if (poly[i][0] >= x) {
      const a = poly[i - 1], b = poly[i], k = (x - a[0]) / Math.max(1e-6, b[0] - a[0]);
      return a[1] + (b[1] - a[1]) * k;
    }
    return poly[poly.length - 1][1];
  }
  function helixPts(a, b, n) { const out = []; for (let i = 0; i <= n; i++) out.push(helixPt(a + (b - a) * i / n)); return out; }
  function style(e, s) { Object.assign(e.style, s); return e; }

  window.GFX.mineSpiral = {
    create(el, L, H) {
      const P = L.params || {};
      const uid = ++UID;
      const S = el._ms = {};
      S.tDraw = P.tDraw || [0, 1.4];
      S.tCollapse = P.tCollapse ?? 2.0;
      S.tCut = P.tCut ?? 3.0;
      S.tTrapped = P.tTrapped ?? 3.6;
      S.lab = Object.assign({ portal: 'المدخل', collapse: 'الانهيار', refuge: 'الملجأ', trapped: '٣٣ عاملًا محاصرون' }, P.labels || {});

      // mode-dependent text treatment (day mode: no dark halo, amber number sits on an amber chip for contrast)
      if (!document.getElementById('msStyle')) {
        const st = document.createElement('style'); st.id = 'msStyle';
        st.textContent = `.msLab{text-shadow:0 2px 10px rgba(0,0,0,.35)} .msLab .msNum{color:var(--accent)}
          body[data-mode="day"] .msLab{text-shadow:none}
          body[data-mode="day"] .msLab .msNum{display:inline-block;line-height:1.1;color:#12161C;background:var(--accent);border-radius:10px;padding:1px 12px 3px;margin-left:6px}`;
        document.head.appendChild(st);
      }
      const wrap = S.wrap = H.el('div', '', el, { position: 'absolute', left: '0px', top: '0px', width: '1080px', height: '1920px' });
      const svg = H.svg('svg', { width: 1080, height: 1920, viewBox: '0 0 1080 1920' }, wrap);
      style(svg, { position: 'absolute', left: '0px', top: '0px', overflow: 'visible' });
      const defs = H.svg('defs', {}, svg);
      const sv = (tag, attrs, parent, st) => { const e = H.svg(tag, attrs, parent); if (st) style(e, st); return e; };

      // glow filter (amber) — region = whole canvas so nothing clips
      const glow = sv('filter', { id: 'msGlow' + uid, filterUnits: 'userSpaceOnUse', x: -60, y: -60, width: 1200, height: 2040 }, defs);
      sv('feGaussianBlur', { in: 'SourceAlpha', stdDeviation: 5, result: 'b' }, glow);
      sv('feFlood', { 'flood-color': '#E9A13B', 'flood-opacity': 0.42 }, glow);
      sv('feComposite', { in2: 'b', operator: 'in', result: 'g' }, glow);
      const fm = sv('feMerge', {}, glow); sv('feMergeNode', { in: 'g' }, fm); sv('feMergeNode', { in: 'SourceGraphic' }, fm);

      // ground fade (interior dissolves before the caption band)
      const lg = sv('linearGradient', { id: 'msFade' + uid, gradientUnits: 'userSpaceOnUse', x1: 0, y1: 0, x2: 0, y2: 1920 }, defs);
      sv('stop', { offset: (1150 / 1920).toFixed(4), 'stop-color': '#fff' }, lg);
      sv('stop', { offset: (1330 / 1920).toFixed(4), 'stop-color': '#000' }, lg);
      const gm = sv('mask', { id: 'msGM' + uid, maskUnits: 'userSpaceOnUse', x: -60, y: -60, width: 1200, height: 2040 }, defs);
      sv('rect', { x: -60, y: -60, width: 1200, height: 2040, fill: 'url(#msFade' + uid + ')' }, gm);

      // ---------- path segments (in driving order) ----------
      const hill = spline(HILL, 24);
      const portalY = yAt(hill, PORTAL_X);
      S.portal = [PORTAL_X, portalY];
      const start = helixPt(0), end = helixPt(TH_END);
      const segs = [];
      const leadIn = cubic([PORTAL_X, portalY + 4], [PORTAL_X + 60, portalY + 6], [start[0], start[1] - 44], start, 28);
      segs.push({ pts: leadIn, front: true, above: true, turn: 0 });
      for (let k = 0; k < HX.turns * 2; k++) {
        const a = k * PI, b = (k + 1) * PI;
        segs.push({ pts: helixPts(a, b, 64), front: k % 2 === 0, above: b <= CUT_TH + 1e-6, turn: Math.floor(k / 2), k });
      }
      const gal = cubic(end, [end[0], end[1] + 42], [REFUGE.x - REFUGE.w / 2 - 70, REFUGE.y], [REFUGE.x - REFUGE.w / 2 - 2, REFUGE.y], 28);
      segs.push({ pts: gal, front: true, above: false, turn: HX.turns - 1 });
      let acc = 0;
      for (const s of segs) { s.len = polyLen(s.pts); s.d0 = acc; acc += s.len; s.d = dOf(s.pts); }
      S.total = acc; S.segs = segs;

      // occlusion mask for the back halves: front arcs punch a gap where they cross
      const hm = sv('mask', { id: 'msHM' + uid, maskUnits: 'userSpaceOnUse', x: -60, y: -60, width: 1200, height: 2040 }, defs);
      sv('rect', { x: -60, y: -60, width: 1200, height: 2040, fill: '#fff' }, hm);
      for (let k = 0; k < HX.turns * 2; k += 2) {
        sv('path', { d: dOf(helixPts(k * PI + 0.35, k * PI + 1.8, 30)), fill: 'none', stroke: '#000', 'stroke-width': 17, 'stroke-linecap': 'round' }, hm);
      }

      const root = S.root = sv('g', {}, svg);

      // ---------- ground: interior, hill crust, surface line, strata ----------
      const gGround = S.gGround = sv('g', { mask: 'url(#msGM' + uid + ')' }, root);
      sv('path', { d: dOf(hill) + ' L1110 1500 L-30 1500 Z' }, gGround, { fill: 'var(--surface)' });
      const crust = hill.concat(hill.slice().reverse().map(p => [p[0], p[1] + 44 + 0.02 * (540 - Math.abs(p[0] - 540))]));
      sv('path', { d: dOf(crust) + 'Z' }, gGround, { fill: 'var(--surface-alt)' });
      for (const y of [600, 980]) {
        sv('line', { x1: -10, y1: y, x2: 1090, y2: y }, gGround, { stroke: 'var(--border)', strokeWidth: '2px', strokeDasharray: '2 12', strokeLinecap: 'round', opacity: 0.8 });
      }
      sv('path', { d: dOf(hill) }, gGround, { fill: 'none', stroke: 'var(--muted)', strokeWidth: '3px', strokeLinecap: 'round', opacity: 0.75 });

      // ---------- ramp ----------
      const gBack = sv('g', { mask: 'url(#msHM' + uid + ')' }, root);
      const gBackGrey = sv('g', {}, gBack), gBackAmb = sv('g', {}, gBack);
      const gFront = sv('g', {}, root);
      const gFrontGrey = sv('g', {}, gFront), gFrontAmb = sv('g', { filter: 'url(#msGlow' + uid + ')' }, gFront);
      for (const s of segs) {
        const grey = sv('path', { d: s.d }, s.front ? gFrontGrey : gBackGrey,
          { fill: 'none', stroke: s.front ? 'var(--muted)' : 'var(--border)', strokeWidth: s.front ? '5px' : '4.5px', strokeLinecap: 'round', strokeLinejoin: 'round' });
        const amb = sv('path', { d: s.d }, s.front ? gFrontAmb : gBackAmb,
          { fill: 'none', stroke: 'var(--accent)', strokeWidth: s.front ? '5.5px' : '4.5px', strokeLinecap: 'round', strokeLinejoin: 'round' });
        amb.style.strokeDasharray = `${f1(s.len + 2)} ${f1(s.len + 2)}`;
        s.grey = grey; s.amb = amb;
      }
      // travelling head (one in the back layer, one in front, shown according to depth)
      S.headB = sv('circle', { r: 7 }, gBackAmb, { fill: 'var(--accent)' });
      S.headF = sv('circle', { r: 8 }, gFrontAmb, { fill: 'var(--accent)' });

      // ---------- portal ----------
      const [px, py] = S.portal;
      // tunnel mouth: dark arch on a small flat yard cut into the slope
      const gPortal = S.gPortal = sv('g', { transform: `translate(${f1(px)} ${f1(py)})` }, root);
      sv('path', { d: 'M-30 8 L30 8 L30 14 L-30 14 Z' }, gPortal, { fill: 'var(--surface-alt)' });
      sv('path', { d: 'M-16 8 L-16 -4 A16 16 0 0 1 16 -4 L16 8 Z' }, gPortal, { fill: 'var(--bg)' });
      sv('path', { d: 'M-16 8 L-16 -4 A16 16 0 0 1 16 -4 L16 8' }, gPortal, { fill: 'none', stroke: 'var(--text)', strokeWidth: '3.5px', strokeLinecap: 'round', strokeLinejoin: 'round' });
      sv('path', { d: 'M-30 8 L30 8' }, gPortal, { fill: 'none', stroke: 'var(--muted)', strokeWidth: '3px', strokeLinecap: 'round' });

      // ---------- refuge ----------
      const gRef = S.gRef = sv('g', {}, root);
      S.refRect = sv('rect', { x: REFUGE.x - REFUGE.w / 2, y: REFUGE.y - REFUGE.h / 2, width: REFUGE.w, height: REFUGE.h, rx: 14 }, gRef,
        { fill: 'var(--surface-alt)', stroke: 'var(--muted)', strokeWidth: '3px' });
      S.refRing = sv('circle', { cx: REFUGE.x, cy: REFUGE.y, r: 10 }, gRef, { fill: 'none', stroke: 'var(--accent)', strokeWidth: '3px' });
      S.refDot = sv('circle', { cx: REFUGE.x, cy: REFUGE.y, r: 10 }, gRef, { fill: 'var(--accent)' });
      S.refDot.setAttribute('filter', 'url(#msGlow' + uid + ')');

      // ---------- collapse: hatched rubble zone (cross-section convention) ----------
      const r = rng(331);
      const gZone = S.gZone = sv('g', {}, root);
      const blobPts = [];
      for (let i = 0; i < 10; i++) {
        const a = (i + (r() - 0.5) * 0.5) / 10 * TAU, k = 0.8 + r() * 0.2;
        blobPts.push([Math.cos(a) * ZONE.rx * k, Math.sin(a) * ZONE.ry * k]);
      }
      const blobD = dOf(blobPts) + 'Z';
      const clip = sv('clipPath', { id: 'msZC' + uid }, defs);
      sv('path', { d: blobD }, clip);
      sv('path', { d: blobD }, gZone, { fill: 'var(--surface)', fillOpacity: 0.88 });
      sv('path', { d: blobD }, gZone, { fill: 'var(--alert)', fillOpacity: 0.16 });
      const hatch = sv('g', { 'clip-path': 'url(#msZC' + uid + ')' }, gZone);
      for (let x = -150; x <= 150; x += 13) sv('line', { x1: x - 60, y1: 60, x2: x + 60, y2: -60 }, hatch, { stroke: 'var(--alert)', strokeWidth: '3px', opacity: 0.8 });
      sv('path', { d: blobD }, gZone, { fill: 'none', stroke: 'var(--alert)', strokeWidth: '3.5px', strokeLinejoin: 'round' });
      // falling rock fragments (land inside the zone)
      S.rocks = [];
      const rockX = [-34, -12, 10, 30, -24, 18];
      for (let i = 0; i < rockX.length; i++) {
        const n = 5 + (i % 2), rad = 9 + r() * 5, pts = [];
        for (let j = 0; j < n; j++) { const a = j / n * TAU + r() * 0.6; pts.push([Math.cos(a) * rad * (0.72 + r() * 0.28), Math.sin(a) * rad * (0.72 + r() * 0.28)]); }
        const g = sv('g', {}, root);
        sv('path', { d: dOf(pts) + 'Z' }, g, { fill: 'var(--muted)', stroke: 'var(--surface)', strokeWidth: '2.5px', strokeLinejoin: 'round' });
        S.rocks.push({ g, x: ZONE.x + rockX[i], y0: ZONE.y - 70 - r() * 24, y1: ZONE.y + 4 + r() * 22, rot: (r() - 0.5) * 140, delay: i * 0.035 });
      }
      // the cut: bold red slash across the ramp at the collapse point
      const [cx0, cy0] = helixPt(CUT_TH);
      const sa = 0.42, sl = 92;
      const slashD = `M${f1(cx0 - Math.cos(sa) * sl)} ${f1(cy0 - Math.sin(sa) * sl)} L${f1(cx0 + Math.cos(sa) * sl)} ${f1(cy0 + Math.sin(sa) * sl)}`;
      S.slashHalo = sv('path', { d: slashD }, root, { fill: 'none', stroke: 'var(--surface)', strokeWidth: '22px', strokeLinecap: 'round' });
      S.slash = sv('path', { d: slashD }, root, { fill: 'none', stroke: 'var(--alert)', strokeWidth: '11px', strokeLinecap: 'round' });
      S.slashLen = 2 * sl + 1;
      for (const p of [S.slashHalo, S.slash]) p.style.strokeDasharray = `${S.slashLen} ${S.slashLen}`;
      // red X on the route out
      const [xx, xy] = helixPt(X_TH);
      const gX = S.gX = sv('g', {}, root);
      S.xPos = [xx, xy];
      sv('circle', { cx: 0, cy: 0, r: 22 }, gX, { fill: 'var(--surface)', stroke: 'var(--alert)', strokeWidth: '3.5px' });
      sv('path', { d: 'M-8.5 -8.5 L8.5 8.5 M8.5 -8.5 L-8.5 8.5' }, gX, { fill: 'none', stroke: 'var(--alert)', strokeWidth: '4.5px', strokeLinecap: 'round' });

      // ---------- labels + leaders ----------
      const gLead = sv('g', {}, root);
      const labelsDiv = H.el('div', '', wrap, { position: 'absolute', left: '0px', top: '0px', width: '1080px', height: '1920px' });
      const mkLabel = (key, html, x, y, leader, size) => {
        const d = H.el('div', 'msLab', labelsDiv, {
          position: 'absolute', left: x + 'px', top: y + 'px', whiteSpace: 'nowrap', direction: 'rtl',
          font: `600 ${size || 52}px/1.25 'Plex Arabic'`, color: 'var(--text)', textAlign: 'center',
        });
        d.innerHTML = html;
        const o = { d, x, y };
        if (leader) {
          const pts = leader;
          o.path = sv('path', { d: dOf(pts) }, gLead, { fill: 'none', stroke: 'var(--muted)', strokeWidth: '2.5px', strokeLinecap: 'round', strokeLinejoin: 'round' });
          o.len = polyLen(pts) + 1; o.path.style.strokeDasharray = `${f1(o.len)} ${f1(o.len)}`;
          o.dot = sv('circle', { cx: pts[pts.length - 1][0], cy: pts[pts.length - 1][1], r: 5 }, gLead, { fill: 'var(--muted)' });
        }
        S['L_' + key] = o;
        return o;
      };
      const amberNum = s => s.replace(/([٠-٩0-9]+)/g, '<span class="msNum">$1</span>');
      mkLabel('portal', S.lab.portal, 168, 246, [[172, 284], [px - 19, py - 22]]);
      mkLabel('collapse', S.lab.collapse, 890, 724, [[862, 760], [ZONE.x + 44, ZONE.y - 38]]);
      mkLabel('refuge', S.lab.refuge, 744, REFUGE.y, [[668, REFUGE.y], [REFUGE.x + REFUGE.w / 2 + 12, REFUGE.y]]);
      mkLabel('trapped', amberNum(S.lab.trapped), 540, 1190, null, 54);
      for (const k of ['portal', 'collapse', 'refuge', 'trapped']) S['L_' + k].d.style.transform = 'translate(-50%,-50%)';
    },

    draw(el, u, L, H) {
      const S = el._ms; if (!S) return;
      const { ez, seg, clamp, lerp } = H;
      const [td0, td1] = S.tDraw, tc = S.tCollapse, tk = S.tCut, tt = S.tTrapped;

      // camera shake at the collapse (decaying, <= 8 px, 0.35 s)
      const sh = u - tc;
      if (sh > 0 && sh < 0.35) {
        const env = 1 - ez('standard', sh / 0.35);
        const dx = 8 * env * Math.sin(sh * TAU * 13), dy = 5 * env * Math.sin(sh * TAU * 17 + 1.3);
        S.wrap.style.transform = `translate(${dx.toFixed(2)}px, ${dy.toFixed(2)}px)`;
      } else S.wrap.style.transform = '';

      // ground + structure fade in
      S.gGround.style.opacity = ez('standard', seg(u, 0, 0.22));
      S.gPortal.style.opacity = ez('standard', seg(u, 0.02, 0.24));
      const cutK = ez('standard', seg(u, tk + 0.08, tk + 0.5));
      for (const s of S.segs) s.grey.style.opacity = ez('standard', seg(u, 0.04 + s.turn * 0.04, 0.3 + s.turn * 0.04)) * (s.above ? 1 - 0.5 * cutK : 1);
      S.gRef.style.opacity = ez('standard', seg(u, 0.3, 0.6));

      // amber drive path
      const p = ez('standard', seg(u, td0, td1));
      const D = p * S.total;
      const dim = 1 - 0.86 * cutK;
      let headSeg = null, headPt = null;
      for (const s of S.segs) {
        const v = clamp((D - s.d0) / s.len, 0, 1);
        if (v <= 0) { s.amb.style.opacity = 0; continue; }
        s.amb.style.opacity = (s.above ? dim : 1) * (s.front ? 1 : 0.55);
        s.amb.style.strokeDashoffset = f1((1 - v) * (s.len + 2));
        if (v < 1 && !headSeg) {
          headSeg = s;
          const want = v * s.len; let a2 = 0;
          for (let i = 1; i < s.pts.length; i++) {
            const l = Math.hypot(s.pts[i][0] - s.pts[i - 1][0], s.pts[i][1] - s.pts[i - 1][1]);
            if (a2 + l >= want) { const k = (want - a2) / Math.max(1e-6, l); headPt = [lerp(s.pts[i - 1][0], s.pts[i][0], k), lerp(s.pts[i - 1][1], s.pts[i][1], k)]; break; }
            a2 += l;
          }
        }
      }
      const headOp = (p > 0 && p < 1 && headPt) ? clamp(p * 40, 0, 1) * clamp((1 - p) * 30, 0, 1) : 0;
      for (const [c, isF] of [[S.headF, true], [S.headB, false]]) {
        const on = headSeg && headSeg.front === isF;
        c.style.opacity = on ? headOp : 0;
        if (on) { c.setAttribute('cx', f1(headPt[0])); c.setAttribute('cy', f1(headPt[1])); }
      }

      // refuge dot appears when the path arrives; pulses once trapped
      const ua = seg(u, td1 - 0.12, td1 + 0.18);
      let dotS = lerp(0.3, 1, ez('snap', ua));
      let ringOp = 0, ringR = 10;
      if (u >= tt) {
        const ph = ((u - tt) % 1.2) / 1.2;
        ringR = 10 + 30 * ez('standard', ph);
        ringOp = 0.75 * (1 - ez('inout', ph)) * ez('standard', seg(u, tt, tt + 0.15));
        dotS *= 1 + 0.14 * Math.sin(PI * ez('inout', Math.min(1, ph * 2)));
      }
      S.refDot.setAttribute('r', f1(10 * dotS));
      S.refDot.style.opacity = clamp(ua * 3, 0, 1);
      S.refRing.setAttribute('r', f1(ringR));
      S.refRing.style.opacity = ringOp;
      S.refRect.style.stroke = u >= tt ? 'var(--accent-dim)' : 'var(--muted)';

      // collapse zone + rocks + cracks
      const uz = seg(u, tc, tc + 0.3);
      const zs = lerp(0.45, 1, ez('snap', uz));
      S.gZone.setAttribute('transform', `translate(${ZONE.x} ${ZONE.y}) scale(${zs.toFixed(4)})`);
      const zFade = 1 - 0.25 * ez('standard', seg(u, tk, tk + 0.3));
      S.gZone.style.opacity = ez('standard', seg(u, tc, tc + 0.12)) * zFade;
      for (const rk of S.rocks) {
        const ur = seg(u, tc + rk.delay, tc + rk.delay + 0.34);
        const fy = lerp(rk.y0, rk.y1, ez('exit', ur));
        const op = u < tc + rk.delay ? 0 : clamp(ur * 6, 0, 1);
        rk.g.setAttribute('transform', `translate(${rk.x} ${f1(fy)}) rotate(${f1(rk.rot * ez('standard', ur))})`);
        rk.g.style.opacity = op * zFade;
      }

      // the cut
      const us = ez('standard', seg(u, tk, tk + 0.24));
      for (const pth of [S.slashHalo, S.slash]) { pth.style.strokeDashoffset = f1((1 - us) * S.slashLen); pth.style.opacity = us > 0 ? 1 : 0; }
      const ux = seg(u, tk + 0.22, tk + 0.47);
      const xs = lerp(0.6, 1, ez('snap', ux));
      S.gX.setAttribute('transform', `translate(${f1(S.xPos[0])} ${f1(S.xPos[1])}) scale(${xs.toFixed(4)})`);
      S.gX.style.opacity = clamp(ux * 2.5, 0, 1);

      // labels: enter 24 px up with snap; leaders draw with standard
      const lab = (o, t0) => {
        const ui = seg(u, t0, t0 + 0.25);
        o.d.style.opacity = clamp(ui * 2, 0, 1);
        o.d.style.transform = `translate(-50%,-50%) translateY(${f1((1 - ez('snap', ui)) * 24)}px)`;
        if (o.path) {
          const ul = ez('standard', seg(u, t0 - 0.05, t0 + 0.3));
          o.path.style.strokeDashoffset = f1((1 - ul) * o.len);
          o.path.style.opacity = ul > 0 ? 1 : 0;
          o.dot.style.opacity = ez('standard', seg(u, t0 + 0.15, t0 + 0.3));
        }
      };
      lab(S.L_portal, td0 + 0.1);
      lab(S.L_refuge, td1 - 0.05);
      lab(S.L_collapse, tc + 0.12);
      lab(S.L_trapped, tt);
    },
  };
})();
