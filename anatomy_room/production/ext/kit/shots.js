// リバースの制作の土台：ショットの一覧から描く（2026-11-01〜、pilot_027 から。kit.js のあとに読む）。
// 各回の renderer.html は、セリフごとのショットの一覧 SHOTS と、その回だけの図（holo）・3D の小物を書くだけでよい。
//   SHOTS = [{ at: "l03", off: 0, kind: "photo" | "holo" | "3d" | "2d", ..., card / slam / tags / credit / note }]
//   at は production_script.py の cues（行ごとに l01・l01m〔0.5 秒後〕など）。ショットは次のショットの始まりまで続く。u はその中の進み（0→1）。
//   kind "photo"：{ img, z0, z1, cx, cy, gray, sepia, box }  本物の写真をゆっくり寄せる
//   kind "holo" ：{ draw(X, t, u, s), holo: { tilt, edge } }  2D の図を 3D のホログラムの台に
//   kind "3d"   ：{ draw(t, u, s) }  roomShot・stageShot・starsShot や、その回だけの 3D
//   kind "2d"   ：{ draw(t, u, s) }  bg に直接描く
//   文字：知的は card（[[文字, 大きさ, 太さ, 色], …]、cardY）と note、ドパ・悲劇は slam（{ s, y, size, cols, sub }、悲劇は kit が明朝体の静かな文字にする）と tags。credit は [行, 行]。
// オープニング：KIT.opening = { img, box, cy, title: [1 行目, 2 行目], credit: [行, 行], bg(t) }。知的・悲劇は青い細い縁、ドパは白い額縁。
let SHOTS = [];
function shotAt(t) {
  let i = 0; for (let k = 0; k < SHOTS.length; k++) { const c = CUE[SHOTS[k].at]; if (c !== undefined && t >= c + (SHOTS[k].off || 0)) i = k; }
  const s = SHOTS[i], a = CUE[s.at] + (s.off || 0), nx = SHOTS[i + 1], b = nx && CUE[nx.at] !== undefined ? CUE[nx.at] + (nx.off || 0) : TL.ending_start;
  return { s, i, a, u: clamp((t - a) / Math.max(.3, b - a)) };
}
const sk = (t, a, d = .45) => easeOut(clamp((t - a) / d));
function drawScene(t, name) {
  if (name === "open") { (KIT.opening.bg || (t => driftShot(t)))(t); return "3d"; }
  const { s, u } = shotAt(t); if (s.kind === "3d") { s.draw(t, u, s); return "3d"; } return "2d";
}
function draw2D(t, name) {
  const { s, a, u } = shotAt(t);
  if (s.kind === "holo") { holoClear(); s.draw(holoX, t, u, s); holoDraw(t, s.holo || {}); return; }
  bg.fillStyle = "#05070c"; bg.fillRect(0, 0, W, H);
  if (s.kind === "photo") { const D = KIT.design, box = s.box || [130, 340, 950, 1300];
    photo(bg, IMG[s.img], sk(t, a, .35), s.z0 ?? 1.0, s.z1 ?? 1.08, u, { box, cx: s.cx ?? .5, cy: s.cy ?? .45, gray: s.gray ?? 1, sepia: s.sepia ?? 0, rot: D === "dopa" ? (s.rot ?? -.02) : 0, frame: D === "dopa" ? "#fff" : "glow", bright: s.bright ?? .95 });
    if (D !== "dopa") photoGlow(t, a, box); }
  if (s.kind === "2d") s.draw(t, u, s);
}
function openingBG(t) {
  const o = KIT.opening; bg.fillStyle = `rgba(2,4,12,${o.img ? .42 : .2})`; bg.fillRect(0, 0, W, H); const box = o.box || [230, 660, 850, 1380];
  if (!o.img) return;   // 権利の確かな写真がない回は、背景の CG と文字だけ
  photo(bg, IMG[o.img], KIT.design === "dopa" ? clamp(t / .3) : k_(t, "t0", .5, .1), 1.0, 1.06, clamp(t / 3), { box, cy: o.cy ?? .45, cx: o.cx ?? .5, gray: o.gray ?? 1, rot: KIT.design === "dopa" ? -.02 : 0, frame: KIT.design === "dopa" ? "#fff" : "glow", bright: .95 });
  if (KIT.design !== "dopa") photoGlow(t, .1, box);
}
function openingUI(t) {
  const o = KIT.opening, k = k_(t, "t0", .4, .05); if (k <= 0) return; const [l1, l2] = o.title;
  if (KIT.design === "intel") HUD.title(ui, [[l1, T(o.size1 || 60), "#EAF2F8"], [l2, T(o.size2 || 88), "#FFD58A"]], 540, 420, k, t);
  else if (KIT.design === "dopa") { slam(ui, l1, 540, 330, o.size1 || 96, .05, t, { cols: WHITE, glow: "rgba(255,120,60,.9)", rot: -.03 }); slam(ui, l2, 540, 500, o.size2 || 110, .25, t, { cols: GOLD, glow: "rgba(255,120,60,.9)", rot: .02 }); }
  else { ui.save(); ui.globalAlpha = k; label(ui, l1, 540, 360, o.size1 || 76, "#EAF2F8", { font: MIN, stroke: "#05080c", sw: .14 }); label(ui, l2, 540, 490, o.size2 || 80, "#FFD58A", { font: MIN, stroke: "#05080c", sw: .14 }); ui.restore(); }
  (o.credit || []).forEach((c, i) => credit(c, k, 1440 + i * 40));
}
function tag(ctx, s, x, y, t0, t, col) { const u = t - t0; if (u < 0) return; const e = 1 + .6 * Math.pow(1 - clamp(u / .16), 2); ctx.save(); ctx.translate(x, y); ctx.scale(e, e); ctx.rotate(-.05);
  ctx.font = `400 46px ${MP}`; const w = ctx.measureText(s).width; ctx.fillStyle = col; rrect(ctx, -w / 2 - 22, -38, w + 44, 76, 38); ctx.fill(); label(ctx, s, 0, 0, 46, "#fff", { font: MP, stroke: "#14080e", sw: .16 }); ctx.restore(); }
