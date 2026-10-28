// Reusable 3D environments. Each env: { group, anchors:{name:[x,y,z]}, update(t), lights:[...] } placed at its own world offset.
import * as THREE from 'three';

export const M = (c, o = {}) => new THREE.MeshStandardMaterial({ color: c, roughness: .7, metalness: .1, ...o });
export const EM = (c, i = 2) => new THREE.MeshStandardMaterial({ color: 0x000000, emissive: c, emissiveIntensity: i });
const box = (w, h, d, m, x = 0, y = 0, z = 0) => { const o = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m); o.position.set(x, y, z); o.castShadow = true; o.receiveShadow = true; return o; };
function rng(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }

export function textTex(lines, o = {}) {
  const w = o.w || 512, h = o.h || 320, c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d');
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 4;
  tex.draw = (t, ls = lines) => {
    g.fillStyle = o.bg || '#06121c'; g.fillRect(0, 0, w, h);
    g.fillStyle = o.fg || '#38ff9c'; g.font = `bold ${o.size || 26}px monospace`;
    const arr = typeof ls === 'function' ? ls(t) : (ls || []); arr.forEach((l, i) => { g.fillStyle = (typeof l === 'object') ? l.c : (o.fg || '#38ff9c'); g.fillText(typeof l === 'object' ? l.t : l, 16, 38 + i * (o.size || 26) * 1.35); });
    if (o.scan) { g.fillStyle = 'rgba(255,255,255,.04)'; for (let y = (t * 40) % 6; y < h; y += 6) g.fillRect(0, y, w, 2); }
    tex.needsUpdate = true;
  };
  tex.draw(0); return tex;
}
export function screen(w, h, tex, bright = 1.6) {
  const g = new THREE.Group(); g.add(box(w + .06, h + .06, .05, M(0x0c0f16, { roughness: .4 })));
  const s = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshStandardMaterial({ map: tex, emissiveMap: tex, emissive: 0xffffff, emissiveIntensity: bright, color: 0x000000 })); s.position.z = .03; g.add(s); g.userData.tex = tex; return g;
}

function floorGrid(size, c1, c2) {
  const g = new THREE.Group();
  const f = new THREE.Mesh(new THREE.PlaneGeometry(size, size), M(c1, { roughness: .62, metalness: .12 })); f.rotation.x = -Math.PI / 2; f.receiveShadow = true; g.add(f);
  const gr = new THREE.GridHelper(size, size / 1.5, c2, c2); gr.material.transparent = true; gr.material.opacity = .25; gr.position.y = .01; g.add(gr); return g;
}
function skyline(group, seed, n, spread, minD, hMax, color = 0x0d1424) {
  const r = rng(seed), geo = new THREE.BoxGeometry(1, 1, 1);
  const bm = new THREE.InstancedMesh(geo, M(color, { roughness: .8 }), n), wm = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1), new THREE.MeshBasicMaterial({ color: 0xffffff }), n * 18);
  const dm = new THREE.Object3D(); let wi = 0; const col = new THREE.Color();
  for (let i = 0; i < n; i++) {
    const a = r() * Math.PI * 2, d = minD + r() * spread, w = 3 + r() * 6, h = 8 + r() * hMax, dd = 3 + r() * 6, x = Math.cos(a) * d, z = Math.sin(a) * d;
    dm.position.set(x, h / 2, z); dm.scale.set(w, h, dd); dm.rotation.set(0, 0, 0); dm.updateMatrix(); bm.setMatrixAt(i, dm.matrix);
    for (let k = 0; k < 18 && wi < n * 18; k++) { const wy = 1.5 + r() * (h - 2); if (r() < .55) { dm.position.set(x + (r() - .5) * (w - 1), wy, z + (dd / 2 + .05) * (r() < .5 ? 1 : 1)); dm.scale.set(.5, .6, .05); dm.updateMatrix(); wm.setMatrixAt(wi, dm.matrix); col.setHSL(.1 + r() * .08, .5, .5 + r() * .3); wm.setColorAt(wi, col); wi++; } }
  }
  wm.count = wi; group.add(bm, wm);
}

