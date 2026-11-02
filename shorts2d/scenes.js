// Scene kinds - "editorial paper" 2D style. Each: (ctx, v, t, dur, acc, seed). v.w = [[word, secondsIntoShot], ...] so actions land on the spoken words.
// Stage y 260..1180 (captions sit below 1250). Light scenes use ink outlines and hard sticker shadows; no neon, no glow, no grids.
import { W, C, MOOD, isDark, fg, ease, easeIO, back, clamp, lerp, rng, hash, rr, fillRR, glow, card, text, fitText, wrap, pill, marker, isoP, isoBox, isoWindows, floorDisc, shadow, shade, cue } from './kit.js';
import { person } from './people.js';
import { drawIcon } from './icons.js';

const CX = 540;
const pop = (t, d = 0, len = .45) => back((t - d) / len);
const ink = v => fg(v.mood);
function headline_(ctx, s, t, v, d = 0) {            // big ink title at the top with a marker swipe
  if (!s) return; const S = String(s).toUpperCase(), sz = fitText(ctx, S, 900, 76, 900); ctx.save(); ctx.font = `900 ${sz}px Inter, Arial`; const w = ctx.measureText(S).width;
  marker(ctx, CX - w / 2 - 14, 300, w + 28, sz * 1.05, ease((t - d - .15) / .35), isDark(v.mood) ? C.red : C.yel); ctx.restore();
  text(ctx, S, CX, 300 + sz * .55, sz, isDark(v.mood) && false ? C.white : (isDark(v.mood) ? C.white : C.ink), { w: 900, a: ease((t - d) / .25) });
}
function bubble(ctx, s, x, y, t, d, o = {}) {        // white speech/screen bubble with ink outline, typed text
  if (!s) return; const k = pop(t, d); if (k <= 0) return; const mono = o.mono, sz = fitText(ctx, s, 760, o.sz || 52, 800);
  ctx.save(); ctx.translate(x, y); ctx.scale(k, k); ctx.font = mono ? `700 ${sz}px monospace` : `800 ${sz}px Inter, Arial`;
  const w = Math.min(880, ctx.measureText(s).width + 90), h = sz * 2.1;
  glow(ctx, 0, 0, () => fillRR(ctx, -w / 2, -h / 2, w, h, 26, o.bg || C.white)); fillRR(ctx, -w / 2, -h / 2, w, h, 26, null, C.ink, 6);
  ctx.fillStyle = o.bg || C.white; ctx.strokeStyle = C.ink; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(-30, h / 2 - 3); ctx.lineTo(0, h / 2 + 34); ctx.lineTo(24, h / 2 - 3); ctx.fill(); ctx.stroke(); ctx.fillRect(-27, h / 2 - 8, 48, 8);
  const shown = s.slice(0, Math.ceil(clamp((t - d) / Math.max(.5, s.length / 28)) * s.length)); ctx.fillStyle = o.color || C.ink; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(shown, 0, 3); ctx.restore();
}
function num(v, k) { const n = v * k; return v >= 1000 ? Math.round(n).toLocaleString('en-US') : (v % 1 ? n.toFixed(2).replace(/\.?0+$/, '') : Math.round(n).toString()); }
function sun(ctx, x, y, r, col, t) { ctx.save(); ctx.translate(x, y); ctx.rotate(t * .15); ctx.fillStyle = col; for (let i = 0; i < 12; i++) { ctx.rotate(Math.PI / 6); ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(r * 1.35, -r * .18); ctx.lineTo(r * 1.35, r * .18); ctx.fill(); } ctx.restore(); }

// ---------------------------------------------------------------- building (isometric, ink edges, sky disc)
const BUILD = {
  bank: { col: '#e9dfc8', w: 7, d: 5, h: 5.2 }, fbi: { col: '#9aa3b2', w: 8, d: 5, h: 7.5 }, office: { col: '#7fa7c9', w: 5, d: 5, h: 11 }, hospital: { col: '#f4f1ea', w: 7, d: 5, h: 6 },
  government: { col: '#efe6d2', w: 8, d: 5, h: 5 }, factory: { col: '#c58b62', w: 8, d: 6, h: 4 }, police: { col: '#6d8fc6', w: 7, d: 5, h: 5 }, airport: { col: '#dfe7ef', w: 9, d: 5, h: 3.2 },
  school: { col: '#e08e5c', w: 8, d: 5, h: 4.5 }, studio: { col: '#9f86c7', w: 8, d: 6, h: 5 }, power: { col: '#b9c2cc', w: 7, d: 5, h: 4 },
};
function building(ctx, v, t, dur, acc, seed) {
  const B = BUILD[v.type] || BUILD.office, k = ease(t / .6), u = 60, ox = CX - (B.w - B.d) * u * .433, oy = 1060 - (B.w + B.d) * u * .25 + 30;
  ctx.save(); ctx.fillStyle = isDark(v.mood) ? C.ink2 : C.sky; ctx.beginPath(); ctx.arc(CX, 760, 400 * ease(t / .5), 0, 6.283); ctx.fill(); ctx.restore();
  if (!isDark(v.mood)) sun(ctx, 820, 470, 50, C.yel, t);
  isoBox(ctx, ox, oy, u, -1, -1, 0, B.w + 2, B.d + 2, .25, '#9fb38a');
  const h = B.h * (.25 + .75 * k);
  isoBox(ctx, ox, oy, u, 0, 0, .25, B.w, B.d, h, B.col);
  const rows = Math.max(2, Math.round(h / 1.15));
  if (v.type !== 'bank' && v.type !== 'government') { isoWindows(ctx, ox, oy, u, 0, 0, .25, B.w, B.d, h, 'left', Math.max(3, Math.round(B.w * 1.1)), rows, t, seed); isoWindows(ctx, ox, oy, u, 0, 0, .25, B.w, B.d, h, 'right', Math.round(B.d * 1.1), rows, t, seed + 3); }
  else {
    for (let i = 0; i < 6; i++) isoBox(ctx, ox, oy, u, .5 + i * (B.w - 1) / 5, B.d + .15, .25, .38, .38, h * .82, '#fbf7ee');
    isoBox(ctx, ox, oy, u, -.2, -.2, .25 + h * .82, B.w + .4, B.d + .7, h * .18, '#f3ecdc');
    const a = isoP(ox, oy, u, -.2, B.d + .5, .25 + h), b = isoP(ox, oy, u, B.w + .2, B.d + .5, .25 + h), c = isoP(ox, oy, u, B.w / 2, B.d + .5, .25 + h + (v.type === 'government' ? 2 : 1.4));
    ctx.beginPath(); ctx.moveTo(...a); ctx.lineTo(...b); ctx.lineTo(...c); ctx.closePath(); ctx.fillStyle = '#fbf7ee'; ctx.fill(); ctx.strokeStyle = C.ink; ctx.lineWidth = 4; ctx.stroke();
  }
  if (v.type === 'hospital') { const [x, y] = isoP(ox, oy, u, B.w / 2, B.d, .25 + h * .8); ctx.fillStyle = C.red; ctx.fillRect(x - 36, y - 11, 72, 22); ctx.fillRect(x - 11, y - 36, 22, 72); }
  if (v.type === 'factory' || v.type === 'power') for (let i = 0; i < 2; i++) { isoBox(ctx, ox, oy, u, 1 + i * 3, 1, .25 + h, .9, .9, 3, '#8f6b52'); for (let p = 0; p < 3; p++) { const [sx, sy] = isoP(ox, oy, u, 1.45 + i * 3, 1.45, .25 + h + 3.3 + ((t * .5 + p * .33) % 1) * 2.6); ctx.fillStyle = '#fbf7ee'; ctx.strokeStyle = C.ink; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(sx + p * 12, sy, 22 + p * 10, 0, 6.283); ctx.fill(); ctx.stroke(); } }
  if (v.type === 'fbi' || v.type === 'police') { const [fx, fy] = isoP(ox, oy, u, B.w + .7, B.d + 1.2, .25); ctx.strokeStyle = C.ink; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(fx, fy); ctx.lineTo(fx, fy - 300); ctx.stroke(); const wv = Math.sin(t * 4) * 8; ctx.fillStyle = C.red; ctx.beginPath(); ctx.moveTo(fx, fy - 300); ctx.quadraticCurveTo(fx + 55, fy - 290 + wv, fx + 110, fy - 300); ctx.lineTo(fx + 110, fy - 236); ctx.quadraticCurveTo(fx + 55, fy - 226 + wv, fx, fy - 236); ctx.closePath(); ctx.fill(); ctx.stroke(); ctx.fillStyle = C.blue; ctx.fillRect(fx + 3, fy - 297, 40, 28); }
  const d1 = isoP(ox, oy, u, B.w / 2 - .6, B.d, .25), d2 = isoP(ox, oy, u, B.w / 2 + .6, B.d, .25), d3 = isoP(ox, oy, u, B.w / 2 + .6, B.d, 1.9), d4 = isoP(ox, oy, u, B.w / 2 - .6, B.d, 1.9);
  ctx.beginPath(); ctx.moveTo(...d1); ctx.lineTo(...d2); ctx.lineTo(...d3); ctx.lineTo(...d4); ctx.closePath(); ctx.fillStyle = C.ink2; ctx.fill();
  if (v.name) { const d = cue(v, (v.name || '').split(/\s+/)[0], .35); const k2 = pop(t, Math.min(d, dur * .5)); if (k2 > 0) { ctx.save(); ctx.translate(CX, 1210 - 40); ctx.scale(k2, k2); const S = v.name.toUpperCase(), sz = fitText(ctx, S, 780, 58, 900); ctx.font = `900 ${sz}px Inter, Arial`; const w = ctx.measureText(S).width + 80; glow(ctx, 0, 0, () => fillRR(ctx, -w / 2, -52, w, 104, 14, C.white)); fillRR(ctx, -w / 2, -52, w, 104, 14, null, C.ink, 6); text(ctx, S, 0, 3, sz, C.ink, { w: 900 }); ctx.restore(); } }
}

