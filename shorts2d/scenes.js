// Scene kinds for the Shorts engine (see docs/SHORTS_SPEC.md). Each: (ctx, v, t, dur, acc, seed). Stage area y 260..1180 (captions sit below).
import { W, C, ease, easeIO, back, clamp, lerp, rng, hash, rr, fillRR, glow, text, fitText, wrap, pill, isoP, isoBox, isoWindows, floorDisc, shadow, shade } from './kit.js';
import { person } from './people.js';
import { drawIcon } from './icons.js';

const CX = 540;
const pop = (t, d = 0, len = .5) => back((t - d) / len);
const topText = (ctx, s, t, color = C.white) => { if (!s) return; const sz = fitText(ctx, s.toUpperCase(), 940, 72, 900); text(ctx, s.toUpperCase(), CX, 330, sz, color, { w: 900, a: ease(t / .35), stroke: 10 }); };
function panel(ctx, x, y, w, h, a = 1) { ctx.save(); ctx.globalAlpha *= a; glow(ctx, 'rgba(0,0,0,.6)', 40, () => fillRR(ctx, x, y, w, h, 34, 'rgba(10,16,32,.92)')); fillRR(ctx, x, y, w, h, 34, null, 'rgba(120,170,255,.35)', 3); ctx.restore(); }
function callout(ctx, s, x, y, t, d = .5, color = C.green) {
  if (!s) return; const k = pop(t, d); if (k <= 0) return; ctx.save(); ctx.translate(x, y); ctx.scale(k, k);
  const sz = fitText(ctx, s, 720, 54, 800); ctx.font = `800 ${sz}px monospace`; const w = Math.min(860, ctx.measureText(s).width + 90);
  glow(ctx, color, 30, () => fillRR(ctx, -w / 2, -60, w, 120, 26, '#061018')); fillRR(ctx, -w / 2, -60, w, 120, 26, null, color, 4);
  const shown = s.slice(0, Math.floor(clamp((t - d) / .9) * s.length)); ctx.fillStyle = color; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(shown + (Math.sin(t * 9) > 0 ? '▌' : ' '), 0, 4); ctx.restore();
}
function counterNum(v, k) { const n = v * k; return v >= 1000 ? Math.round(n).toLocaleString('en-US') : (v % 1 ? n.toFixed(1) : Math.round(n).toString()); }

// ---------------------------------------------------------------- building (semi-3D isometric)
const BUILD = {
  bank: { col: '#c9c1ad', w: 7, d: 5, h: 5.2 }, fbi: { col: '#8e939e', w: 8, d: 5, h: 7.5 }, office: { col: '#3c5c8f', w: 5, d: 5, h: 11 }, hospital: { col: '#e8edf3', w: 7, d: 5, h: 6 },
  government: { col: '#d8d2c2', w: 8, d: 5, h: 5 }, factory: { col: '#7a6a5a', w: 8, d: 6, h: 4 }, police: { col: '#3d5a8f', w: 7, d: 5, h: 5 }, airport: { col: '#cfd8e6', w: 9, d: 5, h: 3.2 },
  school: { col: '#c87a4a', w: 8, d: 5, h: 4.5 }, studio: { col: '#5a4a7a', w: 8, d: 6, h: 5 }, power: { col: '#9aa6b5', w: 7, d: 5, h: 4 },
};
function building(ctx, v, t, dur, acc, seed) {
  const B = BUILD[v.type] || BUILD.office, u = 62 * (.9 + .1 * ease(t / 1.2)), ox = CX - (B.w - B.d) * u * .433, oy = 1040 - (B.w + B.d) * u * .25 + 40, k = ease(t / .7);
  floorDisc(ctx, CX, 1060, 520, acc, .35);
  isoBox(ctx, ox, oy, u, -1, -1, 0, B.w + 2, B.d + 2, .25, '#2a3350');
  const h = B.h * (.3 + .7 * k);
  isoBox(ctx, ox, oy, u, 0, 0, .25, B.w, B.d, h, B.col);
  const cols = Math.max(3, Math.round(B.w * 1.1)), rows = Math.max(2, Math.round(h / 1.1));
  if (v.type !== 'bank' && v.type !== 'government') { isoWindows(ctx, ox, oy, u, 0, 0, .25, B.w, B.d, h, 'left', cols, rows, t, seed); isoWindows(ctx, ox, oy, u, 0, 0, .25, B.w, B.d, h, 'right', Math.round(B.d * 1.1), rows, t, seed + 3); }
  if (v.type === 'bank' || v.type === 'government') {
    for (let i = 0; i < 6; i++) isoBox(ctx, ox, oy, u, .5 + i * (B.w - 1) / 5, B.d + .15, .25, .38, .38, h * .82, '#ece6d6');
    isoBox(ctx, ox, oy, u, -.2, -.2, .25 + h * .82, B.w + .4, B.d + .7, h * .18, '#e2dccb');
    if (v.type === 'government') { ctx.fillStyle = '#e8e2d2'; const [dx, dy] = isoP(ox, oy, u, B.w / 2, B.d / 2, .25 + h + 1.1); ctx.beginPath(); ctx.ellipse(dx, dy, u * 1.6, u * 1.4, 0, Math.PI, 0); ctx.fill(); }
    else { const a = isoP(ox, oy, u, -.2, B.d + .5, .25 + h), b = isoP(ox, oy, u, B.w + .2, B.d + .5, .25 + h), c = isoP(ox, oy, u, B.w / 2, B.d + .5, .25 + h + 1.4); ctx.beginPath(); ctx.moveTo(...a); ctx.lineTo(...b); ctx.lineTo(...c); ctx.closePath(); ctx.fillStyle = '#f0eadb'; ctx.fill(); }
  }
  if (v.type === 'hospital') { const [x, y] = isoP(ox, oy, u, B.w / 2, B.d, .25 + h * .78); ctx.fillStyle = C.red; ctx.fillRect(x - 40, y - 12, 80, 24); ctx.fillRect(x - 12, y - 40, 24, 80); }
  if (v.type === 'factory' || v.type === 'power') for (let i = 0; i < 2; i++) { isoBox(ctx, ox, oy, u, 1 + i * 3, 1, .25 + h, .9, .9, 3.2, '#6b5a4c'); for (let p = 0; p < 4; p++) { const [sx, sy] = isoP(ox, oy, u, 1.45 + i * 3, 1.45, .25 + h + 3.4 + ((t * .6 + p * .25) % 1) * 3); ctx.fillStyle = `rgba(200,200,210,${.35 - p * .07})`; ctx.beginPath(); ctx.arc(sx + p * 14, sy, 30 + p * 14, 0, 6.283); ctx.fill(); } }
  if (v.type === 'airport') { isoBox(ctx, ox, oy, u, B.w - 1.5, 1, .25 + h, 1, 1, 4, '#cfd8e6'); isoBox(ctx, ox, oy, u, B.w - 1.9, .6, .25 + h + 4, 1.8, 1.8, .8, '#7fb0d8'); }
  if (v.type === 'fbi' || v.type === 'police') for (const s of [0, 1]) { const [fx, fy] = isoP(ox, oy, u, s ? B.w + .6 : -.6, B.d + 1.2, .25); ctx.fillStyle = '#c9ced8'; ctx.fillRect(fx - 3, fy - 300, 6, 300); ctx.fillStyle = s ? '#b22234' : '#3c3b6e'; const wv = Math.sin(t * 4 + s) * 8; ctx.beginPath(); ctx.moveTo(fx + 3, fy - 300); ctx.quadraticCurveTo(fx + 50, fy - 290 + wv, fx + 100, fy - 300); ctx.lineTo(fx + 100, fy - 240); ctx.quadraticCurveTo(fx + 50, fy - 230 + wv, fx + 3, fy - 240); ctx.closePath(); ctx.fill(); }
  // door glow
  const d1 = isoP(ox, oy, u, B.w / 2 - .6, B.d, .25), d2 = isoP(ox, oy, u, B.w / 2 + .6, B.d, .25), d3 = isoP(ox, oy, u, B.w / 2 + .6, B.d, 1.9), d4 = isoP(ox, oy, u, B.w / 2 - .6, B.d, 1.9);
  ctx.beginPath(); ctx.moveTo(...d1); ctx.lineTo(...d2); ctx.lineTo(...d3); ctx.lineTo(...d4); ctx.closePath(); ctx.fillStyle = '#ffd27a'; ctx.fill();
  // name sign
  if (v.name) { const k2 = pop(t, .45); if (k2 > 0) { ctx.save(); ctx.translate(CX, 470); ctx.scale(k2, k2); const sz = fitText(ctx, v.name.toUpperCase(), 820, 62, 900); ctx.font = `900 ${sz}px Inter, Arial`; const w = ctx.measureText(v.name.toUpperCase()).width + 90; glow(ctx, 'rgba(0,0,0,.6)', 30, () => fillRR(ctx, -w / 2, -58, w, 116, 22, '#0d1530')); fillRR(ctx, -w / 2, -58, w, 116, 22, null, acc, 4); text(ctx, v.name.toUpperCase(), 0, 2, sz, C.white, { w: 900 }); ctx.restore(); } }
}

