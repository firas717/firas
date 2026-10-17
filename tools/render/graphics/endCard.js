// End card: comment question + short subscribe ask (BRAND: close with a question, subscribe ask <= 3 words).
// params: {question, cta:'تابعنا للمزيد', tQ:0.2, tCta:1.2}
window.GFX.endCard = {
  create(el, L, H) {
    const p = L.params || {};
    const card = H.el('div', '', el, {
      position: 'absolute', left: '96px', width: '888px', top: '430px', boxSizing: 'border-box', padding: '54px 56px 58px',
      background: 'rgba(20,25,34,.88)', borderRadius: '14px', borderTop: '4px solid #E9A13B', textAlign: 'center',
      boxShadow: '0 30px 80px rgba(0,0,0,.45)',
    });
    const icon = H.svg('svg', { width: 88, height: 76, viewBox: '0 0 88 76', style: 'display:block;margin:0 auto 26px' }, card);
    H.svg('path', { d: 'M10 6 H78 a6 6 0 0 1 6 6 V48 a6 6 0 0 1 -6 6 H40 L22 70 V54 H10 a6 6 0 0 1 -6 -6 V12 a6 6 0 0 1 6 -6 Z',
      fill: 'none', stroke: '#E9A13B', 'stroke-width': 4, 'stroke-linejoin': 'round' }, icon);
    [28, 44, 60].forEach(x => H.svg('circle', { cx: x, cy: 30, r: 4, fill: '#E9A13B' }, icon));
    const q = H.el('div', '', card, { font: "600 62px/1.42 'Plex Arabic'", color: '#F2EFE9', textWrap: 'balance' });
    q.textContent = p.question || '';
    const cta = H.el('div', '', el, {
      position: 'absolute', left: '50%', top: '1060px', transform: 'translateX(-50%)', padding: '16px 44px 20px',
      border: '2px solid #E9A13B', borderRadius: '60px', font: "600 48px/1.2 'Plex Arabic'", color: '#E9A13B',
      background: 'rgba(11,14,19,.55)', whiteSpace: 'nowrap',
    });
    cta.textContent = p.cta || '';
    L._card = card; L._q = q; L._cta = cta; L._icon = icon;
  },
  draw(el, u, L, H) {
    const p = L.params || {}, dur = L.end - L.start;
    const tq = p.tQ ?? 0.2, tc = p.tCta ?? 1.2;
    const uc = H.ez('snap', H.seg(u, 0, 0.35));
    const out = 1 - H.ez('exit', H.seg(u, dur - 0.3, dur));
    L._card.style.transform = `translateY(${(1 - uc) * 40}px)`;
    L._card.style.opacity = H.clamp(H.seg(u, 0, 0.25), 0, 1) * out;
    const uq = H.ez('standard', H.seg(u, tq, tq + 0.4));
    L._q.style.opacity = uq; L._q.style.transform = `translateY(${(1 - uq) * 18}px)`;
    const ut = H.ez('snap', H.seg(u, tc, tc + 0.3));
    L._cta.style.opacity = H.clamp(H.seg(u, tc, tc + 0.15) * 2, 0, 1) * out;
    L._cta.style.transform = `translateX(-50%) scale(${H.lerp(0.9, 1, ut)})`;
  },
};
