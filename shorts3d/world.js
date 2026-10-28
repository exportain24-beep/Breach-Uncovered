// The 3D world: renderer + bloom, environments at fixed offsets, cast (characters), camera moves, shot timeline.
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { makeChar, pose } from './chars.js';
import { ENVS, M } from './envs.js';
import { expand } from './recipes.js';

const MOOD = {
  calm: { bg: 0x0a1020, amb: .9, bloom: .55 }, curious: { bg: 0x0a1424, amb: .9, bloom: .6 }, tense: { bg: 0x160b16, amb: .75, bloom: .7 },
  shock: { bg: 0x1c0a0e, amb: .7, bloom: .85 }, reveal: { bg: 0x07181f, amb: .95, bloom: .75 }, sad: { bg: 0x0b0f1a, amb: .75, bloom: .5 }, hopeful: { bg: 0x0d1a24, amb: 1.0, bloom: .6 },
};
const PRESETS = {
  wide: { a: [0, 0], d: [14, 14], h: [3, 3] }, push_in: { a: [0, 0], d: [9, 5], h: [1.8, 1.5] }, pull_out: { a: [0, 0], d: [4, 9], h: [1.5, 2.2] },
  orbit: { a: [-35, 35], d: [7, 7], h: [2, 2] }, orbit_fast: { a: [-70, 70], d: [6, 6], h: [1.8, 2.4] }, crane_up: { a: [0, 12], d: [10, 11], h: [1.5, 9] }, crane_down: { a: [-10, 0], d: [11, 8], h: [9, 2] },
  low_hero: { a: [-12, 12], d: [6, 5], h: [.4, .7] }, closeup: { a: [8, -8], d: [2.6, 2.2], h: [1.65, 1.6] }, over_shoulder: { a: [22, 14], d: [2.9, 2.3], h: [1.75, 1.65] }, truck: { a: [-40, 40], d: [8, 8], h: [1.6, 1.6] },
  top_down: { a: [0, 0], d: [.01, .01], h: [9, 7] }, side: { a: [90, 70], d: [6, 5], h: [1.5, 1.5] },
};
const ease = (x) => { x = Math.max(0, Math.min(1, x)); return x * x * (3 - 2 * x); };
const lerp = (a, b, k) => a + (b - a) * k;