// ---------------------------------------------------------------- OFFICE (night) : desks, monitors, windows
export function office(seed = 1) {
  const g = new THREE.Group(), r = rng(seed), A = {}, scr = [], lights = [];
  g.add(floorGrid(40, 0x161d2c, 0x3b5a8f));
  g.add(box(40, .2, 40, M(0x10141f), 0, 6, 0));                                      // ceiling
  g.add(box(40, 6, .3, M(0x1a2236), 0, 3, -9));                                      // back wall
  g.add(box(.3, 6, 40, M(0x1a2236), -12, 3, 0)); g.add(box(.3, 6, 40, M(0x1a2236), 12, 3, 0));
  const win = new THREE.Group(); win.position.set(0, 3.2, -8.8);                      // big window with city lights
  win.add(box(16, 4, .1, EM(0x0b1a36, .5)));
  for (let i = 0; i < 160; i++) { const l = box(.06 + r() * .1, .06 + r() * .16, .05, new THREE.MeshBasicMaterial({ color: new THREE.Color().setHSL(.08 + r() * .1, .6, .28 + r() * .18) }), (r() - .5) * 15.5, -1.9 + r() * 3.8, .08); l.castShadow = false; win.add(l); }
  g.add(win);
  for (let i = -3; i <= 3; i++) { const s = box(.02, 4, .1, M(0x0a0e16), i * 2.3, 3.2, -8.75); g.add(s); }
  for (let row = 0; row < 3; row++) for (let col = -2; col <= 2; col++) {
    const x = col * 3.4, z = -5 + row * 3.4; g.add(box(2.2, .08, 1.1, M(0x2b3550, { roughness: .35 }), x, .78, z)); g.add(box(.08, .78, .9, M(0x161c2c), x - 1, .39, z)); g.add(box(.08, .78, .9, M(0x161c2c), x + 1, .39, z));
    const tex = textTex(null, { w: 384, h: 256, size: 20, bg: '#071827', fg: '#45e0ff', scan: true }); tex.seedI = row * 9 + col; const sc = screen(.78, .5, tex, 1.4); sc.position.set(x, 1.28, z - .25); g.add(sc); scr.push(tex);
    g.add(box(.1, .22, .1, M(0x10131b), x, .95, z - .25));
  }
  for (let i = -3; i <= 3; i++) g.add(box(.3, .05, 18, EM(0xcfe6ff, 1.6), i * 3.2, 5.88, -2));
  const pl = new THREE.PointLight(0x6fa0ff, 28, 18, 1.6); pl.position.set(0, 4.5, 0); g.add(pl); lights.push(pl);
  const pl2 = new THREE.PointLight(0xffb070, 9, 12, 1.6); pl2.position.set(4, 2.5, -6); g.add(pl2); lights.push(pl2);
  Object.assign(A, { desk: [0, 0, -1.6], wide: [0, 1.4, 0], window: [0, 2.5, -8], printer: [-5.2, .85, -1.6] });
  // printer
  const pr = new THREE.Group(); pr.position.set(-6.8, .82, -1.6); pr.add(box(1.0, .5, .7, M(0xd8dde6, { roughness: .5 }), 0, .25, 0)); pr.add(box(1.0, .06, .5, M(0x9aa3b4), 0, .55, .05)); pr.add(box(.7, .04, .3, M(0xf4f4f4), 0, .12, .38));
  const led = box(.06, .06, .02, EM(0xff2030, 4), .38, .38, .36); pr.add(led); pr.userData.led = led; g.add(pr); A.printerObj = pr; g.add(box(1.4, .8, .8, M(0x232b40), -6.8, .4, -1.6));
  return { group: g, anchors: A, lights, update(t) { scr.forEach(tx => tx.draw(t, (tt) => { const o = []; for (let i = 0; i < 9; i++) o.push((((Math.floor(tt * 3) + i + tx.seedI) * 2654435761) >>> 0).toString(16).padStart(8, '0') + ' ' + ((i * 977 + tx.seedI) >>> 0).toString(36)); return o; })); led.visible = Math.sin(t * 7) > -.2; } };
}

