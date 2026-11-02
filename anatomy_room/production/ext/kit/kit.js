// リバースの制作の土台（kit、2026-11-01〜、pilot_024 から）。テンプレートの外の部品。
// 3 つの設計（知的 intel・ドパ dopa・悲劇 tragedy、templates/DESIGN_MODES.md）で共通の部品を集めたもの。土台は pilot_021（悲劇・派手な文字）と pilot_023（知的・3D）。
// 各回の renderer.html は、stage.js・cine.js・hud_ext.js・three147 のあとにこのファイルと scene_assets.js を読み、
//   Object.assign(KIT, {...}) で設計・場面・カットインを決めて、場面の関数だけを書く：
//   drawScene(t, name) → "3d" | "2d"、draw2D(t, name)、drawUI(t, name)、buildMood()、thumb()（サムネイル）、（任意）openingBG(t)・fxEp(t, name)
//   最後に kitStart(() => { 3D の組み立て }) を呼ぶ。
// カットイン（起承転結の頭）：文字は入れず、カメラの傾き・画角の動きで区切る（camFX）。ドパ設計だけ、切れ目ごとに画面の一打（揺れ・ズーム）を入れる。閃光は使わない。
const S = Stage, { W, H, clamp, lerp, easeOut, easeIn, easeInOut, prog, win, text, rrect } = Stage;
const TS = S.TEXT_SCALE, T = s => Math.round(s * TS);
const bg = document.getElementById("bg").getContext("2d");
const ui = document.getElementById("ui").getContext("2d");
const KIT = {
  design: "intel",      // "intel" | "dopa" | "tragedy"
  scenes: [],           // 場面の名前（production_script.py の segments と同じ順）
  images: [],           // window.ASSETS の本物の写真のキー
  ci: {},               // { きっかけ: [[傾き, 画角の倍率], …] }。1 つなら 1 回、3 つなら転の 3 回
  hits: [],             // [[きっかけ, 強さ, 遅れ], …]：画面の一打（ズームと揺れ）
  darkFrom: null,       // 悲劇：このきっかけから、さらに少しずつ暗く（悲劇は最初から暗い幕がかかる、2026-11-01〜）
  serifFrom: null,      // 明朝体の静かな文字・字幕に切り替えるきっかけ（悲劇は指定しなくても最初から明朝体）
};
let TL, CUE, MOOD = [], NOW = 0, SCN = [];
const k_ = (t, cue, d = .4, off = 0) => easeOut(prog(t, CUE[cue] + off, d));
const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
const b64buf = s => { const bin = atob(s), u = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i); return u.buffer; };

// ---------------------------------------------------------------- カットイン（カメラの傾き・画角）
const CUT = [.45, .95, 1.5];   // 切れ目（秒）
function ciPhase(t) { if (!CUE) return null; for (const c in KIT.ci) { const d = t - CUE[c], n = KIT.ci[c].length; if (d >= 0 && d < CUT[n - 1]) return { c, d, p: d < CUT[0] ? 0 : d < CUT[1] ? 1 : 2 }; } return null; }
function camFX(t) { const P = ciPhase(t); if (!P) return; const [roll, z] = KIT.ci[P.c][P.p], a = P.p ? CUT[P.p - 1] : 0, k = easeOut(clamp((P.d - a) / ((CUT[P.p] - a) * .85)));
  cam.fov *= z + (1 - z) * k; cam.rotateZ(roll * (1 - k)); cam.updateProjectionMatrix(); cam.updateMatrixWorld(); }

// ---------------------------------------------------------------- 文字（フォント：Dela Gothic One＝DG、Mochiy Pop One＝MP、Shippori Mincho＝MIN）
const DG = '"DelaGothic", "Noto Sans CJK JP", sans-serif', MP = '"MochiyPop", "Noto Sans CJK JP", sans-serif', MIN = '"Mincho", "Noto Serif CJK JP", serif';
const fontReady = Promise.all([["DelaGothic", "font_dela"], ["MochiyPop", "font_mochiy"], ["Mincho", "font_mincho"]].filter(([, k]) => window.ASSETS[k])
  .map(([n, k]) => new FontFace(n, b64buf(window.ASSETS[k])).load().then(f => document.fonts.add(f))));