function drawUI(t, name) {
  if (name === "open") { openingUI(t); return; }
  const { s, a, i } = shotAt(t), D = KIT.design;
  if (i === 0 || name === "hook") { const h = CUE.hook; if (D === "intel") uiNote("※再現CGを含みます", 540, 1250, win(t, h + .3, h + 2.6, .3, .3)); else S.note(ui, "※再現CGを含みます", 540, 1290, win(t, h + .3, h + 2.6, .3, .3), 26, true); }
  const ci = ciPhase(t); if (ci) return;   // カットインの間は文字を出さない
  if (s.card) uiCard(s.card, 540, s.cardY || 250, sk(t, a + .15));
  if (s.note) uiNote(s.note, 540, s.noteY || 1320, sk(t, a + .3));
  if (s.slam) { const z = s.slam; slam(ui, z.s, 540, z.y || 330, z.size || 110, a + (z.off ?? .08), t, { cols: z.cols || GOLD, rot: z.rot ?? -.04, sub: z.sub || null, glow: z.glow || "rgba(255,150,60,.9)" }); }
  if (s.slam2) { const z = s.slam2; slam(ui, z.s, 540, z.y || 1320, z.size || 90, a + (z.off ?? .5), t, { cols: z.cols || WHITE, rot: z.rot ?? .03, sub: z.sub || null }); }
  (s.tags || []).forEach(([txt, x, y, off, col]) => tag(ui, txt, x, y, a + off, t, col));
  (s.credit || []).forEach((c, k) => credit(c, sk(t, a + .2), (s.creditY || 1300) + k * 40));
}

