// Flat illustrated characters (front 3/4 view) with poses and expressions.
import { C, rr, shade, clamp } from './kit.js';

export const ROLES = {
  worker:   { top: '#4f86c6', shirt: '#dfe8f5', pants: '#28324a', hair: 'short', hc: '#3a2a1c', skin: 1, acc: 'tie', tie: '#2a3a66' },
  workerF:  { top: '#c46a8e', shirt: '#f4e3ea', pants: '#2b3042', hair: 'long', hc: '#2a1a12', skin: 0 },
  banker:   { top: '#3a4258', shirt: '#f4f4f4', pants: '#2a2f40', hair: 'short', hc: '#1d1814', skin: 2, acc: 'tie', tie: '#1f8a55', glasses: 1 },
  agent:    { top: '#1c2333', shirt: '#f2f2f2', pants: '#1c2333', hair: 'short', hc: '#15110e', skin: 0, acc: 'tie', tie: '#9a1426', shades: 1, badge: 1 },
  agentF:   { top: '#222b40', shirt: '#eef2f8', pants: '#222b40', hair: 'bun', hc: '#2b1b12', skin: 1, badge: 1 },
  hacker:   { top: '#232838', shirt: '#232838', pants: '#151925', hair: 'hood', hc: '#232838', skin: 3, eyes: '#2bff88' },
  guard:    { top: '#25406a', shirt: '#cfd8e6', pants: '#1d2c45', hair: 'cap', hc: '#1a2a44', skin: 3, badge: 1 },
  engineer: { top: '#f0a23a', shirt: '#30343f', pants: '#30343f', hair: 'short', hc: '#15110e', skin: 2, glasses: 1, vest: 1 },
  exec:     { top: '#2d3350', shirt: '#ffffff', pants: '#2d3350', hair: 'grey', hc: '#a9a9a9', skin: 0, acc: 'tie', tie: '#d4a017' },
  crook:    { top: '#7a1f2a', shirt: '#7a1f2a', pants: '#1b1b1f', hair: 'beanie', hc: '#141414', skin: 1 },
  police:   { top: '#1b2c58', shirt: '#1b2c58', pants: '#141f3d', hair: 'cap', hc: '#101a35', skin: 2, badge: 1 },
  doctor:   { top: '#f1f4f8', shirt: '#7fb0d8', pants: '#3c4a66', hair: 'short', hc: '#2a1a12', skin: 1, acc: 'steth' },
  soldier:  { top: '#4b5a3a', shirt: '#4b5a3a', pants: '#3e4a30', hair: 'helmet', hc: '#3a4630', skin: 2 },
  student:  { top: '#3fae8a', shirt: '#f0f0f0', pants: '#33415f', hair: 'messy', hc: '#4a3020', skin: 4 },
};

function limb(ctx, x0, y0, a1, l1, a2, l2, w, col, hand, skin) {
  const x1 = x0 + Math.sin(a1) * l1, y1 = y0 + Math.cos(a1) * l1, x2 = x1 + Math.sin(a1 + a2) * l2, y2 = y1 + Math.cos(a1 + a2) * l2;
  ctx.strokeStyle = col; ctx.lineWidth = w; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
  if (hand) { ctx.fillStyle = skin; ctx.beginPath(); ctx.arc(x2, y2, w * .62, 0, 6.283); ctx.fill(); }
  return [x2, y2];
}
// pose -> arm/leg angles (radians, 0 = straight down; +a = outward for right side after mirroring)
function poseAngles(pose, t, s) {           // positive = arm swings outward (away from the body); a2 = elbow bend
  const sw = Math.sin(t * 2.2 + s) * .05;
  switch (pose) {
    case 'talk': return { L: [.12 + sw, .1], R: [.55 + Math.sin(t * 5) * .2, -1.5 + Math.sin(t * 6) * .25], legs: 0 };
    case 'point': return { L: [.12, .1], R: [1.75, .15], legs: 0 };
    case 'shock': return { L: [2.5, .7], R: [2.5, .7], legs: 0 };
    case 'think': return { L: [-.55, -1.5], R: [-.35, -2.45], legs: 0 };
    case 'phone': return { L: [.12 + sw, .1], R: [-.25, -2.65], legs: 0 };
    case 'type': return { L: [-.32, -.95 + Math.sin(t * 18) * .08], R: [-.32, -.95 + Math.sin(t * 16 + 1) * .08], legs: 0 };
    case 'cheer': return { L: [2.8 + Math.sin(t * 6) * .12, .15], R: [2.8 + Math.sin(t * 6 + 1) * .12, .15], legs: 0 };
    case 'walk': return { L: [Math.sin(t * 6) * .4, .2], R: [-Math.sin(t * 6) * .4, .2], legs: Math.sin(t * 6) * .4 };
    case 'arrest': return { L: [-.25, -.5], R: [-.25, -.5], legs: 0 };
    case 'handsup': return { L: [2.75, .25], R: [2.75, .25], legs: 0 };
    case 'cross': return { L: [-.5, -2.1], R: [-.5, -2.1], legs: 0 };
    case 'sleep': return { L: [.08, .1], R: [.08, .1], legs: 0 };
    default: return { L: [.12 + sw, .12], R: [.12 - sw, .12], legs: 0 };
  }
}
const EXPR = { shock: 'O', handsup: 'O', cheer: 'smile', talk: 'talk', phone: 'talk', think: 'flat', sleep: 'sleep', arrest: 'frown', type: 'flat', point: 'talk' };