let GSEQ = 500000;
function logBox(ctx, s, x0, y0, x1, y1, size) {   // 文字の検査用（stage.js の text() と同じ形で記録）
  if (ctx.globalAlpha < .35 || !s.trim()) return; const m = ctx.getTransform(), pts = [[x0, y0], [x1, y0], [x0, y1], [x1, y1]].map(([x, y]) => [m.a * x + m.c * y + m.e, m.b * x + m.d * y + m.f]);
  S.TEXTLOG.push({ s, box: [Math.min(...pts.map(p => p[0])), Math.min(...pts.map(p => p[1])), Math.max(...pts.map(p => p[0])), Math.max(...pts.map(p => p[1]))], size: size * Math.hypot(m.a, m.b), group: ++GSEQ, container: null, ignore: false });
}
function label(ctx, s, x, y, size, col = "#fff", { font = MP, align = "center", stroke = "#06080e", sw = .2 } = {}) {   // 図の中の文字（縁取りつき、検査に記録）
  ctx.save(); ctx.font = `400 ${size}px ${font}`; ctx.textAlign = align; ctx.textBaseline = "middle"; ctx.lineJoin = "round"; ctx.lineWidth = size * sw; ctx.strokeStyle = stroke; ctx.strokeText(s, x, y); ctx.fillStyle = col; ctx.fillText(s, x, y);
  const w = ctx.measureText(s).width, x0 = align === "center" ? x - w / 2 : align === "right" ? x - w : x; logBox(ctx, s, x0, y - size * .58, x0 + w, y + size * .58, size); ctx.restore();
}
const SERIF = () => KIT.design === "tragedy" ? -Infinity : KIT.serifFrom && CUE && CUE[KIT.serifFrom] !== undefined ? CUE[KIT.serifFrom] : Infinity;   // 悲劇は最初から明朝体（2026-11-01〜）
function calmText(ctx, s, x, y, size, t0, t, sub, dur = 99) {   // 静かな文字：ゆっくり現れる。揺れ・色ずれ・光なし（悲劇の終盤）
  const u = t - t0, a = Math.min(clamp(u / .6), 1 - clamp((u - dur) / .4)); if (u < 0 || a <= 0) return; size = Math.round(size * .62); y = Math.max(y, 230 + size * .7);
  ctx.save(); ctx.globalAlpha *= a; ctx.font = `600 ${size}px ${MIN}`; ctx.textAlign = "center"; ctx.textBaseline = "middle"; let w = ctx.measureText(s).width; if (w > 860) { size = Math.floor(size * 860 / w); ctx.font = `600 ${size}px ${MIN}`; w = ctx.measureText(s).width; }
  ctx.lineJoin = "round"; ctx.lineWidth = size * .12; ctx.strokeStyle = "rgba(4,8,14,.85)"; ctx.strokeText(s, x, y); ctx.fillStyle = "#EEF3F8"; ctx.fillText(s, x, y); logBox(ctx, s, x - w / 2, y - size * .55, x + w / 2, y + size * .55, size);
  if (sub) { const s2 = Math.max(30, Math.round(size * .42)); ctx.font = `600 ${s2}px ${MIN}`; const w2 = ctx.measureText(sub).width; ctx.lineWidth = s2 * .14; ctx.strokeText(sub, x, y + size * .95); ctx.fillStyle = "#C8D6E4"; ctx.fillText(sub, x, y + size * .95); logBox(ctx, sub, x - w2 / 2, y + size * .95 - s2 * .55, x + w2 / 2, y + size * .95 + s2 * .55, s2); }
  ctx.restore(); }
// 叩きつける文字：大きく出て一瞬で縮み（行き過ぎて戻る）、色ずれ・揺れ・光。cols＝[上の色, 下の色]。悲劇の終盤は calmText に切り替わる
function slam(ctx, s, x, y, size, t0, t, { cols = ["#FFF36A", "#FF9A1F"], stroke = "#120606", rot = -.05, font = DG, dur = 99, out = .25, glow = "rgba(255,170,60,.9)", sub = null } = {}) {
  if (t0 >= SERIF()) return calmText(ctx, s, x, y, size, t0, t, sub, dur);
  const u = t - t0; if (u < 0 || u > dur + out) return;
  { ctx.save(); ctx.font = `400 ${size}px ${font}`; const w0 = ctx.measureText(s).width; ctx.restore(); if (w0 > 860) size = Math.floor(size * 860 / w0); }   // 幅 860 まで、上端は 210＋文字の高さ
  y = Math.max(y, 210 + size * .7); if (y > 860 && y < 1660) x = Math.min(x, 950 - Math.min(430, (size * s.length) / 2));
  const kin = clamp(u / .16), e = 1 + 1.6 * Math.pow(1 - kin, 3) - .12 * Math.sin(kin * Math.PI) * (1 - kin * .3);
  const a = Math.min(clamp(u / .06), 1 - clamp((u - dur) / out)); if (a <= 0) return;
  const sh = Math.max(0, 1 - u / .35) * 18, r = S.rng(Math.floor(t * 30) + s.length), dx = (r() - .5) * sh, dy = (r() - .5) * sh;
  ctx.save(); ctx.globalAlpha *= a; ctx.translate(x + dx, y + dy); ctx.rotate(rot); ctx.scale(e, e);
  ctx.font = `400 ${size}px ${font}`; ctx.textAlign = "center"; ctx.textBaseline = "middle"; const w = ctx.measureText(s).width;
  if (u < .25) { ctx.save(); ctx.globalAlpha *= .7 * (1 - u / .25); ctx.fillStyle = "#ff2a4a"; ctx.fillText(s, -10, 0); ctx.fillStyle = "#2af0ff"; ctx.fillText(s, 10, 0); ctx.restore(); }   // 色ずれ
  ctx.lineJoin = "round"; ctx.shadowColor = glow; ctx.shadowBlur = 40; ctx.strokeStyle = stroke; ctx.lineWidth = size * .2; ctx.strokeText(s, 0, 0); ctx.shadowBlur = 0;
  ctx.strokeStyle = "#ffffff"; ctx.lineWidth = size * .06; ctx.strokeText(s, 0, 0);
  const g = ctx.createLinearGradient(0, -size * .5, 0, size * .5); g.addColorStop(0, cols[0]); g.addColorStop(1, cols[1]); ctx.fillStyle = g; ctx.fillText(s, 0, 0);
  logBox(ctx, s, -w / 2 - size * .1, -size * .55, w / 2 + size * .1, size * .55, size);
  if (sub) { ctx.font = `400 ${size * .32}px ${MP}`; const w2 = ctx.measureText(sub).width; ctx.lineWidth = size * .08; ctx.strokeStyle = stroke; ctx.strokeText(sub, 0, size * .98); ctx.fillStyle = "#ffffff"; ctx.fillText(sub, 0, size * .98);
    logBox(ctx, sub, -w2 / 2, size * .98 - size * .19, w2 / 2, size * .98 + size * .19, size * .32); }
  ctx.restore();
}
const RED = ["#FF7A8A", "#E8102E"], GOLD = ["#FFF36A", "#FF9A1F"], PINK = ["#FFD0F0", "#FF4AB8"], CYAN = ["#C8FFFF", "#2AC8FF"], ICE = ["#FFFFFF", "#8FD0FF"], WHITE = ["#FFFFFF", "#C8C8D8"], LIME = ["#F0FFB0", "#5AE04A"];
// 字幕：知的設計は S.docSub。ドパ・悲劇は跳ねる字幕（塊が変わるたびに飛び出す）、悲劇の終盤は明朝体の静かな字幕
function calmSub(ctx, line, rows, u) {
  let size = 54; ctx.font = `600 ${size}px ${MIN}`; const wOf = () => Math.max(...rows.map(r => ctx.measureText(r.replace(/\*\*/g, "")).width)); let wmax = wOf(); if (wmax > 820) { size = Math.floor(size * 820 / wmax); ctx.font = `600 ${size}px ${MIN}`; wmax = wOf(); }
  const lh = size * 1.45, bw = wmax + 90, bh = rows.length * lh + 30, cx = 495, cy = 1495; ctx.save(); ctx.globalAlpha *= clamp(u / .35); ctx.fillStyle = "rgba(4,8,14,.62)"; ctx.fillRect(cx - bw / 2, cy - bh / 2, bw, bh);
  rows.forEach((r, i) => { const parts = r.split("**"), ws = parts.map(q => ctx.measureText(q).width), tw = ws.reduce((a, b) => a + b, 0); let x = cx - tw / 2; const y = cy - (rows.length - 1) * lh / 2 + i * lh;
    parts.forEach((q, j) => { if (!q) return; ctx.textAlign = "left"; ctx.textBaseline = "middle"; ctx.fillStyle = j % 2 ? "#BFE0F8" : "#F2F5F8"; ctx.fillText(q, x, y); x += ws[j]; }); logBox(ctx, r.replace(/\*\*/g, ""), cx - tw / 2, y - size * .6, cx + tw / 2, y + size * .6, size); });
  ctx.restore(); }