// ---------------------------------------------------------------- office (light room, person at desk, monitor side view, screen bubble)
function office(ctx, v, t, dur, acc, seed) {
  const who = v.who || 'worker', act = v.action || 'type', alarm = act === 'shock';
  fillRR(ctx, 110, 430, 860, 430, 18, alarm ? '#f6c9c4' : C.sky, C.ink, 6);                 // window
  const r = rng(seed); for (let i = 0; i < 9; i++) { const bx = 130 + i * 92 + r() * 20, bh = 90 + r() * 200; ctx.fillStyle = shade(C.blue, .9 + r() * .2); ctx.fillRect(bx, 860 - bh, 70, bh - 2); ctx.fillStyle = C.paper; for (let k = 0; k < 4; k++) ctx.fillRect(bx + 12 + (k % 2) * 28, 860 - bh + 20 + Math.floor(k / 2) * 40, 16, 22); }
  ctx.strokeStyle = C.ink; ctx.lineWidth = 6; ctx.strokeRect(110, 430, 860, 430); ctx.beginPath(); ctx.moveTo(540, 430); ctx.lineTo(540, 860); ctx.stroke();
  const pose = { type: 'type', phone: 'phone', shock: 'shock', think: 'think', sleep: 'sleep' }[act] || 'type';
  person(ctx, 450, 1190, 760, who, pose, t, { seed });
  // desk
  glow(ctx, 0, 0, () => fillRR(ctx, 90, 930, 900, 54, 10, '#c8915f')); fillRR(ctx, 90, 930, 900, 54, 10, null, C.ink, 6); fillRR(ctx, 130, 984, 820, 260, 6, '#a8744a', C.ink, 6);
  // monitor (side view) + mug + papers
  ctx.save(); ctx.translate(800, 930); ctx.fillStyle = C.ink2; ctx.fillRect(-14, -46, 28, 46); ctx.beginPath(); ctx.moveTo(-160, -320); ctx.lineTo(120, -350); ctx.lineTo(120, -60); ctx.lineTo(-160, -80); ctx.closePath(); ctx.fillStyle = C.ink2; ctx.fill(); ctx.strokeStyle = C.ink; ctx.lineWidth = 6; ctx.stroke();
  ctx.fillStyle = alarm && Math.sin(t * 10) > 0 ? C.red : C.sky; ctx.beginPath(); ctx.moveTo(-160, -320); ctx.lineTo(-180, -310); ctx.lineTo(-180, -90); ctx.lineTo(-160, -80); ctx.closePath(); ctx.fill(); ctx.stroke(); ctx.restore();
  fillRR(ctx, 170, 870, 70, 62, 10, C.white, C.ink, 5); fillRR(ctx, 300, 912, 260, 18, 4, C.white, C.ink, 4);
  if (alarm) { ctx.save(); ctx.globalAlpha = .12 + .1 * Math.sin(t * 10); ctx.fillStyle = C.red; ctx.fillRect(0, 0, W, 1920); ctx.restore(); }
  bubble(ctx, v.screen, CX, 330, t, Math.min(cue(v, (v.screen || '').split(' ')[0], .3), dur * .5), { mono: true, color: alarm ? C.red : C.ink });
}

// ---------------------------------------------------------------- hacker (ink room - the one intentionally dark scene; no neon)
function hacker(ctx, v, t, dur, acc, seed) {
  ctx.fillStyle = C.ink; ctx.fillRect(0, 0, W, 1920);
  ctx.fillStyle = C.ink2; ctx.beginPath(); ctx.arc(CX, 1150, 620, Math.PI, 0); ctx.fill();
  const n = clamp(v.count || 1, 1, 3), xs = n === 1 ? [CX] : n === 2 ? [330, 750] : [230, 540, 850], hh = n === 1 ? 820 : n === 2 ? 700 : 600;
  xs.forEach((x, i) => person(ctx, x, 1130, hh, 'hacker', 'type', t + i * .7, { seed: seed + i, outline: '#9aa3c7' }));
  xs.forEach((x, i) => { const w = n === 1 ? 460 : 300; ctx.fillStyle = '#c9ced8'; ctx.strokeStyle = '#0b0d1a'; ctx.lineWidth = 5; ctx.beginPath(); ctx.moveTo(x - w / 2 + 20, 905); ctx.lineTo(x + w / 2 - 20, 905); ctx.lineTo(x + w / 2 - 50, 905 - w * .55); ctx.lineTo(x - w / 2 + 50, 905 - w * .55); ctx.closePath(); ctx.fill(); ctx.stroke(); ctx.fillStyle = C.red; ctx.beginPath(); ctx.arc(x, 905 - w * .28, 16, 0, 6.283); ctx.fill(); fillRR(ctx, x - w / 2, 900, w, 26, 8, '#9aa3b2', '#0b0d1a', 5); });
  fillRR(ctx, 50, 930, 980, 36, 8, '#5b4a3a', '#0b0d1a', 5);
  // floating code lines (ink-on-ink, readable, no glow)
  for (let i = 0; i < 7; i++) { const y = 420 + i * 62, x = 80 + (i % 2) * 520, wdt = 140 + ((hash(i + Math.floor(t * 2)) % 260)); ctx.globalAlpha = .45; fillRR(ctx, x, y, wdt, 18, 9, i === 3 ? C.red : C.teal); ctx.globalAlpha = 1; }
  bubble(ctx, v.screen, CX, 330, t, Math.min(cue(v, (v.screen || '').split(' ')[0], .3), dur * .5), { mono: true, bg: C.white, color: C.ink });
}