// ---------------------------------------------------------------- office desk scene
function deskFront(ctx, y, t, screenColor = C.cyan) {
  glow(ctx, 'rgba(0,0,0,.5)', 30, () => fillRR(ctx, 110, y, 860, 56, 14, '#3a4a72')); fillRR(ctx, 150, y + 56, 780, 300, 10, '#2a3656'); fillRR(ctx, 110, y, 860, 16, 10, '#4b5d8c');
  // monitor seen from the side-back, on the right
  ctx.save(); ctx.translate(800, y); fillRR(ctx, -20, -40, 40, 40, 6, '#1c2438'); ctx.beginPath(); ctx.moveTo(-150, -300); ctx.lineTo(120, -330); ctx.lineTo(120, -60); ctx.lineTo(-150, -80); ctx.closePath(); ctx.fillStyle = '#1c2438'; ctx.fill();
  ctx.globalAlpha = .55; glow(ctx, screenColor, 70, () => { ctx.beginPath(); ctx.moveTo(-150, -300); ctx.lineTo(-170, -290); ctx.lineTo(-170, -90); ctx.lineTo(-150, -80); ctx.closePath(); ctx.fillStyle = screenColor; ctx.fill(); }); ctx.restore();
  // keyboard + mug
  fillRR(ctx, 330, y - 22, 300, 26, 8, '#1c2438'); fillRR(ctx, 200, y - 70, 60, 70, 12, '#e9e2d0'); ctx.strokeStyle = '#e9e2d0'; ctx.lineWidth = 10; ctx.beginPath(); ctx.arc(258, y - 36, 18, -1.3, 1.3); ctx.stroke();
}
function office(ctx, v, t, dur, acc, seed) {
  floorDisc(ctx, CX, 1120, 560, acc, .3);
  const who = v.who || 'worker', act = v.action || 'type', alarm = act === 'shock';
  fillRR(ctx, 90, 420, 900, 420, 20, '#0e1834'); const r = rng(seed); for (let i = 0; i < 26; i++) { const bx = 110 + r() * 840, bh = 80 + r() * 260; ctx.fillStyle = '#16244a'; ctx.fillRect(bx, 840 - bh, 40 + r() * 50, bh); for (let k = 0; k < 4; k++) if (r() < .5) { ctx.fillStyle = 'rgba(255,210,120,.6)'; ctx.fillRect(bx + 8 + r() * 24, 840 - bh + 14 + r() * (bh - 30), 8, 10); } }
  fillRR(ctx, 90, 420, 900, 420, 20, null, '#2a3a63', 8); ctx.fillStyle = '#2a3a63'; ctx.fillRect(536, 420, 8, 420);
  const pose = { type: 'type', phone: 'phone', shock: 'shock', think: 'think', sleep: 'sleep' }[act] || 'type';
  person(ctx, 470, 1190, 760, who, pose, t, { seed });
  deskFront(ctx, 925, t, alarm ? C.red : C.cyan);
  if (alarm) { ctx.save(); ctx.globalAlpha = .16 + .12 * Math.sin(t * 10); ctx.fillStyle = C.red; ctx.fillRect(0, 0, W, 1920); ctx.restore(); }
  callout(ctx, v.screen, CX, 330, t, .35, alarm ? C.red : C.green);
}

