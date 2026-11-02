// Drawing kit for the Shorts engine - "editorial paper" 2D style (flat colours, ink outlines, hard sticker shadows, paper grain).
// Canvas 1080x1920. Deliberately NOT the generic neon/dark/glow look.
export const W = 1080, H = 1920;
export const C = {
  paper: '#f3ead8', paper2: '#e9dcc3', ink: '#1b1f3b', ink2: '#3a3f63', white: '#fffdf8',
  red: '#e63946', yel: '#ffb703', teal: '#2a9d8f', sky: '#8ecae6', blue: '#3a6ea5', orange: '#f4845f', green: '#52b788', plum: '#7b5ea7', grey: '#8d8a83',
  // legacy names used by older code paths
  cyan: '#2a9d8f', navy: '#1b1f3b', steel: '#3a3f63', bg0: '#f3ead8', bg1: '#e9dcc3',
  skin: ['#f2c9a5', '#e0a97c', '#c68642', '#8d5524', '#ffdbb4'],
};
// mood -> [background, secondary shape colour, accent]. Light paper for most moods; ink for the dark ones.
export const MOOD = {  // mutable: setTheme() rewrites it per story
  calm: [C.paper, C.sky, C.teal], curious: [C.paper, C.yel, C.blue], tense: [C.ink, C.ink2, C.red], shock: ['#2b1d2f', '#4a2433', C.red],
  reveal: [C.paper, C.orange, C.red], sad: ['#dfe3e8', '#b8c4d0', C.blue], hopeful: [C.paper, C.green, C.teal],
};
export const isDark = mood => mood === 'tense' || mood === 'shock';
export const fg = mood => isDark(mood) ? C.white : C.ink;
export const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
export const ease = x => { x = clamp(x); return 1 - Math.pow(1 - x, 3); };
export const easeIO = x => { x = clamp(x); return x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
export const back = x => { x = clamp(x); const c = 1.70158; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
export const lerp = (a, b, k) => a + (b - a) * k;
export function rng(seed) { let s = (seed * 9301 + 49297) >>> 0 || 1; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }
export function hash(str) { let h = 2166136261; for (const ch of String(str)) { h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619); } return h >>> 0; }

export function rr(ctx, x, y, w, h, r) { ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath(); }
export function fillRR(ctx, x, y, w, h, r, fill, stroke, lw = 6) { rr(ctx, x, y, w, h, r); if (fill) { ctx.fillStyle = fill; ctx.fill(); } if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.lineJoin = 'round'; ctx.stroke(); } }
// "glow" is now a hard offset sticker shadow (flat print look), kept under the old name so every scene uses it.
export function glow(ctx, color, blur, fn) { ctx.save(); ctx.shadowColor = 'rgba(27,31,59,.28)'; ctx.shadowBlur = 0; ctx.shadowOffsetX = 10; ctx.shadowOffsetY = 12; fn(); ctx.restore(); }
export function card(ctx, x, y, w, h, fill = C.white, r = 28) { glow(ctx, 0, 0, () => fillRR(ctx, x, y, w, h, r, fill)); fillRR(ctx, x, y, w, h, r, null, C.ink, 6); }
export function font(sz, w = 800) { return `${w} ${sz}px Inter, "Inter Display", Arial, sans-serif`; }
export function text(ctx, s, x, y, sz, color = C.ink, o = {}) {
  ctx.save(); ctx.font = font(sz, o.w || 800); ctx.textAlign = o.align || 'center'; ctx.textBaseline = o.base || 'middle'; ctx.globalAlpha *= (o.a ?? 1);
  if (o.stroke) { ctx.lineWidth = o.stroke; ctx.strokeStyle = o.sc || C.ink; ctx.lineJoin = 'round'; ctx.strokeText(s, x, y); }
  ctx.fillStyle = color; ctx.fillText(s, x, y); ctx.restore();
}
export function fitText(ctx, s, maxW, sz, w = 800) { ctx.save(); ctx.font = font(sz, w); while (ctx.measureText(s).width > maxW && sz > 18) { sz -= 2; ctx.font = font(sz, w); } ctx.restore(); return sz; }
export function wrap(ctx, s, maxW, sz, w = 800) { ctx.save(); ctx.font = font(sz, w); const out = []; let cur = ''; for (const wd of String(s).split(/\s+/)) { const tr = cur ? cur + ' ' + wd : wd; if (ctx.measureText(tr).width > maxW && cur) { out.push(cur); cur = wd; } else cur = tr; } if (cur) out.push(cur); ctx.restore(); return out; }
// label tag: yellow marker box with ink text and ink border (editorial sticker)
export function pill(ctx, s, x, y, sz, bg = C.yel, fgc = C.ink, a = 1) {
  if (!s || a <= 0) return; ctx.save(); ctx.globalAlpha *= clamp(a); ctx.font = font(sz, 900); const w = ctx.measureText(s).width + sz * 1.1, h = sz * 1.6;
  ctx.translate(x, y); ctx.rotate(-.025); glow(ctx, 0, 0, () => fillRR(ctx, -w / 2, -h / 2, w, h, 12, bg)); fillRR(ctx, -w / 2, -h / 2, w, h, 12, null, C.ink, 5);
  text(ctx, s, 0, 2, sz, fgc, { w: 900 }); ctx.restore();
}
// marker highlight swipe behind a text line (draws left to right with k)
export function marker(ctx, x, y, w, h, k, color = C.yel) { if (k <= 0) return; ctx.save(); ctx.fillStyle = color; ctx.globalAlpha = .85; ctx.beginPath(); ctx.moveTo(x, y + h * .15); ctx.lineTo(x + w * k, y); ctx.lineTo(x + w * k + 6, y + h); ctx.lineTo(x - 4, y + h * .92); ctx.closePath(); ctx.fill(); ctx.restore(); }