// ---------------------------------------------------------------- 使い回せる 3D の場面
// 部屋（研究室・病室・事務所）：床・壁・窓・机・人体（後ろ姿）。PROPS に小物を足す
const room = set("room"); let roomWallM, roomWinM, roomDust, roomPeople = {}, ROOM_PROPS;
function buildRoom({ wall = 0xa8aca8, floorTint = 0x8a8478, table = true } = {}) {
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(16, 16), pbr("old_wood_floor", [6, 6], { tint: floorTint })); floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; room.add(floor);
  roomWallM = M(wall, { roughness: .95 }); Cine.surface(roomWallM, "plaster", { repeat: [4, 2], normal: .4 });
  for (const [x, z, ry] of [[0, -3, 0], [-3.5, 0, Math.PI / 2], [3.5, 0, -Math.PI / 2]]) { const w = new THREE.Mesh(new THREE.PlaneGeometry(10, 4.5), roomWallM); w.position.set(x, 2.25, z); w.rotation.y = ry; w.receiveShadow = true; room.add(w); }
  roomWinM = new THREE.MeshBasicMaterial({ color: C(0x7a90a8) }); const win_ = new THREE.Mesh(new THREE.PlaneGeometry(1.6, 1.5), roomWinM); win_.position.set(-3.48, 2.0, -.8); win_.rotation.y = Math.PI / 2; win_.userData.noAO = true; room.add(win_);
  if (table) { box(2.6, .06, 1.0, pbr("wood_table_001", [4, 1], { tint: 0x6a5040 }), 0, .9, -1.7, room); box(2.6, .84, .9, M(0x5a4a3c, { roughness: .7 }), 0, .44, -1.75, room); }
  roomDust = Cine.dust({ min: [-3, .3, -2.8], max: [3, 2.6, 2], count: 600, size: .01, seed: 33 }); room.add(roomDust.points);
  ROOM_PROPS = new THREE.Group(); room.add(ROOM_PROPS);
  for (const [k, kind, coat] of [["stand", "man_stand", 0x2e3238], ["sit", "man_sit", 0x2e3238], ["walk", "man_walk", 0x2e3238], ["white", "man_stand", 0xe8e8e2]]) {
    const h = human(kind, { coat, hair: 0x2a2018 }); h.rotation.y = Math.PI; h.visible = false; room.add(h); roomPeople[k] = h; }
  const chair = new THREE.Group(); box(.45, .05, .45, M(0x3a2a20), 0, .45, 0, chair); box(.45, .5, .05, M(0x3a2a20), 0, .7, .22, chair); chair.visible = false; room.add(chair); roomPeople.chair = chair;
}
// who：{ stand|sit|walk|white: [x, z] }、night：夜（窓が暗く、机のランプ）、warm：0→1 で暖かい色
function roomShot(t, { cam = [V3(2.6, 1.7, 2.8), V3(-.1, 1.1, -1.5), 40], who = {}, night = 0, warm = 0, dof = null, exp = 1.0, dust = 1 } = {}) {
  show("room"); envOn(.45 + .2 * (1 - night)); roomDust.update(t, dust);
  for (const k of ["stand", "sit", "walk", "white"]) { const p = who[k], h = roomPeople[k]; h.visible = !!p; if (p) h.position.set(p[0], 0, p[1]); }
  roomPeople.chair.visible = !!who.sit; if (who.sit) roomPeople.chair.position.set(who.sit[0], 0, who.sit[1] + .05);
  roomWinM.color = C(0x7a90a8).lerp(C(0x101626), night);
  lights({ keyPos: night ? [.9, 1.5, -1.2] : [-3.2, 3, -.8], keyAt: [0, .9, -1.5], keyI: night ? 12 : 13 + 6 * warm, angle: night ? .9 : .7, keyCol: night ? 0xffc888 : lerpHex(0xf0f4ff, 0xffe0b8, warm),
    rimPos: [2, 3, 3], rimI: .45, rimCol: 0x9fc8ff, hemiI: night ? .07 : .22, hemiSky: night ? 0x2a3448 : 0xb8bcc0, hemiGround: 0x1a1612, fog: .035, fogC: night ? 0x05070c : 0x0e1014, exp });
  setCam(cam[0], cam[1], cam[2] || 40, .02, 40); draw3D({ ao: true, dof });
}
function lerpHex(a, b, k) { return new THREE.Color(a).lerp(new THREE.Color(b), clamp(k)).getHex(); }
// 暗い台座：主役の小物を STAGE_HERO に足して、回しながら見せる
const stage = set("stage"); let STAGE_HERO, stageRing;
function buildStage({ floor = 0x0c0e12 } = {}) {
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(30, 30), M(floor, { roughness: .25, metalness: .5 })); fl.rotation.x = -Math.PI / 2; fl.receiveShadow = true; stage.add(fl);
  const ped = cyl(.9, 1.0, .25, M(0x1a1e26, { roughness: .4, metalness: .6 }), 0, .125, 0, stage, 64); ped.receiveShadow = true;
  stageRing = new THREE.Mesh(new THREE.TorusGeometry(.95, .012, 8, 96), new THREE.MeshBasicMaterial({ color: C(0x8fdcff) })); stageRing.rotation.x = Math.PI / 2; stageRing.position.y = .26; stageRing.userData.noAO = true; stage.add(stageRing);
  STAGE_HERO = new THREE.Group(); STAGE_HERO.position.y = .25; stage.add(STAGE_HERO);
  const d = Cine.dust({ min: [-4, 0, -4], max: [4, 4, 4], count: 500, size: .015, seed: 51 }); stage.add(d.points); stage.userData.dust = d;
}
function stageShot(t, { cam = [V3(0, 1.4, 3.2), V3(0, .9, 0), 38], spin = .3, keyCol = 0xfff0dc, ring = 0x8fdcff, exp = 1.0, dof = null, glow = 0 } = {}) {
  show("stage"); scene.environment = ENV_ROOM; STAGE_HERO.rotation.y = t * spin; stage.userData.dust.update(t, 1); stageRing.material.color = C(ring);
  lights({ keyPos: [1.5, 3.5, 2.5], keyAt: [0, .8, 0], keyI: 22, angle: .5, keyCol, rimPos: [-2.5, 2, -3], rimI: 1.4 + glow, rimCol: ring, hemiI: .08, fog: .03, fogC: 0x04060a, exp });
  setCam(cam[0], cam[1], cam[2] || 38, .02, 60); draw3D({ ao: true, dof });
}
// 星空と球（惑星・泡・原子など）
const stars = set("stars"); let starsPts;
function buildStars() { const n = 2500, sp = new Float32Array(n * 3), r = S.rng(7); for (let i = 0; i < n; i++) { const a = r() * Math.PI * 2, b = Math.acos(2 * r() - 1), d = 60 + r() * 40; sp.set([d * Math.sin(b) * Math.cos(a), d * Math.sin(b) * Math.sin(a), d * Math.cos(b)], i * 3); }
  const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.BufferAttribute(sp, 3)); starsPts = new THREE.Points(g, new THREE.PointsMaterial({ color: 0xdfe8ff, size: .18 })); stars.add(starsPts); }