// ---------------------------------------------------------------- server room (isometric racks; alarm = red beacon + tint)
function servers(ctx, v, t, dur, acc, seed) {
  const st = v.state || 'ok', u = 46, ox = CX, oy = 600, r = rng(seed), blink = Math.sin(t * 10) > 0;
  isoBox(ctx, ox, oy, u, -1, -1, 0, 12, 12, .2, isDark(v.mood) ? '#3a3f63' : '#d8cdb5');
  for (let row = 0; row < 3; row++) for (let i = 0; i < 4; i++) {
    const x = 1 + i * 2.4, y = 1 + row * 3.4, kk = ease((t - (row * 4 + i) * .04) / .4); if (kk <= 0) continue;
    isoBox(ctx, ox, oy, u, x, y, .2, 1.6, 1.4, 5 * kk, st === 'dark' ? '#4b4f6b' : '#5d6a8a');
    for (let q = 0; q < 9; q++) { const [lx, ly] = isoP(ox, oy, u, x + .3 + (q % 3) * .45, y + 1.4, .9 + Math.floor(q / 3) * 1.4); if (1.4 * Math.floor(q / 3) + 1 > 5 * kk) continue; ctx.fillStyle = st === 'dark' ? '#2b2f45' : st === 'alarm' ? ((blink || q % 3 === 0) ? C.red : '#7a2a33') : (r() < .8 && Math.sin(t * 6 + q + i) > -.5 ? C.green : C.yel); ctx.fillRect(lx - 9, ly - 5, 18, 10); }
  }
  if (st === 'alarm') {
    ctx.save(); ctx.globalAlpha = .14 + .1 * Math.sin(t * 10); ctx.fillStyle = C.red; ctx.fillRect(0, 0, W, 1920); ctx.restore();
    const k = pop(t, .25); ctx.save(); ctx.translate(CX, 560); ctx.scale(k, k); ctx.beginPath(); ctx.moveTo(0, -130); ctx.lineTo(140, 105); ctx.lineTo(-140, 105); ctx.closePath(); glow(ctx, 0, 0, () => { ctx.fillStyle = C.yel; ctx.fill(); }); ctx.strokeStyle = C.ink; ctx.lineWidth = 8; ctx.stroke(); text(ctx, '!', 0, 30, 150, C.ink, { w: 900 }); ctx.restore();
  }
  if (v.label) pill(ctx, v.label.toUpperCase(), CX, 330, 52, st === 'alarm' ? C.red : C.yel, st === 'alarm' ? C.white : C.ink, ease(t / .35));
}

// ---------------------------------------------------------------- people (colour disc behind, speech bubble, label)
function people(ctx, v, t, dur, acc, seed) {
  const who = Array.isArray(v.who) ? v.who.slice(0, 4) : [v.who || 'worker'], n = who.length, act = v.action || 'talk';
  ctx.save(); ctx.fillStyle = (MOOD[v.mood] || MOOD.calm)[1]; ctx.beginPath(); ctx.arc(CX, 820, 420 * ease(t / .45), 0, 6.283); ctx.fill(); ctx.restore();
  floorDisc(ctx, CX, 1135, 470, C.ink, .12);
  const spread = n === 1 ? 0 : Math.min(300, 760 / (n - 1)), h = n <= 2 ? 690 : n === 3 ? 600 : 520;
  const pose = { talk: 'talk', shock: 'shock', point: 'point', walk: 'walk', cheer: 'cheer', arrest: 'arrest' }[act] || 'talk';
  who.forEach((role, i) => {
    const x = CX + (i - (n - 1) / 2) * spread, k = pop(t, i * .12, .4), dx = pose === 'walk' ? (t - dur / 2) * 40 : 0;
    let p = pose; if (act === 'arrest') p = (role === 'crook' || role === 'hacker') ? 'arrest' : 'point'; if (act === 'talk' && i % 2 === 1) p = 'idle';
    ctx.save(); ctx.translate(x + dx, 1130); ctx.scale(1, k); person(ctx, 0, 0, h, role, p, t, { seed: seed + i * 5, flip: i >= n / 2 && n > 1 }); ctx.restore();
  });
  if (act === 'talk' && !v.label) { const k = pop(t, .45); if (k > 0) { ctx.save(); ctx.translate(CX - (n - 1) / 2 * spread + 150, 1130 - h - 40); ctx.scale(k, k); fillRR(ctx, -110, -60, 220, 120, 50, C.white, C.ink, 6); for (let i = 0; i < 3; i++) { ctx.fillStyle = C.ink; ctx.beginPath(); ctx.arc(-50 + i * 50, 0, 13 + 5 * Math.sin(t * 6 + i), 0, 6.283); ctx.fill(); } ctx.restore(); } }
  if (v.label) pill(ctx, v.label.toUpperCase(), CX, 330, 54, C.yel, C.ink, ease((t - cue(v, v.label.split(' ')[0], .2)) / .3));
}

// ---------------------------------------------------------------- phone (real-looking app UI on a colour disc)
function phone(ctx, v, t, dur, acc, seed) {
  ctx.save(); ctx.fillStyle = (MOOD[v.mood] || MOOD.calm)[1]; ctx.beginPath(); ctx.arc(CX, 780, 430, 0, 6.283); ctx.fill(); ctx.restore();
  const k = back(t / .45), app = v.app || 'alert'; ctx.save(); ctx.translate(CX, 770 + (1 - k) * 500); ctx.rotate(-.04 + Math.sin(t * 1.4) * .015);
  const w = 500, h = 900; glow(ctx, 0, 0, () => fillRR(ctx, -w / 2, -h / 2, w, h, 70, C.ink)); fillRR(ctx, -w / 2 + 18, -h / 2 + 18, w - 36, h - 36, 54, app === 'alert' ? '#fff1f0' : C.white); fillRR(ctx, -70, -h / 2 + 30, 140, 28, 14, C.ink);
  const L = -w / 2 + 50;
  if (app === 'email' || app === 'bank') {
    text(ctx, app === 'bank' ? 'My Bank' : 'Inbox', L, -h / 2 + 120, 44, C.ink, { align: 'left', w: 900 });
    for (let i = 0; i < 4; i++) { const yy = -h / 2 + 180 + i * 130, hot = i === 0, kk = pop(t, .2 + i * .1); if (kk <= 0) continue; fillRR(ctx, -w / 2 + 34, yy, w - 68, 112, 18, hot ? '#fff3c4' : '#f1ede4', hot ? C.ink : null, 4);
      if (hot) { text(ctx, v.from || 'unknown', L + 10, yy + 34, 28, C.ink, { align: 'left', w: 900 }); wrap(ctx, v.text || '', w - 120, 26, 700).slice(0, 2).forEach((l, j) => text(ctx, l, L + 10, yy + 68 + j * 28, 26, C.ink2, { align: 'left', w: 700 })); }
      else { fillRR(ctx, L + 10, yy + 28, 200, 16, 8, '#d8d1c2'); fillRR(ctx, L + 10, yy + 62, 300, 12, 6, '#e3ddd0'); } }
    if (app === 'bank') { const bal = Math.max(0, 1 - ease((t - .6) / 1.6)); text(ctx, '$' + Math.round(bal * 81000000).toLocaleString('en-US'), 0, 280, 56, bal < .2 ? C.red : C.ink, { w: 900 }); }
  } else if (app === 'chat') {
    const lines = String(v.text || '').split(/(?<=[.?!])\s+/).filter(Boolean); text(ctx, v.from || 'Chat', 0, -h / 2 + 110, 38, C.ink, { w: 900 });
    lines.slice(0, 4).forEach((l, i) => { const kk = pop(t, .3 + i * .55); if (kk <= 0) return; const ls = wrap(ctx, l, 330, 34, 700), bh = 44 + ls.length * 40, yy = -h / 2 + 180 + i * 170, left = i % 2 === 0; ctx.save(); ctx.translate(left ? -w / 2 + 40 : w / 2 - 40 - 360, yy); ctx.scale(kk, kk); fillRR(ctx, 0, 0, 360, bh, 24, left ? '#ece6d8' : C.blue, C.ink, 4); ls.forEach((x, j) => text(ctx, x, 24, 40 + j * 40, 34, left ? C.ink : C.white, { align: 'left', w: 700 })); ctx.restore(); });
  } else if (app === 'call') {
    ctx.fillStyle = C.ink2; ctx.beginPath(); ctx.arc(0, -150, 100, 0, 6.283); ctx.fill(); text(ctx, v.from || 'Unknown', 0, 0, 46, C.ink, { w: 900 }); text(ctx, v.text || 'Incoming call...', 0, 60, 30, C.ink2, { w: 700 });
    for (const [x, c] of [[-120, C.red], [120, C.green]]) { const pr = 1 + .1 * Math.sin(t * 8); ctx.beginPath(); ctx.arc(x, 300, 56 * pr, 0, 6.283); ctx.fillStyle = c; ctx.fill(); ctx.strokeStyle = C.ink; ctx.lineWidth = 5; ctx.stroke(); }
  } else {
    const pr = 1 + .06 * Math.sin(t * 9); ctx.save(); ctx.scale(pr, pr); ctx.beginPath(); ctx.moveTo(0, -270); ctx.lineTo(160, 0); ctx.lineTo(-160, 0); ctx.closePath(); ctx.fillStyle = C.red; ctx.fill(); ctx.strokeStyle = C.ink; ctx.lineWidth = 8; ctx.stroke(); text(ctx, '!', 0, -85, 150, C.white, { w: 900 }); ctx.restore();
    const FR = (v.from || 'WARNING').toUpperCase(); text(ctx, FR, 0, 90, fitText(ctx, FR, w - 90, 46, 900), C.ink, { w: 900 }); wrap(ctx, v.text || '', w - 110, 36, 800).slice(0, 3).forEach((l, i) => text(ctx, l, 0, 160 + i * 44, 36, C.red, { w: 800 }));
  }
  ctx.restore();
}

