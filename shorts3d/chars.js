// Stylised 3D humanoids built from primitives. Reusable roles; each call gives a rigged Group that can be posed by name.
import * as THREE from 'three';

const SKIN = [0xf1c8a5, 0xe0a97c, 0xc68642, 0x8d5524, 0x6b4226, 0xffdbb4];
const mat = (c, o = {}) => new THREE.MeshStandardMaterial({ color: c, roughness: .62, metalness: .05, ...o });
const cap = (r, l, m) => new THREE.Mesh(new THREE.CapsuleGeometry(r, l, 6, 14), m);
const box = (w, h, d, m) => new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m);
const sph = (r, m, ws = 24, hs = 16) => new THREE.Mesh(new THREE.SphereGeometry(r, ws, hs), m);
function shadowize(o) { o.traverse(m => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; } }); return o; }

export const ROLES = {
  agent:    { suit: 0x2a3348, shirt: 0xf2f2f2, tie: 0x7a1020, hair: 0x15110e, glasses: 'shades', skin: 0, bulk: 1.05 },
  agentF:   { suit: 0x2f3a58, shirt: 0xe9eef7, tie: 0x2a3a66, hair: 0x2b1b12, glasses: null, skin: 1, bulk: .95, longhair: true },
  hacker:   { hoodie: 0x39405a, hood: true, skin: 3, visor: 0x3bff9a, bulk: 1.0 },
  worker:   { shirt: 0x6fa4d8, trousers: 0x2b3042, hair: 0x3a2a1c, glasses: 'round', skin: 1, bulk: 1.0, tie: 0x333a55 },
  workerF:  { shirt: 0xe7c6d8, trousers: 0x2b3042, hair: 0x1c1410, skin: 2, bulk: .93, longhair: true },
  exec:     { suit: 0x2a2f45, shirt: 0xffffff, tie: 0xd4a017, hair: 0x9a9a9a, skin: 0, bulk: 1.12 },
  guard:    { suit: 0x20324d, shirt: 0xcfd8e6, tie: null, hair: 0x15110e, cap: 0x1a2a44, skin: 4, bulk: 1.12 },
  engineer: { shirt: 0xf2a33a, trousers: 0x30343f, hair: 0x15110e, glasses: 'round', skin: 2, bulk: 1.0, vest: 0xf2a33a },
  banker:   { suit: 0x3a3f52, shirt: 0xf4f4f4, tie: 0x1f7a4d, hair: 0x25201c, glasses: 'round', skin: 5, bulk: 1.0 },
  crook:    { hoodie: 0x5a1a1a, hood: false, hair: 0x101010, skin: 2, bulk: 1.02, cap: 0x141414 },
};

