// Shared helpers for graphics modules. Each module registers window.GFX[name] = { create(el, L, H), draw(el, u, L, H) }
// where u = seconds since the layer start. Everything must be a pure function of u.
window.GFX = window.GFX || {};
window.GFXU = {
  // brand colours resolved for the current mode
  col(name) { return getComputedStyle(document.body).getPropertyValue('--' + name).trim(); },
  // stroke-dash reveal helper: set on an SVG path, returns its length
  prepDash(p) { const len = p.getTotalLength(); p.style.strokeDasharray = `${len} ${len}`; p.style.strokeDashoffset = len; return len; },
  dash(p, len, v) { p.style.strokeDashoffset = (1 - v) * len; },
};
