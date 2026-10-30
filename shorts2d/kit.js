// Drawing kit for the 2D / semi-3D (isometric) Shorts engine. Canvas 1080x1920.
export const W = 1080, H = 1920;
export const C = { bg0: '#0b1226', bg1: '#050913', ink: '#0a0f1e', navy: '#16213f', steel: '#2a3a63', cyan: '#2ad0ff', blue: '#3d7bff', red: '#ff3b4e', yel: '#ffd400', green: '#2bff88', white: '#ffffff', grey: '#9aa6c4', paper: '#f2efe6', skin: ['#f2c9a5', '#e0a97c', '#c68642', '#8d5524', '#ffdbb4'] };
export const MOOD = { calm: ['#0d1a36', '#060b18', '#2ad0ff'], curious: ['#0d1f3a', '#060c18', '#2ad0ff'], tense: ['#2a0f22', '#0c0610', '#ff3b4e'], shock: ['#3a0d16', '#100508', '#ff3b4e'], reveal: ['#0a2a33', '#041015', '#ffd400'], sad: ['#151a2c', '#07090f', '#7d8fb8'], hopeful: ['#0e2b3a', '#06121a', '#2bff88'] };
export const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
export const ease = x => { x = clamp(x); return 1 - Math.pow(1 - x, 3); };
export const easeIO = x => { x = clamp(x); return x * x * (3 - 2 * x); };
export const back = x => { x = clamp(x); const c = 1.70158; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
export const lerp = (a, b, k) => a + (b - a) * k;
export function rng(seed) { let s = (seed * 9301 + 49297) >>> 0 || 1; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }
export function hash(str) { let h = 2166136261; for (const ch of String(str)) { h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619); } return h >>> 0; }

