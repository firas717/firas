// Amber location pin for the satellite zoom: pulsing dot + label card.
// params: {x:540, y:960, tDot:0, tLabel:0.2, label:'منجم سان خوسيه', sub:'تشيلي · ٢٠١٠', labelY:-170}
window.GFX.mapPin = {
  create(el, L, H) {
    const p = L.params || {};
    const s = H.svg('svg', { width: 1080, height: 1920, viewBox: '0 0 1080 1920', style: 'position:absolute;left:0;top:0' }, el);
    L._ring = H.svg('circle', { cx: p.x ?? 540, cy: p.y ?? 960, r: 18, fill: 'none', stroke: '#E9A13B', 'stroke-width': 3 }, s);
    L._ring2 = H.svg('circle', { cx: p.x ?? 540, cy: p.y ?? 960, r: 18, fill: 'none', stroke: '#E9A13B', 'stroke-width': 2 }, s);
    L._dot = H.svg('circle', { cx: p.x ?? 540, cy: p.y ?? 960, r: 11, fill: '#E9A13B', style: 'filter: drop-shadow(0 0 10px rgba(233,161,59,.8))' }, s);
    L._line = H.svg('line', { x1: p.x ?? 540, y1: (p.y ?? 960) - 22, x2: p.x ?? 540, y2: (p.y ?? 960) + (p.labelY ?? -170) + 70, stroke: '#E9A13B', 'stroke-width': 2 }, s);
    const card = H.el('div', '', el, { position: 'absolute', left: '140px', width: '800px', top: ((p.y ?? 960) + (p.labelY ?? -170) - 120) + 'px', textAlign: 'center' });
    L._t1 = H.el('div', '', card, { font: "700 84px/1.15 'Readex Pro'", color: '#F2EFE9', textShadow: '0 3px 18px rgba(0,0,0,.75)' });
    L._t1.textContent = p.label || '';
    L._t2 = H.el('div', '', card, { font: "600 50px/1.3 'Plex Arabic'", color: '#E9A13B', textShadow: '0 2px 12px rgba(0,0,0,.75)', marginTop: '4px' });
    L._t2.textContent = p.sub || '';
    L._card = card;
  },
  draw(el, u, L, H) {
    const p = L.params || {}, dur = L.end - L.start;
    const a = H.ez('snap', H.seg(u, p.tDot ?? 0, (p.tDot ?? 0) + 0.3));
    const out = 1 - H.ez('exit', H.seg(u, dur - 0.2, dur));
    L._dot.setAttribute('r', 11 * a);
    L._dot.style.opacity = out;
    const ph = ((u - (p.tDot ?? 0)) % 1.2 + 1.2) % 1.2 / 1.2, ph2 = ((u - (p.tDot ?? 0) - 0.6) % 1.2 + 1.2) % 1.2 / 1.2;
    const ring = (c, v) => { const e = H.ez('standard', v); c.setAttribute('r', 14 + 46 * e); c.style.opacity = (1 - e) * 0.9 * a * out; };
    ring(L._ring, ph); ring(L._ring2, ph2);
    const lu = H.seg(u, p.tLabel ?? 0.2, (p.tLabel ?? 0.2) + 0.25);
    const v = H.ez('snap', lu);
    L._card.style.transform = `translateY(${(1 - v) * 24}px)`;
    L._card.style.opacity = H.clamp(lu * 2, 0, 1) * out;
    const lv = H.ez('standard', H.seg(u, (p.tLabel ?? 0.2) - 0.1, (p.tLabel ?? 0.2) + 0.3));
    L._line.style.opacity = lv * out;
  },
};
