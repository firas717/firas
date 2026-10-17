// Lower third (BRAND: from the right, 0.35 s in / hold / 0.25 s out; 42/28 px x1.4 = 59/40 px; 3 px amber vertical line).
// params: {name:'لويس أورسوا', title:'قائد المناوبة — آخر من خرج', y:1040}
window.GFX.lowerThird = {
  create(el, L, H) {
    const p = L.params || {};
    const plate = H.el('div', '', el, {
      position: 'absolute', right: '76px', top: (p.y ?? 1040) + 'px', maxWidth: '860px', padding: '20px 30px 22px 34px',
      background: 'rgba(11,14,19,.70)', borderRadius: '6px', borderRight: '3px solid #E9A13B', textAlign: 'right',
      boxShadow: '0 12px 40px rgba(0,0,0,.35)',
    });
    const n = H.el('div', '', plate, { font: "600 59px/1.25 'Plex Arabic'", color: '#FFFFFF' });
    n.textContent = p.name || '';
    const t = H.el('div', '', plate, { font: "500 40px/1.35 'Plex Arabic'", color: 'rgba(255,255,255,.82)', marginTop: '4px' });
    t.textContent = p.title || '';
    L._plate = plate; L._n = n; L._t = t;
  },
  draw(el, u, L, H) {
    const dur = L.end - L.start;
    const ui = H.ez('snap', H.seg(u, 0, 0.35)), uo = H.ez('exit', H.seg(u, dur - 0.25, dur));
    L._plate.style.transform = `translateX(${(1 - ui) * 120 + uo * 60}px)`;
    L._plate.style.opacity = H.clamp(H.seg(u, 0, 0.2) * 1, 0, 1) * (1 - uo);
    const ut = H.ez('standard', H.seg(u, 0.12, 0.45));
    L._t.style.opacity = ut; L._t.style.transform = `translateX(${(1 - ut) * 30}px)`;
  },
};