export function rr(ctx, x, y, w, h, r) { ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath(); }
export function fillRR(ctx, x, y, w, h, r, fill, stroke, lw = 3) { rr(ctx, x, y, w, h, r); if (fill) { ctx.fillStyle = fill; ctx.fill(); } if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.stroke(); } }
export function glow(ctx, color, blur, fn) { ctx.save(); ctx.shadowColor = color; ctx.shadowBlur = blur; fn(); ctx.restore(); }
export function font(sz, w = 800) { return `${w} ${sz}px Inter, "Inter Display", Arial, sans-serif`; }
export function text(ctx, s, x, y, sz, color = C.white, o = {}) {
  ctx.save(); ctx.font = font(sz, o.w || 800); ctx.textAlign = o.align || 'center'; ctx.textBaseline = o.base || 'middle'; ctx.globalAlpha *= (o.a ?? 1);
  if (o.stroke) { ctx.lineWidth = o.stroke; ctx.strokeStyle = o.sc || 'rgba(0,0,0,.85)'; ctx.lineJoin = 'round'; ctx.strokeText(s, x, y); }
  ctx.fillStyle = color; ctx.fillText(s, x, y); ctx.restore();
}
export function fitText(ctx, s, maxW, sz, w = 800) { ctx.save(); ctx.font = font(sz, w); while (ctx.measureText(s).width > maxW && sz > 18) { sz -= 2; ctx.font = font(sz, w); } ctx.restore(); return sz; }
export function wrap(ctx, s, maxW, sz, w = 800) { ctx.save(); ctx.font = font(sz, w); const out = []; let cur = ''; for (const wd of String(s).split(/\s+/)) { const tr = cur ? cur + ' ' + wd : wd; if (ctx.measureText(tr).width > maxW && cur) { out.push(cur); cur = wd; } else cur = tr; } if (cur) out.push(cur); ctx.restore(); return out; }
export function pill(ctx, s, x, y, sz, bg = C.yel, fg = '#0a0a0a', a = 1) {
  if (!s) return; ctx.save(); ctx.globalAlpha *= a; ctx.font = font(sz, 900); const w = ctx.measureText(s).width + sz * 1.3, h = sz * 1.75;
  glow(ctx, 'rgba(0,0,0,.5)', 24, () => fillRR(ctx, x - w / 2, y - h / 2, w, h, h / 2, bg)); text(ctx, s, x, y + 1, sz, fg, { w: 900 }); ctx.restore();
}
// ---------------------------------------------------------------- background
export function background(ctx, t, mood, seed) {
  const m = MOOD[mood] || MOOD.calm, g = ctx.createRadialGradient(W / 2, 760, 80, W / 2, 900, 1300); g.addColorStop(0, m[0]); g.addColorStop(1, m[1]); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.save(); ctx.globalAlpha = .10; ctx.strokeStyle = m[2]; ctx.lineWidth = 2; const off = (t * 18) % 90;
  for (let x = -90; x < W + 90; x += 90) { ctx.beginPath(); ctx.moveTo(x + off * .0, 0); ctx.lineTo(x, H); ctx.stroke(); }
  for (let y = -90; y < H + 90; y += 90) { ctx.beginPath(); ctx.moveTo(0, y + off); ctx.lineTo(W, y + off); ctx.stroke(); }
  ctx.restore();
  const r = rng(seed || 7); ctx.save(); ctx.fillStyle = m[2];
  for (let i = 0; i < 46; i++) { const x = (r() * W + t * (8 + r() * 26)) % W, y = (r() * H - t * (10 + r() * 30) + H * 4) % H, s = 1.5 + r() * 3.5; ctx.globalAlpha = .12 + r() * .35; ctx.beginPath(); ctx.arc(x, y, s, 0, 6.283); ctx.fill(); }
  ctx.restore();
}
// ---------------------------------------------------------------- isometric helpers (semi-3D)
export function isoP(ox, oy, u, x, y, z) { return [ox + (x - y) * u * 0.866, oy + (x + y) * u * 0.5 - z * u]; }
export function shade(hex, k) { const n = parseInt(hex.slice(1), 16); let r = n >> 16, g = (n >> 8) & 255, b = n & 255; r = Math.round(clamp(r * k, 0, 255)); g = Math.round(clamp(g * k, 0, 255)); b = Math.round(clamp(b * k, 0, 255)); return '#' + ((1 << 24) | (r << 16) | (g << 8) | b).toString(16).slice(1); }
export function isoBox(ctx, ox, oy, u, x, y, z, w, d, h, col, o = {}) {
  const P = (a, b, c) => isoP(ox, oy, u, a, b, c);
  const top = [P(x, y, z + h), P(x + w, y, z + h), P(x + w, y + d, z + h), P(x, y + d, z + h)];
  const left = [P(x, y + d, z), P(x + w, y + d, z), P(x + w, y + d, z + h), P(x, y + d, z + h)];
  const right = [P(x + w, y, z), P(x + w, y + d, z), P(x + w, y + d, z + h), P(x + w, y, z + h)];
  const poly = (pts, c) => { ctx.beginPath(); ctx.moveTo(...pts[0]); for (const p of pts.slice(1)) ctx.lineTo(...p); ctx.closePath(); ctx.fillStyle = c; ctx.fill(); if (o.edge) { ctx.strokeStyle = o.edge; ctx.lineWidth = 1.5; ctx.stroke(); } };
  poly(left, o.left || shade(col, .78)); poly(right, o.right || shade(col, .58)); poly(top, o.top || shade(col, 1.12));
  return { top, left, right };
}
// window grid on an iso face. face: 'left' (y+d plane) or 'right' (x+w plane)
export function isoWindows(ctx, ox, oy, u, x, y, z, w, d, h, face, cols, rows, t, seed, lit = '#ffd27a', dark = '#1b2540') {
  const r = rng(seed); const P = (a, b, c) => isoP(ox, oy, u, a, b, c);
  for (let i = 0; i < cols; i++) for (let j = 0; j < rows; j++) {
    const on = r() < .55 ? (Math.sin(t * 1.3 + i * 3 + j * 7) > -.85) : false, c = on ? lit : dark;
    const fw = (face === 'left' ? w : d) / cols, fh = h / rows, a0 = i * fw + fw * .22, a1 = (i + 1) * fw - fw * .22, z0 = z + j * fh + fh * .25, z1 = z + (j + 1) * fh - fh * .2;
    const q = face === 'left' ? [P(x + a0, y + d, z0), P(x + a1, y + d, z0), P(x + a1, y + d, z1), P(x + a0, y + d, z1)] : [P(x + w, y + a0, z0), P(x + w, y + a1, z0), P(x + w, y + a1, z1), P(x + w, y + a0, z1)];
    ctx.beginPath(); ctx.moveTo(...q[0]); for (const p of q.slice(1)) ctx.lineTo(...p); ctx.closePath(); ctx.fillStyle = c; ctx.fill();
  }
}
export function floorDisc(ctx, x, y, rx, color, a = .35) { ctx.save(); const g = ctx.createRadialGradient(x, y, 10, x, y, rx); g.addColorStop(0, color); g.addColorStop(1, 'rgba(0,0,0,0)'); ctx.globalAlpha = a; ctx.fillStyle = g; ctx.beginPath(); ctx.ellipse(x, y, rx, rx * .32, 0, 0, 6.283); ctx.fill(); ctx.restore(); }
export function shadow(ctx, x, y, rx) { ctx.save(); ctx.fillStyle = 'rgba(0,0,0,.35)'; ctx.beginPath(); ctx.ellipse(x, y, rx, rx * .22, 0, 0, 6.283); ctx.fill(); ctx.restore(); }