// ---------------------------------------------------------------- email window (bad line highlighted when the narrator says it)
function email(ctx, v, t, dur, acc, seed) {
  const k = ease(t / .4), x = 80, y = 460 + (1 - k) * 120, w = 920, h = 660; ctx.save(); ctx.globalAlpha *= k;
  card(ctx, x, y, w, h, C.white, 24); fillRR(ctx, x + 3, y + 3, w - 6, 74, 22, '#ece6d8'); ctx.strokeStyle = C.ink; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(x, y + 78); ctx.lineTo(x + w, y + 78); ctx.stroke();
  [[C.red, 0], [C.yel, 1], [C.green, 2]].forEach(([c, i]) => { ctx.beginPath(); ctx.arc(x + 46 + i * 40, y + 40, 12, 0, 6.283); ctx.fillStyle = c; ctx.fill(); ctx.strokeStyle = C.ink; ctx.lineWidth = 3; ctx.stroke(); });
  text(ctx, 'FROM', x + 50, y + 140, 26, C.grey, { align: 'left', w: 800 }); text(ctx, v.from || '', x + 170, y + 140, fitText(ctx, v.from || '', 680, 38, 700), C.ink, { align: 'left', w: 700 });
  text(ctx, 'SUBJECT', x + 50, y + 215, 26, C.grey, { align: 'left', w: 800 }); text(ctx, v.subject || '', x + 210, y + 215, fitText(ctx, v.subject || '', 640, 42, 900), C.ink, { align: 'left', w: 900 });
  const r = rng(seed); for (let i = 0; i < 4; i++) fillRR(ctx, x + 50, y + 290 + i * 46, 400 + r() * 380, 16, 8, '#e3ddd0');
  if (v.line) { const d = Math.min(cue(v, v.line.split(' ')[0], .9), dur * .55), kk = ease((t - d) / .45); marker(ctx, x + 40, y + 500, w - 80, 90, kk); if (kk > .5) text(ctx, v.line, x + 70, y + 545, fitText(ctx, v.line, w - 160, 46, 900), C.ink, { align: 'left', w: 900 }); }
  ctx.restore();
  const d2 = Math.min(cue(v, v.line ? v.line.split(' ')[0] : null, 1.4) + .6, dur * .7);
  if (t > d2) { const kk = ease((t - d2) / .45), mx = lerp(900, 640, kk), my = lerp(1250, 1015, kk); ctx.beginPath(); ctx.moveTo(mx, my); ctx.lineTo(mx, my + 64); ctx.lineTo(mx + 17, my + 48); ctx.lineTo(mx + 44, my + 48); ctx.closePath(); ctx.fillStyle = C.white; ctx.fill(); ctx.strokeStyle = C.ink; ctx.lineWidth = 5; ctx.stroke(); if (t > d2 + .5) { const ph = ((t - d2 - .5) * 1.4) % 1; ctx.beginPath(); ctx.arc(mx, my, 20 + 70 * ph, 0, 6.283); ctx.strokeStyle = C.red; ctx.globalAlpha = 1 - ph; ctx.lineWidth = 6; ctx.stroke(); ctx.globalAlpha = 1; } }
}

// ---------------------------------------------------------------- hero object on a colour sticker disc
function object(ctx, v, t, dur, acc, seed) {
  const m = MOOD[v.mood] || MOOD.calm, k = back(t / .5);
  ctx.save(); ctx.translate(CX, 770); ctx.scale(k, k); glow(ctx, 0, 0, () => { ctx.fillStyle = m[1]; ctx.beginPath(); ctx.arc(0, 0, 380, 0, 6.283); ctx.fill(); }); ctx.strokeStyle = C.ink; ctx.lineWidth = 8; ctx.beginPath(); ctx.arc(0, 0, 380, 0, 6.283); ctx.stroke();
  ctx.setLineDash([18, 22]); ctx.lineWidth = 4; ctx.rotate(t * .2); ctx.beginPath(); ctx.arc(0, 0, 340, 0, 6.283); ctx.stroke(); ctx.setLineDash([]); ctx.restore();
  const bob = Math.sin(t * 2.2) * 14; ctx.save(); ctx.translate(CX, 770 + bob); ctx.scale(1.4 * k, 1.4 * k); drawIcon(ctx, v.icon, t); ctx.restore();
  if (v.text) pill(ctx, v.text.toUpperCase(), CX, 330, 58, C.yel, C.ink, ease((t - Math.min(cue(v, v.text.split(' ')[0], .25), dur * .5)) / .3));
}