function popSub(ctx, t, endAt) {
  const line = S.currentLine(t); if (!line || t >= endAt || line.id === "L00" || !line.sub) return;
  const subs = Array.isArray(line.sub) ? line.sub : [line.sub], lens = subs.map(s => s.replace(/\*\*/g, "").replace(/ \/ /g, "").length), tot = lens.reduce((a, b) => a + b, 0);
  const kk = clamp((t - line.start) / (line.end - line.start)) * tot; let acc = 0, idx = subs.length - 1, cs = 0;
  for (let i = 0; i < lens.length; i++) { if (kk < acc + lens[i]) { idx = i; break; } acc += lens[i]; }
  { let a2 = 0; for (let i = 0; i < idx; i++) a2 += lens[i]; cs = line.start + (line.end - line.start) * a2 / tot; }
  const rows = subs[idx].split(" / "), u = t - cs, pop = 1 + .35 * Math.pow(1 - clamp(u / .14), 2), cx = 495, cy = 1495;
  if (line.start >= SERIF() - .01) return calmSub(ctx, line, rows, u);
  let size = 66; ctx.font = `400 ${size}px ${DG}`; const wOf = () => Math.max(...rows.map(r => ctx.measureText(r.replace(/\*\*/g, "")).width)); let wmax = wOf();
  if (wmax > 800) { size = Math.floor(size * 800 / wmax); ctx.font = `400 ${size}px ${DG}`; wmax = wOf(); }
  const lh = size * 1.3, bw = wmax + 80, bh = rows.length * lh + 34;
  ctx.save(); ctx.translate(cx, cy); ctx.scale(pop, pop); ctx.rotate(-.025);
  ctx.save(); ctx.transform(1, 0, -.12, 1, 0, 0); ctx.fillStyle = "rgba(8,4,14,.82)"; ctx.fillRect(-bw / 2, -bh / 2, bw, bh);
  const g = ctx.createLinearGradient(-bw / 2, 0, bw / 2, 0); g.addColorStop(0, "#2ad8ff"); g.addColorStop(1, "#e8f4ff"); ctx.fillStyle = g; ctx.fillRect(-bw / 2, bh / 2 - 7, bw, 7); ctx.fillRect(-bw / 2, -bh / 2, 10, bh); ctx.restore();
  rows.forEach((r, i) => { const parts = r.split("**"), ws = parts.map(p => ctx.measureText(p).width), tw = ws.reduce((a, b) => a + b, 0); let x = -tw / 2; const y = -(rows.length - 1) * lh / 2 + i * lh + 3;
    parts.forEach((p, j) => { if (!p) return; ctx.textAlign = "left"; ctx.textBaseline = "middle"; ctx.lineJoin = "round"; ctx.lineWidth = size * .22; ctx.strokeStyle = "#0a0408"; ctx.strokeText(p, x, y);
      ctx.fillStyle = j % 2 ? "#FFE84A" : "#FFFFFF"; ctx.fillText(p, x, y); x += ws[j]; });
    logBox(ctx, r.replace(/\*\*/g, ""), -tw / 2, y - size * .58, tw / 2, y + size * .58, size); });
  ctx.restore();
}
// 知的設計の札（見出し）と小さな注記
function uiCard(lines, x, y, k = 1) {
  if (k <= 0) return; ui.save(); ui.globalAlpha *= clamp(k);
  const ws = lines.map(([s, sz, w = 700]) => { ui.font = `${w} ${sz}px ${S.FONT}`; return ui.measureText(s).width; });
  const pw = Math.max(...ws) + 64, ph = lines.reduce((a, [, sz]) => a + sz * 1.32, 0) + 36, x0 = x - pw / 2, y0 = y - ph / 2;
  rrect(ui, x0, y0, pw, ph, 12); ui.fillStyle = "rgba(8,14,26,.78)"; ui.fill(); ui.strokeStyle = "rgba(143,220,255,.35)"; ui.lineWidth = 1.5; ui.stroke(); ui.fillStyle = "#8fdcff"; ui.fillRect(x0, y0 + 14, 4, ph - 28);
  S.group(() => { let yy = y0 + 18; lines.forEach(([s, sz, w = 700, col = "#EAF2F8"]) => { yy += sz * 1.32 / 2; text(ui, s, x, yy + 2, sz, col, { weight: w }); yy += sz * 1.32 / 2; }); }, [x0, y0, x0 + pw, y0 + ph]);
  ui.restore();
}
function uiNote(s, x, y, k = 1, size = Math.round(24 * TS)) {
  if (k <= 0) return; ui.save(); ui.globalAlpha *= clamp(k); ui.font = `500 ${size}px ${S.FONT}`; const w = ui.measureText(s).width + 28;
  rrect(ui, x - w / 2, y - size * .8, w, size * 1.6, 8); ui.fillStyle = "rgba(8,14,26,.6)"; ui.fill();
  S.group(() => text(ui, s, x, y + 1, size, "#B8C7D6", { weight: 500 }), [x - w / 2, y - size * .8, x + w / 2, y + size * .8]); ui.restore();
}
function credit(s, k, y = 1300) { if (k <= 0) return; ui.save(); ui.globalAlpha = clamp(k) * .9; S.group(() => text(ui, s, 540, y, 26, "#B8C7D6", { weight: 500, stroke: "#04101c", sw: 5 })); ui.restore(); }
function confetti(ctx, t, t0, dur = 2.2, seed = 77) {   // 紙吹雪（ドパ・悲劇の序盤）
  const u = t - t0; if (u < 0 || u > dur) return; const r = S.rng(seed), cols = ["#ff4a8a", "#ffd23a", "#3ad8ff", "#7cff6a", "#b86aff", "#ff8a3a"]; ctx.save(); ctx.globalAlpha = Math.min(1, (dur - u) / .5);
  for (let i = 0; i < 160; i++) { const x0 = r() * W, vy = 400 + r() * 500, x = x0 + Math.sin(u * 3 + i) * 40, y = -40 + vy * u - (r() * 300), a = u * (4 + r() * 6) + i; if (y < -40 || y > H) continue;
    ctx.save(); ctx.translate(x, y); ctx.rotate(a); ctx.fillStyle = cols[i % cols.length]; ctx.fillRect(-9, -5, 18 * Math.abs(Math.cos(a * 1.3)), 10); ctx.restore(); } ctx.restore(); }