export async function createWorld(canvas, W, H) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(1); renderer.setSize(W, H, false); renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
  const scene = new THREE.Scene(); scene.fog = new THREE.FogExp2(0x0a1020, .018);
  const amb = new THREE.HemisphereLight(0x6f8fd0, 0x10131c, .55); scene.add(amb);
  const cam = new THREE.PerspectiveCamera(36, W / H, .1, 300);
  const key = new THREE.PointLight(0xfff2e0, 7, 14, 1.6); scene.add(key); const rim = new THREE.DirectionalLight(0x6fa8ff, 1.6); scene.add(rim, rim.target);
  const rt = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 4 });
  const composer = new EffectComposer(renderer, rt); composer.addPass(new RenderPass(scene, cam));
  const bloom = new UnrealBloomPass(new THREE.Vector2(W / 2, H / 2), .6, .7, .78); composer.addPass(bloom); composer.addPass(new OutputPass());

  const envs = {}, order = Object.keys(ENVS);
  order.forEach((k, i) => { const e = ENVS[k](i + 3); e.group.position.set(i * 120, 0, 0); e.group.visible = false; e.origin = new THREE.Vector3(i * 120, 0, 0); scene.add(e.group); envs[k] = e; });
  const cast = {}, chairs = {};
  function getChar(id, role, opts) { const k = id || role; if (!cast[k] || cast[k].userData.role !== role) { cast[k] = makeChar(role, { seed: (k.length * 7.3) % 10, ...(opts || {}) }); scene.add(cast[k]); } return cast[k]; }
  function chairFor(id) { if (!chairs[id]) { const g = new THREE.Group(); const m = M(0x1a1f2c, { roughness: .5 }); const seat = new THREE.Mesh(new THREE.BoxGeometry(.55, .07, .55), m); seat.position.y = .5; const back = new THREE.Mesh(new THREE.BoxGeometry(.55, .65, .06), m); back.position.set(0, .88, -.27); const post = new THREE.Mesh(new THREE.CylinderGeometry(.04, .04, .5), m); post.position.y = .25; const base = new THREE.Mesh(new THREE.CylinderGeometry(.3, .3, .04, 12), m); base.position.y = .02; g.add(seat, back, post, base); g.traverse(o => { o.castShadow = o.receiveShadow = true; }); scene.add(g); chairs[id] = g; } return chairs[id]; }

  let shots = [], cur = null;
  function load(list) { shots = list.map(s => ({ ...expand(s) })); }
  function vec(env, p) { if (typeof p === 'string') p = envs[env].anchors[p] || [0, 1.2, 0]; return new THREE.Vector3(p[0], p[1], p[2]).add(envs[env].origin); }
  function apply(shot, t) {
    const u = Math.max(0, Math.min(1, (t - shot.t0) / Math.max(.01, shot.t1 - shot.t0))), lt = t - shot.t0, E = envs[shot.env];
    if (cur !== shot.env) { for (const k in envs) envs[k].group.visible = k === shot.env; cur = shot.env; }
    const mood = MOOD[shot.mood || 'calm'] || MOOD.calm; scene.background = new THREE.Color(mood.bg); scene.fog.color.set(mood.bg); scene.fog.density = shot.fog ?? .012; amb.intensity = mood.amb; bloom.strength = mood.bloom * (shot.glow ?? 1);
    // fx -> env state
    const st = { alarm: !!(shot.fx && shot.fx.alarm) };
    if (shot.fx && shot.fx.infect) st.infect = lerp(shot.fx.infect[0], shot.fx.infect[1], ease(u));
    if (shot.fx && shot.fx.route && E.setRoute && shot._route !== JSON.stringify(shot.fx.route)) { E.setRoute(shot.fx.route); shot._route = JSON.stringify(shot.fx.route); }
    st.u = shot.fx && shot.fx.u ? lerp(shot.fx.u[0], shot.fx.u[1], u) : u;
    E.update(lt + (shot.t0 * 1.0), st);
    // cast
    for (const k in cast) cast[k].visible = false; for (const k in chairs) chairs[k].visible = false;
    for (const c of (shot.cast || [])) {
      const ch = getChar(c.id, c.role, c.opts), p = vec(shot.env, c.at || [0, 0, 0]); ch.visible = true;
      let rot = (c.rot || 0) * Math.PI / 180;
      if (c.to) { const q = vec(shot.env, c.to); const k = ease(u); p.lerp(q, k); rot = Math.atan2(q.x - vec(shot.env, c.at || [0, 0, 0]).x, q.z - vec(shot.env, c.at || [0, 0, 0]).z); }
      ch.position.copy(p); ch.rotation.y = rot; ch.scale.setScalar(c.scale || 1);
      const anim = c.anim || 'idle'; pose(ch, anim, lt, 1);
      if (anim === 'sit' || anim === 'type') { const chr = chairFor((c.id || c.role) + '_chair'); chr.visible = true; chr.position.copy(p).add(new THREE.Vector3(Math.sin(rot) * -.18, 0, Math.cos(rot) * -.18)); chr.rotation.y = rot; ch.position.y = p.y - .0; ch.position.add(new THREE.Vector3(Math.sin(rot) * .12, 0, Math.cos(rot) * .12)); }
    }
    // camera
    const c = shot.cam || {}, P = { ...(PRESETS[c.preset || 'wide'] || PRESETS.wide), ...c }; const F = vec(shot.env, c.focus || 'wide');
    const k = ease(u), a = lerp(P.a[0], P.a[1], k) * Math.PI / 180, d = lerp(P.d[0], P.d[1], k), h = lerp(P.h[0], P.h[1], k);
    const shake = c.shake ?? .012, sx = Math.sin(t * 7.3) * shake, sy = Math.sin(t * 5.1 + 1) * shake;
    cam.position.set(F.x + Math.sin(a) * d + sx, F.y * 0 + (typeof c.focus === 'object' ? F.y : F.y) * 0 + h + sy, F.z + Math.cos(a) * d);
    if (P.pos) cam.position.set(...vec(shot.env, P.pos.map((v, i) => Array.isArray(v) ? lerp(v[0], v[1], k) : v)).toArray());
    cam.lookAt(F.x + sx * .5, F.y + (c.lookY || 0), F.z); cam.fov = lerp(c.fov ? c.fov[0] : 40, c.fov ? c.fov[1] : 40, k); cam.updateProjectionMatrix();
    key.position.copy(cam.position).add(new THREE.Vector3(1.2, .6, 0)); rim.position.set(F.x - 3, F.y + 3.5, F.z - 4); rim.target.position.copy(F); rim.color.set(shot.mood === 'tense' || shot.mood === 'shock' ? 0xff4a5a : 0x6fa8ff); key.intensity = (c.key ?? 12) * (P.d[0] < 4 ? 1.3 : 1);
    cam.rotation.z += (c.roll || 0) * Math.PI / 180 * Math.sin(u * 3.14);
  }
  function draw(t) {
    let s = shots.find(x => t >= x.t0 && t < x.t1) || shots[shots.length - 1]; if (!s) return;
    apply(s, t); composer.render();
  }
  return { draw, load, envs, scene, renderer, cam };
}
