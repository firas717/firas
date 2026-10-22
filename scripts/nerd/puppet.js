/* Al-Nerd puppets: articulated characters like episode 1 (McNair), with joints that cannot come apart.
 *
 * Every limb is a round-capped tube. A child segment starts exactly at its parent's joint and both ends
 * are round with the same radius, so at any angle the two tubes share a full disc at the joint: there is
 * never a gap (Firas: "the body must never come apart"). Each body part is drawn in three passes:
 * white sticker border (whole figure, under everything), black outline, colour fill. The fill pass of a
 * layer covers its own outline at the joints, so a bent limb reads as one continuous tube.
 *
 * Motion is procedural and deterministic: pose(t) is a pure function of time. The timeline drives it
 * with one tween per puppet whose `modifiers` function applies the pose on every render, seeks included.
 *
 * Angles (degrees) are anatomical, for a puppet facing right:
 *   arms/legs: + swings forward (toward the face)    knee: + bends (shin goes back)
 *   elbow: + bends (forearm comes forward/up)         spine: + leans forward     head: + nods down
 *   ankle: + toes up                                  wrist: + hand tips up
 */
(function () {
  const NS = "http://www.w3.org/2000/svg";
  const INK = "#17171c", BORDER = "#ffffff";
  const OW = 4.5, BW = 6.5;               // outline and sticker-border widths (units)
  const D2R = Math.PI / 180;

  // ------------------------------------------------------------------ skeleton (units; standing ~500 tall)
  const SK = {
    thigh: 108, shin: 104, footH: 15, footL: 50, footB: 14,
    spine: 150, shoulderY: -136, neck: 14,
    upper: 80, fore: 74, hand: 15,
    wThigh: 36, wShin: 31, wUpper: 27, wFore: 24,
    hipX: [-7, 7], shX: [-15, 13],        // [back, front] lateral offsets give a 3/4 view
  };

  // ------------------------------------------------------------------ costumes
  const COSTUMES = {
    narrator: { top: "#24304f", sleeve: "#24304f", pants: "#3a3f4a", shoes: "#22232a", hat: "cap", hatColor: "#2E4A37",
                hair: "spiky", hairColor: "#141416", hoodie: true },
    "uk-officer": { top: "#2b2e36", sleeve: "#2b2e36", pants: "#2b2e36", shoes: "#141416", hat: "none", hair: "slick",
                    hairColor: "#1b1b1f", tie: "#7d1d1d", collar: "#f4f4f4" },
    "uk-naval": { top: "#1a2340", sleeve: "#1a2340", pants: "#1a2340", shoes: "#111", hat: "peaked", hatColor: "#f4f4f4",
                  hatBand: "#1a2340", hair: "short", hairColor: "#1b1b1f", stripes: "#e8b830", buttons: "#e8b830" },
    "german-officer": { top: "#59665a", sleeve: "#59665a", pants: "#4c574d", shoes: "#141416", boots: true, hat: "peaked",
                        hatColor: "#4c574d", hatBand: "#2f3a31", hair: "short", hairColor: "#2a2420", belt: "#1d1d1d", collar: "#2f3a31" },
    "german-soldier": { top: "#5c6a5d", sleeve: "#5c6a5d", pants: "#4f5a50", shoes: "#141416", boots: true, hat: "helmet",
                        hatColor: "#6b7270", hair: "none", belt: "#1d1d1d", rifle: true },
    "spanish-official": { top: "#c9ad7c", sleeve: "#c9ad7c", pants: "#b99c6c", shoes: "#141416", hat: "peaked",
                          hatColor: "#b99c6c", hatBand: "#3b2f1f", hair: "short", hairColor: "#2a2420", belt: "#5a4630", tie: "#2a2420" },
    fisherman: { top: "#efe9dc", sleeve: "#efe9dc", vest: "#7a4a2a", pants: "#6e6660", shoes: "#141416", hat: "beret",
                 hatColor: "#232838", hair: "short", hairColor: "#3a2a1e", rolled: true },
    "dead-officer": { top: "#7a6c4c", sleeve: "#7a6c4c", pants: "#5d6648", shoes: "#141416", boots: true, hat: "none",
                      hair: "short", hairColor: "#3a2a1e", lifejacket: "#e0661f" },
  };

  // ------------------------------------------------------------------ svg helpers
  function el(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  // a part drawn in one of the three passes
  function tube(g, pass, x1, y1, x2, y2, w, color) {
    const sw = pass === "border" ? w + 2 * (OW + BW) : pass === "ink" ? w + 2 * OW : w;
    const c = pass === "border" ? BORDER : pass === "ink" ? INK : color;
    return el("line", { x1, y1, x2, y2, stroke: c, "stroke-width": sw, "stroke-linecap": "round" }, g);
  }
  function blob(g, pass, d, color, extra) {
    if (pass === "border") return el("path", { d, fill: BORDER, stroke: BORDER, "stroke-width": 2 * (OW + BW), "stroke-linejoin": "round" }, g);
    if (pass === "ink") return el("path", { d, fill: INK, stroke: INK, "stroke-width": 2 * OW, "stroke-linejoin": "round" }, g);
    return el("path", Object.assign({ d, fill: color }, extra || {}), g);
  }
  function detail(g, pass, d, color, w) {          // thin lines drawn only in the fill pass
    if (pass !== "fill") return;
    el("path", { d, fill: "none", stroke: color || INK, "stroke-width": w || 3, "stroke-linecap": "round", "stroke-linejoin": "round" }, g);
  }
  function jg(parent, name, x, y) {               // joint group: pivot at (x, y) in the parent's space
    const g = el("g", { class: "j-" + name, "data-x": x, "data-y": y, transform: `translate(${x},${y})` }, parent);
    return g;
  }

  // ------------------------------------------------------------------ body parts
  function drawLeg(g, pass, C, side) {
    const hip = jg(g, "hip" + side, SK.hipX[side === "F" ? 1 : 0], 0);
    tube(hip, pass, 0, 0, 0, SK.thigh, SK.wThigh, C.pants);
    const knee = jg(hip, "kn" + side, 0, SK.thigh);
    const shinColor = C.boots ? "#1b1b1e" : C.pants;
    tube(knee, pass, 0, 0, 0, SK.shin, SK.wShin, C.boots ? C.pants : C.pants);
    if (C.boots) tube(knee, pass, 0, SK.shin * 0.42, 0, SK.shin, SK.wShin + 3, shinColor);
    if (C.rolled && pass === "fill") tube(knee, pass, 0, SK.shin * 0.55, 0, SK.shin * 0.62, SK.wShin + 4, "#857c74");
    if (C.rolled) tube(knee, pass, 0, SK.shin * 0.64, 0, SK.shin, SK.wShin - 8, "#f2efe8");
    const ank = jg(knee, "an" + side, 0, SK.shin);
    const L = SK.footL, B = SK.footB, H = SK.footH;
    blob(ank, pass, `M${-B},${-6} Q${-B - 4},${H} ${-B + 4},${H} L${L - 6},${H} Q${L + 6},${H} ${L},${H - 10} Q${L - 4},${-2} ${L - 22},${-6} Z`, C.shoes);
    detail(ank, pass, `M${-B + 2},${H - 4} L${L - 4},${H - 4}`, "#55565e", 2.5);
  }

  function drawArm(g, pass, C, side, props) {
    const sh = jg(g, "sh" + side, SK.shX[side === "F" ? 1 : 0], SK.shoulderY);
    tube(sh, pass, 0, 0, 0, SK.upper, SK.wUpper, C.sleeve);
    if (C.stripes && pass === "fill") { /* sleeve stripes go on the forearm */ }
    const el_ = jg(sh, "el" + side, 0, SK.upper);
    tube(el_, pass, 0, 0, 0, SK.fore, SK.wFore, C.sleeve);
    if (C.stripes && pass === "fill") {
      tube(el_, pass, 0, SK.fore - 16, 0, SK.fore - 14, SK.wFore, C.stripes);
      tube(el_, pass, 0, SK.fore - 9, 0, SK.fore - 7, SK.wFore, C.stripes);
    }
    const wr = jg(el_, "wr" + side, 0, SK.fore);
    // white four-finger mitten: palm + thumb
    blob(wr, pass, `M-12,4 Q-14,22 -2,26 Q12,28 13,14 Q14,2 4,0 Q-10,-2 -12,4 Z`, "#ffffff");
    blob(wr, pass, `M10,4 Q22,2 20,12 Q18,18 11,15 Z`, "#ffffff");
    detail(wr, pass, "M-6,16 L-5,23 M0,17 L1,25 M6,15 L7,22", "#9a9aa0", 1.6);
    const p = props && props[side];
    if (p) drawProp(wr, pass, p);
  }

  function drawTorso(g, pass, C) {
    const sp = g;  // spine group
    const top = SK.shoulderY - 14;
    // body: shoulders rounded, hem covers the hips
    blob(sp, pass, `M-44,22 Q-48,-40 -42,${top + 18} Q-38,${top} -18,${top - 2} L20,${top - 2} Q40,${top} 44,${top + 18} Q50,-40 46,22 Q0,30 -44,22 Z`, C.top);
    if (pass !== "fill") return;
    if (C.hoodie) {
      blob(sp, pass, `M-30,${top - 4} Q-44,${top + 20} -26,${top + 30} Q-14,${top + 12} -4,${top + 4} Z`, "#1c2540");       // hood
      detail(sp, pass, `M-6,${top + 6} L-8,${top + 46} M8,${top + 6} L9,${top + 44}`, "#e8e8ee", 2.6);                     // strings
      detail(sp, pass, `M-26,-24 Q0,-34 26,-24 L32,4 Q0,10 -32,4 Z`, "#151d33", 3);                                        // pocket
      detail(sp, pass, `M-44,14 Q0,22 46,14`, "#151d33", 3);                                                                 // hem
    }
    if (C.vest) blob(sp, pass, `M-44,20 Q-48,-40 -40,${top + 22} L-12,${top + 6} L-6,-10 L-8,24 Z M46,20 Q50,-40 42,${top + 22} L14,${top + 6} L8,-10 L10,24 Z`, C.vest);
    if (C.collar) blob(sp, pass, `M-16,${top - 1} L0,${top + 22} L16,${top - 1} Z`, C.collar);
    if (C.tie) blob(sp, pass, `M-4,${top + 8} L4,${top + 8} L7,${top + 60} L0,${top + 70} L-7,${top + 60} Z`, C.tie);
    if (C.buttons) for (const y of [-100, -76, -52, -28]) { el("circle", { cx: -8, cy: y, r: 3.6, fill: C.buttons }, sp); el("circle", { cx: 10, cy: y, r: 3.6, fill: C.buttons }, sp); }
    if (C.belt) blob(sp, pass, `M-46,-6 Q0,2 47,-6 L47,6 Q0,14 -46,6 Z`, C.belt);
    if (C.lifejacket) blob(sp, pass, `M-40,-8 Q-46,-60 -34,${top + 14} L-10,${top + 4} L-8,-6 Z M42,-8 Q48,-60 36,${top + 14} L12,${top + 4} L10,-6 Z`, C.lifejacket);
    if (C.rifle) { /* drawn in its own back layer */ }
  }

  function drawHead(g, pass, C) {
    const neck = jg(g, "neck", 0, SK.shoulderY - 12);
    tube(neck, pass, 0, 0, 0, -SK.neck, 22, "#ffffff");
    const head = jg(neck, "head", 0, -SK.neck);
    const fx = 6, fy = -44;                       // face centre
    // hair behind the face
    if (C.hair === "spiky") blob(head, pass, `M-36,${fy - 30} L-50,${fy - 6} L-40,${fy - 2} L-50,${fy + 18} L-36,${fy + 14} L-40,${fy + 34} L-24,${fy + 22} L-14,${fy + 30} L-6,${fy - 40} Z`, C.hairColor);
    if (C.hair === "short" || C.hair === "slick") blob(head, pass, `M-34,${fy - 6} Q-40,${fy - 46} ${fx},${fy - 48} Q${fx + 38},${fy - 46} ${fx + 36},${fy - 14} L${fx + 26},${fy - 30} Q${fx},${fy - 38} -22,${fy - 22} Q-30,${fy + 6} -24,${fy + 18} Z`, C.hairColor);
    blob(head, pass, `M${fx - 36},${fy} A36,43 0 1,0 ${fx + 36},${fy} A36,43 0 1,0 ${fx - 36},${fy} Z`, "#ffffff");   // blank face
    if (C.hair === "spiky" && pass === "fill") blob(head, pass, `M-30,${fy - 30} L-38,${fy - 6} L-28,${fy - 4} L-34,${fy + 12} L-22,${fy + 6} L-20,${fy + 22} L-14,${fy - 6} Z`, C.hairColor);
    if (C.hat === "cap") {
      blob(head, pass, `M${fx - 40},${fy - 12} Q${fx - 42},${fy - 56} ${fx + 2},${fy - 58} Q${fx + 40},${fy - 56} ${fx + 40},${fy - 16} Z`, C.hatColor);
      blob(head, pass, `M${fx + 14},${fy - 20} Q${fx + 52},${fy - 26} ${fx + 74},${fy - 12} Q${fx + 54},${fy - 4} ${fx + 18},${fy - 8} Z`, C.hatColor);
      detail(head, pass, `M${fx - 2},${fy - 57} L${fx - 2},${fy - 14}`, "#1f3527", 2.2);
    }
    if (C.hat === "peaked") {                      // military peaked cap: tall front crown, flat wide top, black visor
      blob(head, pass, `M${fx - 34},${fy - 26} L${fx - 50},${fy - 62} Q${fx - 6},${fy - 82} ${fx + 56},${fy - 70} L${fx + 40},${fy - 26} Z`, C.hatColor);
      blob(head, pass, `M${fx - 36},${fy - 36} L${fx + 42},${fy - 36} L${fx + 41},${fy - 22} L${fx - 35},${fy - 22} Z`, C.hatBand || INK);
      blob(head, pass, `M${fx + 16},${fy - 24} Q${fx + 46},${fy - 22} ${fx + 62},${fy - 4} Q${fx + 40},${fy - 4} ${fx + 14},${fy - 14} Z`, "#17171c");
      if (pass === "fill") el("circle", { cx: fx + 30, cy: fy - 48, r: 5, fill: "#d9c27a" }, head);
    }
    if (C.hat === "helmet") blob(head, pass, `M${fx - 46},${fy - 2} Q${fx - 48},${fy - 64} ${fx + 2},${fy - 64} Q${fx + 50},${fy - 62} ${fx + 46},${fy - 4} L${fx + 52},${fy + 4} L${fx - 52},${fy + 4} Z`, C.hatColor);
    if (C.hat === "beret") blob(head, pass, `M${fx - 42},${fy - 20} Q${fx - 50},${fy - 60} ${fx + 6},${fy - 62} Q${fx + 58},${fy - 58} ${fx + 42},${fy - 26} Q${fx},${fy - 14} ${fx - 42},${fy - 20} Z`, C.hatColor);
  }

  // ------------------------------------------------------------------ props held in the hand (wrist space)
  function drawProp(g, pass, p) {
    if (p === "magnifier") {
      tube(g, pass, 0, 14, 0, 40, 9, "#6b4a2a");
      if (pass === "fill") { el("circle", { cx: 0, cy: 70, r: 30, fill: "#cfe7f5", "fill-opacity": 0.55, stroke: INK, "stroke-width": 7 }, g); }
      else blob(g, pass, "M-30,70 A30,30 0 1,0 30,70 A30,30 0 1,0 -30,70 Z", "#cfe7f5");
    }
    if (p === "paper") blob(g, pass, "M-8,10 L52,4 L58,80 L-2,86 Z", "#f2eada"), detail(g, pass, "M6,24 L44,20 M7,36 L45,32 M8,48 L46,44 M9,60 L36,58", "#9b9180", 2);
    if (p === "telegram") blob(g, pass, "M-8,10 L56,4 L62,78 L-2,84 Z", "#efe0b8"), detail(g, pass, "M4,18 L50,14", "#b33", 4), detail(g, pass, "M6,34 L48,30 M7,46 L49,42 M8,58 L40,56", "#8a7d5c", 2);
    if (p === "briefcase") { tube(g, pass, 0, 14, 0, 26, 6, "#111"); blob(g, pass, "M-34,26 L34,26 Q38,26 38,30 L38,74 Q38,78 34,78 L-34,78 Q-38,78 -38,74 L-38,30 Q-38,26 -34,26 Z", "#1d1d22"); detail(g, pass, "M-8,40 L8,40", "#c9a24a", 4); }
    if (p === "photo") blob(g, pass, "M-10,6 L40,0 L46,52 L-4,58 Z", "#f4f4f4"), pass === "fill" && el("path", { d: "M-4,12 L36,7 L40,40 L0,45 Z", fill: "#6c6c70" }, g);
    if (p === "letters") blob(g, pass, "M-20,8 L40,8 L40,48 L-20,48 Z", "#efe6d2"), detail(g, pass, "M-20,8 L10,30 L40,8", "#9b9180", 2.4);
    if (p === "sign") { tube(g, pass, 0, 10, 0, 30, 8, "#6b4a2a"); blob(g, pass, "M-60,30 L60,30 L60,120 L-60,120 Z", "#f6c445"); if (pass === "fill") blob(g, pass, "M0,46 L24,92 L-24,92 Z", INK), el("rect", { x: -3, y: 58, width: 6, height: 18, fill: "#f6c445" }, g); }
  }

  // ------------------------------------------------------------------ build
  function build(svg, costume, opts) {
    const C = Object.assign({}, COSTUMES[costume] || COSTUMES.narrator, (opts && opts.costume) || {});
    const props = (opts && opts.props) || {};
    const root = el("g", { class: "pp-root" }, svg);
    const layers = [
      ["armB", (g, ps) => drawArm(g, ps, C, "B", props)],
      ["rifle", (g, ps) => C.rifle && drawRifle(g, ps)],
      ["legB", (g, ps) => drawLeg(g, ps, C, "B")],
      ["legF", (g, ps) => drawLeg(g, ps, C, "F")],
      ["torso", (g, ps) => drawTorso(g, ps, C)],
      ["head", (g, ps) => drawHead(g, ps, C)],
      ["armF", (g, ps) => drawArm(g, ps, C, "F", props)],
    ];
    const needsSpine = { armB: 1, rifle: 1, torso: 1, head: 1, armF: 1 };
    for (const pass of ["border", "ink", "fill"]) {
      for (const [name, fn] of layers) {
        if (pass !== "border" && name === "rifle" && !C.rifle) continue;
        const lg = el("g", { class: `pp-${pass} pp-${name}` }, root);
        const pel = jg(lg, "pelvis", 0, 0);
        const host = needsSpine[name] ? jg(pel, "spine", 0, 0) : pel;
        fn(host, pass);
        // in the ink and fill passes a layer is drawn after the border of every layer
      }
    }
    // reorder: all borders first, then for each layer ink then fill
    const byPass = (ps, nm) => root.querySelector(`.pp-${ps}.pp-${nm}`);
    for (const [name] of layers) { const a = byPass("ink", name), b = byPass("fill", name); if (a) root.appendChild(a); if (b) root.appendChild(b); }
    const joints = {}, base = {};
    root.querySelectorAll("[class^='j-']").forEach(n => {
      const k = n.getAttribute("class").slice(2);
      (joints[k] = joints[k] || []).push(n);
      if (!(k in base)) base[k] = [+n.getAttribute("data-x"), +n.getAttribute("data-y")];
    });
    return { root, joints, base, C };
  }

  function drawRifle(g, pass) {                    // slung on the back: part of the torso, not of an arm
    tube(g, pass, -40, SK.shoulderY - 28, 2, SK.shoulderY + 122, 9, "#5a3a22");
    tube(g, pass, -44, SK.shoulderY - 42, -39, SK.shoulderY - 24, 6, "#2a2a2e");
  }

  // ------------------------------------------------------------------ pose maths
  const NEUTRAL = { x: 0, lift: 0, rot: 0, spine: 0, neck: 0, head: 0,
    shF: 4, elF: 10, wrF: 0, shB: -4, elB: 10, wrB: 0, hipF: 0, knF: 2, anF: 0, hipB: 0, knB: 2, anB: 0 };
  const KEYS = Object.keys(NEUTRAL);

  function mix(a, b, w) { const o = {}; for (const k of KEYS) o[k] = a[k] + (b[k] - a[k]) * w; return o; }
  function add(p, d) { for (const k in d) p[k] = (p[k] || 0) + d[k]; return p; }
  const smooth = x => x <= 0 ? 0 : x >= 1 ? 1 : x * x * (3 - 2 * x);
  const pulse = (u, beats, pk) => { let s = 0; for (const b of beats || []) { const x = (u - b) / (pk || 0.18); if (x > 0) s += x * Math.exp(1 - x); } return Math.min(s, 1.2); };
  const S = Math.sin, PI2 = Math.PI * 2;

  // two-bone reach: set shoulder and elbow so the hand lands on (tx, ty) in torso space
  function reach(P, side, tx, ty) {
    const sx = SK.shX[side === "F" ? 1 : 0], sy = SK.shoulderY;
    const a = SK.upper, b = SK.fore + SK.hand * 0.7;
    let dx = tx - sx, dy = ty - sy, d = Math.hypot(dx, dy);
    d = Math.min(Math.max(d, Math.abs(a - b) + 1), a + b - 1);
    const phi = Math.atan2(dx, dy) / D2R;
    const alpha = Math.acos((a * a + d * d - b * b) / (2 * a * d)) / D2R;
    const inner = Math.acos((a * a + b * b - d * d) / (2 * a * b)) / D2R;
    P["sh" + side] = phi - alpha;
    P["el" + side] = 180 - inner;
    return P;
  }

  // forward kinematics of the points that may touch the ground (for the ground snap)
  function rotp(x, y, a) { const c = Math.cos(a), s = Math.sin(a); return [x * c - y * s, x * s + y * c]; }
  function legPoints(P, side) {
    const hip = -P["hip" + side] * D2R, kn = P["kn" + side] * D2R, an = -P["an" + side] * D2R;
    const rot = P.rot * D2R;
    let a = rot + hip;
    let [x, y] = rotp(SK.hipX[side === "F" ? 1 : 0], 0, rot);
    let [dx, dy] = rotp(0, SK.thigh, a); const knee = [x + dx, y + dy];
    a += kn; [dx, dy] = rotp(0, SK.shin, a); const ankle = [knee[0] + dx, knee[1] + dy];
    a += an;
    const heel = rotp(-SK.footB + 2, SK.footH, a), toe = rotp(SK.footL, SK.footH, a);
    return [knee, [ankle[0] + heel[0], ankle[1] + heel[1]], [ankle[0] + toe[0], ankle[1] + toe[1]]];
  }
  function armPoint(P, side) {
    const rot = P.rot * D2R, sp = P.spine * D2R;
    let [x, y] = rotp(SK.shX[side === "F" ? 1 : 0], SK.shoulderY, rot + sp);
    let a = rot + sp - P["sh" + side] * D2R;
    let [dx, dy] = rotp(0, SK.upper, a); x += dx; y += dy;
    a += -P["el" + side] * D2R; [dx, dy] = rotp(0, SK.fore + SK.hand, a);
    return [x + dx, y + dy];
  }
  function headPoint(P) {
    const a = (P.rot + P.spine) * D2R;
    return rotp(0, SK.shoulderY - 12 - SK.neck - 90, a);
  }

  function apply(pp, P, groundMode) {
    // ground snap: the lowest contact point rests on y = 0 (wrapper origin = ground under the pelvis)
    let pts = [...legPoints(P, "F"), ...legPoints(P, "B")];
    if (groundMode === "all") pts = pts.concat([armPoint(P, "F"), armPoint(P, "B"), headPoint(P)]);
    let low = -1e9; for (const p of pts) low = Math.max(low, p[1]);
    const py = -low - P.lift;
    const set = (k, tr) => { const L = pp.joints[k]; if (L) for (const n of L) n.setAttribute("transform", tr); };
    const B = pp.base;
    const T = (k, ang) => `translate(${B[k][0]},${B[k][1]}) rotate(${ang.toFixed(2)})`;
    set("pelvis", `translate(${P.x.toFixed(2)},${py.toFixed(2)}) rotate(${P.rot.toFixed(2)})`);
    set("spine", `rotate(${P.spine.toFixed(2)})`);
    set("neck", T("neck", P.neck)); set("head", T("head", P.head));
    for (const s of ["F", "B"]) {
      set("sh" + s, T("sh" + s, -P["sh" + s])); set("el" + s, T("el" + s, -P["el" + s])); set("wr" + s, T("wr" + s, -P["wr" + s]));
      set("hip" + s, T("hip" + s, -P["hip" + s])); set("kn" + s, T("kn" + s, P["kn" + s])); set("an" + s, T("an" + s, -P["an" + s]));
    }
  }

  // ------------------------------------------------------------------ actions: f(u, dur, opt) -> pose
  const ACT = {};
  ACT.idle = (u, d, o) => {
    const P = Object.assign({}, NEUTRAL), b = S(PI2 * u / 3.4 + (o.seed || 0));
    P.spine += 1.2 * b; P.head += -1 * b; P.shF += 2 * b; P.shB -= 2 * b;
    P.hipF += 1.5 * S(PI2 * u / 5 + 1); P.hipB -= 1.5 * S(PI2 * u / 5 + 1);
    return P;
  };
  ACT.talk = (u, d, o) => {
    const P = ACT.idle(u, d, o), p = pulse(u, o.beats), q = pulse(u, (o.beats || []).map(b => b + 0.05));
    P.shF += 18 + 34 * p; P.elF += 40 + 40 * p; P.wrF += 20 * p;
    P.shB += 6 + 10 * q; P.elB += 20 + 20 * q;
    P.head += 5 * p; P.spine += 2 * p;
    return P;
  };
  ACT.present = (u, d, o) => {                     // open palm toward the subject, the other hand in the pocket
    const P = ACT.idle(u, d, o), p = pulse(u, o.beats);
    P.shF += 52 + 12 * p; P.elF += 38 - 10 * p; P.wrF += 35;
    P.shB = -6; P.elB = 40; P.spine += 3 + 2 * p; P.head += 3 * p;
    return P;
  };
  ACT.point = (u, d, o) => {
    const P = ACT.idle(u, d, o), p = pulse(u, o.beats), up = o.up || 0;
    const reach = smooth(u / 0.25);
    P.shF = 4 + (86 + up - 4) * reach + 5 * p; P.elF = 10 + (4 - 10) * reach; P.wrF = 4;
    P.spine += 4 * reach + 2 * p; P.head += -2 + 3 * p;
    P.shB = -8; P.elB = 20;
    return P;
  };
  ACT.pointDown = (u, d, o) => { const P = ACT.point(u, d, Object.assign({}, o, { up: -40 })); P.spine += 14; P.knF += 10; P.knB += 10; return P; };
  ACT.count = (u, d, o) => {
    const P = ACT.idle(u, d, o), p = pulse(u, o.beats);
    P.shF = 30 + 6 * p; P.elF = 95; P.wrF = 20;          // front hand forward, palm up
    P.shB = 22 + 4 * p; P.elB = 110 - 10 * p;            // back hand taps the fingers
    P.head += 6 + 4 * p; P.spine += 3;
    return P;
  };
  ACT.thumbsUp = (u, d, o) => {
    const P = ACT.idle(u, d, o), p = pulse(u, [0.1].concat(o.beats || []));
    P.shF = 40 + 25 * p; P.elF = 75 - 20 * p; P.wrF = 0;
    P.shB = -6; P.elB = 30; P.spine += -2 * p; P.lift += 6 * p;
    return P;
  };
  ACT.think = (u, d, o) => {                      // hand to the chin, slow head tilt
    const P = ACT.idle(u, d, o);
    reach(P, "F", 26, -160); P.wrF = 40;            // hand under the chin
    reach(P, "B", 18, -86);                         // supports the elbow
    P.head += 6 + 4 * S(PI2 * u / 3.6); P.neck = -3 * S(PI2 * u / 3.6); P.spine += 2;
    return P;
  };
  ACT.listen = (u, d, o) => { const P = ACT.idle(u, d, o); reach(P, "F", -14, -212); P.wrF = 60; P.neck = -8 + 3 * S(PI2 * u / 3); P.head += -4; P.spine += -3; return P; };
  ACT.search = (u, d, o) => {                     // magnifier at the eye, lean and scan
    const P = ACT.idle(u, d, o), sc = S(PI2 * u / 2.6);
    P.shF = 62 + 6 * sc; P.elF = 120 - 6 * sc; P.wrF = 10;
    P.spine += 16 + 6 * sc; P.head += 6; P.knF += 12; P.knB += 14; P.hipF += 10; P.hipB -= 4;
    P.shB = 6; P.elB = 70;
    return P;
  };
  ACT.shocked = (u, d, o) => {                    // jump back, open hands out in front ("whoa"), then tremble
    const P = Object.assign({}, NEUTRAL), j = u < 0.42 ? S(Math.PI * u / 0.42) : 0, tr = u > 0.4 ? S(PI2 * 9 * u) : 0;
    P.lift = 60 * j; P.x = -26 * smooth(u / 0.4);
    P.shF = 78 + 3 * tr; P.elF = 48; P.wrF = 70; P.shB = 96 - 3 * tr; P.elB = 52; P.wrB = 70;
    P.spine = -11 + 1.5 * tr; P.head = -8; P.knF = 34 * j + 6; P.knB = 44 * j + 6; P.hipF = 20 * j; P.hipB = -6;
    return P;
  };
  ACT.handsOnHead = (u, d, o) => {
    const P = ACT.idle(u, d, o), sh = S(PI2 * 2.2 * u) * smooth(u / 0.3);
    reach(P, "F", 14, -262); reach(P, "B", -14, -258); P.head += 8; P.neck = 8 * sh; P.spine += 4;
    return P;
  };
  ACT.refuse = (u, d, o) => {                    // "no": palm pushed forward, head shakes
    const P = ACT.idle(u, d, o), p = pulse(u, o.beats), sh = S(PI2 * 2.4 * u) * Math.min(1, 0.35 + p);
    const r = smooth(u / 0.25);
    P.shF = 4 + 78 * r + 4 * p; P.elF = 10 + 12 * r; P.wrF = 85 * r; P.shB = -4; P.elB = 24;
    P.neck = 10 * sh; P.spine += -4; P.head += -2;
    return P;
  };
  ACT.laugh = (u, d, o) => {
    const P = ACT.idle(u, d, o), b = Math.abs(S(PI2 * 3.2 * u));
    reach(P, "F", 34, -46); reach(P, "B", 14, -36);    // hands on the belly
    P.spine += -8 - 6 * b; P.head += -14 - 8 * b; P.lift += 4 * b; P.knF += 4 * b; P.knB += 4 * b;
    return P;
  };
  ACT.idea = (u, d, o) => {                      // finger up with a small hop
    const P = ACT.idle(u, d, o), j = u > 0.08 && u < 0.46 ? S(Math.PI * (u - 0.08) / 0.38) : 0;
    P.shF = 150; P.elF = 20; P.wrF = 10; P.lift = 34 * j; P.knF += 20 * j; P.knB += 26 * j; P.head += -6;
    P.shB = -6; P.elB = 30;
    return P;
  };
  ACT.fingerUp = ACT.idea;
  ACT.wide = (u, d, o) => {
    const P = ACT.idle(u, d, o), p = pulse(u, o.beats), r = smooth(u / 0.3);
    P.shF = 4 + 84 * r + 6 * p; P.elF = 8; P.wrF = 20; P.shB = -4 - 82 * r - 6 * p; P.elB = 8; P.wrB = 20;
    P.head += -4 * p; P.spine += -3;
    return P;
  };
  ACT.wave = (u, d, o) => { const P = ACT.idle(u, d, o); P.shF = 160; P.elF = 25 + 25 * S(PI2 * 2.2 * u); return P; };
  ACT.salute = (u, d, o) => {
    const P = ACT.idle(u, d, o), r = smooth(u / 0.3);
    const Q = reach(Object.assign({}, P), "F", 40, -236);
    P.shF = 4 + (Q.shF - 4) * r; P.elF = 10 + (Q.elF - 10) * r; P.wrF = 40 * r; P.spine = -2; P.head = -3; P.shB = -2; P.elB = 4;
    return P;
  };
  ACT.read = (u, d, o) => {                      // holds a paper, head nods along the lines
    const P = ACT.idle(u, d, o);
    P.shF = 38; P.elF = 100; P.wrF = 20; P.shB = 26; P.elB = 105; P.head += 14 + 3 * S(PI2 * u / 1.6); P.spine += 4;
    return P;
  };
  ACT.worried = (u, d, o) => { const P = ACT.read(u, d, o), t = S(PI2 * 8 * u); P.shF += 1.5 * t; P.shB -= 1.5 * t; P.head += 4; P.spine += 6; return P; };
  ACT.holdSign = (u, d, o) => { const P = ACT.idle(u, d, o); P.shF = 48; P.elF = 70; P.wrF = 0; P.shB = 44; P.elB = 76; return P; };

  // locomotion: cycle period chosen so the feet do not slide over the ground at the given speed
  function gait(u, o, run) {
    const P = Object.assign({}, NEUTRAL);
    const A = run ? 38 : 24;                              // hip swing amplitude
    const step = 2 * (SK.thigh + SK.shin) * Math.sin(A * D2R) * (run ? 1.25 : 0.95);   // one step length
    const speed = Math.abs(o.speed || (run ? 600 : 300));  // units per second
    const T = Math.max(run ? 0.45 : 0.75, 2 * step / Math.max(speed, 1));
    const ph = PI2 * (u / T) + (o.phase || 0);
    const sF = S(ph), sB = S(ph + Math.PI), cF = Math.cos(ph), cB = Math.cos(ph + Math.PI);
    P.hipF = A * sF; P.hipB = A * sB;
    const flex = run ? 95 : 38;
    P.knF = 6 + flex * Math.pow(Math.max(0, cF), 1.4); P.knB = 6 + flex * Math.pow(Math.max(0, cB), 1.4);
    P.anF = 6 * sF; P.anB = 6 * sB;
    const arm = run ? 34 : 20;
    P.shF = -arm * sF + (run ? 10 : 0); P.shB = -arm * sB + (run ? 10 : 0);
    P.elF = run ? 92 : 16 + 8 * Math.max(0, -sF); P.elB = run ? 92 : 16 + 8 * Math.max(0, -sB);
    P.spine = run ? 12 : 4; P.head = run ? -6 : -2;
    P.lift = run ? 22 * Math.max(0, Math.cos(2 * ph)) : 0;
    return P;
  }
  ACT.walk = (u, d, o) => gait(u, o, false);
  ACT.run = (u, d, o) => gait(u, o, true);
  ACT.crawl = (u, d, o) => {                     // on hands and knees: torso level, limbs step in diagonal pairs
    const P = Object.assign({}, NEUTRAL), T = 1.0, ph = PI2 * u / T + (o.phase || 0), a = S(ph), b = S(ph + Math.PI);
    P.rot = 80; P.spine = -4; P.neck = -20; P.head = -50;
    P.hipF = 80 + 14 * a; P.knF = 96 - 10 * a + 10 * Math.max(0, Math.cos(ph)); P.anF = 20;
    P.hipB = 80 + 14 * b; P.knB = 96 - 10 * b + 10 * Math.max(0, Math.cos(ph + Math.PI)); P.anB = 20;
    P.shF = 74 + 16 * b; P.elF = 6 + 16 * Math.max(0, Math.cos(ph + Math.PI)); P.wrF = 70;
    P.shB = 74 + 16 * a; P.elB = 6 + 16 * Math.max(0, Math.cos(ph)); P.wrB = 70;
    return P;
  };
  ACT.lie = (u, d, o) => {                       // lying still on the back, head to the left
    const P = Object.assign({}, NEUTRAL);
    P.rot = -90; P.shF = 4; P.elF = 4; P.shB = 2; P.elB = 6; P.hipF = 4; P.knF = 4; P.hipB = -2; P.knB = 6;
    P.anF = -40; P.anB = -40; P.head = -6;
    return P;
  };
  ACT.float = (u, d, o) => { const P = ACT.lie(u, d, o); P.lift = 6 * S(PI2 * u / 2.2); P.rot = -90 + 2 * S(PI2 * u / 2.9); return P; };
  ACT.fall = (u, d, o) => {                      // stumble, knees, then lying face down
    if (u < 0.35) { const P = ACT.shocked(u, d, o); return P; }
    const P = Object.assign({}, NEUTRAL), k = smooth((u - 0.35) / 0.35), l = smooth((u - 0.75) / 0.4);
    P.knF = 90 * k * (1 - l); P.knB = 90 * k * (1 - l); P.hipF = -10 * k * (1 - l); P.hipB = -10 * k * (1 - l);
    P.spine = 20 * k * (1 - l); P.rot = 90 * l; P.anF = -50 * l; P.anB = -50 * l;
    P.shF = 40 * k * (1 - l) + 150 * l; P.elF = 30; P.shB = 30 * k * (1 - l) + 160 * l; P.elB = 30; P.head = 20 * k * (1 - l) - 30 * l;
    return P;
  };
  ACT.sad = (u, d, o) => { const P = ACT.idle(u, d, o); P.head += 26; P.spine += 10; P.shF = -2; P.shB = 2; P.elF = 6; P.elB = 6; return P; };
  ACT.cheer = (u, d, o) => {
    const P = ACT.idle(u, d, o), j = Math.max(0, S(PI2 * u / 0.6)) * (u < 1.2 ? 1 : 0);
    P.shF = 160; P.elF = 30 + 30 * j; P.shB = 150; P.elB = 30 + 30 * j; P.lift = 40 * j; P.knF += 30 * j; P.knB += 30 * j; P.head -= 8;
    return P;
  };

  const GROUND_ALL = { crawl: 1, lie: 1, float: 1, fall: 1 };

  // pose at local time u for a list of segments [{t, act, opt}] with 0.22 s blends between them
  function poseAt(segs, u) {
    let k = 0; for (let i = 0; i < segs.length; i++) if (segs[i].t <= u) k = i;
    const s = segs[k], f = ACT[s.act] || ACT.idle;
    let P = f(u - s.t, 0, s.opt || {});
    if (k > 0) {
      const prev = segs[k - 1], w = smooth((u - s.t) / 0.22);
      if (w < 1) P = mix((ACT[prev.act] || ACT.idle)(u - prev.t, 0, prev.opt || {}), P, w);
    }
    return { P, ground: GROUND_ALL[s.act] ? "all" : "feet" };
  }

  window.NerdPuppet = { build, apply, poseAt, ACT, NEUTRAL, COSTUMES, SK };
})();