// ---------------------------------------------------------------- network: laptops linked by ink lines, infection spreads over the shot
function laptopMini(ctx, x, y, hit, s = 1) { ctx.save(); ctx.translate(x, y); ctx.scale(s, s); fillRR(ctx, -26, -22, 52, 34, 5, hit ? C.red : C.sky, C.ink, 4); fillRR(ctx, -32, 12, 64, 10, 4, C.white, C.ink, 4); if (hit) text(ctx, '!', 0, -5, 26, C.white, { w: 900 }); ctx.restore(); }
function network(ctx, v, t, dur, acc, seed) {
  const r = rng(seed + 11), N = 34, pts = [];
  for (let g = 0; g < 4000 && pts.length < N; g++) { const x = 110 + r() * 860, y = 540 + r() * 620; if (pts.every(([a, b]) => (a - x) ** 2 + (b - y) ** 2 > 100 ** 2)) pts.push([x, y]); }
  const c0 = pts[0], order = pts.map((p, i) => [(p[0] - c0[0]) ** 2 + (p[1] - c0[1]) ** 2, i]).sort((a, b) => a[0] - b[0]), rank = []; order.forEach(([, i], k) => rank[i] = k);
  const n = pts.length, frac = easeIO((t - .2) / Math.max(1.5, dur * .85)), inf = frac * n, edges = [];
  pts.forEach((p, i) => pts.map((q, j) => [(p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2, j]).sort((a, b) => a[0] - b[0]).slice(1, 3).forEach(([, j]) => edges.push([i, j])));
  ctx.lineCap = 'round'; const col = fg(v.mood);
  edges.forEach(([i, j]) => { const on = rank[i] < inf && rank[j] < inf; ctx.strokeStyle = on ? C.red : col; ctx.globalAlpha = on ? 1 : .35; ctx.lineWidth = on ? 6 : 3; ctx.beginPath(); ctx.moveTo(...pts[i]); ctx.lineTo(...pts[j]); ctx.stroke(); ctx.globalAlpha = 1; });
  pts.forEach(([x, y], i) => laptopMini(ctx, x, y, rank[i] < inf, rank[i] < inf ? 1 + .15 * Math.max(0, 1 - (inf - rank[i]) / 3) : 1));
  if (v.total) { const tv = Number(String(v.total).replace(/,/g, '')), s = num(tv, easeIO(t / Math.max(.8, cue(v, String(v.total).slice(0, 2), 1.2) + .4))); ctx.save(); ctx.font = '900 130px Inter'; const w = ctx.measureText(s).width; ctx.restore(); marker(ctx, CX - w / 2 - 20, 300, w + 40, 130, 1, isDark(v.mood) ? C.red : C.yel); text(ctx, s, CX, 368, 130, isDark(v.mood) ? C.white : C.ink, { w: 900 }); text(ctx, (v.text || 'computers hit').toUpperCase(), CX, 470, 46, isDark(v.mood) ? C.yel : C.red, { w: 900 }); }
  else headline_(ctx, v.text, t, v);
}

// ---------------------------------------------------------------- globe: flat teal ocean, ink meridians, dashed route arcs drawn when each place is said, map pins
function globe(ctx, v, t, dur, acc, seed) {
  const R = 390, cx = CX, cy = 820, pts = (v.points || []).map(p => [String(p[0]), +p[1], +p[2]]); const mid = pts.length ? pts.reduce((s, p) => s + p[2], 0) / pts.length : 0, yaw = -mid * Math.PI / 180 + Math.sin(t * .3) * .15, lat0 = (pts.length ? pts.reduce((s, p) => s + p[1], 0) / pts.length : 20) * Math.PI / 180 * .6;
  const proj = (la, lo) => { la *= Math.PI / 180; lo = lo * Math.PI / 180 + yaw; const x = Math.cos(la) * Math.sin(lo), y = Math.sin(la), z = Math.cos(la) * Math.cos(lo); const y2 = y * Math.cos(lat0) - z * Math.sin(lat0), z2 = y * Math.sin(lat0) + z * Math.cos(lat0); return [cx + x * R, cy - y2 * R, z2]; };
  glow(ctx, 0, 0, () => { ctx.beginPath(); ctx.arc(cx, cy, R, 0, 6.283); ctx.fillStyle = C.teal; ctx.fill(); });
  // blobby "continents": deterministic dots clustered (flat land patches)
  const r = rng(77); ctx.fillStyle = '#9ccc9a'; for (let i = 0; i < 260; i++) { const la = (r() * 2 - 1) * 70, lo = r() * 360 - 180; if (Math.sin(la * .09) * Math.cos(lo * .05) + Math.sin(lo * .11) < .35) continue; const [x, y, z] = proj(la, lo); if (z > 0) { ctx.beginPath(); ctx.arc(x, y, 22 * (.5 + z * .5), 0, 6.283); ctx.fill(); } }
  ctx.strokeStyle = C.ink; ctx.globalAlpha = .25; ctx.lineWidth = 2;
  for (let la = -60; la <= 60; la += 30) { ctx.beginPath(); let f = true; for (let lo = -180; lo <= 180; lo += 6) { const [x, y, z] = proj(la, lo); if (z < 0) { f = true; continue; } f ? ctx.moveTo(x, y) : ctx.lineTo(x, y); f = false; } ctx.stroke(); }
  for (let lo = -180; lo < 180; lo += 30) { ctx.beginPath(); let f = true; for (let la = -90; la <= 90; la += 6) { const [x, y, z] = proj(la, lo); if (z < 0) { f = true; continue; } f ? ctx.moveTo(x, y) : ctx.lineTo(x, y); f = false; } ctx.stroke(); }
  ctx.globalAlpha = 1; ctx.strokeStyle = C.ink; ctx.lineWidth = 8; ctx.beginPath(); ctx.arc(cx, cy, R, 0, 6.283); ctx.stroke();
  for (let i = 0; i < pts.length - 1; i++) {
    const st = Math.min(cue(v, pts[i + 1][0], .4 + i * 1.0) - .2, dur * .6), k = easeIO((t - st) / 1.2); if (k <= 0) continue;
    const a = proj(pts[i][1], pts[i][2]), b = proj(pts[i + 1][1], pts[i + 1][2]), mx = (a[0] + b[0]) / 2, my = Math.min(a[1], b[1]) - 230;
    ctx.strokeStyle = C.red; ctx.lineWidth = 9; ctx.setLineDash([22, 16]); ctx.lineDashOffset = -t * 60; ctx.beginPath(); const N = 40; for (let s = 0; s <= N * k; s++) { const q = s / N, x = (1 - q) ** 2 * a[0] + 2 * (1 - q) * q * mx + q * q * b[0], y = (1 - q) ** 2 * a[1] + 2 * (1 - q) * q * my + q * q * b[1]; s ? ctx.lineTo(x, y) : ctx.moveTo(x, y); } ctx.stroke(); ctx.setLineDash([]);
    const q = k, hx = (1 - q) ** 2 * a[0] + 2 * (1 - q) * q * mx + q * q * b[0], hy = (1 - q) ** 2 * a[1] + 2 * (1 - q) * q * my + q * q * b[1]; ctx.fillStyle = C.white; ctx.strokeStyle = C.ink; ctx.lineWidth = 5; ctx.beginPath(); ctx.arc(hx, hy, 15, 0, 6.283); ctx.fill(); ctx.stroke();
  }
  pts.forEach(([nm, la, lo], i) => { const [x, y, z] = proj(la, lo); if (z < -.1) return; const kk = pop(t, Math.min(cue(v, nm, .15 + i * .3), dur * .6)); if (kk <= 0) return;
    ctx.save(); ctx.translate(x, y); ctx.scale(kk, kk); ctx.fillStyle = i === 0 ? C.yel : C.red; ctx.strokeStyle = C.ink; ctx.lineWidth = 5; ctx.beginPath(); ctx.moveTo(0, 0); ctx.bezierCurveTo(-34, -40, -30, -84, 0, -84); ctx.bezierCurveTo(30, -84, 34, -40, 0, 0); ctx.fill(); ctx.stroke(); ctx.fillStyle = C.white; ctx.beginPath(); ctx.arc(0, -58, 12, 0, 6.283); ctx.fill(); ctx.stroke(); ctx.restore();
    const near = pts.some(([, la2, lo2], j) => j < i && Math.hypot(la2 - la, lo2 - lo) < 12); pill(ctx, nm.toUpperCase(), x + (near ? 150 : 0), near ? y + 60 : y - 130, 38, C.white, C.ink, kk); });
}

// ---------------------------------------------------------------- flow: parties as cards, money hops when the next party is named
function flow(ctx, v, t, dur, acc, seed) {
  const nodes = (v.nodes || ['A', 'B']).slice(0, 4), n = nodes.length, y0 = 430, y1 = 1120, ys = nodes.map((_, i) => n > 1 ? y0 + (y1 - y0) * i / (n - 1) : 760);
  for (let i = 0; i < n - 1; i++) {
    const st = Math.min(cue(v, nodes[i + 1].split(' ')[0], .45 + i * .8) - .35, dur * .7), k = easeIO((t - st) / .8), a = ys[i] + 72, b = ys[i + 1] - 72, blocked = v.blocked && i === n - 2 && k >= 1;
    ctx.strokeStyle = fg(v.mood); ctx.globalAlpha = .3; ctx.lineWidth = 8; ctx.setLineDash([16, 14]); ctx.beginPath(); ctx.moveTo(CX, a); ctx.lineTo(CX, b); ctx.stroke(); ctx.setLineDash([]); ctx.globalAlpha = 1;
    if (k > 0) {
      ctx.strokeStyle = blocked ? C.red : C.green; ctx.lineWidth = 12; ctx.beginPath(); ctx.moveTo(CX, a); ctx.lineTo(CX, lerp(a, b, k)); ctx.stroke();
      ctx.fillStyle = blocked ? C.red : C.green; ctx.beginPath(); const ay = lerp(a, b, k); ctx.moveTo(CX - 26, ay - 20); ctx.lineTo(CX + 26, ay - 20); ctx.lineTo(CX, ay + 12); ctx.closePath(); ctx.fill();
      for (let q = 0; q < 2; q++) { const yy = lerp(a, lerp(a, b, k), (t * .9 + q / 2) % 1); ctx.save(); ctx.translate(CX + 70 + q * 10, yy); ctx.rotate(Math.sin(t * 3 + q) * .3); fillRR(ctx, -42, -20, 84, 40, 6, '#8fd19e', C.ink, 4); text(ctx, '$', 0, 2, 26, C.ink, { w: 900 }); ctx.restore(); }
      if (v.amount && k > .4) pill(ctx, v.amount, CX - 240, (a + b) / 2, 50, C.yel, C.ink, clamp((k - .4) * 3));
    }
    if (blocked) { const kk = back((t - st - 1.1) / .3); if (kk > 0) { ctx.save(); ctx.translate(CX, (a + b) / 2); ctx.scale(kk, kk); ctx.strokeStyle = C.red; ctx.lineWidth = 28; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(-70, -70); ctx.lineTo(70, 70); ctx.moveTo(70, -70); ctx.lineTo(-70, 70); ctx.stroke(); ctx.restore(); } }
  }
  nodes.forEach((nm, i) => { const k = pop(t, i === 0 ? 0 : Math.min(cue(v, nm.split(' ')[0], i * .2) - .3, dur * .6)); if (k <= 0) return; ctx.save(); ctx.translate(CX, ys[i]); ctx.scale(k, k); const S = nm.toUpperCase(), sz = fitText(ctx, S, 560, 50, 900); card(ctx, -340, -72, 680, 144, i === 0 ? C.white : i === n - 1 ? '#ffe8a3' : C.white, 22); text(ctx, S, 0, 3, sz, C.ink, { w: 900 }); ctx.restore(); });
}

// ---------------------------------------------------------------- counter: finishes counting exactly when the number is spoken
function counter(ctx, v, t, dur, acc, seed) {
  const val = Number(String(v.value).replace(/,/g, '')) || 0, d = cue(v, String(v.value).replace(/\..*$/, ''), Math.min(1.6, dur * .6)), k = easeIO(t / Math.max(.8, d + .35));
  const cx = CX, cy = 760, R = 330, m = MOOD[v.mood] || MOOD.calm;
  glow(ctx, 0, 0, () => { ctx.fillStyle = C.white; ctx.beginPath(); ctx.arc(cx, cy, R, 0, 6.283); ctx.fill(); }); ctx.strokeStyle = C.ink; ctx.lineWidth = 8; ctx.beginPath(); ctx.arc(cx, cy, R, 0, 6.283); ctx.stroke();
  ctx.strokeStyle = m[2] === C.teal ? C.red : m[2]; ctx.lineWidth = 34; ctx.lineCap = 'butt'; ctx.beginPath(); ctx.arc(cx, cy, R - 40, -Math.PI / 2, -Math.PI / 2 + k * 6.283); ctx.stroke();
  for (let i = 0; i < 60; i++) { const a = i / 60 * 6.283; ctx.strokeStyle = C.ink; ctx.lineWidth = i % 5 ? 3 : 6; ctx.beginPath(); ctx.moveTo(cx + Math.cos(a) * (R - 8), cy + Math.sin(a) * (R - 8)); ctx.lineTo(cx + Math.cos(a) * (R - (i % 5 ? 22 : 34)), cy + Math.sin(a) * (R - (i % 5 ? 22 : 34))); ctx.stroke(); }
  const s = `${v.prefix || ''}${num(val, k)}${v.suffix || ''}`, sz = fitText(ctx, s, 470, 170, 900); text(ctx, s, cx, cy - 10, sz, C.ink, { w: 900 });
  if (v.label) pill(ctx, String(v.label).toUpperCase(), cx, cy + R + 70, 44, C.yel, C.ink, ease((t - d) / .3));
}

// ---------------------------------------------------------------- timeline: each date appears when it is spoken
function timeline(ctx, v, t, dur, acc, seed) {
  const items = (v.items || []).slice(0, 4), n = items.length || 1, y0 = 470, y1 = 1110, ys = items.map((_, i) => n > 1 ? y0 + (y1 - y0) * i / (n - 1) : 790), x = 250, col = fg(v.mood);
  const starts = items.map(([d], i) => Math.min(cue(v, String(d).split(' ')[0], .2 + i * Math.min(.9, dur * .7 / n)), dur * .8));
  const last = starts.reduce((m, s, i) => (t >= s ? i : m), 0), rev = n > 1 ? clamp((last + clamp((t - starts[last]) / .5)) / (n - 1)) : 1;
  ctx.strokeStyle = col; ctx.lineWidth = 8; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(x, y0 - 40); ctx.lineTo(x, lerp(y0 - 40, y1 + 40, ease(rev))); ctx.stroke();
  items.forEach(([d, e], i) => { const k = pop(t, starts[i]); if (k <= 0) return; ctx.save(); ctx.translate(x, ys[i]); ctx.scale(k, k); ctx.fillStyle = i === last ? C.red : C.yel; ctx.strokeStyle = C.ink; ctx.lineWidth = 6; ctx.beginPath(); ctx.arc(0, 0, 32, 0, 6.283); ctx.fill(); ctx.stroke(); ctx.restore();
    const D = String(d).toUpperCase(), sz = fitText(ctx, D, 600, 66, 900); ctx.save(); ctx.font = `900 ${sz}px Inter`; const wd = ctx.measureText(D).width; ctx.restore(); marker(ctx, x + 70, ys[i] - 78, wd + 30, sz * .95, ease((t - starts[i]) / .3));
    text(ctx, D, x + 85, ys[i] - 36, sz, C.ink, { align: 'left', w: 900, a: k }); wrap(ctx, String(e), 660, 52, 800).slice(0, 2).forEach((l, j) => text(ctx, l, x + 85, ys[i] + 34 + j * 58, 52, col, { align: 'left', w: 800, a: k })); });
}

// ---------------------------------------------------------------- padlock: opens / cracks on the spoken trigger word
function lock(ctx, v, t, dur, acc, seed) {
  const st = v.state || 'locked', trig = Math.min(cue(v, st === 'crack' ? 'stol' : st === 'open' ? 'open' : (v.text || '').split(' ')[0], dur * .45), dur * .7), k = easeIO((t - trig) / .5), cx = CX, cy = 860;
  const body = st === 'locked' ? C.green : st === 'crack' ? C.red : C.yel, lift = st === 'open' ? k * 120 : 0;
  ctx.save(); ctx.fillStyle = (MOOD[v.mood] || MOOD.calm)[1]; ctx.beginPath(); ctx.arc(cx, 780, 420, 0, 6.283); ctx.fill(); ctx.restore();
  ctx.lineCap = 'round'; ctx.strokeStyle = C.ink; ctx.lineWidth = 74; ctx.beginPath(); ctx.arc(cx, cy - 180 - lift, 150, Math.PI, 0); ctx.moveTo(cx - 150, cy - 180 - lift); ctx.lineTo(cx - 150, cy - 90 - (st === 'open' ? lift : 0)); ctx.moveTo(cx + 150, cy - 180 - lift); ctx.lineTo(cx + 150, cy - 90); ctx.stroke();
  ctx.strokeStyle = '#cfd5de'; ctx.lineWidth = 56; ctx.stroke();
  glow(ctx, 0, 0, () => fillRR(ctx, cx - 250, cy - 120, 500, 380, 46, body)); fillRR(ctx, cx - 250, cy - 120, 500, 380, 46, null, C.ink, 8);
  ctx.fillStyle = C.ink; ctx.beginPath(); ctx.arc(cx, cy + 40, 52, 0, 6.283); ctx.fill(); ctx.fillRect(cx - 20, cy + 40, 40, 115);
  if (st === 'crack' && k > 0) { const r = rng(5); ctx.strokeStyle = C.white; ctx.lineWidth = 12; ctx.beginPath(); let x = cx - 60, y = cy - 120; ctx.moveTo(x, y); for (let i = 0; i < 8 * k; i++) { x += r() * 90 - 35; y += 45; ctx.lineTo(x, y); } ctx.stroke(); }
  if (v.text) pill(ctx, v.text.toUpperCase(), CX, 330, 56, st === 'crack' ? C.red : C.yel, st === 'crack' ? C.white : C.ink, ease((t - .1) / .3));
}

// ---------------------------------------------------------------- terminal (light editor window, typed as narrated)
function terminal(ctx, v, t, dur, acc, seed) {
  const lines = (v.lines || []).slice(0, 5).map(l => (l.startsWith('>') ? l : '> ' + l)), x = 70, y = 470, w = 940, h = 660;
  card(ctx, x, y, w, h, '#1f2440', 26); fillRR(ctx, x + 3, y + 3, w - 6, 70, 24, '#2c3256'); [[C.red, 0], [C.yel, 1], [C.green, 2]].forEach(([c, i]) => { ctx.beginPath(); ctx.arc(x + 44 + i * 38, y + 38, 11, 0, 6.283); ctx.fillStyle = c; ctx.fill(); });
  const speed = Math.max(18, lines.join('').length / Math.max(1, dur * .7)); let budget = Math.floor(Math.max(0, t - .25) * speed); ctx.font = '700 46px monospace'; ctx.textBaseline = 'middle'; ctx.textAlign = 'left';
  lines.forEach((l, i) => { if (budget <= 0) return; const s = l.slice(0, budget); budget -= l.length + 4; ctx.fillStyle = /fail|denied|error|wiped|locked|not found/i.test(l) ? '#ff8a80' : '#e9f5db'; ctx.fillText(s, x + 44, y + 145 + i * 92); if (budget < 0 && Math.sin(t * 9) > 0) ctx.fillRect(x + 50 + ctx.measureText(s).width, y + 122 + i * 92, 24, 46); });
}

// ---------------------------------------------------------------- dossier: manila case file with photo, stamp lands on the name
function dossier(ctx, v, t, dur, acc, seed) {
  const k = ease(t / .4), x = 90, y = 430 + (1 - k) * 90, w = 900, h = 740, rows = (v.rows || []).slice(0, 4); ctx.save(); ctx.globalAlpha *= k;
  fillRR(ctx, x + 40, y - 50, 300, 80, 18, '#d9b26f', C.ink, 6); card(ctx, x, y, w, h, '#e7c98b', 22); text(ctx, 'CASE FILE', x + 190, y - 12, 34, C.ink, { w: 900 });
  card(ctx, x + 40, y + 50, 260, 320, '#f7efe0', 10); ctx.save(); rr(ctx, x + 40, y + 50, 260, 320, 10); ctx.clip(); ctx.fillStyle = C.ink2; ctx.beginPath(); ctx.arc(x + 170, y + 170, 70, 0, 6.283); ctx.fill(); ctx.beginPath(); ctx.ellipse(x + 170, y + 360, 120, 110, 0, Math.PI, 0); ctx.fill(); ctx.restore();
  text(ctx, '?', x + 170, y + 175, 80, C.white, { w: 900 });
  const T = String(v.title || '').toUpperCase(); text(ctx, T, x + 330, y + 100, fitText(ctx, T, 530, 62, 900), C.ink, { align: 'left', w: 900 });
  rows.forEach(([a, b], i) => { const kk = ease((t - .5 - i * .35) / .3), yy = y + 200 + i * 74; text(ctx, String(a).toUpperCase(), x + 330, yy, 30, C.ink2, { align: 'left', w: 900, a: kk }); text(ctx, String(b), x + 330, yy + 34, fitText(ctx, String(b), 520, 40, 800), C.ink, { align: 'left', w: 800, a: kk }); });
  ctx.restore();
  const sk = clamp((t - Math.min(cue(v, (v.title || '').split(' ')[0], 1.2) + .6, dur * .7)) / .22); if (sk > 0) { ctx.save(); ctx.translate(x + 640, y + 620); ctx.rotate(-.14); const sc = 1.8 - .8 * ease(sk); ctx.scale(sc, sc); ctx.globalAlpha = clamp(sk * 2); fillRR(ctx, -200, -60, 400, 120, 14, null, C.red, 12); text(ctx, 'WANTED', 0, 4, 84, C.red, { w: 900 }); ctx.restore(); }
}

// ---------------------------------------------------------------- headline: a real newspaper page
function headline(ctx, v, t, dur, acc, seed) {
  const k = back(t / .45); ctx.save(); ctx.translate(CX, 800 + (1 - k) * 600); ctx.rotate(-.05 + (1 - k) * .3);
  const ls = wrap(ctx, String(v.text || '').toUpperCase(), 760, 92, 900).slice(0, 4), h = 330 + ls.length * 104;
  card(ctx, -440, -h / 2, 880, h, '#fbf7ee', 6); text(ctx, 'THE DAILY TECH', 0, -h / 2 + 62, 58, C.ink, { w: 900 }); ctx.fillStyle = C.ink; ctx.fillRect(-400, -h / 2 + 104, 800, 6); ctx.fillRect(-400, -h / 2 + 116, 800, 2);
  ls.forEach((l, i) => text(ctx, l, 0, -h / 2 + 190 + i * 104, fitText(ctx, l, 800, 92, 900), C.ink, { w: 900 }));
  const r = rng(seed); for (let c = 0; c < 3; c++) for (let i = 0; i < 4; i++) fillRR(ctx, -400 + c * 275, h / 2 - 150 + i * 28, 240 - r() * 60, 12, 4, '#cbc3b2');
  ctx.restore();
}

// ---------------------------------------------------------------- stamp: document redacted, stamp slams when its word is spoken
function stamp(ctx, v, t, dur, acc, seed) {
  const x = 140, y = 420, w = 800, h = 820, slam = Math.min(cue(v, (v.text || '').split(' ')[0], dur * .45), dur * .7);
  ctx.save(); ctx.translate(CX, 830); ctx.rotate(.03); ctx.translate(-CX, -830); card(ctx, x, y, w, h, '#fbf7ee', 8);
  const r = rng(seed); for (let i = 0; i < 14; i++) fillRR(ctx, x + 60, y + 80 + i * 50, 380 + r() * 300, 16, 6, '#cbc3b2');
  for (let i = 0; i < 6; i++) { const kk = easeIO((t - .1 - i * .1) / .35); if (kk > 0) fillRR(ctx, x + 60 + r() * 80, y + 130 + i * 100, (300 + r() * 340) * kk, 40, 3, C.ink); } ctx.restore();
  const k = clamp((t - slam) / .2); if (k > 0) { const sc = 2.2 - 1.2 * ease(k); ctx.save(); ctx.translate(CX, 820); ctx.rotate(-.18); ctx.scale(sc, sc); ctx.globalAlpha = clamp(k * 2); const S = String(v.text || 'HACKED').toUpperCase(), sz = fitText(ctx, S, 600, 130, 900); fillRR(ctx, -360, -110, 720, 220, 20, null, C.red, 16); text(ctx, S, 0, 6, sz, C.red, { w: 900 }); ctx.restore(); }
}

// ---------------------------------------------------------------- split: before/after cards, the difference circled when spoken
function lcsMask(a, b) { const n = a.length, m = b.length, D = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0)); for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--) D[i][j] = a[i] === b[j] ? D[i + 1][j + 1] + 1 : Math.max(D[i + 1][j], D[i][j + 1]); const mask = new Array(m).fill(false); let i = 0, j = 0; while (i < n && j < m) { if (a[i] === b[j]) { mask[j] = true; i++; j++; } else if (D[i + 1][j] >= D[i][j + 1]) i++; else j++; } return mask; }
function split(ctx, v, t, dur, acc, seed) {
  const L = String(v.left || ''), R = String(v.right || ''), d2 = Math.min(cue(v, R, .5), dur * .6), k1 = pop(t, 0), k2 = pop(t, d2);
  [[L, 520, k1, C.green, 'RIGHT'], [R, 1000, k2, C.red, 'WRONG']].forEach(([s, y, k, c, tag], i) => { if (k <= 0) return; ctx.save(); ctx.translate(CX, y); ctx.scale(k, k); card(ctx, -440, -150, 880, 300, C.white, 26);
    fillRR(ctx, -440, -150, 880, 300, 26, null, c, 10); pill(ctx, tag, -300, -150, 34, c, C.white);
    const sz = fitText(ctx, s, 760, 120, 900); ctx.font = `900 ${sz}px Inter, Arial`; let x = -ctx.measureText(s).width / 2; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; let mask = i === 1 ? lcsMask(L.toLowerCase(), s.toLowerCase()) : null; if (mask && mask.filter(x => !x).length > 4) mask = null;
    for (let j = 0; j < s.length; j++) { const diff = mask && !mask[j], cw = ctx.measureText(s[j]).width; ctx.fillStyle = diff || (i === 1 && !mask) ? C.red : C.ink; ctx.fillText(s[j], x, 14);
      if (diff && t > d2 + .5) { ctx.strokeStyle = C.red; ctx.lineWidth = 7; ctx.beginPath(); ctx.ellipse(x + cw / 2, 14, cw * .9, sz * .62, -.2, 0, 6.283 * clamp((t - d2 - .5) / .4)); ctx.stroke(); } x += cw; }
    ctx.restore(); });
  const kv = pop(t, Math.max(.2, d2 - .2)); if (kv > 0) { ctx.save(); ctx.translate(CX, 760); ctx.scale(kv, kv); ctx.beginPath(); ctx.arc(0, 0, 66, 0, 6.283); ctx.fillStyle = C.yel; ctx.fill(); ctx.strokeStyle = C.ink; ctx.lineWidth = 6; ctx.stroke(); text(ctx, 'VS', 0, 4, 56, C.ink, { w: 900 }); ctx.restore(); }
}


