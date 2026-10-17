// noteReveal — the miners' handwritten note "Estamos bien en el refugio los 33" (22 Aug 2010)
// shown as a real paper card: the card lands, the red handwriting is revealed left-to-right (Spanish is LTR),
// an amber highlighter sweeps behind each line, then the Arabic translation + source label rise in below.
//
// params (all optional except the two image paths):
// { paperSrc:'file:///…/brand/templates/backgrounds/paper.png',
//   noteSrc:'file:///…/build/commons/thumbs/c149.jpg',          // red handwriting on white/transparent
//   noteAspect: 500/166,                                       // source image w/h
//   topoSrc:'file:///…/topo_night.png', topoDaySrc:'…/topo_day.png' (default: derived from topoSrc),
//   tCard:0, tWrite:0.35, writeDur:0.8, writeStagger:0.25,
//   tHighlight:1.4, hlDur:0.5, hlGap:0.5, hlOpacity:0.32,
//   tTranslate:2.1, tSource:null (default tTranslate+0.3), tOut:null (optional exit, 0.18 s),
//   translation:'«نحن بخير في الملجأ — الـ٣٣»', source:'نص رسالة العمال · ٢٢ أغسطس ٢٠١٠',
//   kicker:null, tKicker:null (optional small label above the card, default tCard+0.15) }
// draw() is a pure function of u.
(function () {
  let UID = 0;
  const CARD = { w: 880, h: 510, cx: 540, cy: 618, tilt: -2.5 };
  const INK_W = 790;
  // line geometry as fractions of the note image (measured on c149: 500x166)
  //   split = horizontal cut between the two lines; x0/x1/y0/y1 = ink extents of each line
  const LINES = [
    { y0: 0.048, y1: 0.428, x0: 0.018, x1: 0.974 },
    { y0: 0.470, y1: 0.988, x0: 0.006, x1: 0.994 },
  ];
  const SPLIT = 0.452;

  function rng(seed) { let s = seed >>> 0; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }
  const f1 = v => (+v).toFixed(1);
  function css(e, s) { Object.assign(e.style, s); return e; }

  function injectStyle() {
    if (document.getElementById('nrv-style')) return;
    const s = document.createElement('style');
    s.id = 'nrv-style';
    s.textContent = `
      .nrv-root { position:absolute; left:0; top:0; width:1080px; height:1920px; overflow:hidden; }
      .nrv-bg { position:absolute; inset:0; background:var(--bg); }
      .nrv-topo { position:absolute; left:-160px; top:-120px; width:1400px; height:2400px; }
      .nrv-topoN { mix-blend-mode:screen; opacity:0.30; }
      .nrv-topoD { mix-blend-mode:multiply; opacity:0.34; display:none; }
      body[data-mode="day"] .nrv-topoN { display:none; }
      body[data-mode="day"] .nrv-topoD { display:block; }
      .nrv-pool { position:absolute; inset:0; background:radial-gradient(ellipse 62% 30% at 50% 34%, rgba(255,246,228,0.075), rgba(255,246,228,0) 100%); }
      body[data-mode="day"] .nrv-pool { background:radial-gradient(ellipse 62% 30% at 50% 34%, rgba(255,255,255,0.55), rgba(255,255,255,0) 100%); }
      .nrv-vig { position:absolute; inset:0; background:radial-gradient(ellipse 78% 62% at 50% 40%, rgba(0,0,0,0) 45%, rgba(0,0,0,0.62) 100%); }
      body[data-mode="day"] .nrv-vig { background:radial-gradient(ellipse 78% 62% at 50% 40%, rgba(60,44,20,0) 50%, rgba(60,44,20,0.13) 100%); }

      .nrv-grp { position:absolute; transform-origin:50% 50%; will-change:transform,opacity; }
      .nrv-card { position:absolute; inset:0; border-radius:4px; overflow:hidden; background:#E6E2DA;
        box-shadow: 0 1px 2px rgba(0,0,0,0.55), 0 10px 22px rgba(0,0,0,0.42), 0 34px 70px rgba(0,0,0,0.55); }
      body[data-mode="day"] .nrv-card {
        box-shadow: 0 1px 2px rgba(48,36,18,0.24), 0 10px 22px rgba(48,36,18,0.14), 0 34px 70px rgba(48,36,18,0.20); }
      .nrv-paper { position:absolute; left:-40px; top:-40px; right:-40px; bottom:-40px; background-size:cover; background-position:42% 38%; }
      .nrv-warm { position:absolute; inset:0; background:#F8F0E0; mix-blend-mode:multiply; opacity:0.45; }
      .nrv-lift { position:absolute; inset:0; background:#FFFDF8; opacity:0.16; }
      body[data-mode="day"] .nrv-lift { opacity:0.34; }
      .nrv-light { position:absolute; inset:0;
        background: linear-gradient(168deg, rgba(255,255,255,0.30) 0%, rgba(255,255,255,0.06) 38%, rgba(0,0,0,0) 62%, rgba(70,52,28,0.10) 100%); }
      .nrv-edge { position:absolute; inset:0; box-shadow: inset 0 0 36px rgba(110,86,52,0.20), inset 0 0 3px rgba(90,70,40,0.25); }
      body[data-mode="night"] .nrv-dim { position:absolute; inset:0; background:rgba(20,22,28,0.07); }

      .nrv-hl, .nrv-ink { position:absolute; mix-blend-mode:multiply; }
      .nrv-hl svg { position:absolute; left:0; top:0; overflow:visible; }
      .nrv-ink { overflow:hidden; }
      .nrv-ink img { position:absolute; left:0; filter: saturate(0.94) brightness(0.84) contrast(1.06); }

      .nrv-tapeW { position:absolute; filter: drop-shadow(0 1px 1.5px rgba(0,0,0,0.22)); }
      .nrv-tape { position:absolute; inset:0;
        background: linear-gradient(180deg, rgba(250,246,234,0.64) 0%, rgba(238,231,212,0.52) 55%, rgba(244,239,224,0.60) 100%); }
      body[data-mode="day"] .nrv-tape {
        background: linear-gradient(180deg, rgba(232,224,202,0.70) 0%, rgba(220,210,184,0.58) 55%, rgba(228,220,198,0.66) 100%); }
      body[data-mode="day"] .nrv-tapeW { filter: drop-shadow(0 1px 1.5px rgba(60,44,20,0.28)); }
      .nrv-tape::after { content:''; position:absolute; left:0; right:0; top:0; height:2px; background:rgba(255,255,255,0.35); }

      .nrv-col { position:absolute; left:76px; width:928px; display:flex; flex-direction:column; align-items:center; }
      .nrv-tx { width:928px; text-align:center; direction:rtl; white-space:pre-line; }
      .nrv-kick { position:absolute; left:76px; }
      .nrv-trans { font: 700 80px/1.22 'Readex Pro'; color:var(--text); text-shadow: 0 2px 14px rgba(0,0,0,0.55); }
      .nrv-src { font: 500 40px/1.35 'Plex Arabic'; color:var(--muted); text-shadow: 0 1px 8px rgba(0,0,0,0.5); margin-top:10px; }
      .nrv-kick { font: 600 48px/1.3 'Plex Arabic'; color:var(--muted); text-shadow: 0 1px 8px rgba(0,0,0,0.5); }
      body[data-mode="day"] .nrv-tx { text-shadow:none; }
      .nrv-rule { width:60px; height:3px; border-radius:2px; background:var(--accent); margin-top:18px; }
    `;
    document.head.appendChild(s);
  }

  // rough highlighter band (card coordinates): chisel-tip slanted ends, slightly wavy edges, slight rise LTR
  function bandPath(R, x0, x1, yt, yb) {
    const n = Math.max(6, Math.round((x1 - x0) / 22));
    const rise = -3 + R() * 2;
    const top = [], bot = [];
    const nz = () => (R() - 0.5) * 4.2;
    let pt = 0, pb = 0;
    for (let i = 0; i <= n; i++) {
      const k = i / n, x = x0 + (x1 - x0) * k, r = rise * k;
      pt = pt * 0.45 + nz() * 0.55; pb = pb * 0.45 + nz() * 0.55;
      top.push([x, yt + r + pt]);
      bot.push([x, yb + r + pb]);
    }
    // chisel ends: left end leans one way, right end the other, slightly rounded
    const sl = 9;
    top[0][0] += sl; bot[0][0] -= sl * 0.4;
    top[n][0] += sl * 0.4; bot[n][0] -= sl;
    let d = `M${f1(top[0][0])},${f1(top[0][1])}`;
    for (let i = 1; i <= n; i++) {
      const a = top[i - 1], b = top[i];
      d += `Q${f1(a[0])},${f1(a[1])} ${f1((a[0] + b[0]) / 2)},${f1((a[1] + b[1]) / 2)}`;
    }
    d += `L${f1(top[n][0])},${f1(top[n][1])}`;
    d += `Q${f1(top[n][0] + 4)},${f1((top[n][1] + bot[n][1]) / 2)} ${f1(bot[n][0])},${f1(bot[n][1])}`;
    for (let i = n - 1; i >= 0; i--) {
      const a = bot[i + 1], b = bot[i];
      d += `Q${f1(a[0])},${f1(a[1])} ${f1((a[0] + b[0]) / 2)},${f1((a[1] + b[1]) / 2)}`;
    }
    d += `L${f1(bot[0][0])},${f1(bot[0][1])}`;
    d += `Q${f1(bot[0][0] - 4)},${f1((top[0][1] + bot[0][1]) / 2)} ${f1(top[0][0])},${f1(top[0][1])}Z`;
    return d;
  }

  // jagged (torn) ends for tape
  function tapeClip(R, w, h) {
    const pts = [];
    const n = 7;
    for (let i = 0; i <= n; i++) pts.push([(R() * 5).toFixed(1), (h * i / n).toFixed(1)]);           // left edge, top->bottom
    const right = [];
    for (let i = 0; i <= n; i++) right.push([(w - R() * 5).toFixed(1), (h * (n - i) / n).toFixed(1)]); // right edge, bottom->top
    return 'polygon(' + pts.concat(right).map(p => p[0] + 'px ' + p[1] + 'px').join(',') + ')';
  }

  window.GFX.noteReveal = {
    create(el, L, H) {
      injectStyle();
      const P = L.params || {};
      const uid = ++UID;
      const S = el._nrv = {};
      S.tCard = P.tCard ?? 0;
      S.tWrite = P.tWrite ?? 0.35;
      S.writeDur = P.writeDur ?? 0.8;
      S.writeStagger = P.writeStagger ?? 0.25;
      S.tHighlight = P.tHighlight ?? 1.4;
      S.hlDur = P.hlDur ?? 0.5;
      S.hlGap = P.hlGap ?? 0.5;
      S.tTranslate = P.tTranslate ?? 2.1;
      S.tSource = P.tSource ?? (S.tTranslate + 0.3);
      S.tOut = P.tOut ?? null;
      S.tKicker = P.tKicker ?? (S.tCard + 0.15);
      S.dur = Math.max(0.5, (L.end ?? 6) - (L.start ?? 0));
      const aspect = P.noteAspect || (500 / 166);
      const inkH = INK_W / aspect;

      const root = H.el('div', 'nrv-root', el);

      // ---------- background ----------
      const bg = H.el('div', 'nrv-bg', root);
      const topoSrc = P.topoSrc || 'file:///home/user/firas/brand/templates/backgrounds/topo_night.png';
      const topoDaySrc = P.topoDaySrc || topoSrc.replace('topo_night', 'topo_day');
      S.topoN = H.el('img', 'nrv-topo nrv-topoN', bg); S.topoN.src = topoSrc;
      S.topoD = H.el('img', 'nrv-topo nrv-topoD', bg); S.topoD.src = topoDaySrc;
      H.el('div', 'nrv-pool', bg);
      H.el('div', 'nrv-vig', bg);

      // ---------- optional kicker above the card ----------
      if (P.kicker) {
        S.kick = H.el('div', 'nrv-tx nrv-kick', root, { top: '212px' });
        S.kick.textContent = P.kicker;
      }

      // ---------- card group ----------
      const grp = S.grp = H.el('div', 'nrv-grp', root, {
        left: (CARD.cx - CARD.w / 2) + 'px', top: (CARD.cy - CARD.h / 2) + 'px', width: CARD.w + 'px', height: CARD.h + 'px',
      });
      const card = H.el('div', 'nrv-card', grp);
      const paper = H.el('div', 'nrv-paper', card);
      paper.style.backgroundImage = `url("${P.paperSrc || 'file:///home/user/firas/brand/templates/backgrounds/paper.png'}")`;
      H.el('div', 'nrv-warm', card);
      H.el('div', 'nrv-lift', card);
      H.el('div', 'nrv-light', card);
      H.el('div', 'nrv-dim', card);

      const inkL = (CARD.w - INK_W) / 2;
      const inkT = Math.round((CARD.h - inkH) / 2) - 4;
      S.inkL = inkL; S.inkT = inkT;
      const R = rng(4733 + uid * 17);

      // highlighter bands (behind the ink; both multiply onto the paper, so order is visual only)
      const HLB = P.hlBand || [[0.16, 0.97], [0.17, 0.86]];   // band top/bottom as fractions of each line's ink height
      S.hl = LINES.map((ln, i) => {
        const x0 = inkL + ln.x0 * INK_W - 16, x1 = inkL + ln.x1 * INK_W + 16;
        const lh = (ln.y1 - ln.y0) * inkH;
        const yt = inkT + ln.y0 * inkH + lh * HLB[i][0], yb = inkT + ln.y0 * inkH + lh * HLB[i][1];
        const w = H.el('div', 'nrv-hl', card, { left: '0px', top: '0px', width: CARD.w + 'px', height: CARD.h + 'px' });
        const sv = H.svg('svg', { width: CARD.w, height: CARD.h, viewBox: `0 0 ${CARD.w} ${CARD.h}` }, w);
        // felt-tip texture: displaced (rough) edges + long horizontal streaks in the ink density (static noise, seeded)
        const fid = `nrvHL${uid}_${i}`;
        const flt = H.svg('filter', { id: fid, filterUnits: 'userSpaceOnUse', x: 0, y: 0, width: CARD.w, height: CARD.h, 'color-interpolation-filters': 'sRGB' }, sv);
        H.svg('feTurbulence', { type: 'fractalNoise', baseFrequency: '0.11 0.07', numOctaves: 2, seed: 5 + i * 7, result: 'n1' }, flt);
        H.svg('feDisplacementMap', { in: 'SourceGraphic', in2: 'n1', scale: 6, xChannelSelector: 'R', yChannelSelector: 'G', result: 'd' }, flt);
        H.svg('feTurbulence', { type: 'fractalNoise', baseFrequency: '0.0035 0.085', numOctaves: 2, seed: 19 + i * 3, result: 'n2' }, flt);
        H.svg('feColorMatrix', { in: 'n2', type: 'matrix', values: '0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0.55 0 0 0 0.60', result: 'n2a' }, flt);
        H.svg('feComposite', { in: 'd', in2: 'n2a', operator: 'in' }, flt);
        const op = P.hlOpacity ?? 0.42;
        const g = H.svg('g', { filter: `url(#${fid})`, style: `opacity:${op}` }, sv);
        H.svg('path', { d: bandPath(R, x0, x1, yt, yb), style: 'fill:var(--accent)' }, g);
        // denser streak where the felt tip overlaps itself (along the top edge) — very subtle
        H.svg('path', { d: bandPath(R, x0 + 14, x1 - 8, yt + 1, yt + (yb - yt) * 0.2), style: 'fill:var(--accent);opacity:0.30' }, g);
        return { w, x0: x0 - 14, x1: x1 + 14, yt, yb };
      });

      // handwriting: two horizontal slices so each line can be wiped on its own
      const cut = Math.round(SPLIT * inkH);
      S.ink = [[0, cut], [cut, inkH]].map(([a, b], i) => {
        const w = H.el('div', 'nrv-ink', card, { left: inkL + 'px', top: (inkT + a) + 'px', width: INK_W + 'px', height: (b - a) + 'px' });
        const img = H.el('img', '', w, { width: INK_W + 'px', height: inkH + 'px', top: (-a) + 'px' });
        img.src = P.noteSrc;
        const ln = LINES[i];
        return { w, x0: ln.x0 * INK_W, x1: ln.x1 * INK_W };
      });
      H.el('div', 'nrv-edge', card);

      // tape strips along the top edge
      const tapes = [
        { x: 168, y: -8, w: 196, h: 58, rot: -7 },
        { x: 738, y: -10, w: 186, h: 58, rot: 6 },
      ];
      tapes.forEach(t => {
        const tw = H.el('div', 'nrv-tapeW', grp, {
          left: (t.x - t.w / 2) + 'px', top: (t.y - t.h / 2) + 'px', width: t.w + 'px', height: t.h + 'px',
          transform: `rotate(${t.rot}deg)`,
        });
        const tp = H.el('div', 'nrv-tape', tw);
        tp.style.clipPath = tapeClip(R, t.w, t.h);
      });

      // ---------- translation + source ----------
      // translation: '\n' forces a break; otherwise break before an em dash so the signature sits on its own line
      let tr = P.translation ?? '«نحن بخير في الملجأ — الـ٣٣»';
      if (tr.indexOf('\n') < 0 && P.translationOneLine !== true) tr = tr.replace(/\s+—\s+/, '\n— ');
      const col = H.el('div', 'nrv-col', root, { top: (P.textTop ?? 938) + 'px' });
      S.trans = H.el('div', 'nrv-tx nrv-trans', col);
      S.trans.textContent = tr;
      S.rule = H.el('div', 'nrv-rule', col);
      S.src = H.el('div', 'nrv-tx nrv-src', col);
      S.src.textContent = P.source ?? 'نص رسالة العمال · ٢٢ أغسطس ٢٠١٠';
      if (!P.source && P.source !== undefined) { S.src.style.display = 'none'; S.rule.style.display = 'none'; }
    },

    draw(el, u, L, H) {
      const S = el._nrv;
      const out = S.tOut == null ? 0 : H.ez('exit', H.seg(u, S.tOut, S.tOut + 0.18));
      const outY = -12 * out, outOp = 1 - out;

      // card: slides up 40 px + fades in (snap), settles its tilt, then a slow push-in for the rest of the layer
      const uc = H.seg(u, S.tCard, S.tCard + 0.5);
      const vc = H.ez('snap', uc);
      const opc = H.ez('standard', H.seg(u, S.tCard, S.tCard + 0.2));
      const push = H.ez('kb', H.seg(u, S.tCard + 0.3, S.dur));
      const sc = 1 + 0.014 * push;
      const rot = H.lerp(CARD.tilt - 1.2, CARD.tilt, vc);
      S.grp.style.transform = `translateY(${f1((1 - vc) * 40 + outY)}px) rotate(${rot.toFixed(3)}deg) scale(${sc.toFixed(4)})`;
      S.grp.style.opacity = (opc * outOp).toFixed(3);

      // handwriting: soft-edged left-to-right wipe, line 2 starts a beat after line 1
      const per = Math.max(0.2, S.writeDur - S.writeStagger);
      const F = 34;
      S.ink.forEach((k, i) => {
        const t0 = S.tWrite + i * S.writeStagger;
        const v = H.ez('standard', H.seg(u, t0, t0 + per));
        if (v >= 1) { k.w.style.webkitMaskImage = k.w.style.maskImage = 'none'; k.w.style.visibility = ''; return; }
        if (v <= 0) { k.w.style.visibility = 'hidden'; return; }
        k.w.style.visibility = '';
        const e = H.lerp(k.x0 - F, k.x1 + F, v);
        const m = `linear-gradient(90deg, #000 0px, #000 ${f1(e - F)}px, rgba(0,0,0,0) ${f1(e + F)}px)`;
        k.w.style.webkitMaskImage = m; k.w.style.maskImage = m;
      });

      // highlighter: sweeps LTR behind each line
      S.hl.forEach((h, i) => {
        const t0 = S.tHighlight + i * S.hlGap;
        const v = H.ez('standard', H.seg(u, t0, t0 + S.hlDur));
        if (v <= 0) { h.w.style.visibility = 'hidden'; return; }
        h.w.style.visibility = '';
        // chisel-tip leading edge (slanted like the band ends)
        const e = H.lerp(h.x0, h.x1 + 10, v), a = f1(e + 7), b = f1(e - 7);
        h.w.style.clipPath = v >= 1 ? 'none' :
          `polygon(-20px -20px, ${a}px -20px, ${a}px ${f1(h.yt - 6)}px, ${b}px ${f1(h.yb + 6)}px, ${b}px ${CARD.h + 20}px, -20px ${CARD.h + 20}px)`;
      });

      // texts: 'up' (24 px, snap, 0.25 s)
      const up = (node, t0) => {
        const ui = H.seg(u, t0, t0 + 0.25);
        const v = H.ez('snap', ui);
        node.style.transform = `translateY(${f1((1 - v) * 24 + outY)}px)`;
        node.style.opacity = (H.clamp(ui * 2, 0, 1) * outOp).toFixed(3);
      };
      up(S.trans, S.tTranslate);
      up(S.src, S.tSource);
      // short amber rule draws out from the centre between translation and source
      const vr = H.ez('standard', H.seg(u, S.tSource - 0.05, S.tSource + 0.35));
      S.rule.style.transform = `scaleX(${vr.toFixed(3)})`;
      S.rule.style.opacity = ((vr > 0 ? 1 : 0) * outOp).toFixed(3);
      if (S.kick) up(S.kick, S.tKicker);
    },
  };
})();