export function makeChar(role = 'worker', opts = {}) {
  const R = { ...(ROLES[role] || ROLES.worker), ...opts };
  const skin = mat(SKIN[R.skin ?? 0]);
  const top = mat(R.suit || R.hoodie || R.shirt || 0x444444);
  const shirt = mat(R.shirt || R.suit || R.hoodie || 0xdddddd);
  const pants = mat(R.suit && !R.trousers ? R.suit : (R.trousers || 0x222733));
  const dark = mat(0x0b0d12);
  const root = new THREE.Group(); const J = {};
  const hips = new THREE.Group(); hips.position.y = .98; root.add(hips); J.hips = hips;
  const torso = new THREE.Group(); torso.position.y = .05; hips.add(torso); J.torso = torso;
  const chest = cap(.25 * R.bulk, .34, top); chest.scale.set(1.12, 1, .74); chest.position.y = .3; torso.add(chest);
  if (R.shirt && R.suit) { const v = box(.2, .42, .02, shirt); v.position.set(0, .34, .19); torso.add(v); }
  if (R.tie) { const t = box(.07, .36, .02, mat(R.tie)); t.position.set(0, .3, .205); torso.add(t); }
  if (R.vest) { const v = cap(.262 * R.bulk, .2, mat(R.vest, { emissive: 0x201000 })); v.scale.set(1.14, .8, .78); v.position.y = .27; torso.add(v); }
  const waist = cap(.2 * R.bulk, .05, pants); waist.scale.set(1.2, 1, .8); waist.position.y = -.03; torso.add(waist);
  const neck = cap(.065, .06, skin); neck.position.y = .66; torso.add(neck);
  const head = new THREE.Group(); head.position.y = .84; torso.add(head); J.head = head;
  const skull = sph(.17, skin); skull.scale.set(.96, 1.08, 1); head.add(skull);
  const eyeM = R.visor ? new THREE.MeshStandardMaterial({ color: 0x000000, emissive: R.visor, emissiveIntensity: 3 }) : dark;
  for (const s of [-1, 1]) { const e = sph(R.visor ? .03 : .022, eyeM, 12, 8); e.position.set(s * .062, .02, .155); e.scale.z = .6; head.add(e); }
  if (!R.visor) for (const s of [-1, 1]) { const b = box(.065, .012, .012, mat(0x1a1410)); b.position.set(s * .062, .066, .158); b.rotation.z = s * -.12; head.add(b); }
  const mouth = box(.07, .012, .012, mat(0x7a2d2d)); mouth.position.set(0, -.07, .152); head.add(mouth); J.mouth = mouth;
  const nose = sph(.02, skin, 8, 6); nose.position.set(0, -.015, .168); nose.scale.set(1, 1.2, .9); head.add(nose);
  if (R.hair && !R.hood) { const h = sph(.178, mat(R.hair), 20, 12); h.scale.set(1, .85, 1.02); h.position.set(0, .06, -.02); head.add(h); if (R.longhair) { const l = cap(.15, .22, mat(R.hair)); l.position.set(0, -.08, -.08); l.scale.set(1, 1, .8); head.add(l); } }
  if (R.hood) { const hd = sph(.215, mat(R.hoodie), 24, 14); hd.scale.set(1.02, 1.08, 1.04); hd.position.set(0, .015, -.045); head.add(hd); const op = sph(.13, dark, 16, 12); op.scale.set(1, 1.1, .6); op.position.set(0, .0, .14); head.add(op); skull.visible = false; for (const o of head.children) if (o.geometry && o.geometry.type === 'SphereGeometry' && o.material === eyeM) o.position.z = .15; }
  if (R.cap) { const c1 = sph(.18, mat(R.cap), 20, 10); c1.scale.set(1, .6, 1.02); c1.position.y = .1; head.add(c1); const br = box(.2, .02, .12, mat(R.cap)); br.position.set(0, .08, .17); head.add(br); }
  if (R.glasses === 'shades') { const g = box(.25, .05, .02, dark); g.position.set(0, .025, .165); head.add(g); }
  if (R.glasses === 'round') for (const s of [-1, 1]) { const g = new THREE.Mesh(new THREE.TorusGeometry(.04, .005, 8, 20), dark); g.position.set(s * .062, .02, .165); head.add(g); }
  const mkArm = (side) => {
    const sh = new THREE.Group(); sh.position.set(side * .33 * R.bulk, .52, 0); torso.add(sh);
    const up = cap(.062, .24, R.hoodie || R.suit ? top : shirt); up.position.y = -.17; sh.add(up);
    const el = new THREE.Group(); el.position.y = -.34; sh.add(el);
    const lo = cap(.055, .22, R.hoodie || R.suit ? top : shirt); lo.position.y = -.16; el.add(lo);
    const hand = sph(.058, skin, 12, 8); hand.position.y = -.33; el.add(hand);
    return { sh, el };
  };
  const mkLeg = (side) => {
    const hp = new THREE.Group(); hp.position.set(side * .12, -.02, 0); hips.add(hp);
    const th = cap(.085, .32, pants); th.position.y = -.24; hp.add(th);
    const kn = new THREE.Group(); kn.position.y = -.48; hp.add(kn);
    const sn = cap(.072, .34, pants); sn.position.y = -.22; kn.add(sn);
    const ft = box(.12, .07, .26, mat(0x0a0a0c)); ft.position.set(0, -.46, .05); kn.add(ft);
    return { hp, kn };
  };
  J.armL = mkArm(-1); J.armR = mkArm(1); J.legL = mkLeg(-1); J.legR = mkLeg(1);
  root.scale.setScalar(opts.scale || 1);
  shadowize(root);
  root.userData = { J, role, seed: opts.seed || Math.random() * 10 };
  return root;
}