// ---------------------------------------------------------------- 本物の写真
const IMG = {}; const imgReady = [];
function loadImages(keys) { for (const k of keys) { const im = new Image(); imgReady.push(new Promise(r => { im.onload = r; im.onerror = r; })); im.src = window.ASSETS[k]; IMG[k] = im; } }
// frame："glow"（青い細い縁、知的）・色（白い額縁、ドパ・悲劇）・null
function photo(ctx, im, k, z0, z1, u, { cx = .5, cy = .45, box = [90, 330, 990, 1290], gray = 1, rot = 0, sepia = 0, frame = "glow", bright = .95 } = {}) {
  if (k <= 0 || !im || !im.width) return; const [x0, y0, x1, y1] = box, bw = x1 - x0, bh = y1 - y0, z = lerp(z0, z1, u), sc = Math.max(bw / im.width, bh / im.height) * z, dw = im.width * sc, dh = im.height * sc;
  ctx.save(); ctx.globalAlpha *= clamp(k); ctx.translate((x0 + x1) / 2, (y0 + y1) / 2); ctx.rotate(rot); ctx.translate(-(x0 + x1) / 2, -(y0 + y1) / 2);
  if (frame && frame !== "glow") { ctx.fillStyle = frame; ctx.fillRect(x0 - 14, y0 - 14, bw + 28, bh + 28); }
  ctx.save(); rrect(ctx, x0, y0, bw, bh, frame === "glow" ? 10 : 4); ctx.clip();
  ctx.filter = `grayscale(${gray}) sepia(${sepia}) contrast(1.08) brightness(${bright})`; ctx.drawImage(im, x0 + bw / 2 - dw * cx, y0 + bh / 2 - dh * cy, dw, dh); ctx.filter = "none";
  const g = ctx.createRadialGradient((x0 + x1) / 2, (y0 + y1) / 2, Math.min(bw, bh) * .38, (x0 + x1) / 2, (y0 + y1) / 2, Math.max(bw, bh) * .78); g.addColorStop(0, "rgba(0,0,0,0)"); g.addColorStop(1, "rgba(2,6,12,.6)");
  ctx.fillStyle = g; ctx.fillRect(x0, y0, bw, bh); ctx.restore();
  if (frame === "glow") { ctx.strokeStyle = "rgba(143,220,255,.45)"; ctx.lineWidth = 2; rrect(ctx, x0, y0, bw, bh, 10); ctx.stroke(); }
  ctx.restore();
}
function photoGlow(t, t0, box) {   // 本物の写真に、やわらかい光と小さな粒を重ねる
  const k = easeOut(prog(t, t0, .8)); if (k <= 0) return; const [x0, y0, x1, y1] = box; bg.save(); bg.globalCompositeOperation = "screen";
  const g = bg.createLinearGradient(x0, y0, x0 + (x1 - x0) * .7, y1); g.addColorStop(0, `rgba(160,210,255,${.12 * k})`); g.addColorStop(1, "rgba(160,210,255,0)"); bg.fillStyle = g; bg.fillRect(x0, y0, x1 - x0, y1 - y0);
  const r = S.rng(23); for (let i = 0; i < 90; i++) { const x = x0 + r() * (x1 - x0), y = y0 + (((r() * (y1 - y0) - t * 20 * (.5 + r())) % (y1 - y0)) + (y1 - y0)) % (y1 - y0); bg.fillStyle = `rgba(220,240,255,${.3 * k * r()})`; bg.fillRect(x, y, 2, 2); }
  bg.restore();
}