// ---------------------------------------------------------------- SERVER ROOM
export function serverRoom(seed = 2) {
  const g = new THREE.Group(), r = rng(seed), A = {}, lights = [], leds = [];
  g.add(floorGrid(60, 0x0b1220, 0x00c8ff)); g.add(box(8, .2, 60, M(0x0a0d14), 0, 5, 0));
  g.add(box(.3, 5, 60, M(0x0e1422), -5.5, 2.5, 0)); g.add(box(.3, 5, 60, M(0x0e1422), 5.5, 2.5, 0)); g.add(box(12, 5, .3, M(0x0e1422), 0, 2.5, -20));
  const ledGeo = new THREE.BoxGeometry(.06, .03, .02), nLed = 36 * 2 * 16 * 3, lm = new THREE.InstancedMesh(ledGeo, new THREE.MeshBasicMaterial({ color: 0xffffff }), nLed), dm = new THREE.Object3D(), c = new THREE.Color(); let li = 0;
  for (const side of [-1, 1]) for (let i = 0; i < 20; i++) {
    const z = 6 - i * 1.5; g.add(box(1.1, 3.4, .9, M(0x12182a, { roughness: .35, metalness: .6 }), side * 3.9, 1.7, z));
    for (let k = 0; k < 16; k++) { g.add(box(.95, .1, .02, M(0x1b2338), side * 3.9 - side * .01, .4 + k * .2, z + .46 * 0)); for (let q = 0; q < 3 && li < nLed; q++) { dm.position.set(side * 3.35, .4 + k * .2, z - .3 + q * .24 + .3); dm.scale.set(1, 1, 1); dm.updateMatrix(); lm.setMatrixAt(li, dm.matrix); const v = r(); c.set(v < .7 ? 0x24ff90 : v < .9 ? 0x2ad0ff : 0xff3040); lm.setColorAt(li, c); li++; } }
  }
  lm.count = li; g.add(lm);
  for (let i = 0; i < 8; i++) g.add(box(.25, .06, 4, EM(0x9fd4ff, 1.4), 0, 4.9, 5 - i * 5));
  const pl = new THREE.PointLight(0x35a0ff, 24, 20, 1.5); pl.position.set(0, 3.5, 2); g.add(pl); lights.push(pl);
  const alarm = new THREE.PointLight(0xff1020, 0, 16, 1.6); alarm.position.set(0, 4, -8); g.add(alarm); lights.push(alarm);
  Object.assign(A, { aisle: [0, 1.5, 0], end: [0, 1.6, -16] });
  return { group: g, anchors: A, lights, update(t, st) { alarm.intensity = st && st.alarm ? 30 * (.5 + .5 * Math.sin(t * 9)) : 0; pl.intensity = st && st.alarm ? 6 : 24; } };
}