// ---------------------------------------------------------------- hacker den
function hacker(ctx, v, t, dur, acc, seed) {
  ctx.save(); ctx.fillStyle = 'rgba(0,0,0,.5)'; ctx.fillRect(0, 0, W, 1920); ctx.restore();
  const n = clamp(v.count || 1, 1, 3), xs = n === 1 ? [CX] : n === 2 ? [330, 750] : [230, 540, 850], hh = n === 1 ? 820 : n === 2 ? 700 : 600;
  glow(ctx, C.green, 120, () => { ctx.fillStyle = 'rgba(43,255,136,.08)'; ctx.fillRect(0, 700, W, 400); });
  xs.forEach((x, i) => { person(ctx, x, 1130, hh, 'hacker', 'type', t + i * .7, { seed: seed + i }); });
  xs.forEach((x, i) => { const w = n === 1 ? 460 : 300; fillRR(ctx, x - w / 2, 905, w, 30, 10, '#2b3346'); ctx.beginPath(); ctx.moveTo(x - w / 2 + 20, 905); ctx.lineTo(x + w / 2 - 20, 905); ctx.lineTo(x + w / 2 - 50, 905 - w * .55); ctx.lineTo(x - w / 2 + 50, 905 - w * .55); ctx.closePath(); ctx.fillStyle = '#1c2230'; ctx.fill(); glow(ctx, C.green, 40, () => { ctx.fillStyle = C.green; ctx.beginPath(); ctx.arc(x, 905 - w * .28, 16, 0, 6.283); ctx.fill(); }); });
  fillRR(ctx, 60, 935, 960, 40, 10, '#151a26');
  for (let i = 0; i < 14; i++) { const r = rng(seed + i * 9)(); const x = 60 + i * 70, y = (r * 600 + t * 120 * (0.6 + r)) % 700 + 360; text(ctx, (hash(i + Math.floor(t * 4)) % 2 ? '1' : '0'), x, y, 34, 'rgba(43,255,136,.35)', { w: 700 }); }
  callout(ctx, v.screen, CX, 330, t, .4, C.green);
}

// ---------------------------------------------------------------- server room (iso racks)
function servers(ctx, v, t, dur, acc, seed) {
  const st = v.state || 'ok', u = 46, ox = CX, oy = 610, r = rng(seed);
  isoBox(ctx, ox, oy, u, -1, -1, 0, 12, 12, .2, '#182340');
  const blink = st === 'alarm' && Math.sin(t * 10) > 0;
  for (let row = 0; row < 3; row++) for (let i = 0; i < 4; i++) {
    const x = 1 + i * 2.4, y = 1 + row * 3.4; isoBox(ctx, ox, oy, u, x, y, .2, 1.6, 1.4, 5, st === 'dark' ? '#141a28' : '#232f4d');
    for (let k = 0; k < 9; k++) { const [lx, ly] = isoP(ox, oy, u, x + .3 + (k % 3) * .45, y + 1.4, .9 + Math.floor(k / 3) * 1.4); const on = r() < .8; ctx.fillStyle = st === 'dark' ? '#1b2132' : st === 'alarm' ? (blink || k % 3 === 0 ? C.red : '#5a1d22') : (on && Math.sin(t * 7 + k + i) > -.6 ? (k % 4 ? C.green : C.cyan) : '#123'); ctx.fillRect(lx - 8, ly - 4, 16, 8); }
  }
  if (st === 'alarm') { ctx.save(); ctx.globalAlpha = .2 + .14 * Math.sin(t * 10); ctx.fillStyle = C.red; ctx.fillRect(0, 0, W, 1920); ctx.restore();
    const k = pop(t, .3); ctx.save(); ctx.translate(CX, 560); ctx.scale(k, k); ctx.beginPath(); ctx.moveTo(0, -120); ctx.lineTo(130, 100); ctx.lineTo(-130, 100); ctx.closePath(); glow(ctx, C.red, 50, () => { ctx.fillStyle = C.yel; ctx.fill(); }); text(ctx, '!', 0, 30, 150, '#111', { w: 900 }); ctx.restore(); }
  if (v.label) pill(ctx, v.label.toUpperCase(), CX, 340, 50, st === 'alarm' ? C.red : C.yel, st === 'alarm' ? '#fff' : '#111', ease(t / .4));
}

// ---------------------------------------------------------------- people group
function people(ctx, v, t, dur, acc, seed) {
  const who = Array.isArray(v.who) ? v.who.slice(0, 4) : [v.who || 'worker'], n = who.length, act = v.action || 'talk';
  floorDisc(ctx, CX, 1130, 560, acc, .35);
  const spread = n === 1 ? 0 : Math.min(300, 760 / (n - 1)), h = n <= 2 ? 690 : n === 3 ? 600 : 520;
  const pose = { talk: 'talk', shock: 'shock', point: 'point', walk: 'walk', cheer: 'cheer', arrest: 'arrest' }[act] || 'talk';
  who.forEach((role, i) => {
    const x = CX + (i - (n - 1) / 2) * spread, k = pop(t, i * .12, .45), dx = pose === 'walk' ? (t - dur / 2) * 40 : 0;
    let p = pose; if (act === 'arrest') p = (role === 'crook' || role === 'hacker') ? 'arrest' : 'point';
    if (act === 'talk' && i % 2 === 1) p = 'idle';
    ctx.save(); ctx.translate(x + dx, 1130); ctx.scale(1, k); person(ctx, 0, 0, h, role, p, t, { seed: seed + i * 5, flip: i >= n / 2 && n > 1 }); ctx.restore();
  });
  if (act === 'talk') { const k = pop(t, .5); if (k > 0) { ctx.save(); ctx.translate(CX + 160, 520); ctx.scale(k, k); fillRR(ctx, -110, -60, 220, 120, 50, '#fff'); for (let i = 0; i < 3; i++) { ctx.fillStyle = '#16213f'; ctx.beginPath(); ctx.arc(-50 + i * 50, 0, 14 + 5 * Math.sin(t * 6 + i), 0, 6.283); ctx.fill(); } ctx.restore(); } }
  if (v.label) pill(ctx, v.label.toUpperCase(), CX, 340, 52, C.yel, '#111', ease(t / .4));
}

