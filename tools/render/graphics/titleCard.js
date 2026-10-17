// Episode title card (BRAND: within the hook, <= 2.5 s, amber line 4x120 (x1.4 for Shorts) drawn right-to-left over 0.4 s).
// params: {title:'٦٩ يومًا تحت الأرض', accent:'٦٩', y:470, onPhoto:true}
window.GFX.titleCard = {
  create(el, L, H) {
    const p = L.params || {};
    const y = p.y ?? 470;
    if (p.onPhoto) {
      H.el('div', '', el, { position: 'absolute', left: '0', top: (y - 260) + 'px', width: '1080px', height: '760px',
        background: 'radial-gradient(ellipse 70% 50% at 50% 50%, rgba(11,14,19,.62) 0%, rgba(11,14,19,0) 100%)' });
    }
    const box = H.el('div', '', el, { position: 'absolute', left: '76px', width: '928px', top: y + 'px', textAlign: 'center' });
    const t = H.el('div', '', box, {
      font: "700 172px/1.12 'Readex Pro'", fontVariationSettings: "'wght' 800", color: p.onPhoto ? '#F2EFE9' : 'var(--text)',
      textShadow: p.onPhoto ? '0 4px 24px rgba(0,0,0,.65), 0 1px 3px rgba(0,0,0,.5)' : 'none', textWrap: 'balance',
    });
    const title = p.title || '';
    const acc = p.accent || '';
    t.innerHTML = acc && title.includes(acc) ? title.replace(acc, `<span style="color:#E9A13B">${acc}</span>`) : title;
    const line = H.el('div', '', box, { height: '6px', width: '170px', background: '#E9A13B', margin: '26px auto 0', borderRadius: '3px',
      transformOrigin: '100% 50%' });
    L._box = box; L._t = t; L._line = line; L._shade = el.firstChild;
  },
  draw(el, u, L, H) {
    const dur = L.end - L.start;
    const ui = H.seg(u, 0, 0.25), v = H.ez('snap', ui);
    const out = 1 - H.ez('exit', H.seg(u, dur - 0.25, dur));
    L._t.style.transform = `translateY(${(1 - v) * 24 - (1 - out) * 12}px)`;
    L._t.style.opacity = H.clamp(ui * 2, 0, 1) * out;
    const lv = H.ez('standard', H.seg(u, 0.25, 0.65));      // draws right-to-left (origin on the right)
    L._line.style.transform = `scaleX(${lv})`;
    L._line.style.opacity = out;
    if (L._shade && L._shade !== L._box) L._shade.style.opacity = H.ez('standard', H.seg(u, 0, 0.3)) * out;
  },
};