// ---------------------------------------------------------------- BANK exterior (columns, steps, sign)
export function bank(seed = 3) {
  const g = new THREE.Group(), A = {}, lights = [];
  g.add(floorGrid(120, 0x10151f, 0x2a3f66)); skyline(g, seed, 90, 60, 26, 55);
  const st = M(0xc9c3b5, { roughness: .8 });
  for (let i = 0; i < 5; i++) g.add(box(18 - i * 1.2, .3, 8 - i * .5, st, 0, .15 + i * .3, 6 - i * .3));
  g.add(box(14, 9, 7, M(0xb9b3a4, { roughness: .85 }), 0, 6.2, -.5));                      // body
  for (let i = -3; i <= 3; i++) { const cl = new THREE.Mesh(new THREE.CylinderGeometry(.55, .6, 8.4, 20), st); cl.position.set(i * 1.9, 5.7, 3.6); cl.castShadow = cl.receiveShadow = true; g.add(cl); }
  g.add(box(14.5, 1.6, 8, st, 0, 10.8, 0)); const ped = new THREE.Mesh(new THREE.CylinderGeometry(0, 1, 1, 3), st); ped.scale.set(7.2, 2.6, 8); ped.rotation.set(Math.PI / 2, 0, 0); ped.position.set(0, 12.6, 0); ped.rotation.z = Math.PI; g.add(ped);
  const tex = textTex(['CENTRAL BANK'], { w: 1024, h: 160, size: 84, bg: '#b9b3a4', fg: '#2a2418' }); tex.draw(0, ['  CENTRAL BANK']);
  const sign = new THREE.Mesh(new THREE.PlaneGeometry(9, 1.4), new THREE.MeshStandardMaterial({ map: tex, emissiveMap: tex, emissive: 0xffffff, emissiveIntensity: .5 })); sign.position.set(0, 10.8, 4.05); g.add(sign);
  g.add(box(2.6, 4.6, .15, EM(0xffc26b, .9), 0, 2.9, 3.0));                              // glowing door
  for (const s of [-1, 1]) { const lp = new THREE.Group(); lp.position.set(s * 9.5, 0, 9); lp.add(box(.15, 5, .15, M(0x222b3a), 0, 2.5, 0)); lp.add(box(.7, .2, .7, EM(0xffe2a8, 4), 0, 5.1, 0)); const l = new THREE.PointLight(0xffe2a8, 18, 20, 1.6); l.position.set(0, 5, 0); lp.add(l); lights.push(l); g.add(lp); }
  const key = new THREE.SpotLight(0xbcd2ff, 80, 60, .55, .5, 1.4); key.position.set(-10, 16, 22); key.target.position.set(0, 5, 0); g.add(key, key.target); lights.push(key);
  Object.assign(A, { front: [0, 4, 3], street: [0, 1.5, 14], top: [0, 12, 4] });
  return { group: g, anchors: A, lights, update() {} };
}

// ---------------------------------------------------------------- VAULT / MONEY
export function vault(seed = 4) {
  const g = new THREE.Group(), A = {}, lights = [];
  g.add(floorGrid(30, 0x1a1c22, 0x998040)); g.add(box(20, 6, .3, M(0x24272f), 0, 3, -8)); g.add(box(.3, 6, 20, M(0x24272f), -8, 3, 0)); g.add(box(.3, 6, 20, M(0x24272f), 8, 3, 0)); g.add(box(20, .2, 20, M(0x181a20), 0, 6, 0));
  const ring = new THREE.Mesh(new THREE.TorusGeometry(2.4, .35, 20, 48), M(0x9aa3b0, { roughness: .55, metalness: .5 })); ring.position.set(0, 2.8, -7.7); g.add(ring);
  const door = new THREE.Mesh(new THREE.CylinderGeometry(2.3, 2.3, .5, 48), M(0x7f8896, { roughness: .55, metalness: .5 })); door.rotation.x = Math.PI / 2; door.position.set(0, 2.8, -7.4); g.add(door);
  const wheel = new THREE.Group(); wheel.position.set(0, 2.8, -7.0); for (let i = 0; i < 6; i++) { const sp = box(.14, 1.7, .14, M(0xcfd5df, { metalness: .9, roughness: .2 })); sp.rotation.z = i * Math.PI / 3; wheel.add(sp); } const hub = new THREE.Mesh(new THREE.CylinderGeometry(.35, .35, .3, 20), M(0xe3c36a, { metalness: .9, roughness: .25 })); hub.rotation.x = Math.PI / 2; wheel.add(hub); g.add(wheel);
  const money = M(0x4f9a63, { roughness: .8 }), gold = M(0xe3b341, { roughness: .25, metalness: .95 });
  for (let i = 0; i < 6; i++) for (let k = 0; k < 4; k++) g.add(box(.9, .22 * (1 + (i + k) % 3), .45, money, -5 + i * 1.0, .12 * (1 + (i + k) % 3), 1 + k * .6));
  for (let i = 0; i < 4; i++) for (let k = 0; k < 3; k++) for (let q = 0; q < 3 - k; q++) g.add(box(.55, .2, .28, gold, 3 + i * .65, .1 + k * .2, .8 + q * .0 + (q % 2) * .01));
  const pl = new THREE.PointLight(0xffe0a0, 14, 16, 1.5); pl.position.set(0, 4.5, -3); g.add(pl); lights.push(pl);
  Object.assign(A, { door: [0, 2.8, -7], cash: [-2.5, .5, 1.8] });
  return { group: g, anchors: A, lights, update(t) { wheel.rotation.z = Math.min(t * .8, 6.28) * .5; } };
}