// ---------------------------------------------------------------- steps: numbered story steps, each card lands when its first word is spoken
function steps(ctx, v, t, dur, acc, seed) {
  const items = (v.items || []).slice(0, 4), n = items.length || 1, gap = Math.min(250, 760 / n), y0 = 790 - (n - 1) * gap / 2;
  if (v.title) pill(ctx, String(v.title).toUpperCase(), CX, 330, 52, C.yel, C.ink, ease(t / .3));
  const cols = [C.yel, C.sky, C.orange, C.green];
  items.forEach((it, i) => {
    const [ic, tx] = Array.isArray(it) ? it : [null, it], d = Math.min(cue(v, String(tx).split(' ')[0], .25 + i * Math.min(1, dur * .7 / n)), dur * .8), k = pop(t, d); if (k <= 0) return;
    const y = y0 + i * gap; ctx.save(); ctx.translate(CX + (1 - ease((t - d) / .4)) * 300, y);
    card(ctx, -440, -gap * .38, 880, gap * .76, C.white, 26);
    ctx.fillStyle = cols[i % 4]; ctx.strokeStyle = C.ink; ctx.lineWidth = 6; ctx.beginPath(); ctx.arc(-350, 0, 58, 0, 6.283); ctx.fill(); ctx.stroke(); text(ctx, String(i + 1), -350, 4, 70, C.ink, { w: 900 });
    if (ic) { ctx.save(); ctx.translate(330, 0); ctx.scale(.36, .36); drawIcon(ctx, ic, t); ctx.restore(); }
    const ls = wrap(ctx, String(tx), ic ? 470 : 640, 50, 800).slice(0, 2); ls.forEach((l, j) => text(ctx, l, -260, (j - (ls.length - 1) / 2) * 56, 50, C.ink, { align: 'left', w: 800 }));
    ctx.restore();
    if (i < n - 1 && t > d + .4) { ctx.strokeStyle = fg(v.mood); ctx.lineWidth = 7; ctx.setLineDash([12, 12]); ctx.beginPath(); ctx.moveTo(CX - 350, y + gap * .38); ctx.lineTo(CX - 350, y + gap * .62); ctx.stroke(); ctx.setLineDash([]); }
  });
}