// ---------------------------------------------------------------- background: paper + big soft shapes + grain (no grid, no glow, no particles)
let GRAIN = null;
function grain() {
  if (GRAIN) return GRAIN; const c = document.createElement('canvas'); c.width = 270; c.height = 480; const g = c.getContext('2d'), d = g.createImageData(270, 480), r = rng(11);
  for (let i = 0; i < d.data.length; i += 4) { const v = r() * 255; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 14; }
  g.putImageData(d, 0, 0); GRAIN = c; return c;
}
// Per-story look: every Short gets its own colours + background pattern (owner: "don't use the same graphics everywhere").
export const THEMES = {
  paper: { light: '#f3ead8', s1: '#8ecae6', s2: '#2a9d8f', dark: '#1b1f3b', d2: '#3a3f63', acc: '#ffb703', pat: 'blobs' },
  mint:  { light: '#dff3e4', s1: '#9ad1b0', s2: '#2a9d8f', dark: '#123c3a', d2: '#1f5a55', acc: '#ffb703', pat: 'dots' },
  lilac: { light: '#ece4f7', s1: '#c3b1e1', s2: '#7b5ea7', dark: '#2a1f45', d2: '#41336b', acc: '#ffb703', pat: 'stripes' },
  sky:   { light: '#e3f1fb', s1: '#8ecae6', s2: '#3a6ea5', dark: '#10243f', d2: '#21406a', acc: '#ffb703', pat: 'grid' },
  peach: { light: '#fde8dc', s1: '#f4a582', s2: '#e63946', dark: '#3b1b1b', d2: '#5c2a2a', acc: '#ffd166', pat: 'halftone' },
  news:  { light: '#efefea', s1: '#cfcfc6', s2: '#8d8a83', dark: '#1d1d1f', d2: '#3a3a3e', acc: '#e63946', pat: 'lines' },
  sun:   { light: '#fff3c4', s1: '#ffd166', s2: '#f4845f', dark: '#2d2340', d2: '#47385f', acc: '#e63946', pat: 'rays' },
};
export let THEME = THEMES.paper;
export function setTheme(name) {
  THEME = THEMES[name] || THEMES.paper; const T = THEME;
  Object.assign(MOOD, { calm: [T.light, T.s1, T.s2], curious: [T.light, T.acc, T.s2], tense: [T.dark, T.d2, C.red], shock: [T.dark, T.d2, C.red],
    reveal: [T.light, C.orange, C.red], sad: [shade(T.light, .93), T.s1, C.blue], hopeful: [T.light, C.green, T.s2] });
}
function pattern(ctx, t, col, a) {
  const P = THEME.pat; ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = col; ctx.strokeStyle = col;
  if (P === 'dots') { const o = (t * 12) % 60; for (let y = -60; y < H + 60; y += 60) for (let x = (y / 60 % 2) * 30 - 60; x < W + 60; x += 60) { ctx.beginPath(); ctx.arc(x + o, y + o, 7, 0, 6.283); ctx.fill(); } }
  else if (P === 'stripes') { ctx.lineWidth = 34; const o = (t * 20) % 120; for (let x = -H; x < W + H; x += 120) { ctx.beginPath(); ctx.moveTo(x + o, 0); ctx.lineTo(x + o + H * .5, H); ctx.stroke(); } }
  else if (P === 'grid') { ctx.lineWidth = 3; const o = (t * 10) % 90; for (let x = -90; x < W + 90; x += 90) { ctx.beginPath(); ctx.moveTo(x + o, 0); ctx.lineTo(x + o, H); ctx.stroke(); } for (let y = -90; y < H + 90; y += 90) { ctx.beginPath(); ctx.moveTo(0, y + o); ctx.lineTo(W, y + o); ctx.stroke(); } }
  else if (P === 'halftone') { for (let y = 0; y < H; y += 46) for (let x = (y / 46 % 2) * 23; x < W; x += 46) { const r = 3 + 11 * (y / H) * (.75 + .25 * Math.sin(t + x * .01)); ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.fill(); } }
  else if (P === 'lines') { ctx.lineWidth = 2; for (let y = 40; y < H; y += 34) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); } ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(70, 0); ctx.lineTo(70, H); ctx.stroke(); }
  else if (P === 'rays') { ctx.translate(W / 2, 820); ctx.rotate(t * .05); for (let i = 0; i < 16; i++) { ctx.rotate(Math.PI / 8); ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(1800, -170); ctx.lineTo(1800, 170); ctx.fill(); } }
  ctx.restore();
}
export function background(ctx, t, mood, seed) {
  const m = MOOD[mood] || MOOD.calm; ctx.fillStyle = m[0]; ctx.fillRect(0, 0, W, H);
  const dark = isDark(mood);
  if (THEME.pat !== 'blobs') pattern(ctx, t, dark ? m[1] : m[1], dark ? .35 : .45);
  const r = rng(seed || 7); ctx.save();
  for (let i = 0; i < (THEME.pat === 'blobs' ? 3 : 1); i++) {
    const x = r() * W, y = 300 + r() * 1100, rad = 260 + r() * 260, dx = Math.sin(t * .25 + i) * 30, dy = Math.cos(t * .2 + i * 2) * 24;
    ctx.globalAlpha = dark ? .5 : .22; ctx.fillStyle = dark ? m[1] : (i === 1 ? m[2] : m[1]); ctx.beginPath();
    if (i === 2) { ctx.save(); ctx.translate(x + dx, y + dy); ctx.rotate(.3 + t * .03); ctx.fillRect(-rad * .6, -rad * .6, rad * 1.2, rad * 1.2); ctx.restore(); }
    else { ctx.arc(x + dx, y + dy, rad, 0, 6.283); ctx.fill(); }
  }
  ctx.globalAlpha = 1; ctx.drawImage(grain(), 0, 0, W, H); ctx.restore();
}
// ---------------------------------------------------------------- isometric helpers (semi-3D with ink edges)
export function isoP(ox, oy, u, x, y, z) { return [ox + (x - y) * u * 0.866, oy + (x + y) * u * 0.5 - z * u]; }
export function shade(hex, k) { const n = parseInt(hex.slice(1), 16); let r = n >> 16, g = (n >> 8) & 255, b = n & 255; r = Math.round(clamp(r * k, 0, 255)); g = Math.round(clamp(g * k, 0, 255)); b = Math.round(clamp(b * k, 0, 255)); return '#' + ((1 << 24) | (r << 16) | (g << 8) | b).toString(16).slice(1); }
export function isoBox(ctx, ox, oy, u, x, y, z, w, d, h, col, o = {}) {
  const P = (a, b, c) => isoP(ox, oy, u, a, b, c);
  const top = [P(x, y, z + h), P(x + w, y, z + h), P(x + w, y + d, z + h), P(x, y + d, z + h)];
  const left = [P(x, y + d, z), P(x + w, y + d, z), P(x + w, y + d, z + h), P(x, y + d, z + h)];
  const right = [P(x + w, y, z), P(x + w, y + d, z), P(x + w, y + d, z + h), P(x + w, y, z + h)];
  const edge = o.edge === undefined ? C.ink : o.edge;
  const poly = (pts, c) => { ctx.beginPath(); ctx.moveTo(...pts[0]); for (const p of pts.slice(1)) ctx.lineTo(...p); ctx.closePath(); ctx.fillStyle = c; ctx.fill(); if (edge) { ctx.strokeStyle = edge; ctx.lineWidth = o.lw || 4; ctx.lineJoin = 'round'; ctx.stroke(); } };
  poly(left, o.left || shade(col, .9)); poly(right, o.right || shade(col, .72)); poly(top, o.top || shade(col, 1.08));
  return { top, left, right };
}
export function isoWindows(ctx, ox, oy, u, x, y, z, w, d, h, face, cols, rows, t, seed, lit = '#ffd27a', dark = '#2d3557') {
  const r = rng(seed); const P = (a, b, c) => isoP(ox, oy, u, a, b, c);
  for (let i = 0; i < cols; i++) for (let j = 0; j < rows; j++) {
    const on = r() < .5 ? (Math.sin(t * 1.1 + i * 3 + j * 7) > -.9) : false, c = on ? lit : dark;
    const fw = (face === 'left' ? w : d) / cols, fh = h / rows, a0 = i * fw + fw * .25, a1 = (i + 1) * fw - fw * .25, z0 = z + j * fh + fh * .28, z1 = z + (j + 1) * fh - fh * .22;
    const q = face === 'left' ? [P(x + a0, y + d, z0), P(x + a1, y + d, z0), P(x + a1, y + d, z1), P(x + a0, y + d, z1)] : [P(x + w, y + a0, z0), P(x + w, y + a1, z0), P(x + w, y + a1, z1), P(x + w, y + a0, z1)];
    ctx.beginPath(); ctx.moveTo(...q[0]); for (const p of q.slice(1)) ctx.lineTo(...p); ctx.closePath(); ctx.fillStyle = c; ctx.fill(); ctx.strokeStyle = C.ink; ctx.lineWidth = 2; ctx.stroke();
  }
}
export function floorDisc(ctx, x, y, rx, color, a = .35) { ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = color; ctx.beginPath(); ctx.ellipse(x, y, rx, rx * .3, 0, 0, 6.283); ctx.fill(); ctx.restore(); }
export function shadow(ctx, x, y, rx) { ctx.save(); ctx.fillStyle = 'rgba(27,31,59,.22)'; ctx.beginPath(); ctx.ellipse(x, y, rx, rx * .22, 0, 0, 6.283); ctx.fill(); ctx.restore(); }
// time (seconds into the shot) when the narrator says a word containing `needle`; fallback if not found
export function cue(v, needle, fallback) {
  const w = v && v.w; if (!w || needle == null) return fallback;
  const n = String(needle).toLowerCase().replace(/[^a-z0-9$]/g, ''); if (!n) return fallback;
  for (const [word, tt] of w) { const x = word.replace(/[^a-z0-9$]/g, ''); if (x && (x.includes(n) || n.includes(x) && x.length > 3)) return tt; }
  return fallback;
}
// Draw fn() with a solid ink outline around its silhouette (sticker look) - used for people and hero icons.
let _oc = null, _sc = null;
export function outlined(ctx, fn, px = 7, col = '#1b1f3b') {
  if (!_oc) { _oc = new OffscreenCanvas(W, H); _sc = new OffscreenCanvas(W, H); }
  const o = _oc.getContext('2d'), s = _sc.getContext('2d'); o.setTransform(1, 0, 0, 1, 0, 0); o.clearRect(0, 0, W, H); o.setTransform(ctx.getTransform()); fn(o);
  s.setTransform(1, 0, 0, 1, 0, 0); s.clearRect(0, 0, W, H); s.globalCompositeOperation = 'source-over'; s.drawImage(_oc, 0, 0); s.globalCompositeOperation = 'source-in'; s.fillStyle = col; s.fillRect(0, 0, W, H); s.globalCompositeOperation = 'source-over';
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
  for (let i = 0; i < 12; i++) { const a = i / 12 * 6.283; ctx.drawImage(_sc, Math.cos(a) * px, Math.sin(a) * px); }
  ctx.drawImage(_oc, 0, 0); ctx.restore();
}
