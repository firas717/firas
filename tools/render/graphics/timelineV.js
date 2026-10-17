// timelineV — vertical timeline that summarises a span of days (here: the 69 days underground).
// A centred vertical line draws downward and reaches node i exactly at tItems[i]; each node pops in
// (snap) and becomes the "current" node (amber, 1.15x, soft halo) until the next one is reached, then
// settles to a 1.0x ring outlined in var(--text). Date on the right of the line, label on the left.
// At tTotal a thin amber brace links the first and last node and the total rises in under the line.
// The whole group drifts up slowly (camera drift). Works in night and day mode (CSS variables only).
//
// params (all optional):
//   items   [{date:'٥ أغسطس', label:'الانهيار'}, {date:'٢٢ أغسطس', label:'الرسالة'}, {date:'١٣ أكتوبر', label:'الإنقاذ'}]
//   tItems  [0.3, 1.4, 2.5]   time each node is reached (line arrives exactly then; 'inout' between nodes)
//   total   '٦٩ يومًا'         digits are converted to Eastern Arabic and coloured amber
//   tTotal  3.4               brace draws from tTotal-0.25 ('standard', 0.7 s); total rises at tTotal ('snap', 0.25 s)
//                             null = no total / brace
//   tOut    null              optional exit: everything fades ('exit', 0.18 s) and lifts 12 px
//   y0 330, y1 1000           first / last node y (group coordinates, before drift)
//   totalY  1142              centre of the total's text line (group coordinates)
//   drift   60                px the group rises over the whole layer ('inout')
//   braceSide 'left'          'left' (beside the labels) or 'right' (beside the dates)
//   settleLast false          true: the last node also settles to a ring when the total appears
// draw() is a pure function of u.
(function () {
  window.GFX = window.GFX || {};
  const CX = 540;
  const R = 20;           // node radius at scale 1.0
  const GAP = 58;         // text distance from the line centre
  const f1 = v => (+v).toFixed(1);

  function injectStyle() {
    if (document.getElementById('tlv-style')) return;
    const s = document.createElement('style');
    s.id = 'tlv-style';
    s.textContent = `
      .tlv-root { position:absolute; left:0; top:0; width:1080px; height:1920px; overflow:hidden; }
      .tlv-grp { position:absolute; left:0; top:0; width:1080px; height:1920px; will-change:transform,opacity; }
      .tlv-svg { position:absolute; left:0; top:0; overflow:visible; }
      .tlv-row { position:absolute; height:120px; display:flex; align-items:center; white-space:nowrap; will-change:transform,opacity; }
      .tlv-row > span { display:inline-block; direction:rtl; }
      .tlv-date { left:${CX + GAP}px; width:${1004 - CX - GAP}px; justify-content:flex-end; }
      .tlv-date > span { font:700 76px/1 'Readex Pro'; color:var(--text); }
      .tlv-lab { left:76px; width:${CX - GAP - 76}px; justify-content:flex-start; }
      .tlv-lab > span { font:600 52px/1 'Plex Arabic'; color:var(--muted); }
      .tlv-total { position:absolute; left:76px; width:928px; height:200px; display:flex; align-items:center; justify-content:center;
        white-space:nowrap; will-change:transform,opacity; }
      .tlv-total > span { display:inline-block; direction:rtl; font:700 150px/1 'Readex Pro'; font-variation-settings:'wght' 800; color:var(--text); }
      .tlv-total .acc { color:var(--accent); position:relative; isolation:isolate; display:inline-block; }
      .tlv-total .tlv-hl { position:absolute; left:-0.08em; right:-0.08em; top:0.56em; bottom:0.05em; border-radius:0.05em;
        background:var(--accent); z-index:-1; transform-origin:100% 50%; display:none; }
      /* day mode: amber digits on cream fail 4.5:1, so the digits turn dark on an amber highlighter band */
      body[data-mode="day"] .tlv-total .acc { color:var(--text); }
      body[data-mode="day"] .tlv-total .tlv-hl { display:block; }
      body[data-mode="day"] .tlv-brace { stroke:var(--accent-dim); }
      body[data-mode="night"] .tlv-date > span, body[data-mode="night"] .tlv-lab > span { text-shadow:0 2px 14px rgba(0,0,0,0.55); }
      body[data-mode="night"] .tlv-total > span { text-shadow:0 3px 22px rgba(0,0,0,0.6); }
      .tlv-line { stroke:var(--text); }
      .tlv-track { stroke:var(--border); }
      .tlv-ghost { fill:var(--bg); stroke:var(--border); }
      body[data-mode="day"] .tlv-track, body[data-mode="day"] .tlv-ghost { stroke:#C4BDAF; }
      .tlv-ring { fill:var(--bg); stroke:var(--text); }
      .tlv-act { fill:var(--accent); stroke:var(--accent); }
      .tlv-halo { fill:var(--accent); }
      .tlv-tip { fill:var(--accent); }
      .tlv-brace { stroke:var(--accent); fill:none; }
      body[data-mode="night"] .tlv-act { filter:drop-shadow(0 0 12px rgba(233,161,59,.45)); }
      body[data-mode="night"] .tlv-tip { filter:drop-shadow(0 0 8px rgba(233,161,59,.7)); }
      body[data-mode="night"] .tlv-brace { filter:drop-shadow(0 0 8px rgba(233,161,59,.30)); }
    `;
    document.head.appendChild(s);
  }

  // RTL text for the total: Eastern digits, digit runs wrapped in an amber span
  function totalHTML(str, H) {
    const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
    return esc(H.arNum(str)).replace(/[٠-٩]+(?:[٫,.][٠-٩]+)?/g, m => `<span class="acc">${m}</span>`);
  }

  // vertical curly brace from (x, a) to (x, b), cusp pointing outward by w (dir -1 = left, +1 = right).
  // Returned as two halves that both start at the cusp so it can draw outward from the middle.
  function braceHalves(x, a, b, w, dir) {
    const q = w / 2, m = (a + b) / 2, sx = x + dir * q, cx = x + dir * w;
    const up = `M${f1(cx)},${f1(m)} Q${f1(sx)},${f1(m)} ${f1(sx)},${f1(m - q)} L${f1(sx)},${f1(a + q)} Q${f1(sx)},${f1(a)} ${f1(x)},${f1(a)}`;
    const dn = `M${f1(cx)},${f1(m)} Q${f1(sx)},${f1(m)} ${f1(sx)},${f1(m + q)} L${f1(sx)},${f1(b - q)} Q${f1(sx)},${f1(b)} ${f1(x)},${f1(b)}`;
    return [up, dn];
  }

  window.GFX.timelineV = {
    create(el, L, H) {
      injectStyle();
      const P = L.params || {};
      const items = P.items || [
        { date: '٥ أغسطس', label: 'الانهيار' },
        { date: '٢٢ أغسطس', label: 'الرسالة' },
        { date: '١٣ أكتوبر', label: 'الإنقاذ' },
      ];
      const n = items.length;
      const y0 = P.y0 ?? 330, y1 = P.y1 ?? 970;
      const Y = items.map((_, i) => n > 1 ? y0 + (y1 - y0) * i / (n - 1) : (y0 + y1) / 2);
      const T = (P.tItems && P.tItems.length >= n) ? P.tItems.slice(0, n) : items.map((_, i) => 0.3 + 1.1 * i);
      const S = L._tlv = {
        n, Y, T, items,
        tTotal: P.tTotal === undefined ? T[n - 1] + 0.9 : P.tTotal,
        tOut: P.tOut ?? null,
        totalY: P.totalY ?? 1170,
        drift: P.drift ?? 60,
        braceSide: P.braceSide === 'right' ? 1 : -1,
        settleLast: !!P.settleLast,
        measured: false,
      };

      // the layer is display:none during create, so request the faces now: ENGINE_READY (document.fonts.ready)
      // then waits for them and _measure() sees real glyph widths
      if (document.fonts && document.fonts.load) {
        const txt = items.map(it => (it.date || '') + (it.label || '')).join('') + H.arNum(P.total || '٦٩ يومًا') + '٠١٢٣٤٥٦٧٨٩';
        ["700 76px 'Readex Pro'", "600 52px 'Plex Arabic'"].forEach(f => document.fonts.load(f, txt).catch(() => {}));
      }
      const root = H.el('div', 'tlv-root', el);
      const grp = S.grp = H.el('div', 'tlv-grp', root);
      const svg = H.svg('svg', { class: 'tlv-svg', width: 1080, height: 1920, viewBox: '0 0 1080 1920' }, grp);

      // faint dotted guide track along the whole span, then the drawn line and its amber tip
      S.track = H.svg('line', { class: 'tlv-track', x1: CX, y1: Y[0], x2: CX, y2: Y[n - 1],
        'stroke-width': 3, 'stroke-linecap': 'round', 'stroke-dasharray': '0.1 14' }, svg);
      S.line = H.svg('line', { class: 'tlv-line', x1: CX, y1: Y[0], x2: CX, y2: Y[0], 'stroke-width': 3, 'stroke-linecap': 'round' }, svg);
      // ghost markers: where the next nodes will land (covered by the real node when it pops)
      S.ghosts = Y.map(y => H.svg('circle', { class: 'tlv-ghost', cx: CX, cy: y, r: 7, 'stroke-width': 2.5 }, svg));
      S.braceG = H.svg('g', {}, svg);
      S.tip = H.svg('circle', { class: 'tlv-tip', cx: CX, cy: Y[0], r: 6.5 }, svg);

      // nodes
      S.nodes = Y.map(y => {
        const g = H.svg('g', { transform: `translate(${CX},${y}) scale(0)` }, svg);
        const halo = H.svg('circle', { class: 'tlv-halo', cx: 0, cy: 0, r: R + 18 }, g);
        const ring = H.svg('circle', { class: 'tlv-ring', cx: 0, cy: 0, r: R, 'stroke-width': 4 }, g);
        const act = H.svg('circle', { class: 'tlv-act', cx: 0, cy: 0, r: R, 'stroke-width': 4 }, g);
        return { g, halo, ring, act };
      });

      // texts (rows are 120 px tall, flex-centred on the node; small optical offsets per font)
      S.rows = items.map((it, i) => {
        const d = H.el('div', 'tlv-row tlv-date', grp, { top: (Y[i] - 60 + (P.dateDy ?? -8)) + 'px' });
        const ds = H.el('span', '', d); ds.textContent = H.arNum(it.date || '');
        const l = H.el('div', 'tlv-row tlv-lab', grp, { top: (Y[i] - 60 + (P.labelDy ?? -5)) + 'px' });
        const ls = H.el('span', '', l); ls.textContent = it.label || '';
        return { d, ds, l, ls };
      });

      if (S.tTotal != null) {
        // keep the total's descenders above y 1228 once it has fully risen (drift at that moment included)
        const dur = L.end - L.start;
        const driftIn = S.drift * H.ez('inout', H.seg(S.tTotal + 0.25, 0, dur));
        const cy = Math.min(S.totalY, 1228 - 98 + driftIn);
        S.total = H.el('div', 'tlv-total', grp, { top: f1(cy - 100) + 'px' });
        S.totalSpan = H.el('span', '', S.total);
        S.totalSpan.innerHTML = totalHTML(P.total || '٦٩ يومًا', H);
        S.hls = Array.from(S.totalSpan.querySelectorAll('.acc')).map(a => H.el('span', 'tlv-hl', a));
      }
    },

    // brace geometry needs the rendered label / date widths (fonts are loaded by the time draw runs)
    _measure(S, H) {
      // only measure with the real faces (a fallback-font measurement would mis-size everything)
      if (document.fonts && document.fonts.check && !(document.fonts.check("700 76px 'Readex Pro'", 'أغسطس') &&
          document.fonts.check("600 52px 'Plex Arabic'", 'الرسالة'))) return;
      S.measured = true;
      // shrink dates / labels uniformly if the widest one would leave its column (dates must end by x 960)
      const fit = (spans, base, avail) => {
        const w = Math.max(...spans.map(s => s.getBoundingClientRect().width));
        if (w > avail) { const fs = Math.floor(base * avail / w); spans.forEach(s => { s.style.fontSize = fs + 'px'; }); }
      };
      fit(S.rows.map(r => r.ds), 76, 960 - (CX + GAP));
      fit(S.rows.map(r => r.ls), 52, (CX - GAP) - 96);
      if (S.tTotal == null || S.n < 2) return;
      const grpRect = S.grp.getBoundingClientRect();
      let edge;
      if (S.braceSide < 0) {
        edge = Math.min(...S.rows.map(r => r.ls.getBoundingClientRect().left - grpRect.left));
        edge = Math.min(edge - 34, CX - GAP - 150);
      } else {
        edge = Math.max(...S.rows.map(r => r.ds.getBoundingClientRect().right - grpRect.left));
        edge = Math.max(edge + 34, CX + GAP + 150);
      }
      const w = 34;
      const x = S.braceSide < 0 ? H.clamp(edge, 80 + w, CX - 80) : H.clamp(edge, CX + 80, 1000 - w);
      const halves = braceHalves(x, S.Y[0], S.Y[S.n - 1], w, S.braceSide);
      S.brace = halves.map(d => {
        const p = H.svg('path', { class: 'tlv-brace', d, 'stroke-width': 3, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, S.braceG);
        return { p, len: window.GFXU.prepDash(p) };
      });
    },

    draw(el, u, L, H) {
      const S = L._tlv; if (!S) return;
      if (!S.measured) this._measure(S, H);
      const { n, Y, T } = S;
      const dur = L.end - L.start;
      const out = S.tOut == null ? 0 : H.ez('exit', H.seg(u, S.tOut, S.tOut + 0.18));

      // camera drift + exit on the whole group
      const dy = -S.drift * H.ez('inout', H.seg(u, 0, dur)) - out * 12;
      S.grp.style.transform = `translateY(${f1(dy)}px)`;
      S.grp.style.opacity = (1 - out).toFixed(3);

      // guide track fades in shortly before the first node
      const tr = H.ez('standard', H.seg(u, T[0] - 0.35, T[0] + 0.1));
      S.track.style.opacity = (tr * 0.9).toFixed(3);
      for (let i = 0; i < n; i++) S.ghosts[i].style.opacity = (u < T[i] + 0.05 ? tr * 0.9 : 0).toFixed(3);

      // line tip: reaches node i exactly at T[i]
      let tipY = Y[0], moving = 0;
      if (u >= T[0]) {
        tipY = Y[n - 1];
        for (let i = 0; i < n - 1; i++) {
          if (u < T[i + 1]) {
            const a = T[i] + Math.min(0.08, (T[i + 1] - T[i]) * 0.1);
            tipY = H.lerp(Y[i], Y[i + 1], H.ez('inout', H.seg(u, a, T[i + 1])));
            moving = H.ez('standard', H.seg(u, a, a + 0.18)) * (1 - H.ez('standard', H.seg(u, T[i + 1] - 0.14, T[i + 1])));
            break;
          }
        }
      }
      S.line.setAttribute('y2', f1(tipY));
      S.line.style.opacity = u >= T[0] ? '1' : '0';
      S.tip.setAttribute('cy', f1(tipY));
      S.tip.style.opacity = moving.toFixed(3);

      // nodes
      const settleT = S.tTotal != null && S.settleLast ? S.tTotal : null;
      for (let i = 0; i < n; i++) {
        const N = S.nodes[i];
        const pop = H.ez('snap', H.seg(u, T[i], T[i] + 0.3));
        const tSettle = i < n - 1 ? T[i + 1] : settleT;
        const st = tSettle == null ? 0 : H.ez('standard', H.seg(u, tSettle, tSettle + 0.35));
        const sc = pop * H.lerp(1.15, 1.0, st);
        N.g.setAttribute('transform', `translate(${CX},${Y[i]}) scale(${sc.toFixed(4)})`);
        N.g.style.opacity = u < T[i] ? '0' : '1';
        N.act.style.opacity = (1 - st).toFixed(3);
        // soft halo on the current node, subtle 'inout' breathing
        const ph = ((u - T[i]) % 1.8 + 1.8) % 1.8 / 1.8;
        const breathe = H.ez('inout', ph < 0.5 ? ph * 2 : 2 - ph * 2);
        const haloIn = H.ez('standard', H.seg(u, T[i] + 0.05, T[i] + 0.45));
        N.halo.style.opacity = ((0.13 + 0.07 * breathe) * haloIn * (1 - st)).toFixed(3);
        N.halo.setAttribute('r', f1(R + 14 + 6 * breathe));

        // texts: 'up' motion (24 px, snap, 0.25 s); label follows the date by 0.06 s
        const rw = S.rows[i];
        const ud = H.seg(u, T[i] + 0.02, T[i] + 0.27), ul = H.seg(u, T[i] + 0.08, T[i] + 0.33);
        rw.d.style.transform = `translateY(${f1((1 - H.ez('snap', ud)) * 24)}px)`;
        rw.d.style.opacity = H.clamp(ud * 2, 0, 1).toFixed(3);
        rw.l.style.transform = `translateY(${f1((1 - H.ez('snap', ul)) * 24)}px)`;
        rw.l.style.opacity = H.clamp(ul * 2, 0, 1).toFixed(3);
      }

      // brace + total
      if (S.tTotal != null) {
        if (S.brace) {
          const bv = H.ez('standard', H.seg(u, S.tTotal - 0.25, S.tTotal + 0.45));
          for (const b of S.brace) { window.GFXU.dash(b.p, b.len, bv); b.p.style.opacity = bv > 0 ? '1' : '0'; }
        }
        const ut = H.seg(u, S.tTotal, S.tTotal + 0.25);
        S.total.style.transform = `translateY(${f1((1 - H.ez('snap', ut)) * 24)}px)`;
        S.total.style.opacity = H.clamp(ut * 2, 0, 1).toFixed(3);
        // day-mode highlighter band behind the digits wipes in right-to-left
        const hv = H.ez('standard', H.seg(u, S.tTotal + 0.12, S.tTotal + 0.57));
        for (const h of S.hls) h.style.transform = `scaleX(${hv.toFixed(4)})`;
      }
    },
  };
})();