// x = centre, y = feet line, h = full height in px.
export function person(ctx, x, y, h, role = 'worker', pose = 'idle', t = 0, o = {}) {
  const R = { ...(ROLES[role] || ROLES.worker), ...(o.style || {}) }, skin = C.skin[R.skin || 0], s = o.seed || 0;
  const k = h / 1000, A = poseAngles(pose, t, s), expr = o.expr || EXPR[pose] || 'smile';
  ctx.save(); ctx.translate(x, y); ctx.scale(o.flip ? -k : k, k);
  const bob = pose === 'walk' ? Math.abs(Math.cos(t * 6)) * -14 : Math.sin(t * 2 + s) * 4;
  // shadow
  ctx.fillStyle = 'rgba(0,0,0,.33)'; ctx.beginPath(); ctx.ellipse(0, 0, 190, 34, 0, 0, 6.283); ctx.fill();
  ctx.translate(0, bob);
  // legs
  if (!o.seated) {
    limb(ctx, -48, -430, A.legs, 210, -A.legs * .3, 200, 74, R.pants);
    limb(ctx, 48, -430, -A.legs, 210, A.legs * .3, 200, 74, R.pants);
    ctx.fillStyle = '#0d0e12'; rr(ctx, -110 + Math.sin(A.legs) * 200, -40, 100, 46, 20); ctx.fill(); rr(ctx, 10 - Math.sin(A.legs) * 200, -40, 100, 46, 20); ctx.fill();
  }
  // torso
  ctx.fillStyle = R.top; ctx.beginPath(); ctx.moveTo(-150, -760); ctx.quadraticCurveTo(0, -800, 150, -760); ctx.lineTo(130, -420); ctx.quadraticCurveTo(0, -395, -130, -420); ctx.closePath(); ctx.fill();
  ctx.fillStyle = 'rgba(0,0,0,.14)'; ctx.beginPath(); ctx.moveTo(30, -790); ctx.quadraticCurveTo(110, -780, 150, -760); ctx.lineTo(130, -420); ctx.quadraticCurveTo(80, -405, 40, -404); ctx.closePath(); ctx.fill();
  if (R.shirt !== R.top) { ctx.fillStyle = R.shirt; ctx.beginPath(); ctx.moveTo(-55, -785); ctx.lineTo(55, -785); ctx.lineTo(0, -600); ctx.closePath(); ctx.fill(); }
  if (R.acc === 'tie') { ctx.fillStyle = R.tie; ctx.beginPath(); ctx.moveTo(-16, -770); ctx.lineTo(16, -770); ctx.lineTo(24, -620); ctx.lineTo(0, -585); ctx.lineTo(-24, -620); ctx.closePath(); ctx.fill(); }
  if (R.vest) { ctx.fillStyle = '#d9ff3a'; ctx.fillRect(-140, -560, 280, 26); }
  if (R.badge) { ctx.fillStyle = '#e9c44a'; ctx.beginPath(); ctx.arc(-80, -660, 18, 0, 6.283); ctx.fill(); }
  if (R.acc === 'steth') { ctx.strokeStyle = '#2b2f3a'; ctx.lineWidth = 10; ctx.beginPath(); ctx.arc(0, -700, 70, .2, 2.9); ctx.stroke(); }
  if (R.hair === 'hood') { ctx.fillStyle = shade(R.top, 1.15); ctx.beginPath(); ctx.moveTo(-60, -560); ctx.lineTo(60, -560); ctx.lineTo(50, -470); ctx.lineTo(-50, -470); ctx.closePath(); ctx.fill(); }
  // arms (left side of screen = character's right)
  const sleeve = R.top;
  const hl = limb(ctx, -150, -740, -A.L[0], 190, -A.L[1], 180, 66, sleeve, true, skin);
  ctx.save(); ctx.scale(-1, 1); const hr = limb(ctx, -150, -740, -A.R[0], 190, -A.R[1], 180, 66, sleeve, true, skin); ctx.restore();
  if (pose === 'phone') { ctx.fillStyle = '#111'; rr(ctx, -hr[0] - 22 - 0, hr[1] - 70, 44, 86, 10); ctx.fill(); ctx.fillStyle = C.cyan; rr(ctx, -hr[0] - 16, hr[1] - 62, 32, 64, 6); ctx.fill(); }
  if (pose === 'arrest') { ctx.strokeStyle = '#c9ced8'; ctx.lineWidth = 12; ctx.beginPath(); ctx.arc(-70, -390, 22, 0, 6.283); ctx.stroke(); ctx.beginPath(); ctx.arc(70, -390, 22, 0, 6.283); ctx.stroke(); }
  // neck + head
  ctx.fillStyle = shade(skin, .9); ctx.fillRect(-36, -840, 72, 70);
  const hy = -945 + (pose === 'sleep' ? 20 : 0), tilt = pose === 'sleep' ? .25 : pose === 'think' ? .08 : Math.sin(t * 1.1 + s) * .04;
  ctx.save(); ctx.translate(0, hy); ctx.rotate(tilt);
  if (R.hair === 'long') { ctx.fillStyle = R.hc; rr(ctx, -128, -60, 256, 230, 90); ctx.fill(); }
  if (R.hair === 'hood') { ctx.fillStyle = shade(R.top, 1.12); ctx.beginPath(); ctx.ellipse(0, -4, 150, 168, 0, 0, 6.283); ctx.fill(); }
  ctx.fillStyle = skin; ctx.beginPath(); ctx.ellipse(0, 0, 112, 128, 0, 0, 6.283); ctx.fill();
  ctx.fillStyle = 'rgba(0,0,0,.08)'; ctx.beginPath(); ctx.ellipse(30, 6, 82, 122, 0, -1.2, 1.2); ctx.fill();
  ctx.fillStyle = skin; ctx.beginPath(); ctx.ellipse(-110, 10, 22, 32, 0, 0, 6.283); ctx.ellipse(110, 10, 22, 32, 0, 0, 6.283); ctx.fill();
  if (R.hair === 'hood') { ctx.fillStyle = 'rgba(5,7,12,.82)'; ctx.beginPath(); ctx.ellipse(0, 12, 104, 116, 0, 0, 6.283); ctx.fill(); }
  // eyes
  const blink = (Math.sin(t * 2.7 + s * 3) > .985 || pose === 'sleep') ? .12 : 1, ex = 40, ey = -6;
  if (R.hair === 'hood') { ctx.save(); ctx.shadowColor = R.eyes; ctx.shadowBlur = 30; ctx.fillStyle = R.eyes; for (const sx of [-1, 1]) { ctx.beginPath(); ctx.ellipse(sx * ex, ey, 18, 10 * blink + 1, 0, 0, 6.283); ctx.fill(); } ctx.restore(); }
  else {
    for (const sx of [-1, 1]) { ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.ellipse(sx * ex, ey, 20, 22 * blink, 0, 0, 6.283); ctx.fill(); ctx.fillStyle = '#1a1410'; ctx.beginPath(); ctx.ellipse(sx * ex + 3, ey + 3, 11, 12 * blink, 0, 0, 6.283); ctx.fill(); }
    const brow = expr === 'O' ? -18 : expr === 'frown' ? 8 : 0; ctx.strokeStyle = shade(R.hc === '#a9a9a9' ? '#777777' : R.hc, 1); ctx.lineWidth = 10; ctx.lineCap = 'round';
    for (const sx of [-1, 1]) { ctx.beginPath(); ctx.moveTo(sx * (ex - 24), -44 + brow * (sx > 0 ? 1 : 1)); ctx.lineTo(sx * (ex + 22), -48 + (expr === 'frown' ? -brow : brow * .3)); ctx.stroke(); }
    if (R.glasses) { ctx.strokeStyle = '#1c1c22'; ctx.lineWidth = 7; for (const sx of [-1, 1]) { ctx.beginPath(); ctx.arc(sx * ex, ey, 30, 0, 6.283); ctx.stroke(); } ctx.beginPath(); ctx.moveTo(-10, ey); ctx.lineTo(10, ey); ctx.stroke(); }
    if (R.shades) { ctx.fillStyle = '#0b0c10'; rr(ctx, -82, -30, 72, 40, 14); ctx.fill(); rr(ctx, 10, -30, 72, 40, 14); ctx.fill(); ctx.fillRect(-12, -20, 24, 8); }
    // mouth
    ctx.strokeStyle = '#6e2a2a'; ctx.fillStyle = '#5a1d22'; ctx.lineWidth = 9;
    if (expr === 'O') { ctx.beginPath(); ctx.ellipse(0, 62, 20, 28, 0, 0, 6.283); ctx.fill(); }
    else if (expr === 'talk') { const m = 6 + Math.abs(Math.sin(t * 13)) * 18; ctx.beginPath(); ctx.ellipse(0, 62, 26, m, 0, 0, 6.283); ctx.fill(); }
    else if (expr === 'frown') { ctx.beginPath(); ctx.arc(0, 90, 30, -2.5, -.64); ctx.stroke(); }
    else if (expr === 'flat') { ctx.beginPath(); ctx.moveTo(-22, 64); ctx.lineTo(22, 64); ctx.stroke(); }
    else if (expr === 'sleep') { ctx.beginPath(); ctx.arc(0, 62, 10, 0, 6.283); ctx.stroke(); }
    else { ctx.beginPath(); ctx.arc(0, 40, 34, .5, 2.64); ctx.stroke(); }
  }
  // hair / hats
  ctx.fillStyle = R.hc;
  if (R.hair === 'short' || R.hair === 'grey') { ctx.beginPath(); ctx.ellipse(0, -70, 118, 72, 0, Math.PI, 0); ctx.fill(); ctx.beginPath(); ctx.ellipse(-60, -66, 70, 40, -.3, 0, 6.283); ctx.fill(); }
  if (R.hair === 'messy') { for (let i = -4; i <= 4; i++) { ctx.beginPath(); ctx.ellipse(i * 26, -96 + Math.abs(i) * 6, 34, 44, i * .15, 0, 6.283); ctx.fill(); } }
  if (R.hair === 'long') { ctx.beginPath(); ctx.ellipse(0, -66, 124, 80, 0, Math.PI, 0); ctx.fill(); ctx.beginPath(); ctx.ellipse(-70, -50, 60, 50, -.6, 0, 6.283); ctx.fill(); }
  if (R.hair === 'bun') { ctx.beginPath(); ctx.ellipse(0, -66, 120, 74, 0, Math.PI, 0); ctx.fill(); ctx.beginPath(); ctx.arc(0, -150, 46, 0, 6.283); ctx.fill(); }
  if (R.hair === 'cap') { ctx.beginPath(); ctx.ellipse(0, -70, 124, 70, 0, Math.PI, 0); ctx.fill(); ctx.fillRect(-124, -76, 248, 22); ctx.fillStyle = shade(R.hc, .7); rr(ctx, -20, -76, 170, 26, 12); ctx.fill(); ctx.fillStyle = '#e9c44a'; ctx.beginPath(); ctx.arc(0, -110, 14, 0, 6.283); ctx.fill(); }
  if (R.hair === 'beanie') { ctx.beginPath(); ctx.ellipse(0, -62, 124, 92, 0, Math.PI, 0); ctx.fill(); ctx.fillStyle = shade(R.hc, 1.6); ctx.fillRect(-124, -74, 248, 26); }
  if (R.hair === 'helmet') { ctx.beginPath(); ctx.ellipse(0, -60, 136, 100, 0, Math.PI, 0); ctx.fill(); ctx.fillRect(-140, -66, 280, 18); }
  ctx.restore();
  if (pose === 'sleep') { ctx.fillStyle = '#fff'; ctx.font = '900 70px Inter, Arial'; ctx.globalAlpha = .7 + .3 * Math.sin(t * 3); ctx.fillText('z', 150, -1100 - (t * 30) % 60); ctx.fillText('Z', 210, -1180 - (t * 30) % 60); ctx.globalAlpha = 1; }
  ctx.restore();
}