// ---------------------------------------------------------------- HACKER DEN
export function den(seed = 5) {
  const g = new THREE.Group(), A = {}, lights = [], scr = [], r = rng(seed);
  g.add(floorGrid(30, 0x0a0c12, 0x7a1fff)); g.add(box(20, 6, .3, M(0x0c0e18), 0, 3, -6)); g.add(box(.3, 6, 20, M(0x0c0e18), -7, 3, 0)); g.add(box(.3, 6, 20, M(0x0c0e18), 7, 3, 0)); g.add(box(20, .2, 20, M(0x07080d), 0, 6, 0));
  g.add(box(6.5, .1, 1.7, M(0x1a1d2b, { roughness: .3 }), 0, .8, -4)); g.add(box(.12, .8, 1.5, M(0x10121c), -3, .4, -4)); g.add(box(.12, .8, 1.5, M(0x10121c), 3, .4, -4));
  const prog = (t) => { const o = []; for (let i = 0; i < 11; i++) { const h = (Math.floor(t * 2.5) + i) * 2654435761 >>> 0; o.push({ t: (i % 4 === 0 ? '> ' : '  ') + h.toString(16).padStart(8, '0') + ' ' + ['inject', 'bypass', 'auth ok', 'exfil', 'root'][h % 5], c: i === 5 ? '#ff4060' : '#38ff9c' }); } return o; };
  for (let i = -1; i <= 1; i++) { const tex = textTex(null, { w: 512, h: 400, size: 24, bg: '#050a0d', fg: '#38ff9c', scan: true }); tex.prog = prog; const sc = screen(1.5, 1.1, tex, 1.7); sc.position.set(i * 1.7, 1.55, -4.5); sc.rotation.y = -i * .22; g.add(sc); scr.push(tex); }
  g.add(box(.9, .06, .35, M(0x0b0c12), 0, .86, -3.55)); const kb = box(.9, .02, .3, EM(0x7a1fff, 1.2), 0, .895, -3.55); g.add(kb);
  g.add(box(12, .05, .05, EM(0xff2d9a, 3), 0, 4.5, -5.8)); g.add(box(.05, 3, .05, EM(0x2dd8ff, 3), 6.9, 3, -2));
  const l1 = new THREE.PointLight(0x8a3cff, 18, 14, 1.6); l1.position.set(-3, 3, -2); g.add(l1); const lg = new THREE.PointLight(0x38ff9c, 5, 9, 1.6); lg.position.set(0, 1.8, -3.2); g.add(lg); lights.push(lg); const l2 = new THREE.PointLight(0x2dd8ff, 14, 14, 1.6); l2.position.set(3, 2.5, -1); g.add(l2); lights.push(l1, l2);
  Object.assign(A, { desk: [0, 1.4, -4], chair: [0, 0, -3.2], wide: [0, 1.6, 0] });
  return { group: g, anchors: A, lights, update(t) { scr.forEach(tx => tx.draw(t, tx.prog)); } };
}