function starsShot(t, { cam = [V3(0, 0, 6), V3(0, 0, -10), 42], extra = [], exp = 1.0 } = {}) { show("stars", ...extra); scene.environment = null; starsPts.rotation.y = t * .01;
  lights({ keyPos: [6, 3, 6], keyAt: [0, 0, 0], keyI: 26, angle: .9, keyCol: 0xfff2e0, rimPos: [-6, 2, -8], rimI: 1.2, rimCol: 0x8fcfff, hemiI: .06, fog: .002, fogC: 0x020309, exp });
  setCam(cam[0], cam[1], cam[2] || 42, .05, 300); draw3D({ ao: false }); }
// 2D の図の小さな部品
function arrow(X, x0, y0, x1, y1, col = "#FFE2A8", w = 6) { X.save(); X.strokeStyle = col; X.fillStyle = col; X.lineWidth = w; X.lineCap = "round"; X.beginPath(); X.moveTo(x0, y0); X.lineTo(x1, y1); X.stroke();
  const a = Math.atan2(y1 - y0, x1 - x0); X.beginPath(); X.moveTo(x1, y1); X.lineTo(x1 - 26 * Math.cos(a - .45), y1 - 26 * Math.sin(a - .45)); X.lineTo(x1 - 26 * Math.cos(a + .45), y1 - 26 * Math.sin(a + .45)); X.closePath(); X.fill(); X.restore(); }
function bigNum(X, s, y, size, col = "#FFE2A8") { lab2(X, s, 540, y, T(size), col, 900); }