// ---------------------------------------------------------------- phone mockup
function phone(ctx, v, t, dur, acc, seed) {
  const k = back(t / .5), app = v.app || 'alert'; ctx.save(); ctx.translate(CX, 760 + (1 - k) * 400); ctx.rotate(Math.sin(t * 1.5) * .03);
  const w = 500, h = 900; glow(ctx, 'rgba(0,0,0,.7)', 60, () => fillRR(ctx, -w / 2, -h / 2, w, h, 70, '#10131c')); fillRR(ctx, -w / 2 + 18, -h / 2 + 18, w - 36, h - 36, 54, app === 'alert' ? '#2a0b12' : '#f3f5fa'); fillRR(ctx, -70, -h / 2 + 30, 140, 30, 15, '#10131c');
  const ink = app === 'alert' ? '#fff' : '#16213f';
  if (app === 'email' || app === 'bank') { text(ctx, app === 'bank' ? 'MY BANK' : 'Inbox', -w / 2 + 50, -h / 2 + 120, 42, ink, { align: 'left', w: 900 });
    for (let i = 0; i < 4; i++) { const yy = -h / 2 + 190 + i * 130, hot = i === 0; fillRR(ctx, -w / 2 + 36, yy, w - 72, 110, 20, hot ? '#fff3c4' : '#e6eaf2'); if (hot) { text(ctx, v.from || 'unknown', -w / 2 + 60, yy + 34, 28, '#16213f', { align: 'left', w: 900 }); const ls = wrap(ctx, v.text || '', w - 120, 26, 700); ls.slice(0, 2).forEach((l, j) => text(ctx, l, -w / 2 + 60, yy + 68 + j * 28, 26, '#4a5570', { align: 'left', w: 700 })); } else { fillRR(ctx, -w / 2 + 60, yy + 26, 200, 18, 8, '#c3c9d6'); fillRR(ctx, -w / 2 + 60, yy + 62, 300, 14, 7, '#d2d7e2'); } }
    if (app === 'bank') { const bal = Math.max(0, 1 - ease((t - .6) / 1.6)); text(ctx, '$' + Math.round(bal * 81000000).toLocaleString('en-US'), 0, 260, 54, bal < .2 ? C.red : '#16213f', { w: 900 }); } }
  else if (app === 'chat') { const lines = String(v.text || '').split(/(?<=[.?!])\s+/).filter(Boolean); text(ctx, v.from || 'Chat', 0, -h / 2 + 110, 38, ink, { w: 900 }); lines.slice(0, 4).forEach((l, i) => { const kk = pop(t, .3 + i * .5); if (kk <= 0) return; const ls = wrap(ctx, l, 320, 30, 700), bh = 40 + ls.length * 36, yy = -h / 2 + 180 + i * 170, left = i % 2 === 0; ctx.save(); ctx.translate(left ? -w / 2 + 40 : w / 2 - 40 - 360, yy); ctx.scale(kk, kk); fillRR(ctx, 0, 0, 360, bh, 26, left ? '#e2e7f0' : '#3d7bff'); ls.forEach((x, j) => text(ctx, x, 24, 38 + j * 36, 30, left ? '#16213f' : '#fff', { align: 'left', w: 700 })); ctx.restore(); }); }
  else if (app === 'call') { ctx.fillStyle = '#16213f'; ctx.beginPath(); ctx.arc(0, -150, 100, 0, 6.283); ctx.fill(); text(ctx, v.from || 'Unknown', 0, 0, 46, '#16213f', { w: 900 }); text(ctx, v.text || 'Incoming call...', 0, 60, 30, '#4a5570', { w: 700 }); for (const [x, c] of [[-120, C.red], [120, '#2bd66a']]) { const pr = 1 + .1 * Math.sin(t * 8); ctx.beginPath(); ctx.arc(x, 300, 56 * pr, 0, 6.283); ctx.fillStyle = c; ctx.fill(); } }
  else { const pr = 1 + .08 * Math.sin(t * 9); ctx.save(); ctx.scale(pr, pr); ctx.beginPath(); ctx.moveTo(0, -260); ctx.lineTo(150, 0); ctx.lineTo(-150, 0); ctx.closePath(); glow(ctx, C.red, 60, () => { ctx.fillStyle = C.red; ctx.fill(); }); text(ctx, '!', 0, -80, 150, '#fff', { w: 900 }); ctx.restore(); text(ctx, (v.from || 'WARNING').toUpperCase(), 0, 90, 46, '#fff', { w: 900 }); wrap(ctx, v.text || '', w - 110, 36, 800).slice(0, 3).forEach((l, i) => text(ctx, l, 0, 160 + i * 44, 36, '#ffd0d6', { w: 800 })); }
  ctx.restore();
}

// ---------------------------------------------------------------- email window
function email(ctx, v, t, dur, acc, seed) {
  const k = ease(t / .45), x = 80, y = 470 + (1 - k) * 120, w = 920, h = 640; ctx.save(); ctx.globalAlpha *= k;
  glow(ctx, 'rgba(0,0,0,.6)', 50, () => fillRR(ctx, x, y, w, h, 28, '#f3f5fa')); fillRR(ctx, x, y, w, 80, 28, '#2a3a63'); ctx.fillRect(x, y + 50, w, 30);
  [['#ff5f56', 0], ['#ffbd2e', 1], ['#27c93f', 2]].forEach(([c, i]) => { ctx.beginPath(); ctx.arc(x + 46 + i * 40, y + 40, 12, 0, 6.283); ctx.fillStyle = c; ctx.fill(); });
  text(ctx, 'FROM', x + 50, y + 140, 26, '#7a849c', { align: 'left', w: 800 }); text(ctx, v.from || '', x + 170, y + 140, fitText(ctx, v.from || '', 680, 38, 700), '#16213f', { align: 'left', w: 700 });
  text(ctx, 'SUBJECT', x + 50, y + 215, 26, '#7a849c', { align: 'left', w: 800 }); text(ctx, v.subject || '', x + 210, y + 215, fitText(ctx, v.subject || '', 640, 42, 900), '#16213f', { align: 'left', w: 900 });
  ctx.fillStyle = '#d6dbe6'; ctx.fillRect(x + 40, y + 255, w - 80, 3); const r = rng(seed); for (let i = 0; i < 4; i++) fillRR(ctx, x + 50, y + 290 + i * 46, 400 + r() * 380, 18, 8, '#c9cfdb');
  if (v.line) { const kk = ease((t - .9) / .5), lw = Math.min(w - 100, 60 + ctx.measureText(v.line).width * 1.9); fillRR(ctx, x + 40, y + 490, (w - 80) * kk, 90, 18, C.yel); if (kk > .7) text(ctx, v.line, x + 70, y + 535, fitText(ctx, v.line, w - 160, 44, 900), '#111', { align: 'left', w: 900 }); }
  ctx.restore();
  if (t > 1.6) { const kk = ease((t - 1.6) / .5), mx = lerp(900, 640, kk), my = lerp(1250, 1015, kk); ctx.beginPath(); ctx.moveTo(mx, my); ctx.lineTo(mx, my + 60); ctx.lineTo(mx + 16, my + 46); ctx.lineTo(mx + 42, my + 46); ctx.closePath(); ctx.fillStyle = '#fff'; ctx.fill(); ctx.strokeStyle = '#111'; ctx.lineWidth = 4; ctx.stroke(); if (t > 2.2) { const ph = ((t - 2.2) * 1.5) % 1; ctx.beginPath(); ctx.arc(mx, my, 20 + 70 * ph, 0, 6.283); ctx.strokeStyle = `rgba(255,59,78,${1 - ph})`; ctx.lineWidth = 6; ctx.stroke(); } }
}