// ---------------------------------------------------------------- FBI HQ (exterior) + war room
export function fbi(seed = 6) {
  const g = new THREE.Group(), A = {}, lights = [], r = rng(seed);
  g.add(floorGrid(120, 0x121722, 0x3a5080)); skyline(g, seed + 4, 70, 50, 30, 40);
  const concrete = M(0x8e939e, { roughness: .9 });
  g.add(box(26, 18, 10, concrete, 0, 9, 0));
  for (let y = 0; y < 5; y++) for (let x = -5; x <= 5; x++) { const lit = r() < .55; g.add(box(1.5, 1.8, .15, lit ? EM(0xffd48a, .9) : M(0x1b2434, { roughness: .2, metalness: .6 }), x * 2.2, 3 + y * 3.1, 5.05)); }
  g.add(box(30, 1, 14, concrete, 0, .5, 3)); g.add(box(10, 4, 6, M(0x70757f), 0, 2, 8));
  const tex = textTex(null, { w: 1024, h: 200, size: 110, bg: '#14213a', fg: '#e8edf7' }); tex.draw(0, ['  FBI  CYBER DIVISION']); tex.image.getContext('2d').font = 'bold 74px sans-serif';
  const sign = new THREE.Mesh(new THREE.PlaneGeometry(9, 1.2), new THREE.MeshStandardMaterial({ map: tex, emissiveMap: tex, emissive: 0xffffff, emissiveIntensity: .8 })); sign.position.set(0, 4.5, 11.05); g.add(sign);
  for (const s of [-1, 1]) { const p = new THREE.Group(); p.position.set(s * 8, 0, 10); p.add(box(.12, 9, .12, M(0xb0b6c2, { metalness: .8 }), 0, 4.5, 0)); const fl = box(1.8, 1.1, .03, M(s < 0 ? 0x24407a : 0xaa2233), .95, 8.2, 0); fl.userData.flag = 1; p.add(fl); g.add(p); }
  const k = new THREE.SpotLight(0xb4ccff, 90, 70, .6, .5, 1.3); k.position.set(-14, 20, 30); k.target.position.set(0, 6, 4); g.add(k, k.target); lights.push(k);
  const k2 = new THREE.PointLight(0xffe0b0, 25, 26, 1.6); k2.position.set(0, 4, 14); g.add(k2); lights.push(k2);
  Object.assign(A, { front: [0, 6, 6], plaza: [0, 1.5, 16], top: [0, 14, 8] });
  return { group: g, anchors: A, lights, update() {} };
}