const lerp = (a, b, k) => a + (b - a) * k;
export function pose(ch, mode, t, k = 1) {
  const { J, seed } = ch.userData, s = t + seed, br = Math.sin(s * 1.6) * .012;
  const set = (o, x = 0, y = 0, z = 0) => { o.rotation.set(x, y, z); };
  J.hips.position.y = .98; set(J.hips); set(J.torso, 0, 0, 0); set(J.head, 0, 0, 0);
  set(J.armL.sh, 0, 0, .08); set(J.armR.sh, 0, 0, -.08); set(J.armL.el, 0, 0, 0); set(J.armR.el, 0, 0, 0);
  set(J.legL.hp); set(J.legR.hp); set(J.legL.kn); set(J.legR.kn); J.mouth.scale.y = 1;
  J.torso.position.y = .05 + br;
  const talk = () => { J.mouth.scale.y = 1 + Math.abs(Math.sin(s * 13)) * 2.2; J.head.rotation.x = Math.sin(s * 2.1) * .06; J.head.rotation.y = Math.sin(s * 1.3) * .18; };
  switch (mode) {
    case 'walk': { const p = s * 5.2; set(J.legL.hp, Math.sin(p) * .6); set(J.legR.hp, -Math.sin(p) * .6); set(J.legL.kn, Math.max(0, -Math.sin(p)) * .9); set(J.legR.kn, Math.max(0, Math.sin(p)) * .9);
      set(J.armL.sh, -Math.sin(p) * .55, 0, .08); set(J.armR.sh, Math.sin(p) * .55, 0, -.08); set(J.armL.el, -.35); set(J.armR.el, -.35); J.hips.position.y = .98 + Math.abs(Math.cos(p)) * .035; set(J.torso, .05); break; }
    case 'run': { const p = s * 8.5; set(J.legL.hp, Math.sin(p) * .95); set(J.legR.hp, -Math.sin(p) * .95); set(J.legL.kn, Math.max(0, -Math.sin(p)) * 1.4); set(J.legR.kn, Math.max(0, Math.sin(p)) * 1.4);
      set(J.armL.sh, -Math.sin(p) * .9, 0, .1); set(J.armR.sh, Math.sin(p) * .9, 0, -.1); set(J.armL.el, -1.2); set(J.armR.el, -1.2); J.hips.position.y = .98 + Math.abs(Math.cos(p)) * .06; set(J.torso, .22); break; }
    case 'sit': { J.hips.position.y = .55; set(J.legL.hp, -1.5); set(J.legR.hp, -1.5); set(J.legL.kn, 1.5); set(J.legR.kn, 1.5); set(J.armL.sh, -.3, 0, .08); set(J.armR.sh, -.3, 0, -.08); set(J.armL.el, -.4); set(J.armR.el, -.4); break; }
    case 'type': { J.hips.position.y = .55; set(J.legL.hp, -1.5); set(J.legR.hp, -1.5); set(J.legL.kn, 1.5); set(J.legR.kn, 1.5); set(J.torso, .12);
      set(J.armL.sh, -1.05 + Math.sin(s * 18) * .04, 0, .12); set(J.armR.sh, -1.05 + Math.sin(s * 15 + 1) * .04, 0, -.12); set(J.armL.el, -.85 + Math.sin(s * 22) * .08); set(J.armR.el, -.85 + Math.sin(s * 19) * .08); J.head.rotation.x = .18 + Math.sin(s * .9) * .03; break; }
    case 'point': { set(J.armR.sh, -1.45, .35, -.1); set(J.armR.el, -.1); set(J.armL.sh, 0, 0, .1); talk(); break; }
    case 'shock': { const w = Math.min(1, t * 4); set(J.armL.sh, -2.4 * w, 0, .5 * w); set(J.armR.sh, -2.4 * w, 0, -.5 * w); set(J.armL.el, -.4); set(J.armR.el, -.4); set(J.head, -.25 * w); set(J.torso, -.1 * w); J.mouth.scale.y = 3.5; J.mouth.scale.x = .7; break; }
    case 'think': { set(J.armR.sh, -1.7, .2, -.2); set(J.armR.el, -1.9); set(J.armL.sh, -.9, 0, .1); set(J.armL.el, -1.6); set(J.head, .05, .25 + Math.sin(s * .8) * .1, .04); break; }
    case 'phone': { set(J.armR.sh, -2.4, 0, -.2); set(J.armR.el, -1.6); set(J.head, 0, .2, -.07); talk(); break; }
    case 'talk': { set(J.armR.sh, -.7 + Math.sin(s * 3) * .3, 0, -.25); set(J.armR.el, -.9 + Math.sin(s * 3.6) * .3); set(J.armL.sh, -.4 + Math.sin(s * 2.7) * .25, 0, .2); set(J.armL.el, -.7); talk(); break; }
    case 'slump': { set(J.torso, .35); set(J.head, .4); set(J.armL.sh, .15, 0, .06); set(J.armR.sh, .15, 0, -.06); break; }
    case 'handsup': { set(J.armL.sh, -2.9, 0, .25); set(J.armR.sh, -2.9, 0, -.25); break; }
    case 'cross': { set(J.armL.sh, -.9, 0, -.5); set(J.armR.sh, -.9, 0, .5); set(J.armL.el, -1.7); set(J.armR.el, -1.7); break; }
    default: set(J.head, 0, Math.sin(s * .7) * .12, 0); set(J.armL.sh, Math.sin(s * 1.6) * .03, 0, .08); set(J.armR.sh, -Math.sin(s * 1.6) * .03, 0, -.08);
  }
}