// ---------------------------------------------------------------- 3D の土台（pilot_017・023 と同じ）
const SS = 1.5, GW = W * SS, GH = H * SS;
const glc = document.createElement("canvas"); glc.width = GW; glc.height = GH;
const R = new THREE.WebGLRenderer({ canvas: glc, antialias: true, alpha: false, preserveDrawingBuffer: true });
R.setPixelRatio(1); R.setSize(GW, GH, false); R.outputEncoding = THREE.sRGBEncoding; R.toneMapping = THREE.ACESFilmicToneMapping; R.toneMappingExposure = 1.0;
R.shadowMap.enabled = true; R.shadowMap.type = THREE.PCFSoftShadowMap; R.shadowMap.autoUpdate = false;
Cine.init(THREE, R);
const scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(40, W / H, .02, 300);
const C = c => new THREE.Color(c).convertSRGBToLinear();
let FOGC = C(0x05070b); scene.fog = new THREE.FogExp2(FOGC, .02);
const hemi = new THREE.HemisphereLight(C(0x8ea2bd), C(0x1a1612), .3); scene.add(hemi);
const key = new THREE.SpotLight(C(0xffd9a8), 2, 0, .7, .55, 1); key.castShadow = true; scene.add(key); scene.add(key.target);
key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -.0003; key.shadow.normalBias = .01; key.shadow.camera.near = .2; key.shadow.camera.far = 60;
const rim = new THREE.DirectionalLight(C(0x9fd4ff), .6); scene.add(rim); scene.add(rim.target);
const sets = {}; function set(n) { const g = new THREE.Group(); g.visible = false; scene.add(g); sets[n] = g; return g; }
function show(...n) { for (const k in sets) sets[k].visible = n.includes(k); }
function setCam(pos, look, fov = 40, near = .02, far = 300) { cam.position.copy(pos); cam.fov = fov; cam.near = near; cam.far = far; cam.lookAt(look); cam.updateProjectionMatrix(); cam.updateMatrixWorld(); }
function lights({ hemiI = .3, keyI = 30, keyPos = [0, 5, 0], keyAt = [0, 0, 0], keyCol = 0xffd9a8, angle = .7, rimI = .6, rimCol = 0x9fd4ff, rimPos = [3, 4, -4], fog = .02, fogC = 0x05070b, exp = 1.0, hemiSky = 0x8ea2bd, hemiGround = 0x1a1612 } = {}) {
  hemi.intensity = hemiI; hemi.color = C(hemiSky); hemi.groundColor = C(hemiGround); key.intensity = keyI * .085; key.color = C(keyCol); key.angle = angle;
  key.position.set(...keyPos); key.target.position.set(...keyAt); key.target.updateMatrixWorld(); rim.intensity = rimI; rim.color = C(rimCol); rim.position.set(...rimPos);
  FOGC = C(fogC); scene.fog.color = FOGC; scene.fog.density = fog; OUT.uniforms.exposure.value = exp;
}
const OUT = new THREE.ShaderPass({   // 仕上げ：ACES の色調と sRGB
  uniforms: { tDiffuse: { value: null }, exposure: { value: 1.0 } },
  vertexShader: "varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
  fragmentShader: `uniform sampler2D tDiffuse; uniform float exposure; varying vec2 vUv;
    vec3 rvFit(vec3 v){ vec3 a = v * (v + 0.0245786) - 0.000090537; vec3 b = v * (0.983729 * v + 0.4329510) + 0.238081; return a / b; }
    vec3 rvAces(vec3 c){ const mat3 I = mat3(vec3(0.59719,0.07600,0.02840), vec3(0.35458,0.90834,0.13383), vec3(0.04823,0.01566,0.83777));
      const mat3 O = mat3(vec3(1.60475,-0.10208,-0.00327), vec3(-0.53108,1.10813,-0.07276), vec3(-0.07367,-0.00605,1.07602));
      c *= exposure / 0.6; c = I * c; c = rvFit(c); c = O * c; return clamp(c, 0.0, 1.0); }
    vec3 rvSRGB(vec3 c){ return mix(pow(c, vec3(0.41666)) * 1.055 - vec3(0.055), c * 12.92, vec3(lessThanEqual(c, vec3(0.0031308)))); }
    void main(){ vec4 c = texture2D(tDiffuse, vUv); gl_FragColor = vec4(rvSRGB(rvAces(c.rgb)), 1.0); }` });