export function warRoom(seed = 7) {
  const g = new THREE.Group(), A = {}, lights = [], scr = [];
  g.add(floorGrid(30, 0x10151f, 0x3b5a8f)); g.add(box(24, 6, .3, M(0x131a2a), 0, 3, -8)); g.add(box(.3, 6, 24, M(0x131a2a), -9, 3, 0)); g.add(box(.3, 6, 24, M(0x131a2a), 9, 3, 0)); g.add(box(24, .2, 24, M(0x0d111a), 0, 6, 0));
  const tex = textTex(null, { w: 1024, h: 512, size: 30, bg: '#06101c', fg: '#58b8ff', scan: true }); tex.m = (t) => { const o = ['LIVE INCIDENT FEED', '', ...[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map(i => ((Math.floor(t * 2) + i) * 40503 >>> 0).toString(16) + '  ' + ['SWIFT', 'AUTH', 'ALERT', 'TRACE', 'LINK'][(i + Math.floor(t)) % 5])]; return o; };
  const sc = screen(7, 3.5, tex, 1.5); sc.position.set(0, 3.2, -7.7); g.add(sc); scr.push(tex);
  g.add(box(5.5, .14, 2, M(0x2a3550, { roughness: .35 }), 0, .85, 0)); for (let i = 0; i < 5; i++) for (const s of [-1, 1]) g.add(box(.5, .9, .5, M(0x161c2c), -2.2 + i * 1.1, .45, s * 1.6));
  for (let i = -2; i <= 2; i++) { const ph = box(1.1, 1.4, .04, M(0xdde3ee), i * 1.5, 3.5, -7.85 + 8.0 * 0); ph.position.z = -7.9; ph.visible = false; g.add(ph); }
  const l1 = new THREE.PointLight(0x7ab4ff, 55, 20, 1.4); l1.position.set(0, 4.5, 1); g.add(l1); lights.push(l1);
  Object.assign(A, { table: [0, 1, 0], screen: [0, 3, -7] });
  return { group: g, anchors: A, lights, update(t) { scr.forEach(tx => tx.draw(t, tx.m)); } };
}

// ---------------------------------------------------------------- CYBERSPACE: floating computers linked by glowing lines, infection spreads
export function cyberspace(seed = 8) {
  const g = new THREE.Group(), A = {}, lights = [], r = rng(seed), nodes = [], N = 70;
  for (let i = 0; i < N; i++) nodes.push(new THREE.Vector3((r() - .5) * 34, (r() - .5) * 18, (r() - .5) * 34));
  const cube = new THREE.BoxGeometry(.7, .5, .5), mats = nodes.map(() => EM(0x2ad0ff, 1.6)), meshes = [];
  nodes.forEach((p, i) => { const m = new THREE.Mesh(cube, mats[i]); m.position.copy(p); m.rotation.y = r() * 3; g.add(m); meshes.push(m); const sc = box(.5, .05, .4, M(0x101827), 0, 0, 0); });
  const edges = []; for (let i = 0; i < N; i++) { const near = nodes.map((p, j) => [p.distanceTo(nodes[i]), j]).sort((a, b) => a[0] - b[0]).slice(1, 4); near.forEach(([d, j]) => edges.push([i, j])); }
  const lg = new THREE.BufferGeometry().setFromPoints(edges.flatMap(([a, b]) => [nodes[a], nodes[b]])); const lines = new THREE.LineSegments(lg, new THREE.LineBasicMaterial({ color: 0x2a6fbf, transparent: true, opacity: .55 })); g.add(lines);
  const pk = new THREE.InstancedMesh(new THREE.SphereGeometry(.12, 8, 6), new THREE.MeshBasicMaterial({ color: 0xffffff }), edges.length); g.add(pk); const dm = new THREE.Object3D();
  const order = nodes.map((p, i) => [p.distanceTo(nodes[0]), i]).sort((a, b) => a[0] - b[0]).map(x => x[1]); const rank = []; order.forEach((n, k) => rank[n] = k);
  const l = new THREE.PointLight(0x2ad0ff, 30, 40, 1.4); l.position.set(0, 0, 0); g.add(l); lights.push(l);
  Object.assign(A, { center: [0, 0, 0] });
  return { group: g, anchors: A, lights, update(t, st) {
    const spread = st && st.infect != null ? st.infect : 0, inf = spread * N;
    nodes.forEach((p, i) => { const on = rank[i] < inf; mats[i].emissive.set(on ? 0xff2d45 : 0x2ad0ff); mats[i].emissiveIntensity = on ? 3.2 : 1.4; meshes[i].scale.setScalar(on ? 1.25 : 1); });
    edges.forEach(([a, b], i) => { const k = (t * .7 + i * .137) % 1, on = rank[a] < inf && rank[b] < inf; dm.position.lerpVectors(nodes[a], nodes[b], k); dm.scale.setScalar(on ? 1.4 : .6); dm.updateMatrix(); pk.setMatrixAt(i, dm.matrix); }); pk.instanceMatrix.needsUpdate = true;
    l.color.set(spread > .5 ? 0xff2d45 : 0x2ad0ff);
  } };
}

// ---------------------------------------------------------------- HOLO GLOBE
export function globe(seed = 9) {
  const g = new THREE.Group(), A = {}, lights = [], R = 4;
  const sph = new THREE.Mesh(new THREE.SphereGeometry(R, 48, 32), new THREE.MeshStandardMaterial({ color: 0x0a1630, roughness: .5, metalness: .3, emissive: 0x0a2050, emissiveIntensity: .6 })); g.add(sph);
  const wire = new THREE.LineSegments(new THREE.WireframeGeometry(new THREE.SphereGeometry(R * 1.003, 24, 16)), new THREE.LineBasicMaterial({ color: 0x2f8fff, transparent: true, opacity: .35 })); g.add(wire);
  const halo = new THREE.Mesh(new THREE.SphereGeometry(R * 1.08, 32, 24), new THREE.MeshBasicMaterial({ color: 0x2a7fff, transparent: true, opacity: .08, side: THREE.BackSide })); g.add(halo);
  const r = rng(seed); const dots = new THREE.InstancedMesh(new THREE.SphereGeometry(.03, 6, 4), new THREE.MeshBasicMaterial({ color: 0x6fd0ff }), 900), dm = new THREE.Object3D();
  for (let i = 0; i < 900; i++) { const la = Math.asin(2 * r() - 1), lo = r() * 6.283; dm.position.set(R * 1.006 * Math.cos(la) * Math.sin(lo), R * 1.006 * Math.sin(la), R * 1.006 * Math.cos(la) * Math.cos(lo)); dm.updateMatrix(); dots.setMatrixAt(i, dm.matrix); } g.add(dots);
  const arcs = new THREE.Group(); g.add(arcs); const pins = new THREE.Group(); g.add(pins);
  const l = new THREE.PointLight(0x4aa0ff, 40, 30, 1.4); l.position.set(6, 4, 8); g.add(l); lights.push(l);
  const ll = (lat, lon, rr = R) => { const la = lat * Math.PI / 180, lo = lon * Math.PI / 180; return new THREE.Vector3(rr * Math.cos(la) * Math.sin(lo), rr * Math.sin(la), rr * Math.cos(la) * Math.cos(lo)); };
  function setRoute(points, color = 0xff3050) {
    arcs.clear(); pins.clear(); const vs = points.map(p => ll(p[1], p[2]));
    vs.forEach((v, i) => { const m = new THREE.Mesh(new THREE.SphereGeometry(.12, 12, 8), new THREE.MeshBasicMaterial({ color: i === 0 ? 0xffd400 : 0xffffff })); m.position.copy(v.clone().multiplyScalar(1.01)); pins.add(m); const ring = new THREE.Mesh(new THREE.RingGeometry(.18, .22, 24), new THREE.MeshBasicMaterial({ color: 0xffd400, side: THREE.DoubleSide, transparent: true, opacity: .8 })); ring.position.copy(m.position); ring.lookAt(v.clone().multiplyScalar(2)); ring.userData.pin = i; pins.add(ring); });
    for (let i = 0; i < vs.length - 1; i++) { const a = vs[i], b = vs[i + 1], mid = a.clone().add(b).multiplyScalar(.5).normalize().multiplyScalar(R + a.distanceTo(b) * .45); const curve = new THREE.QuadraticBezierCurve3(a, mid, b); const tube = new THREE.Mesh(new THREE.TubeGeometry(curve, 48, .035, 6, false), new THREE.MeshBasicMaterial({ color })); tube.userData.curve = curve; tube.userData.idx = i; arcs.add(tube); const head = new THREE.Mesh(new THREE.SphereGeometry(.1, 10, 8), new THREE.MeshBasicMaterial({ color: 0xffffff })); head.userData.curve = curve; head.userData.i = i; arcs.add(head); }
    A.focus = vs.length ? vs.reduce((s, v) => s.add(v), new THREE.Vector3()).multiplyScalar(1 / vs.length).toArray() : [0, 0, 0];
  }
  Object.assign(A, { center: [0, 0, 0] });
  return { group: g, anchors: A, lights, setRoute, update(t, st) {
    const u = st && st.u != null ? st.u : t / 4, n = Math.max(1, arcs.children.length / 2);
    arcs.children.forEach(c => {
      if (c.userData.idx != null) { const k = Math.min(1, Math.max(0, u * n - c.userData.idx)); c.visible = k > 0; }
      if (c.userData.i != null) { const k = Math.min(1, Math.max(0, u * n - c.userData.i)); c.position.copy(c.userData.curve.getPoint(k)); c.visible = k > 0 && k < 1; }
    });
    pins.children.forEach(c => { if (c.userData.pin != null) c.scale.setScalar(1 + ((t * .9) % 1) * 2); });
  } };
}

export const ENVS = { office, serverRoom, bank, vault, den, fbi, warRoom, cyberspace, globe };