// ---------------------------------------------------------------- face: one character close-up showing a feeling, with a speech or thought bubble
function face(ctx, v, t, dur, acc, seed) {
  const emo = v.emotion || 'worried', pose = { shock: 'shock', happy: 'cheer', worried: 'think', think: 'think', angry: 'point', sad: 'idle', talk: 'talk' }[emo] || 'talk';
  const expr = { shock: 'O', happy: 'smile', worried: 'frown', think: 'flat', angry: 'frown', sad: 'frown', talk: 'talk' }[emo];
  const m = MOOD[v.mood] || MOOD.calm; ctx.save(); ctx.fillStyle = m[1]; ctx.beginPath(); ctx.arc(CX, 1000, 470 * ease(t / .4), 0, 6.283); ctx.fill(); ctx.restore();
  if (emo === 'shock') { ctx.save(); ctx.strokeStyle = C.ink; ctx.lineWidth = 8; for (let i = 0; i < 10; i++) { const a = i / 10 * 6.283 + .2, r1 = 520 + 30 * Math.sin(t * 12 + i); ctx.beginPath(); ctx.moveTo(CX + Math.cos(a) * r1, 1000 + Math.sin(a) * r1); ctx.lineTo(CX + Math.cos(a) * (r1 + 70), 1000 + Math.sin(a) * (r1 + 70)); ctx.stroke(); } ctx.restore(); }
  const k = back(t / .5); ctx.save(); ctx.beginPath(); ctx.rect(0, 0, W, 1240); ctx.clip();
  person(ctx, CX, 1240 + 1500 * .62 + (1 - k) * 300, 1500, v.who || 'worker', pose, t, { seed, expr }); ctx.restore();
  if (emo === 'think' || emo === 'worried') for (let i = 0; i < 3; i++) { const kk = pop(t, .3 + i * .12); if (kk > 0) { ctx.fillStyle = C.white; ctx.strokeStyle = C.ink; ctx.lineWidth = 5; ctx.beginPath(); ctx.arc(CX + 200 + i * 40, 560 - i * 50, (14 + i * 8) * kk, 0, 6.283); ctx.fill(); ctx.stroke(); } }
  if (v.text) bubble(ctx, v.text, CX, 360, t, Math.min(cue(v, v.text.split(' ')[0], .35), dur * .5), { sz: 54 });
}