// ---------------------------------------------------------------- hero object
function object(ctx, v, t, dur, acc, seed) {
  floorDisc(ctx, CX, 1040, 420, acc, .55);
  ctx.save(); ctx.translate(CX, 1040); ctx.scale(1, .3); glow(ctx, acc, 60, () => { ctx.beginPath(); ctx.arc(0, 0, 300, 0, 6.283); ctx.strokeStyle = acc; ctx.lineWidth = 10; ctx.stroke(); }); ctx.restore();
  const k = back(t / .55), bob = Math.sin(t * 2.2) * 16; ctx.save(); ctx.translate(CX, 760 + bob); ctx.scale(1.45 * k, 1.45 * k); drawIcon(ctx, v.icon, t); ctx.restore();
  const r = rng(seed); for (let i = 0; i < 10; i++) { const a = r() * 6.283 + t * .6, d = 330 + r() * 80; ctx.fillStyle = acc; ctx.globalAlpha = .5 + .5 * Math.sin(t * 4 + i); ctx.beginPath(); ctx.arc(CX + Math.cos(a) * d, 760 + Math.sin(a) * d * .7, 5 + r() * 6, 0, 6.283); ctx.fill(); ctx.globalAlpha = 1; }
  if (v.text) pill(ctx, v.text.toUpperCase(), CX, 340, 54, C.yel, '#111', ease((t - .25) / .4));
}