const composer = new THREE.EffectComposer(R); composer.setPixelRatio(1); composer.setSize(GW, GH);
const rpass = new THREE.RenderPass(scene, cam);
const ssao = new THREE.SSAOPass(scene, cam, GW, GH); ssao.kernelRadius = .22; ssao.minDistance = .0004; ssao.maxDistance = .02;
{ const ro = ssao.renderOverride.bind(ssao); ssao.renderOverride = (...a) => { const hid = []; scene.traverse(o => { if (o.visible && (o.isPoints || o.userData.noAO)) { o.visible = false; hid.push(o); } }); ro(...a); hid.forEach(o => o.visible = true); }; }
const bokeh = new THREE.BokehPass(scene, cam, { focus: 1, aperture: .002, maxblur: .008, width: GW, height: GH });
composer.addPass(rpass); composer.addPass(ssao); composer.addPass(bokeh); composer.addPass(OUT);
function draw3D({ ao = true, dof = null } = {}) {   // dof＝{ focus：焦点までの距離（m）, aperture, maxblur }
  camFX(NOW); R.shadowMap.needsUpdate = true; R.setClearColor(FOGC, 1);
  rpass.enabled = !ao; ssao.enabled = ao; bokeh.enabled = !!dof;
  if (dof) { bokeh.uniforms.focus.value = dof.focus; bokeh.uniforms.aperture.value = dof.aperture ?? .002; bokeh.uniforms.maxblur.value = dof.maxblur ?? .008; bokeh.uniforms.nearClip.value = cam.near; bokeh.uniforms.farClip.value = cam.far; bokeh.uniforms.aspect.value = cam.aspect; }
  composer.render(); bg.imageSmoothingQuality = "high"; bg.drawImage(glc, 0, 0, W, H);
}
const M = (c, o = {}) => new THREE.MeshStandardMaterial({ color: C(c), roughness: .7, metalness: 0, ...o });
function box(w, h, d, mat, x = 0, y = 0, z = 0, parent) { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); m.position.set(x, y, z); m.castShadow = m.receiveShadow = true; if (parent) parent.add(m); return m; }
function cyl(r0, r1, h, mat, x = 0, y = 0, z = 0, parent, seg = 32) { const m = new THREE.Mesh(new THREE.CylinderGeometry(r0, r1, h, seg), mat); m.position.set(x, y, z); m.castShadow = m.receiveShadow = true; if (parent) parent.add(m); return m; }
function sph(r, mat, x = 0, y = 0, z = 0, parent, seg = 32) { const m = new THREE.Mesh(new THREE.SphereGeometry(r, seg, Math.max(8, seg / 2)), mat); m.position.set(x, y, z); m.castShadow = m.receiveShadow = true; if (parent) parent.add(m); return m; }
const TEX = {}; const texLoader = new THREE.TextureLoader();
function pbr(name, rep, o = {}) {   // Poly Haven の質感（色・凹凸・粗さ）
  const t = k => { const key_ = name + "_" + k, tx = TEX[key_] || (TEX[key_] = texLoader.load(window.ASSETS3D.tex[key_])); tx.wrapS = tx.wrapT = THREE.RepeatWrapping; tx.anisotropy = 16; return tx; };
  const map = t("Diffuse").clone(), nm = t("nor_gl").clone(), rm = t("Rough").clone(); map.encoding = THREE.sRGBEncoding;
  for (const x of [map, nm, rm]) { x.repeat.set(...rep); x.needsUpdate = true; }
  return new THREE.MeshStandardMaterial({ map, normalMap: nm, roughnessMap: rm, roughness: 1, normalScale: new THREE.Vector2(o.normal ?? 1, o.normal ?? 1), color: C(o.tint ?? 0xffffff), envMapIntensity: o.env ?? .6 });
}
let ENV_ROOM = null;
function loadEnv() {
  const d = new THREE.RGBELoader().parse(b64buf(window.ASSETS3D.hdr));
  const tx = new THREE.DataTexture(d.data, d.width, d.height, THREE.RGBAFormat, d.type); tx.flipY = true; tx.minFilter = tx.magFilter = THREE.LinearFilter; tx.generateMipmaps = false; tx.mapping = THREE.EquirectangularReflectionMapping; tx.needsUpdate = true;
  const pm = new THREE.PMREMGenerator(R); ENV_ROOM = pm.fromEquirectangular(tx).texture; pm.dispose();
}
function envOn(k = .7) { scene.environment = ENV_ROOM; scene.traverse(o => { if (o.isMesh) for (const m of [].concat(o.material)) if (m && "envMapIntensity" in m) m.envMapIntensity = k; }); }
// 人体（MPFB の GLB：man_stand・man_sit・man_walk・man_haulA/B・man2_*。後ろ姿で使う。顔は描かない）
const HUMANS = {};
function loadHumans() { const L = new THREE.GLTFLoader(); return Promise.all(Object.entries(window.ASSETS3D.glb).map(([k, s]) => new Promise(res => L.parse(b64buf(s), "", g => { HUMANS[k] = g.scene; res(); }, e => { console.error(e); res(); })))); }
function human(kindKey, { coat = 0x2a2a30, hair = 0x3a2a20, skin = 0xc9a08a } = {}) {
  const g = new THREE.Group(), body = HUMANS[kindKey].clone(true);
  const coatM = M(coat, { roughness: .85 }), hairM = M(hair, { roughness: .5 }); hairM.color.multiplyScalar(.55); Cine.surface(coatM, "fabric", { repeat: [8, 8], normal: .7 }); Cine.surface(hairM, "wood", { repeat: [1, 6], normal: .9, roughness: 1 });
  const bb = new THREE.Box3(); let bodyMesh = null;
  body.traverse(o => { if (!o.isMesh) return; o.castShadow = o.receiveShadow = true; const n = o.name.toLowerCase();
    if (/short|hair/.test(n)) o.material = hairM; else if (/suit/.test(n)) o.material = coatM; else if (/shoe/.test(n)) o.material = M(0x141010, { roughness: .4 });
    else { o.material = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: .8 }); Cine.surface(o.material, "fabric", { repeat: [8, 8], normal: .5 }); bodyMesh = o; } });
  bb.setFromObject(body); body.position.y = -bb.min.y; g.add(body);
  let hb0 = null; body.traverse(o => { if (o.isMesh && o.material === hairM) hb0 = new THREE.Box3().setFromObject(o); });
  if (bodyMesh && hb0) { const P = bodyMesh.geometry.attributes.position, col = new Float32Array(P.count * 3), cs = C(skin), cc = C(coat), hc = new THREE.Vector3(); hb0.getCenter(hc); hc.y = hb0.max.y - .11;
    for (let i = 0; i < P.count; i++) { const d = Math.hypot(P.getX(i) - hc.x, (P.getY(i) - hc.y) * .8, P.getZ(i) - hc.z), k = clamp((.135 - d) / .02) * clamp((P.getY(i) - (hc.y - .16)) / .02); const cl = cc.clone().lerp(cs, k); col.set([cl.r, cl.g, cl.b], i * 3); }
    bodyMesh.geometry.setAttribute("color", new THREE.BufferAttribute(col, 3)); }
  return g;
}
// オープニングなどの背景：漂う光の粒
const drift = set("drift"); const floaters = [];
{ for (let i = 0; i < 120; i++) { const r = S.rng(500 + i), warm = r() > .55, m = new THREE.MeshStandardMaterial({ color: C(warm ? 0xffc880 : 0x8fcfff), emissive: C(warm ? 0x9a5a18 : 0x1a5a8a), emissiveIntensity: 1.2, roughness: .3 });
    const b = new THREE.Mesh(new THREE.SphereGeometry(.03 + r() * .07, 16, 10), m); b.position.set((r() - .5) * 9, (r() - .5) * 15, -2 - r() * 10); b.userData = { y0: b.position.y, sp: .1 + r() * .3 }; drift.add(b); floaters.push(b); } }
