// Named shot recipes: a script picks a recipe name (+ optional overrides); the world expands it into env / cast / camera.
// cam arrays are [start, end] over the shot. Positions are local to the environment.
const R = (o) => o;
export const RECIPES = {
  // ---- office (the victim side)
  office_type:    R({ env: 'office', mood: 'curious', cast: [{ id: 'w1', role: 'worker', at: [0, 0, -4.4], rot: 180, anim: 'type' }], cam: { preset: 'over_shoulder', focus: [0, 1.25, -4.8], a: [20, 10], d: [3.4, 2.7], h: [1.75, 1.6] } }),
  office_wide:    R({ env: 'office', mood: 'calm', cast: [{ id: 'w1', role: 'worker', at: [0, 0, -4.4], rot: 180, anim: 'type' }, { id: 'w2', role: 'workerF', at: [3.4, 0, -4.4], rot: 180, anim: 'type' }, { id: 'a1', role: 'banker', at: [-2.2, 0, 1.5], rot: 160, anim: 'walk', to: [-2.2, 0, -1.5] }], cam: { preset: 'orbit', focus: [0, 1.3, -3], a: [-25, 22], d: [10, 9], h: [2.8, 2.4], fov: [40, 40] } }),
  office_phone:   R({ env: 'office', mood: 'tense', cast: [{ id: 'w1', role: 'worker', at: [0, 0, -2], rot: 200, anim: 'phone' }], cam: { preset: 'closeup', focus: [0, 1.55, -2], a: [-20, -8], d: [3.2, 2.5], h: [1.7, 1.6] } }),
  office_alarm:   R({ env: 'office', mood: 'shock', cast: [{ id: 'w1', role: 'worker', at: [0, 0, -2.6], rot: 0, anim: 'shock' }, { id: 'w2', role: 'workerF', at: [2.2, 0, -3], rot: 20, anim: 'shock' }], cam: { preset: 'low_hero', focus: [1, 1.3, -2.8], a: [-12, 8], d: [7, 5.4], h: [.6, 1.2] } }),
  printer_close:  R({ env: 'office', mood: 'tense', cast: [{ id: 'w1', role: 'worker', at: [-5.1, 0, -.4], rot: 205, anim: 'think' }], cam: { preset: 'closeup', focus: [-6.8, 1.15, -1.6], a: [28, 14], d: [4.2, 2.8], h: [1.6, 1.45] } }),
  // ---- server room
  server_alarm:   R({ env: 'serverRoom', mood: 'shock', fx: { alarm: true }, cast: [{ id: 'e1', role: 'engineer', at: [0, 0, -4], rot: 0, anim: 'shock' }], cam: { preset: 'low_hero', focus: [0, 1.2, -4], a: [-10, 8], d: [7.5, 5.8], h: [.6, 1] } }),
  server_dolly:   R({ env: 'serverRoom', mood: 'tense', cast: [{ id: 'e1', role: 'engineer', at: [0, 0, -9], rot: 0, anim: 'walk', to: [0, 0, -14] }], cam: { preset: 'wide', focus: [0, 1.4, -14], pos: [0, 1.5, [8, -4]], fov: [40, 40], shake: .02 } }),
  server_crane:   R({ env: 'serverRoom', mood: 'curious', cast: [{ id: 'e1', role: 'engineer', at: [0, 0, -3], rot: 0, anim: 'point' }], cam: { preset: 'crane_down', focus: [0, 1.2, -3], d: [10, 7], h: [8, 2.4] } }),
  // ---- the attacker
  den_back:       R({ env: 'den', mood: 'tense', cast: [{ id: 'h1', role: 'hacker', at: [0, 0, -3.3], rot: 180, anim: 'type' }], cam: { preset: 'over_shoulder', focus: [0, 1.4, -3.9], a: [18, 8], d: [3.6, 2.8], h: [1.8, 1.7] } }),
  den_front:      R({ env: 'den', mood: 'reveal', cast: [{ id: 'h1', role: 'hacker', at: [0, 0, -3.3], rot: 0, anim: 'type' }], cam: { preset: 'closeup', focus: [0, 1.3, -3.3], a: [-8, 8], d: [3.4, 2.4], h: [1.5, 1.4] } }),
  den_wide:       R({ env: 'den', mood: 'tense', cast: [{ id: 'h1', role: 'hacker', at: [0, 0, -3.3], rot: 180, anim: 'type' }], cam: { preset: 'crane_up', focus: [0, 1.4, -4], a: [10, -8], d: [8, 9], h: [1.6, 5] } }),
  den_two:        R({ env: 'den', mood: 'tense', cast: [{ id: 'h1', role: 'hacker', at: [-1.4, 0, -3.3], rot: 180, anim: 'type' }, { id: 'h2', role: 'crook', at: [1.6, 0, -2.2], rot: 215, anim: 'point' }], cam: { preset: 'orbit', focus: [0, 1.3, -3], a: [-30, 30], d: [7, 6.5], h: [1.8, 2] } }),
  // ---- places
  bank_front:     R({ env: 'bank', mood: 'calm', fog: .003, cam: { preset: 'wide', focus: [0, 7, 3], a: [-16, 10], d: [40, 32], h: [5, 8], fov: [44, 44] } }),
  bank_crane:     R({ env: 'bank', mood: 'curious', fog: .003, cam: { preset: 'crane_up', focus: [0, 6, 3], a: [-14, 6], d: [38, 36], h: [1.2, 22], fov: [40, 40] } }),
  bank_guard:     R({ env: 'bank', mood: 'calm', fog: .006, cast: [{ id: 'g1', role: 'guard', at: [-3, 0, 14], rot: 180, anim: 'walk', to: [-1, 0, 9] }], cam: { preset: 'low_hero', focus: [-2, 2.5, 11], a: [-25, -5], d: [12, 9], h: [.8, 1.3] } }),
  vault_door:     R({ env: 'vault', mood: 'tense', cast: [{ id: 'b1', role: 'banker', at: [2.6, 0, -2.6], rot: 235, anim: 'talk' }], cam: { preset: 'push_in', focus: [0, 2.6, -6], a: [5, -5], d: [11, 6.5], h: [2.2, 2.6] } }),
  vault_cash:     R({ env: 'vault', mood: 'reveal', cam: { key: 1, preset: 'orbit', focus: [-1, .6, 1.8], a: [-40, 30], d: [8, 5.5], h: [3, 1.8] } }),
  fbi_front:      R({ env: 'fbi', mood: 'calm', fog: .003, cam: { preset: 'wide', focus: [0, 9, 6], a: [-22, 12], d: [64, 54], h: [4, 9], fov: [42, 42] } }),
  fbi_agents:     R({ env: 'fbi', mood: 'reveal', fog: .006, cast: [{ id: 'a1', role: 'agent', at: [-1.3, 0, 22], rot: 180, anim: 'walk', to: [-1.3, 0, 15] }, { id: 'a2', role: 'agentF', at: [1.3, 0, 22], rot: 180, anim: 'walk', to: [1.3, 0, 15] }], cam: { preset: 'low_hero', focus: [0, 1.4, 17], a: [0, 0], d: [10, 7.5], h: [.5, .7] } }),
  war_room:       R({ env: 'warRoom', mood: 'reveal', cast: [{ id: 'a1', role: 'agent', at: [-.9, 0, .9], rot: 180, anim: 'point' }, { id: 'a2', role: 'agentF', at: [1.0, 0, .9], rot: 180, anim: 'talk' }], cam: { preset: 'orbit', focus: [0, 1.6, 0], a: [-20, 18], d: [9.5, 8], h: [1.8, 2.4] } }),
  war_screen:     R({ env: 'warRoom', mood: 'tense', cast: [{ id: 'a1', role: 'agent', at: [-1.6, 0, -5.4], rot: 0, anim: 'point' }], cam: { preset: 'push_in', focus: [0, 3, -7], a: [8, -4], d: [11, 6], h: [2.2, 2.8] } }),
  // ---- the attack itself
  cyber_spread:   R({ env: 'cyberspace', mood: 'tense', fx: { infect: [0.05, 0.9] }, cam: { preset: 'orbit', focus: [0, 0, 0], a: [-50, 60], d: [26, 20], h: [4, 6], fov: [40, 40] } }),
  cyber_fly:      R({ env: 'cyberspace', mood: 'shock', fx: { infect: [0.5, 1] }, cam: { preset: 'wide', focus: [0, 0, 0], pos: [[-14, 12], [2, -2], [24, 6]], fov: [46, 46], shake: .03 } }),
  globe_route:    R({ env: 'globe', mood: 'reveal', fx: { route: [['A', 23.8, 90.4], ['B', 40.7, -74.0]] }, cam: { preset: 'orbit', focus: [0, 0, 0], a: [-25, 25], d: [19, 17], h: [2, 3], fov: [40, 40] } }),
};
export function expand(s) {
  if (!s.recipe) return s;
  const base = RECIPES[s.recipe]; if (!base) throw new Error('unknown recipe ' + s.recipe);
  const o = JSON.parse(JSON.stringify(base)); const { recipe, cast, cam, fx, ...rest } = s;
  Object.assign(o, rest); if (cam) o.cam = { ...o.cam, ...cam }; if (fx) o.fx = { ...(o.fx || {}), ...fx };
  if (cast) o.cast = cast.map((c, i) => ({ ...(o.cast || [])[i], ...c }));
  return o;
}