// ---------------------------------------------------------------- network infection
function network(ctx, v, t, dur, acc, seed) {
  const r = rng(seed + 11), n = 64, pts = [];
  while (pts.length < n) { const x = 110 + r() * 860, y = 470 + r() * 680; if (pts.every(([a, b]) => (a - x) ** 2 + (b - y) ** 2 > 82 ** 2)) pts.push([x, y]); }
  const c0 = pts[0], order = pts.map((p, i) => [(p[0] - c0[0]) ** 2 + (p[1] - c0[1]) ** 2, i]).sort((a, b) => a[0] - b[0]), rank = []; order.forEach(([, i], k) => rank[i] = k);
  const frac = easeIO(t / Math.max(2, Math.min(dur * .85, 5))), inf = frac * n, edges = [];
  pts.forEach((p, i) => pts.map((q, j) => [(p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2, j]).sort((a, b) => a[0] - b[0]).slice(1, 4).forEach(([, j]) => edges.push([i, j])));
  ctx.lineCap = 'round';
  edges.forEach(([i, j], e) => { const on = rank[i] < inf && rank[j] < inf; ctx.strokeStyle = on ? 'rgba(255,59,78,.85)' : 'rgba(80,110,160,.45)'; ctx.lineWidth = on ? 5 : 2; ctx.beginPath(); ctx.moveTo(...pts[i]); ctx.lineTo(...pts[j]); ctx.stroke();
    if (on) { const q = (t * 1.2 + e * .13) % 1; ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(lerp(pts[i][0], pts[j][0], q), lerp(pts[i][1], pts[j][1], q), 6, 0, 6.283); ctx.fill(); } });
  pts.forEach(([x, y], i) => { const on = rank[i] < inf; if (on) glow(ctx, C.red, 24, () => { fillRR(ctx, x - 26, y - 18, 52, 36, 6, C.red); }); else { fillRR(ctx, x - 22, y - 15, 44, 30, 6, '#2a6fbf'); fillRR(ctx, x - 16, y - 10, 32, 18, 3, '#9fd4ff'); } });
  if (v.total) { const tv = Number(String(v.total).replace(/,/g, '')); text(ctx, counterNum(tv, frac), CX, 330, 120, C.white, { w: 900, stroke: 12 }); text(ctx, (v.text || 'computers hit').toUpperCase(), CX, 420, 44, C.red, { w: 900, stroke: 8 }); }
  else topText(ctx, v.text, t);
}

// ---------------------------------------------------------------- globe with arcs
function globe(ctx, v, t, dur, acc, seed) {
  const R = 400, cx = CX, cy = 800, pts = (v.points || []).map(p => [String(p[0]), +p[1], +p[2]]); const mid = pts.length ? pts.reduce((s, p) => s + p[2], 0) / pts.length : 0, yaw = -mid * Math.PI / 180 + Math.sin(t * .35) * .2, lat0 = (pts.length ? pts.reduce((s, p) => s + p[1], 0) / pts.length : 20) * Math.PI / 180 * .6;
  const proj = (la, lo) => { la *= Math.PI / 180; lo = lo * Math.PI / 180 + yaw; let x = Math.cos(la) * Math.sin(lo), y = Math.sin(la), z = Math.cos(la) * Math.cos(lo); const y2 = y * Math.cos(lat0) - z * Math.sin(lat0), z2 = y * Math.sin(lat0) + z * Math.cos(lat0); return [cx + x * R, cy - y2 * R, z2]; };
  const g = ctx.createRadialGradient(cx - 120, cy - 140, 40, cx, cy, R); g.addColorStop(0, '#1d4f9a'); g.addColorStop(1, '#081a3a'); glow(ctx, 'rgba(42,208,255,.6)', 80, () => { ctx.beginPath(); ctx.arc(cx, cy, R, 0, 6.283); ctx.fillStyle = g; ctx.fill(); });
  ctx.strokeStyle = 'rgba(120,190,255,.28)'; ctx.lineWidth = 2;
  for (let la = -60; la <= 60; la += 30) { ctx.beginPath(); let f = true; for (let lo = -180; lo <= 180; lo += 6) { const [x, y, z] = proj(la, lo); if (z < 0) { f = true; continue; } f ? ctx.moveTo(x, y) : ctx.lineTo(x, y); f = false; } ctx.stroke(); }
  for (let lo = -180; lo < 180; lo += 30) { ctx.beginPath(); let f = true; for (let la = -90; la <= 90; la += 6) { const [x, y, z] = proj(la, lo); if (z < 0) { f = true; continue; } f ? ctx.moveTo(x, y) : ctx.lineTo(x, y); f = false; } ctx.stroke(); }
  const r = rng(77); ctx.fillStyle = 'rgba(160,220,255,.55)'; for (let i = 0; i < 520; i++) { const la = Math.asin(2 * r() - 1) * 180 / Math.PI, lo = r() * 360 - 180, [x, y, z] = proj(la, lo); if (z > 0) { ctx.globalAlpha = .3 + z * .7; ctx.fillRect(x - 2, y - 2, 4, 4); } } ctx.globalAlpha = 1;
  for (let i = 0; i < pts.length - 1; i++) { const k = easeIO((t - .4 - i * 1.0) / 1.4); if (k <= 0) continue; const a = proj(pts[i][1], pts[i][2]), b = proj(pts[i + 1][1], pts[i + 1][2]), mx = (a[0] + b[0]) / 2, my = Math.min(a[1], b[1]) - 220; ctx.strokeStyle = C.red; ctx.lineWidth = 8; ctx.beginPath(); const N = 40; for (let s = 0; s <= N * k; s++) { const q = s / N, x = (1 - q) ** 2 * a[0] + 2 * (1 - q) * q * mx + q * q * b[0], y = (1 - q) ** 2 * a[1] + 2 * (1 - q) * q * my + q * q * b[1]; s ? ctx.lineTo(x, y) : ctx.moveTo(x, y); } glow(ctx, C.red, 30, () => ctx.stroke());
    const q = k, hx = (1 - q) ** 2 * a[0] + 2 * (1 - q) * q * mx + q * q * b[0], hy = (1 - q) ** 2 * a[1] + 2 * (1 - q) * q * my + q * q * b[1]; ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(hx, hy, 12, 0, 6.283); ctx.fill(); }
  pts.forEach(([nm, la, lo], i) => { const [x, y, z] = proj(la, lo); if (z < -.1) return; const ph = (t * .9) % 1; ctx.fillStyle = C.yel; ctx.beginPath(); ctx.arc(x, y, 14, 0, 6.283); ctx.fill(); ctx.strokeStyle = `rgba(255,212,0,${1 - ph})`; ctx.lineWidth = 5; ctx.beginPath(); ctx.arc(x, y, 18 + 50 * ph, 0, 6.283); ctx.stroke(); const k = pop(t, .2 + i * .3); if (k > 0) pill(ctx, nm.toUpperCase(), x, y - 70, 38, '#ffffff', '#0b1226', k); });
}

// ---------------------------------------------------------------- flow (money/data) between parties, vertical
function flow(ctx, v, t, dur, acc, seed) {
  const nodes = (v.nodes || ['A', 'B']).slice(0, 4), n = nodes.length, y0 = 430, y1 = 1120, ys = nodes.map((_, i) => n > 1 ? y0 + (y1 - y0) * i / (n - 1) : 760);
  for (let i = 0; i < n - 1; i++) { const k = easeIO((t - .4 - i * .8) / 1.0), a = ys[i] + 70, b = ys[i + 1] - 70, blocked = v.blocked && i === n - 2 && k >= 1;
    ctx.strokeStyle = 'rgba(120,150,200,.35)'; ctx.lineWidth = 10; ctx.setLineDash([18, 16]); ctx.beginPath(); ctx.moveTo(CX, a); ctx.lineTo(CX, b); ctx.stroke(); ctx.setLineDash([]);
    if (k > 0) { ctx.strokeStyle = blocked ? C.red : C.yel; ctx.lineWidth = 12; ctx.beginPath(); ctx.moveTo(CX, a); ctx.lineTo(CX, lerp(a, b, k)); glow(ctx, blocked ? C.red : C.yel, 30, () => ctx.stroke());
      for (let q = 0; q < 3; q++) { const yy = lerp(a, lerp(a, b, k), (t * .9 + q / 3) % 1); ctx.save(); ctx.translate(CX + Math.sin(t * 4 + q) * 26, yy); ctx.rotate(Math.sin(t * 3 + q) * .4); fillRR(ctx, -44, -20, 88, 40, 6, '#4fb874'); ctx.restore(); }
      if (v.amount && k > .5) pill(ctx, v.amount, CX + 250, (a + b) / 2, 50, C.yel, '#111', clamp((k - .5) * 3)); }
    if (blocked) { const kk = back((t - 2.6) / .35); if (kk > 0) { ctx.save(); ctx.translate(CX, (a + b) / 2); ctx.scale(kk, kk); ctx.strokeStyle = C.red; ctx.lineWidth = 26; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(-70, -70); ctx.lineTo(70, 70); ctx.moveTo(70, -70); ctx.lineTo(-70, 70); glow(ctx, C.red, 30, () => ctx.stroke()); ctx.restore(); } } }
  nodes.forEach((nm, i) => { const k = pop(t, i * .2); if (k <= 0) return; ctx.save(); ctx.translate(CX, ys[i]); ctx.scale(k, k); const sz = fitText(ctx, nm.toUpperCase(), 600, 50, 900), w = 700; glow(ctx, 'rgba(0,0,0,.6)', 30, () => fillRR(ctx, -w / 2, -70, w, 140, 30, '#13204a')); fillRR(ctx, -w / 2, -70, w, 140, 30, null, acc, 5); text(ctx, nm.toUpperCase(), 0, 2, sz, C.white, { w: 900 }); ctx.restore(); });
}

// ---------------------------------------------------------------- counter gauge
function counter(ctx, v, t, dur, acc, seed) {
  const val = Number(String(v.value).replace(/,/g, '')) || 0, k = easeIO(t / Math.min(2.2, Math.max(1.2, dur * .6))), cx = CX, cy = 760, R = 360;
  for (let i = 0; i < 120; i++) { const a = i / 120 * 6.283 - Math.PI / 2, on = i / 120 <= k, r0 = R - (i % 5 ? 26 : 50); ctx.strokeStyle = on ? C.yel : 'rgba(120,150,200,.3)'; ctx.lineWidth = i % 5 ? 5 : 9; ctx.beginPath(); ctx.moveTo(cx + Math.cos(a) * r0, cy + Math.sin(a) * r0); ctx.lineTo(cx + Math.cos(a) * R, cy + Math.sin(a) * R); ctx.stroke(); }
  ctx.strokeStyle = acc; ctx.lineWidth = 12; ctx.beginPath(); ctx.arc(cx, cy, R + 36, -Math.PI / 2, -Math.PI / 2 + k * 6.283); glow(ctx, acc, 30, () => ctx.stroke());
  const s = `${v.prefix || ''}${counterNum(val, k)}${v.suffix || ''}`, sz = fitText(ctx, s, 560, 200, 900); text(ctx, s, cx, cy - 10, sz, C.white, { w: 900, stroke: 10 });
  if (v.label) text(ctx, String(v.label).toUpperCase(), cx, cy + 130, fitText(ctx, String(v.label).toUpperCase(), 560, 50, 900), C.yel, { w: 900, a: ease((t - .4) / .4) });
}

// ---------------------------------------------------------------- vertical timeline
function timeline(ctx, v, t, dur, acc, seed) {
  const items = (v.items || []).slice(0, 4), n = items.length || 1, y0 = 460, y1 = 1120, ys = items.map((_, i) => n > 1 ? y0 + (y1 - y0) * i / (n - 1) : 790), x = 260;
  const rev = easeIO(t / Math.min(Math.max(1.4, .8 * n), dur * .85 + .01)); ctx.strokeStyle = 'rgba(255,255,255,.85)'; ctx.lineWidth = 8; ctx.beginPath(); ctx.moveTo(x, y0 - 40); ctx.lineTo(x, lerp(y0 - 40, y1 + 40, rev)); ctx.stroke();
  items.forEach(([d, e], i) => { const fr = n > 1 ? i / (n - 1) : .5; if (rev + .001 < fr * .98) return; const k = pop(t, .2 + i * Math.min(.8, dur * .7 / n)); if (k <= 0) return;
    ctx.save(); ctx.translate(x, ys[i]); ctx.scale(k, k); glow(ctx, acc, 30, () => { ctx.beginPath(); ctx.arc(0, 0, 30, 0, 6.283); ctx.fillStyle = acc; ctx.fill(); }); ctx.beginPath(); ctx.arc(0, 0, 44, 0, 6.283); ctx.strokeStyle = '#fff'; ctx.lineWidth = 6; ctx.stroke(); ctx.restore();
    text(ctx, String(d).toUpperCase(), x + 90, ys[i] - 36, fitText(ctx, String(d).toUpperCase(), 640, 66, 900), C.yel, { align: 'left', w: 900, a: k }); wrap(ctx, String(e), 640, 44, 800).slice(0, 2).forEach((l, j) => text(ctx, l, x + 90, ys[i] + 28 + j * 50, 44, C.white, { align: 'left', w: 800, a: k })); });
}

// ---------------------------------------------------------------- padlock
function lock(ctx, v, t, dur, acc, seed) {
  const st = v.state || 'locked', k = easeIO((t - 1.0) / .6), cx = CX, cy = 840, col = st === 'locked' ? C.green : st === 'crack' ? C.red : C.cyan;
  const lift = st === 'open' ? k * 110 : 0; ctx.lineCap = 'round'; ctx.strokeStyle = '#c9ced8'; ctx.lineWidth = 56; ctx.beginPath(); ctx.arc(cx, cy - 180 - lift, 150, Math.PI, 0); ctx.moveTo(cx - 150, cy - 180 - lift); ctx.lineTo(cx - 150, cy - 90 - (st === 'open' ? lift : 0)); ctx.moveTo(cx + 150, cy - 180 - lift); ctx.lineTo(cx + 150, cy - 90); ctx.stroke();
  glow(ctx, col, 60, () => fillRR(ctx, cx - 250, cy - 120, 500, 380, 50, col)); fillRR(ctx, cx - 250, cy - 120, 500, 380, 50, null, 'rgba(255,255,255,.35)', 6);
  ctx.fillStyle = '#0b1226'; ctx.beginPath(); ctx.arc(cx, cy + 40, 54, 0, 6.283); ctx.fill(); ctx.fillRect(cx - 20, cy + 40, 40, 120);
  if (st === 'crack' && k > 0) { const r = rng(5); ctx.strokeStyle = '#fff'; ctx.lineWidth = 10; ctx.beginPath(); let x = cx - 60, y = cy - 120; ctx.moveTo(x, y); for (let i = 0; i < 8 * k; i++) { x += r() * 90 - 35; y += 45; ctx.lineTo(x, y); } ctx.stroke(); if (t - 1 < .2) { ctx.fillStyle = 'rgba(255,255,255,.3)'; ctx.fillRect(0, 0, W, 1300); } }
  if (v.text) pill(ctx, v.text.toUpperCase(), CX, 340, 54, st === 'crack' ? C.red : C.yel, st === 'crack' ? '#fff' : '#111', ease(t / .4));
}

// ---------------------------------------------------------------- terminal
function terminal(ctx, v, t, dur, acc, seed) {
  const lines = (v.lines || []).slice(0, 5).map(l => (l.startsWith('>') ? l : '> ' + l)), x = 70, y = 480, w = 940, h = 640;
  glow(ctx, 'rgba(0,0,0,.6)', 50, () => fillRR(ctx, x, y, w, h, 28, '#050a0e')); fillRR(ctx, x, y, w, h, 28, null, C.green, 4); fillRR(ctx, x, y, w, 70, 28, '#16202c'); ctx.fillRect(x, y + 40, w, 30);
  [['#ff5f56', 0], ['#ffbd2e', 1], ['#27c93f', 2]].forEach(([c, i]) => { ctx.beginPath(); ctx.arc(x + 44 + i * 38, y + 36, 11, 0, 6.283); ctx.fillStyle = c; ctx.fill(); });
  let budget = Math.floor(Math.max(0, t - .3) * 30); ctx.font = '700 46px monospace'; ctx.textBaseline = 'middle'; ctx.textAlign = 'left';
  lines.forEach((l, i) => { if (budget <= 0) return; const s = l.slice(0, budget); budget -= l.length + 6; ctx.fillStyle = /fail|denied|error|wiped|locked/i.test(l) ? C.red : C.green; ctx.fillText(s, x + 44, y + 140 + i * 92); if (budget < 0 && Math.sin(t * 9) > 0) ctx.fillRect(x + 50 + ctx.measureText(s).width, y + 116 + i * 92, 26, 46); });
}

// ---------------------------------------------------------------- dossier card
function dossier(ctx, v, t, dur, acc, seed) {
  const k = ease(t / .5), x = 90, y = 430 + (1 - k) * 80, w = 900, h = 720, rows = (v.rows || []).slice(0, 4); ctx.save(); ctx.globalAlpha *= k;
  glow(ctx, 'rgba(0,0,0,.6)', 50, () => fillRR(ctx, x, y, w, h, 30, '#0f1830')); fillRR(ctx, x, y, w, h, 30, null, acc, 4);
  fillRR(ctx, x + 40, y + 40, 260, 300, 20, '#1b2a50'); ctx.save(); ctx.beginPath(); rr(ctx, x + 40, y + 40, 260, 300, 20); ctx.clip(); ctx.fillStyle = '#2f4578'; ctx.beginPath(); ctx.arc(x + 170, y + 160, 70, 0, 6.283); ctx.fill(); ctx.beginPath(); ctx.ellipse(x + 170, y + 330, 120, 110, 0, Math.PI, 0); ctx.fill(); const sy = y + 40 + ((t * .8) % 1) * 300; ctx.fillStyle = C.green; ctx.fillRect(x + 40, sy, 260, 6); ctx.restore();
  text(ctx, String(v.title || '').toUpperCase(), x + 330, y + 90, fitText(ctx, String(v.title || '').toUpperCase(), 540, 60, 900), C.white, { align: 'left', w: 900 }); fillRR(ctx, x + 330, y + 140, 520 * ease((t - .2) / .5), 8, 4, C.yel);
  rows.forEach(([a, b], i) => { const kk = ease((t - .5 - i * .35) / .35), yy = y + 400 + i * 78; text(ctx, String(a).toUpperCase(), x + 50, yy, 34, C.yel, { align: 'left', w: 900, a: kk }); text(ctx, String(b), x + 330, yy, fitText(ctx, String(b), 520, 44, 800), C.white, { align: 'left', w: 800, a: kk }); ctx.fillStyle = 'rgba(120,150,200,.25)'; ctx.fillRect(x + 50, yy + 34, (w - 100) * kk, 3); });
  ctx.restore();
}

// ---------------------------------------------------------------- headline
function headline(ctx, v, t, dur, acc, seed) {
  const k = back(t / .5); ctx.save(); ctx.translate(CX, 800 + (1 - k) * 500); ctx.rotate(-.04);
  const ls = wrap(ctx, String(v.text || '').toUpperCase(), 780, 84, 900).slice(0, 4), h = 200 + ls.length * 100;
  glow(ctx, 'rgba(0,0,0,.6)', 50, () => fillRR(ctx, -460, -h / 2, 920, h, 18, '#f4f1e8')); fillRR(ctx, -460, -h / 2, 920, 110, 18, '#c8142a'); ctx.fillRect(-460, -h / 2 + 80, 920, 30);
  text(ctx, 'BREAKING NEWS', -410, -h / 2 + 56, 50, '#fff', { align: 'left', w: 900 }); ls.forEach((l, i) => text(ctx, l, -410, -h / 2 + 170 + i * 100, 84, '#111', { align: 'left', w: 900 }));
  ctx.restore(); const tx = (-t * 260) % 1400; ctx.fillStyle = '#c8142a'; ctx.fillRect(0, 1150, W, 70); text(ctx, 'LIVE  •  CYBER ATTACK  •  LIVE  •  CYBER ATTACK  •  LIVE  •  CYBER ATTACK', tx + 1300, 1186, 40, '#fff', { align: 'left', w: 900 });
}

// ---------------------------------------------------------------- stamp on a document
function stamp(ctx, v, t, dur, acc, seed) {
  const x = 140, y = 420, w = 800, h = 820; ctx.save(); ctx.translate(CX, 830); ctx.rotate(.03); ctx.translate(-CX, -830); glow(ctx, 'rgba(0,0,0,.6)', 50, () => fillRR(ctx, x, y, w, h, 14, C.paper));
  const r = rng(seed); for (let i = 0; i < 14; i++) fillRR(ctx, x + 60, y + 80 + i * 50, 380 + r() * 300, 16, 6, '#b9b5aa');
  for (let i = 0; i < 6; i++) { const kk = easeIO((t - .2 - i * .12) / .4); if (kk > 0) fillRR(ctx, x + 60 + r() * 80, y + 130 + i * 100, (300 + r() * 340) * kk, 40, 4, '#111'); } ctx.restore();
  const k = clamp((t - 1.1) / .25); if (k > 0) { const sc = 2.2 - 1.2 * ease(k); ctx.save(); ctx.translate(CX, 820); ctx.rotate(-.18); ctx.scale(sc, sc); ctx.globalAlpha = clamp(k * 2); const s = String(v.text || 'HACKED').toUpperCase(), sz = fitText(ctx, s, 620, 130, 900); fillRR(ctx, -360, -110, 720, 220, 24, null, '#d0202e', 16); text(ctx, s, 0, 6, sz, '#d0202e', { w: 900 }); ctx.restore(); if (k < 1 && t - 1.1 < .32) { ctx.fillStyle = 'rgba(255,255,255,.12)'; ctx.fillRect(0, 0, W, 1920); } }
}

// ---------------------------------------------------------------- split comparison
function lcsMask(a, b) { const n = a.length, m = b.length, D = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0)); for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--) D[i][j] = a[i] === b[j] ? D[i + 1][j + 1] + 1 : Math.max(D[i + 1][j], D[i][j + 1]); const mask = new Array(m).fill(false); let i = 0, j = 0; while (i < n && j < m) { if (a[i] === b[j]) { mask[j] = true; i++; j++; } else if (D[i + 1][j] >= D[i][j + 1]) i++; else j++; } return mask; }
function split(ctx, v, t, dur, acc, seed) {
  const k1 = pop(t, 0), k2 = pop(t, .45), L = String(v.left || ''), R = String(v.right || '');
  [[L, 290, k1, C.green], [R, 790, k2, C.red]].forEach(([s, y, k, c], i) => { if (k <= 0) return; ctx.save(); ctx.translate(CX, y + 250); ctx.scale(k, k); glow(ctx, 'rgba(0,0,0,.6)', 40, () => fillRR(ctx, -440, -170, 880, 340, 36, '#101a36')); fillRR(ctx, -440, -170, 880, 340, 36, null, c, 6);
    const sz = fitText(ctx, s, 760, 110, 900); ctx.font = `900 ${sz}px Inter, Arial`; let x = -ctx.measureText(s).width / 2; ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    const keepM = lcsMask(L.toLowerCase(), s.toLowerCase()); for (let j = 0; j < s.length; j++) { const diff = i === 1 && !keepM[j]; ctx.fillStyle = diff ? C.red : '#fff'; if (diff) { ctx.save(); ctx.shadowColor = C.red; ctx.shadowBlur = 30; ctx.fillText(s[j], x, 10); ctx.restore(); } else ctx.fillText(s[j], x, 10); x += ctx.measureText(s[j]).width; }
    ctx.restore(); });
  const kv = pop(t, .3); if (kv > 0) { ctx.save(); ctx.translate(CX, 790); ctx.scale(kv, kv); ctx.beginPath(); ctx.arc(0, 0, 70, 0, 6.283); ctx.fillStyle = C.yel; ctx.fill(); text(ctx, 'VS', 0, 4, 60, '#111', { w: 900 }); ctx.restore(); }
}

export const KINDS = { building, office, hacker, servers, people, phone, email, object, network, globe, flow, counter, timeline, lock, terminal, dossier, headline, stamp, split };