function driftShot(t, { warm = 0xffe0c0, exp = .9 } = {}) { show("drift"); scene.environment = null; floaters.forEach(b => { b.position.y = b.userData.y0 + t * b.userData.sp; });
  lights({ keyPos: [3, 5, 6], keyAt: [0, 0, -5], keyI: 10, angle: .8, keyCol: warm, rimPos: [-3, 2, -8], rimI: .6, rimCol: 0x8fdcff, hemiI: .2, hemiSky: 0x3a4a6a, hemiGround: 0x0a0a1a, fog: .06, fogC: 0x060812, exp });
  setCam(V3(Math.sin(t * .2) * .5, Math.cos(t * .15) * .3, 4), V3(0, 0, -6), 44, .05, 100); draw3D({ ao: false, dof: { focus: 6, aperture: .006, maxblur: .012 } }); }
// 2D の図を 3D のホログラムの台に置く（holoX に描いてから holoDraw）
const holoC = document.createElement("canvas"); holoC.width = W; holoC.height = H; const holoX = holoC.getContext("2d");
const holoTex = new THREE.CanvasTexture(holoC); holoTex.encoding = THREE.sRGBEncoding; holoTex.anisotropy = 16;
const holo = set("holo"); const holoEdgeM = new THREE.LineBasicMaterial({ color: C(0x8fdcff), transparent: true, opacity: .8 });
{ holo.add(new THREE.Mesh(new THREE.PlaneGeometry(10.8, 19.2), new THREE.MeshBasicMaterial({ map: holoTex, toneMapped: false, transparent: true })));
  holo.add(new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.PlaneGeometry(10.95, 19.35)), holoEdgeM));
  const grid = new THREE.GridHelper(120, 120, 0x2a7aa0, 0x10304a); grid.position.y = -12; holo.add(grid);
  const hd = Cine.dust({ min: [-10, -12, -8], max: [10, 12, 8], count: 1400, size: .05, seed: 71 }); holo.add(hd.points); holo.userData.dust = hd; }
function holoDraw(t, { tilt = -.18, yaw = 0, dist = 23, edge = 0x8fdcff, fogC = 0x02060c } = {}) {
  holoTex.needsUpdate = true; show("holo"); scene.environment = null; holo.children[0].rotation.set(tilt, yaw, 0); holo.children[1].rotation.set(tilt, yaw, 0); holo.userData.dust.update(t, 1); holoEdgeM.color = C(edge);
  lights({ keyI: 0, rimI: 0, hemiI: .3, fog: .006, fogC, exp: 1.0 }); setCam(V3(0, -1.0, dist), V3(0, -.5, 0), 40); draw3D({ ao: false });
}
function holoClear() { holoX.setTransform(1, 0, 0, 1, 0, 0); holoX.clearRect(0, 0, W, H); }
function panel(ctx, y0 = 330, y1 = 1280) { ctx.fillStyle = "rgba(4,14,26,.82)"; rrect(ctx, 90, y0, 900, y1 - y0, 18); ctx.fill(); ctx.strokeStyle = "rgba(143,220,255,.35)"; ctx.lineWidth = 2; ctx.stroke(); }
function lab2(ctx, s, x, y, size, col = "#B8DFF2", w = 800) { S.group(() => text(ctx, s, x, y, size, col, { weight: w, stroke: "#04101c", sw: 6 })); }

// ---------------------------------------------------------------- 画面の一打・粒子・色
const tmpC = document.createElement("canvas"); tmpC.width = W; tmpC.height = H; const tmpX = tmpC.getContext("2d");
function punch(ctx, z, sx = 0, sy = 0) { if (z <= 1.001 && !sx && !sy) return; tmpX.clearRect(0, 0, W, H); tmpX.drawImage(ctx.canvas, 0, 0); ctx.clearRect(0, 0, W, H);
  ctx.save(); ctx.translate(W / 2 + sx, H / 2 + sy); ctx.scale(z, z); ctx.drawImage(tmpC, -W / 2, -H / 2); ctx.restore(); }