// ---------------------------------------------------------------- bigtext: the key words slam in one by one, the important word highlighted
function bigtext(ctx, v, t, dur, acc, seed) {
  const words = String(v.text || '').toUpperCase().split(/\s+/).filter(Boolean).slice(0, 7), hot = new Set(String(v.hl || '').toUpperCase().split(/\s+/));
  let sz = 170, lines; const lay = () => { ctx.font = `900 ${sz}px Inter, Arial`; lines = []; let cur = []; for (const w of words) { if (cur.length && ctx.measureText([...cur, w].join(' ')).width > 920) { lines.push(cur); cur = [w]; } else cur.push(w); } if (cur.length) lines.push(cur); };
  lay(); while ((lines.length > 4 || lines.some(l => ctx.measureText(l.join(' ')).width > 920)) && sz > 80) { sz -= 8; lay(); }
  let idx = 0, y = 760 - (lines.length - 1) * sz * .58; const dk = isDark(v.mood);
  for (const ln of lines) { ctx.font = `900 ${sz}px Inter, Arial`; let x = CX - ctx.measureText(ln.join(' ')).width / 2;
    for (const w of ln) { const d = Math.min(cue(v, w, .12 + idx * .22), dur * .75), k = clamp((t - d) / .18), ww = ctx.measureText(w).width, isHot = hot.has(w.replace(/[^A-Z0-9$%]/g, '')) || hot.has(w);
      if (k > 0) { ctx.save(); ctx.translate(x + ww / 2, y); const sc = 1 + (1 - ease(k)) * .9; ctx.scale(sc, sc); ctx.rotate((1 - ease(k)) * (idx % 2 ? .15 : -.15)); ctx.globalAlpha = k;
        if (isHot) { ctx.fillStyle = C.red; ctx.fillRect(-ww / 2 - 14, -sz * .55, ww + 28, sz * 1.04); }
        ctx.fillStyle = isHot ? C.white : (dk ? C.white : C.ink); ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(w, 0, sz * .04); ctx.restore(); }
      x += ctx.measureText(w + ' ').width; idx++; }
    y += sz * 1.12; }
}

export const KINDS = { steps, face, bigtext, building, office, hacker, servers, people, phone, email, object, network, globe, flow, counter, timeline, lock, terminal, dossier, headline, stamp, split };