let HITS = [];   // [時刻, 強さ]
function hitAmt(t) { let z = 0, s = 0; const fade = 1 - .6 * darkK(t); for (const [t0, k] of HITS) { const u = t - t0; if (u >= 0 && u < .45) { const e = Math.exp(-u * 9); z += .09 * k * e * fade; s += 26 * k * e * fade; } } return [1 + z, s]; }
function darkK(t) { if (!TL || !KIT.darkFrom || CUE[KIT.darkFrom] === undefined) return 0; return clamp((t - CUE[KIT.darkFrom]) / (TL.ending_start - CUE[KIT.darkFrom])); }
const grain = (() => { const c = document.createElement("canvas"); c.width = c.height = 256; const x = c.getContext("2d"), d = x.createImageData(256, 256), r = S.rng(99);
  for (let i = 0; i < d.data.length; i += 4) { const v = r() * 255; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 15; } x.putImageData(d, 0, 0); return c; })();
function addGrain(t) { const ox = Math.floor(S.rng(Math.floor(t * 30) + 7)() * 256), oy = Math.floor(S.rng(Math.floor(t * 30) + 91)() * 256);
  bg.save(); bg.globalCompositeOperation = "overlay"; bg.globalAlpha = .5; bg.fillStyle = bg.createPattern(grain, "repeat"); bg.translate(-ox, -oy); bg.fillRect(ox, oy, W, H); bg.restore(); }

// ---------------------------------------------------------------- 1 コマの描画（設計ごとの違いはここで）
function renderFrame(t) {
  NOW = t; bg.clearRect(0, 0, W, H); ui.clearRect(0, 0, W, H);
  const D = KIT.design, es = TL.ending_start, name = S.sceneAt(Math.min(t, es - .001));
  const kind = drawScene(t, name); if (kind === "2d") draw2D(Math.min(t, es - .001), name);
  if (name === "open" && typeof openingBG === "function") openingBG(t);
  S.moodGrade(bg, t, MOOD); Cine.bloom(bg, (D === "intel" ? .28 : .34) * (1 - .5 * darkK(t)));
  { const [z, s] = hitAmt(t), r = S.rng(Math.floor(t * 30) + 11); punch(bg, z, (r() - .5) * s, (r() - .5) * s); }
  if (D === "dopa") { const P = ciPhase(t); if (P) { const a = P.p ? CUT[P.p - 1] : 0; if (P.d - a < .1) S.glitch(bg, t, 8 * (1 - (P.d - a) / .1), 3); } }   // ドパ：カットインの切れ目で一瞬乱れる
  if (typeof fxEp === "function") fxEp(t, name);
  addGrain(t);
  if (D === "tragedy" && name !== "open") { const dk = darkK(t); bg.fillStyle = `rgba(0,6,14,${.32 + .22 * Math.pow(dk, 1.2)})`; bg.fillRect(0, 0, W, H); }   // 悲劇：最初から暗く張り詰めた画面、終盤ほどさらに暗く（2026-11-01〜）
  if (t < es) { drawUI(t, name); if (name !== "open") { if (D === "intel") S.docSub(ui, t, { endAt: es }); else popSub(ui, t, es); } }
  else if (D === "tragedy" || TL.no_ending) { const k = easeInOut(clamp((t - es) / Math.max(.1, (TL.blackout || .25) - .3))); bg.fillStyle = `rgba(0,0,0,${k})`; bg.fillRect(0, 0, W, H); }   // 共通エンディングなし：時間をかけて暗転
  else { const e = TL.lines.filter(x => x.ending), cr = TL.credits.join("／").split("／"), two = cr.length > 2;   // 声が 3 人以上なら、クレジットを 2 行に分けて描く（pilot_019 と同じ）
    HUD.endingOverlay(ui, t - es, { end1: e[0].start - es, end2: e[1].start - es, credits: two ? [] : TL.credits });
    if (two) { const k = clamp((t - es) / .4); ui.save(); ui.globalAlpha = k * .9; S.group(() => { text(ui, "音声：" + cr.slice(0, 2).join("／").replace(/^音声：/, ""), 540, 1150, 28, "#B8C7D6", { weight: 500 }); text(ui, cr.slice(2).join("／"), 540, 1192, 28, "#B8C7D6", { weight: 500 }); }); ui.restore(); } }
  const [a] = S.sceneRange(name), i = SCN.indexOf(name);
  if (i > 0 && t < es && !ciPhase(t)) { const d = D === "intel" ? .25 : .14, k = 1 - prog(t, a, d); if (k > 0) { bg.fillStyle = `rgba(4,8,14,${(D === "intel" ? .85 : .75) * k})`; bg.fillRect(0, 0, W, H); } }   // 場面の切り替え（閃光なし）
  bg.getImageData(0, 0, 1, 1); ui.getImageData(0, 0, 1, 1);
}
function setTimeline(tl) {
  TL = tl; SCN = KIT.scenes; S.setup(tl, SCN); CUE = S.CUE; buildMood();
  HITS = KIT.hits.filter(([c]) => CUE[c] !== undefined).map(([c, k, off = 0]) => [CUE[c] + off, k]);
  if (KIT.design === "dopa") for (const c in KIT.ci) if (CUE[c] !== undefined) KIT.ci[c].forEach((_, p) => HITS.push([CUE[c] + (p ? CUT[p - 1] : 0), 1.5]));   // ドパ：カットインの切れ目ごとに一打
}
function kitStart(build) {
  window.READY = Promise.all([...imgReady, fontReady, loadHumans()]).then(() => { loadEnv(); build(); });
  window.renderFrame = renderFrame; window.setTimeline = setTimeline; window.renderThumb = () => { bg.clearRect(0, 0, W, H); ui.clearRect(0, 0, W, H); NOW = 0; thumb(); bg.getImageData(0, 0, 1, 1); ui.getImageData(0, 0, 1, 1); };
}
