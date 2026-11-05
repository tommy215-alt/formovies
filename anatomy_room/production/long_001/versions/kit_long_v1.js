// long_001 の描画の部品（長い動画・横長 1920×1080）。2D の図・ピクトグラム・アイコン・矢印・字幕、3D の問いかけの場面（three.js）。
// ユーザーの指示（2026-11-05）：ピクトグラム・矢印・アイコンを多めに、なめらかに動かし、画面の動きにメリハリを付ける。
// すべて時刻 t だけで決まる（前のコマの状態を使わない）。renderer.html が場面を組み立てる。
"use strict";
const W = 1920, H = 1080;
const FONT = '"Noto Sans CJK JP", sans-serif';
const C = {
  bg0: "#0a1220", bg1: "#122238", grid: "rgba(120,170,230,0.07)", ink: "#eaf2ff", dim: "#8fa3bf", mute: "#4a5d78",
  cyan: "#4fd1ff", amber: "#ffb648", red: "#ff5a6a", green: "#58e0a0", violet: "#a98bff", pink: "#ff8fc7", panel: "rgba(20,36,60,0.86)", line: "rgba(140,190,255,0.35)",
};

// ---------------------------------------------------------------- 時間と動き
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, k) => a + (b - a) * k;
const ease = {
  out: k => 1 - Math.pow(1 - clamp(k), 3),
  inOut: k => { k = clamp(k); return k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2; },
  back: k => { k = clamp(k); const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(k - 1, 3) + c1 * Math.pow(k - 1, 2); },
  pop: k => { k = clamp(k); return k >= 1 ? 1 : 1 - Math.exp(-6 * k) * Math.cos(10 * k); },   // 跳ねて止まる
};
let TL = null, LN = {}, NOW = 0;
// 行の開始・終了の時刻。frac で行の途中（0〜1）
const S = (id, frac = 0) => { const x = LN[id]; if (!x) throw new Error("no line " + id); return x.start + frac * (x.end - x.start); };
const E = id => LN[id].end;
// t が a から d 秒かけて 0→1（イージングつき）
const pr = (t, a, d = .6, f = ease.out) => f((t - a) / d);
const win = (t, a, b, fi = .4, fo = .4) => clamp(Math.min((t - a) / fi, (b - t) / fo));   // 表示の窓（フェード）

// ---------------------------------------------------------------- 2D の土台
const cv = document.getElementById("ui"), g = cv.getContext("2d");
const TEXTLOG = [];
function txt(s, x, y, size = 48, color = C.ink, align = "center", weight = 700, alpha = 1, maxW = 0) {
  if (alpha <= 0.01 || !s) return;
  g.save(); g.globalAlpha *= alpha; g.font = `${weight} ${size}px ${FONT}`; g.textAlign = align; g.textBaseline = "middle"; g.fillStyle = color;
  let w = g.measureText(s).width;
  if (maxW && w > maxW) { g.font = `${weight} ${size * maxW / w}px ${FONT}`; w = maxW; }
  g.fillText(s, x, y);
  const m = g.getTransform();
  const x0 = align === "center" ? x - w / 2 : align === "right" ? x - w : x;
  TEXTLOG.push({ s, x0: m.a * x0 + m.e, x1: m.a * (x0 + w) + m.e, y0: m.d * (y - size / 2) + m.f, y1: m.d * (y + size / 2) + m.f, a: g.globalAlpha });
  g.restore();
}
function rr(x, y, w, h, r) { g.beginPath(); g.roundRect(x, y, w, h, r); }
function panel(x, y, w, h, a = 1, stroke = C.line, fill = C.panel, r = 22) {
  if (a <= .01) return;
  g.save(); g.globalAlpha *= a; g.shadowColor = "rgba(0,0,0,0.45)"; g.shadowBlur = 30; g.shadowOffsetY = 10;
  rr(x, y, w, h, r); g.fillStyle = fill; g.fill(); g.shadowColor = "transparent"; g.lineWidth = 2; g.strokeStyle = stroke; g.stroke(); g.restore();
}
// 拡大・回転・不透明度をまとめて、(x, y) を中心に描く
function at(x, y, s, a, fn, rot = 0) {
  if (a <= .01 || s <= .001) return;
  g.save(); g.translate(x, y); if (rot) g.rotate(rot); g.scale(s, s); g.globalAlpha *= a; fn(); g.restore();
}
function glow(color, blur = 24) { g.shadowColor = color; g.shadowBlur = blur; }

// 背景：暗い青のグラデーション＋うっすらした格子＋漂う光の粒（場面の色 hue で少し変える）
function background(t, tint = C.bg1, gridA = 1) {
  const gr = g.createRadialGradient(W * .5, H * .42, 80, W * .5, H * .5, W * .75);
  gr.addColorStop(0, tint); gr.addColorStop(1, C.bg0);
  g.fillStyle = gr; g.fillRect(0, 0, W, H);
  g.save(); g.globalAlpha = gridA; g.strokeStyle = C.grid; g.lineWidth = 1;
  const off = (t * 6) % 80;
  for (let x = -off; x < W; x += 80) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, H); g.stroke(); }
  for (let y = -off * .5; y < H; y += 80) { g.beginPath(); g.moveTo(0, y); g.lineTo(W, y); g.stroke(); }
  g.restore();
  for (let i = 0; i < 46; i++) {
    const r1 = hash(i * 3.1), r2 = hash(i * 7.7), r3 = hash(i * 1.9);
    const x = (r1 * W + t * (8 + r3 * 18)) % (W + 40) - 20, y = (r2 * H - t * (4 + r1 * 10) + H * 10) % H;
    g.fillStyle = `rgba(150,200,255,${.05 + .12 * r3 * (.6 + .4 * Math.sin(t * 1.3 + i))})`;
    g.beginPath(); g.arc(x, y, 1.5 + r3 * 2.5, 0, 7); g.fill();
  }
  const vg = g.createRadialGradient(W / 2, H / 2, H * .45, W / 2, H / 2, W * .72);
  vg.addColorStop(0, "rgba(0,0,0,0)"); vg.addColorStop(1, "rgba(0,0,0,0.55)");
  g.fillStyle = vg; g.fillRect(0, 0, W, H);
}
function hash(n) { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); }

// ---------------------------------------------------------------- ピクトグラム（顔のない人型）
// pose: "stand" | "up"（両手を上）| "power"（胸を張る・腰に手）| "point"（右を指す）| "think"（あごに手）| "sit" | "walk"
function picto(x, y, s, color = C.ink, pose = "stand", t = 0, a = 1) {
  at(x, y, s, a, () => {
    g.fillStyle = color; g.strokeStyle = color; g.lineCap = "round"; g.lineJoin = "round";
    const sw = Math.sin(t * 6) * (pose === "walk" ? 1 : 0);
    g.beginPath(); g.arc(0, -78, 17, 0, 7); g.fill();                         // 頭
    rr(-20, -56, 40, 58, 16); g.fill();                                      // 胴
    g.lineWidth = 14;
    const arm = (sx, ex, ey, mx = null, my = null) => { g.beginPath(); g.moveTo(sx, -48); if (mx !== null) g.lineTo(mx, my); g.lineTo(ex, ey); g.stroke(); };
    if (pose === "up") { arm(-16, -40, -112, -30, -80); arm(16, 40, -112, 30, -80); }
    else if (pose === "power") { arm(-16, -26, -2, -44, -24); arm(16, 26, -2, 44, -24); }
    else if (pose === "point") { arm(-16, -30, 0); arm(16, 70, -52, 40, -50); }
    else if (pose === "think") { arm(-16, -30, 0); arm(16, 6, -66, 34, -30); }
    else { arm(-16, -30 - sw * 8, 0); arm(16, 30 + sw * 8, 0); }
    g.lineWidth = 15;
    if (pose === "sit") { g.beginPath(); g.moveTo(-10, 0); g.lineTo(-10, 18); g.lineTo(-34, 22); g.stroke(); g.beginPath(); g.moveTo(10, 0); g.lineTo(10, 18); g.lineTo(34, 22); g.stroke(); }
    else if (pose === "power") { g.beginPath(); g.moveTo(-10, 0); g.lineTo(-26, 56); g.stroke(); g.beginPath(); g.moveTo(10, 0); g.lineTo(26, 56); g.stroke(); }
    else { g.beginPath(); g.moveTo(-10, 0); g.lineTo(-12 - sw * 10, 56); g.stroke(); g.beginPath(); g.moveTo(10, 0); g.lineTo(12 + sw * 10, 56); g.stroke(); }
  });
}
// 子ども（小さく、頭が大きめ）
function child(x, y, s, color, a = 1) { at(x, y, s, a, () => { picto(0, 0, .72, color); g.fillStyle = color; g.beginPath(); g.arc(0, -60, 15, 0, 7); g.fill(); }); }

// ---------------------------------------------------------------- アイコン（線画、中心 0,0、大きさ 100 前後）
const ICON = {
  eye(c) { g.lineWidth = 7; g.strokeStyle = c; g.beginPath(); g.moveTo(-50, 0); g.quadraticCurveTo(0, -42, 50, 0); g.quadraticCurveTo(0, 42, -50, 0); g.stroke(); g.fillStyle = c; g.beginPath(); g.arc(0, 0, 15, 0, 7); g.fill(); },
  note(c) { g.fillStyle = c; g.strokeStyle = c; g.lineWidth = 8; g.beginPath(); g.ellipse(-22, 30, 16, 12, -.4, 0, 7); g.fill(); g.beginPath(); g.ellipse(26, 20, 16, 12, -.4, 0, 7); g.fill(); g.beginPath(); g.moveTo(-8, 28); g.lineTo(-8, -40); g.lineTo(40, -52); g.lineTo(40, 18); g.stroke(); },
  brain(c) {
    g.strokeStyle = c; g.lineWidth = 7; g.beginPath();
    g.moveTo(0, -44); g.bezierCurveTo(-30, -60, -62, -36, -52, -8); g.bezierCurveTo(-70, 10, -52, 44, -22, 40); g.bezierCurveTo(-10, 52, 0, 44, 0, 36);
    g.moveTo(0, -44); g.bezierCurveTo(30, -60, 62, -36, 52, -8); g.bezierCurveTo(70, 10, 52, 44, 22, 40); g.bezierCurveTo(10, 52, 0, 44, 0, 36); g.lineTo(0, -44);
    g.moveTo(-34, -14); g.quadraticCurveTo(-16, -6, -24, 12); g.moveTo(34, -14); g.quadraticCurveTo(16, -6, 24, 12); g.stroke();
  },
  film(c) { g.strokeStyle = c; g.lineWidth = 6; rr(-52, -36, 104, 72, 8); g.stroke(); g.fillStyle = c; for (let i = -40; i <= 40; i += 20) { g.fillRect(i - 5, -32, 10, 8); g.fillRect(i - 5, 24, 10, 8); } g.strokeRect(-30, -16, 60, 32); },
  bottle(c) { g.fillStyle = c; g.beginPath(); g.moveTo(-8, -56); g.lineTo(8, -56); g.lineTo(8, -34); g.quadraticCurveTo(24, -20, 22, 10); g.lineTo(22, 50); g.quadraticCurveTo(0, 58, -22, 50); g.lineTo(-22, 10); g.quadraticCurveTo(-24, -20, -8, -34); g.closePath(); g.fill(); g.fillStyle = C.bg0; g.fillRect(-22, 4, 44, 14); },
  molecule(c) { g.strokeStyle = c; g.fillStyle = c; g.lineWidth = 6; const P = [[-36, -20], [0, -40], [36, -20], [36, 20], [0, 40], [-36, 20]]; g.beginPath(); P.forEach((p, i) => i ? g.lineTo(...p) : g.moveTo(...p)); g.closePath(); g.stroke(); P.forEach(p => { g.beginPath(); g.arc(p[0], p[1], 8, 0, 7); g.fill(); }); },
  marsh(c) { g.fillStyle = c; rr(-34, -26, 68, 52, 18); g.fill(); g.fillStyle = "rgba(0,0,0,0.15)"; rr(-34, 4, 68, 22, 12); g.fill(); },
  trophy(c) { g.fillStyle = c; g.strokeStyle = c; g.lineWidth = 7; g.beginPath(); g.moveTo(-30, -44); g.lineTo(30, -44); g.lineTo(26, -4); g.quadraticCurveTo(0, 18, -26, -4); g.closePath(); g.fill(); g.beginPath(); g.arc(-32, -26, 14, Math.PI * .5, Math.PI * 1.5); g.stroke(); g.beginPath(); g.arc(32, -26, 14, -Math.PI * .5, Math.PI * .5); g.stroke(); g.fillRect(-6, 10, 12, 22); g.fillRect(-24, 32, 48, 12); },
  paper(c, lines = 4) { g.fillStyle = c; g.beginPath(); g.moveTo(-36, -48); g.lineTo(18, -48); g.lineTo(36, -30); g.lineTo(36, 48); g.lineTo(-36, 48); g.closePath(); g.fill(); g.fillStyle = "rgba(10,18,32,0.45)"; for (let i = 0; i < lines; i++) g.fillRect(-24, -26 + i * 16, i === lines - 1 ? 30 : 48, 6); },
  magnifier(c) { g.strokeStyle = c; g.lineWidth = 9; g.beginPath(); g.arc(-10, -10, 32, 0, 7); g.stroke(); g.lineWidth = 13; g.lineCap = "round"; g.beginPath(); g.moveTo(14, 14); g.lineTo(44, 44); g.stroke(); },
  headphones(c) { g.strokeStyle = c; g.lineWidth = 9; g.beginPath(); g.arc(0, 4, 40, Math.PI, 0); g.stroke(); g.fillStyle = c; rr(-50, 2, 20, 38, 8); g.fill(); rr(30, 2, 20, 38, 8); g.fill(); },
  building(c) { g.fillStyle = c; g.beginPath(); g.moveTo(-54, -18); g.lineTo(0, -50); g.lineTo(54, -18); g.closePath(); g.fill(); g.fillRect(-48, 34, 96, 12); for (let i = -36; i <= 36; i += 24) g.fillRect(i - 6, -12, 12, 44); },
  news(c) { g.fillStyle = c; rr(-50, -40, 100, 80, 6); g.fill(); g.fillStyle = "rgba(10,18,32,0.6)"; g.fillRect(-40, -30, 80, 14); g.fillRect(-40, -8, 36, 34); for (let i = 0; i < 4; i++) g.fillRect(4, -8 + i * 10, 36, 5); },
  tv(c) { g.strokeStyle = c; g.lineWidth = 7; rr(-50, -34, 100, 66, 10); g.stroke(); g.beginPath(); g.moveTo(-20, 48); g.lineTo(20, 48); g.moveTo(0, 32); g.lineTo(0, 48); g.stroke(); g.fillStyle = c; g.beginPath(); g.moveTo(-8, -14); g.lineTo(14, 0); g.lineTo(-8, 14); g.fill(); },
  book(c) { g.fillStyle = c; g.beginPath(); g.moveTo(0, -30); g.quadraticCurveTo(-30, -44, -54, -34); g.lineTo(-54, 38); g.quadraticCurveTo(-30, 28, 0, 42); g.quadraticCurveTo(30, 28, 54, 38); g.lineTo(54, -34); g.quadraticCurveTo(30, -44, 0, -30); g.fill(); g.strokeStyle = C.bg0; g.lineWidth = 4; g.beginPath(); g.moveTo(0, -28); g.lineTo(0, 40); g.stroke(); },
  phone(c) { g.strokeStyle = c; g.lineWidth = 7; rr(-26, -48, 52, 96, 10); g.stroke(); g.fillStyle = c; g.beginPath(); g.arc(0, 36, 5, 0, 7); g.fill(); g.fillRect(-12, -30, 24, 5); g.fillRect(-12, -18, 24, 5); },
  drawer(c, open = 0) { g.fillStyle = c; rr(-60, -44, 120, 88, 8); g.fill(); g.fillStyle = "rgba(10,18,32,0.5)"; rr(-50 - open * 10, -30 + open * 20, 100 + open * 20, 54, 6); g.fill(); g.fillStyle = c; rr(-14 - open * 10, -6 + open * 20, 28, 8, 4); g.fill(); },
  globe(c) { g.strokeStyle = c; g.lineWidth = 6; g.beginPath(); g.arc(0, 0, 44, 0, 7); g.stroke(); g.beginPath(); g.ellipse(0, 0, 18, 44, 0, 0, 7); g.stroke(); g.beginPath(); g.moveTo(-44, 0); g.lineTo(44, 0); g.moveTo(-38, -22); g.lineTo(38, -22); g.moveTo(-38, 22); g.lineTo(38, 22); g.stroke(); },
  lock(c) { g.strokeStyle = c; g.lineWidth = 9; g.beginPath(); g.arc(0, -16, 24, Math.PI, 0); g.lineTo(24, 0); g.moveTo(-24, 0); g.lineTo(-24, -16); g.stroke(); g.fillStyle = c; rr(-36, -2, 72, 52, 10); g.fill(); g.fillStyle = C.bg0; g.beginPath(); g.arc(0, 20, 7, 0, 7); g.fill(); g.fillRect(-3, 22, 6, 14); },
  bulb(c) { g.fillStyle = c; g.beginPath(); g.arc(0, -12, 32, Math.PI * .8, Math.PI * .2); g.lineTo(14, 24); g.lineTo(-14, 24); g.closePath(); g.fill(); g.fillRect(-14, 28, 28, 7); g.fillRect(-10, 38, 20, 7); },
  baby(c) { g.fillStyle = c; g.beginPath(); g.arc(0, -26, 20, 0, 7); g.fill(); rr(-28, -2, 56, 46, 22); g.fill(); },
  cd(c) { g.fillStyle = c; g.beginPath(); g.arc(0, 0, 44, 0, 7); g.fill(); g.fillStyle = C.bg0; g.beginPath(); g.arc(0, 0, 10, 0, 7); g.fill(); g.strokeStyle = "rgba(10,18,32,0.35)"; g.lineWidth = 3; g.beginPath(); g.arc(0, 0, 28, -.6, .8); g.stroke(); },
  car(c) { g.fillStyle = c; g.beginPath(); g.moveTo(-56, 14); g.lineTo(-56, -4); g.lineTo(-34, -8); g.lineTo(-20, -30); g.lineTo(24, -30); g.lineTo(40, -8); g.lineTo(56, -2); g.lineTo(56, 14); g.closePath(); g.fill(); g.fillStyle = C.bg0; g.beginPath(); g.arc(-30, 16, 13, 0, 7); g.arc(30, 16, 13, 0, 7); g.fill(); g.fillStyle = c; g.beginPath(); g.arc(-30, 16, 7, 0, 7); g.arc(30, 16, 7, 0, 7); g.fill(); },
  pen(c) { g.save(); g.rotate(-.7); g.fillStyle = c; rr(-8, -50, 16, 80, 4); g.fill(); g.beginPath(); g.moveTo(-8, 30); g.lineTo(8, 30); g.lineTo(0, 48); g.fill(); g.restore(); },
  flask(c) { g.strokeStyle = c; g.lineWidth = 7; g.beginPath(); g.moveTo(-12, -46); g.lineTo(-12, -12); g.lineTo(-40, 40); g.lineTo(40, 40); g.lineTo(12, -12); g.lineTo(12, -46); g.stroke(); g.fillStyle = c; g.globalAlpha *= .6; g.beginPath(); g.moveTo(-26, 14); g.lineTo(26, 14); g.lineTo(38, 38); g.lineTo(-38, 38); g.fill(); },
  chart(c) { g.fillStyle = c; [[-40, 10, 22], [-12, -14, 46], [16, -34, 66]].forEach(([x, y, h]) => g.fillRect(x, y, 22, h + 2 - 34 + 34)); g.fillRect(-50, 36, 100, 6); },
  check(c) { g.strokeStyle = c; g.lineWidth = 14; g.lineCap = "round"; g.lineJoin = "round"; g.beginPath(); g.moveTo(-34, 2); g.lineTo(-10, 28); g.lineTo(38, -28); g.stroke(); },
  cross(c) { g.strokeStyle = c; g.lineWidth = 14; g.lineCap = "round"; g.beginPath(); g.moveTo(-30, -30); g.lineTo(30, 30); g.moveTo(30, -30); g.lineTo(-30, 30); g.stroke(); },
  question(c) { g.fillStyle = c; g.font = `900 110px ${FONT}`; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText("?", 0, 6); },
  speech(c) { g.fillStyle = c; rr(-52, -36, 104, 62, 18); g.fill(); g.beginPath(); g.moveTo(-20, 24); g.lineTo(-34, 46); g.lineTo(0, 24); g.fill(); },
  wave(c) { g.strokeStyle = c; g.lineWidth = 7; g.lineCap = "round"; for (let k = 0; k < 3; k++) { g.beginPath(); g.arc(-26, 0, 16 + k * 18, -.8, .8); g.stroke(); } g.fillStyle = c; rr(-50, -14, 18, 28, 4); g.fill(); },
  face(c) { g.strokeStyle = c; g.lineWidth = 7; g.beginPath(); g.arc(0, 0, 42, 0, 7); g.stroke(); },
  heart(c) { g.fillStyle = c; g.beginPath(); g.moveTo(0, 40); g.bezierCurveTo(-60, 0, -40, -46, 0, -20); g.bezierCurveTo(40, -46, 60, 0, 0, 40); g.fill(); },
  dice(c) { g.fillStyle = c; rr(-40, -40, 80, 80, 14); g.fill(); g.fillStyle = C.bg0; [[-18, -18], [18, 18], [0, 0], [18, -18], [-18, 18]].forEach(p => { g.beginPath(); g.arc(p[0], p[1], 7, 0, 7); g.fill(); }); },
  clock(c) { g.strokeStyle = c; g.lineWidth = 7; g.beginPath(); g.arc(0, 0, 42, 0, 7); g.stroke(); g.lineCap = "round"; g.beginPath(); g.moveTo(0, 0); g.lineTo(0, -26); g.moveTo(0, 0); g.lineTo(20, 10); g.stroke(); },
  cube(c) { g.strokeStyle = c; g.lineWidth = 6; g.lineJoin = "round"; g.beginPath(); g.moveTo(0, -46); g.lineTo(40, -24); g.lineTo(40, 24); g.lineTo(0, 46); g.lineTo(-40, 24); g.lineTo(-40, -24); g.closePath(); g.moveTo(0, -2); g.lineTo(40, -24); g.moveTo(0, -2); g.lineTo(-40, -24); g.moveTo(0, -2); g.lineTo(0, 46); g.stroke(); },
  odometer(c) { g.strokeStyle = c; g.lineWidth = 7; g.beginPath(); g.arc(0, 10, 44, Math.PI * 1.05, Math.PI * 1.95); g.stroke(); g.lineCap = "round"; g.beginPath(); g.moveTo(0, 10); g.lineTo(24, -18); g.stroke(); g.fillStyle = c; g.beginPath(); g.arc(0, 10, 7, 0, 7); g.fill(); },
  mask(c) { g.fillStyle = c; g.beginPath(); g.moveTo(-48, -30); g.quadraticCurveTo(0, -46, 48, -30); g.quadraticCurveTo(52, 30, 0, 44); g.quadraticCurveTo(-52, 30, -48, -30); g.fill(); g.fillStyle = C.bg0; g.beginPath(); g.ellipse(-20, -8, 11, 7, .2, 0, 7); g.ellipse(20, -8, 11, 7, -.2, 0, 7); g.fill(); g.strokeStyle = C.bg0; g.lineWidth = 5; g.beginPath(); g.arc(0, 30, 16, Math.PI * 1.15, Math.PI * 1.85); g.stroke(); },
  repeat(c) { g.strokeStyle = c; g.lineWidth = 8; g.beginPath(); g.arc(0, 0, 36, .3, Math.PI * 1.1); g.stroke(); g.beginPath(); g.arc(0, 0, 36, Math.PI * 1.3, Math.PI * 2.1); g.stroke(); g.fillStyle = c; tri(-36, 6, Math.PI * .5); tri(36, -6, -Math.PI * .5); },
  sieve(c) { g.strokeStyle = c; g.lineWidth = 7; g.beginPath(); g.moveTo(-50, -20); g.lineTo(50, -20); g.lineTo(30, 30); g.lineTo(-30, 30); g.closePath(); g.stroke(); for (let x = -30; x <= 30; x += 15) { g.beginPath(); g.moveTo(x, -10); g.lineTo(x * .7, 22); g.stroke(); } },
};
function tri(x, y, rot) { g.save(); g.translate(x, y); g.rotate(rot); g.beginPath(); g.moveTo(0, -14); g.lineTo(12, 6); g.lineTo(-12, 6); g.fill(); g.restore(); }
function icon(name, x, y, s, color = C.ink, a = 1, rot = 0, ...args) { at(x, y, s, a, () => ICON[name](color, ...args), rot); }

// 丸い台に乗せたアイコン（強調）
function badge(name, x, y, s, color, a = 1, ring = true) {
  at(x, y, s, a, () => {
    if (ring) { g.fillStyle = "rgba(15,28,48,0.9)"; g.beginPath(); g.arc(0, 0, 70, 0, 7); g.fill(); g.lineWidth = 4; g.strokeStyle = color; glow(color, 18); g.stroke(); g.shadowBlur = 0; }
    g.save(); g.scale(.8, .8); ICON[name](color); g.restore();
  });
}

// ---------------------------------------------------------------- 矢印
// p：伸びる進み（0〜1）。bend：曲がり（垂直方向のずれ px）
function arrow(x1, y1, x2, y2, p, color = C.cyan, w = 8, bend = 0, a = 1, dash = false) {
  if (p <= 0.01 || a <= .01) return;
  const mx = (x1 + x2) / 2 - (y2 - y1) * bend / Math.hypot(x2 - x1, y2 - y1 || 1), my = (y1 + y2) / 2 + (x2 - x1) * bend / Math.hypot(x2 - x1, y2 - y1 || 1);
  const pt = k => [(1 - k) * (1 - k) * x1 + 2 * (1 - k) * k * mx + k * k * x2, (1 - k) * (1 - k) * y1 + 2 * (1 - k) * k * my + k * k * y2];
  g.save(); g.globalAlpha *= a; g.strokeStyle = color; g.fillStyle = color; g.lineWidth = w; g.lineCap = "round"; glow(color, 12);
  if (dash) g.setLineDash([w * 1.6, w * 1.6]);
  g.beginPath(); const N = 30; for (let i = 0; i <= N * p; i++) { const q = pt(i / N); i ? g.lineTo(...q) : g.moveTo(...q); } const e = pt(p); g.lineTo(...e); g.stroke();
  g.setLineDash([]);
  const b = pt(Math.max(0, p - .02)), ang = Math.atan2(e[1] - b[1], e[0] - b[0]);
  g.translate(...e); g.rotate(ang); g.beginPath(); g.moveTo(w * 2.4, 0); g.lineTo(-w * 1.2, -w * 1.8); g.lineTo(-w * 1.2, w * 1.8); g.closePath(); g.fill();
  g.restore();
}

// ---------------------------------------------------------------- 札・カード・判子
function chip(s, x, y, color, a = 1, size = 34, fill = null) {
  if (a <= .01) return;
  g.save(); g.font = `800 ${size}px ${FONT}`; const w = g.measureText(s).width + size * 1.1; g.restore();
  panel(x - w / 2, y - size * .85, w, size * 1.7, a, color, fill || "rgba(14,26,44,0.92)", size * .85);
  txt(s, x, y + 1, size, color, "center", 800, a);
}
function stamp(s, x, y, p, color = C.red, size = 120, rot = -.18) {
  if (p <= 0) return;
  const k = ease.pop(p), sc = lerp(2.4, 1, Math.min(1, p * 3)), a = Math.min(1, p * 4);
  at(x, y, sc, a, () => {
    g.save(); g.font = `900 ${size}px ${FONT}`; const w = g.measureText(s).width + size * .7; g.restore();
    g.lineWidth = size * .08; g.strokeStyle = color; glow(color, 16); rr(-w / 2, -size * .7, w, size * 1.4, size * .18); g.stroke(); g.shadowBlur = 0;
    txt(s, 0, 4, size, color, "center", 900);
  }, rot * k);
}
// 数字の棒グラフ（縦）。v：0〜1、label は下、valueText は上
function vbar(x, yBase, w, hMax, v, color, label, valueText, a = 1) {
  if (a <= .01) return;
  g.save(); g.globalAlpha *= a;
  g.fillStyle = "rgba(255,255,255,0.06)"; rr(x - w / 2, yBase - hMax, w, hMax, 10); g.fill();
  const h = Math.max(4, hMax * v); g.fillStyle = color; glow(color, 18); rr(x - w / 2, yBase - h, w, h, 10); g.fill(); g.restore();
  txt(valueText, x, yBase - h - 40, 64, color, "center", 900, a);
  txt(label, x, yBase + 42, 34, C.ink, "center", 700, a);
}
// メーター（横）
function hbar(x, y, w, h, v, color, a = 1) {
  if (a <= .01) return;
  g.save(); g.globalAlpha *= a; g.fillStyle = "rgba(255,255,255,0.08)"; rr(x, y, w, h, h / 2); g.fill();
  g.fillStyle = color; glow(color, 14); rr(x, y, Math.max(h, w * clamp(v)), h, h / 2); g.fill(); g.restore();
}

// ---------------------------------------------------------------- 字幕（下）と章の表示（左上）
function subtitle(t) {
  const ln = TL.lines.find(x => !x.ending && t >= x.start - .05 && t < x.end + .25);
  if (!ln) return;
  const parts = ln.sub.split(" / "), tot = parts.reduce((s, p) => s + p.length, 0);
  let acc = 0, k = 0;
  const f = (t - ln.start) / (ln.end - ln.start);
  for (; k < parts.length - 1; k++) { acc += parts[k].length / tot; if (f < acc) break; }
  const s = parts[k];
  const a = clamp(Math.min((t - ln.start + .05) / .12, (ln.end + .25 - t) / .15));
  g.save(); g.font = `700 50px ${FONT}`; const w = Math.min(1700, g.measureText(s).width) + 80; g.restore();
  g.save(); g.globalAlpha = a * .78; g.fillStyle = "#060b14"; rr(W / 2 - w / 2, H - 132, w, 84, 16); g.fill(); g.restore();
  txt(s, W / 2, H - 89, 50, "#ffffff", "center", 700, a, 1660);
}
function chapterTag(s, color, a) {
  if (a <= .01) return;
  g.save(); g.globalAlpha *= a; g.fillStyle = color; rr(52, 46, 10, 44, 4); g.fill(); g.restore();
  txt(s, 80, 69, 32, C.ink, "left", 700, a * .9);
}

// ---------------------------------------------------------------- 文字の検査（render_frames.js --textcheck）
window.Stage = {
  TEXTLOG,
  clearTextLog() { TEXTLOG.length = 0; },
  checkText(t) {
    const out = [];
    for (const e of TEXTLOG) if (e.a > .3 && (e.x0 < -2 || e.x1 > W + 2 || e.y0 < -2 || e.y1 > H + 2)) out.push({ t, kind: "画面の外", s: e.s });
    return out;
  },
};

// ---------------------------------------------------------------- 画像
const IMG = {};
const READY_IMG = Promise.all(Object.entries(window.ASSETS || {}).map(([k, src]) => new Promise(r => { const im = new Image(); im.onload = () => { IMG[k] = im; r(); }; im.src = src; })));
function image(name, x, y, w, a = 1, rot = 0, frame = true) {
  const im = IMG[name]; if (!im || a <= .01) return;
  const h = w * im.height / im.width;
  at(x, y, 1, a, () => {
    if (frame) { g.shadowColor = "rgba(0,0,0,.6)"; g.shadowBlur = 40; g.shadowOffsetY = 14; g.fillStyle = "#fff"; g.fillRect(-w / 2 - 8, -h / 2 - 8, w + 16, h + 16); g.shadowColor = "transparent"; }
    g.drawImage(im, -w / 2, -h / 2, w, h);
  }, rot);
  return h;
}
function imageCrop(name, sx, sy, sw, sh, x, y, w, a = 1, rot = 0) {
  const im = IMG[name]; if (!im || a <= .01) return;
  const h = w * sh / sw;
  at(x, y, 1, a, () => {
    g.shadowColor = "rgba(0,0,0,.6)"; g.shadowBlur = 40; g.shadowOffsetY = 14; g.fillStyle = "#fff"; g.fillRect(-w / 2 - 8, -h / 2 - 8, w + 16, h + 16); g.shadowColor = "transparent";
    g.drawImage(im, sx, sy, sw, sh, -w / 2, -h / 2, w, h);
  }, rot);
}

// ---------------------------------------------------------------- 3D（問いかけの場面だけ）
const G3 = (() => {
  const canvas = document.getElementById("gl");
  const R = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
  R.setSize(W, H, false); R.setPixelRatio(1); R.outputEncoding = THREE.sRGBEncoding; R.toneMapping = THREE.ACESFilmicToneMapping; R.toneMappingExposure = 1.15;
  const scene = new THREE.Scene(); scene.fog = new THREE.FogExp2(0x060c18, 0.055); scene.background = new THREE.Color(0x060c18);
  const cam = new THREE.PerspectiveCamera(38, W / H, .1, 200);
  scene.add(new THREE.HemisphereLight(0x9fc8ff, 0x0a1020, .55));
  const key = new THREE.SpotLight(0xffe2c0, 2.4, 40, .5, .6, 1); key.position.set(4, 8, 6); scene.add(key); scene.add(key.target);
  const rim = new THREE.PointLight(0x4fd1ff, 1.6, 30, 1); rim.position.set(-6, 2, -4); scene.add(rim);
  const floor = new THREE.Mesh(new THREE.CircleGeometry(30, 64), new THREE.MeshStandardMaterial({ color: 0x0c1626, roughness: .35, metalness: .4 }));
  floor.rotation.x = -Math.PI / 2; floor.position.y = -2.2; scene.add(floor);
  function texText(lines, w = 1024, h = 512, color = "#c81e2e", bg = null, font = 120) {
    const c = document.createElement("canvas"); c.width = w; c.height = h; const x = c.getContext("2d");
    if (bg) { x.fillStyle = bg; x.fillRect(0, 0, w, h); }
    x.fillStyle = color; x.textAlign = "center"; x.textBaseline = "middle";
    lines.forEach((s, i) => { x.font = `900 ${font}px ${FONT}`; x.fillText(s, w / 2, h / 2 + (i - (lines.length - 1) / 2) * font * 1.15); });
    const tx = new THREE.CanvasTexture(c); tx.encoding = THREE.sRGBEncoding; tx.anisotropy = 8; return tx;
  }
  // 判子：持ち手＋台＋印面（文字を左右反転した面を下に、手前に見える側面に文字）
  const stampG = new THREE.Group();
  const wood = new THREE.MeshStandardMaterial({ color: 0x5a3a24, roughness: .55, metalness: .05 });
  const handle = new THREE.Mesh(new THREE.CylinderGeometry(.42, .55, 1.6, 48), wood); handle.position.y = 1.5;
  const knob = new THREE.Mesh(new THREE.SphereGeometry(.62, 48, 24), wood); knob.position.y = 2.45;
  const base = new THREE.Mesh(new THREE.BoxGeometry(3.4, .55, 1.7), new THREE.MeshStandardMaterial({ color: 0x2b1a10, roughness: .5 }));
  base.position.y = .45;
  const face = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 1.5), new THREE.MeshStandardMaterial({ map: texText(["科学的に", "証明済み"], 1024, 480, "#ff3b4b", "#1a0c08", 150), roughness: .6, emissive: 0x330608 }));
  face.position.set(0, .45, .86);
  stampG.add(handle, knob, base, face); scene.add(stampG);
  // 漂う点（第 2 章の「消えた点」）
  const dots = new THREE.Group();
  const dotM = new THREE.MeshStandardMaterial({ color: 0x8fb8ff, emissive: 0x4fd1ff, emissiveIntensity: .9, roughness: .3, transparent: true, opacity: .85 });
  for (let i = 0; i < 64; i++) { const m = new THREE.Mesh(new THREE.SphereGeometry(.16, 24, 12), dotM); m.userData = { a: hash(i * 3.3) * 6.28, r: 2.2 + hash(i * 1.7) * 7, y: (hash(i * 9.1) - .5) * 5, s: .15 + hash(i * 4.4) * .25 }; dots.add(m); }
  const hero = new THREE.Mesh(new THREE.SphereGeometry(.42, 48, 24), new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xffb648, emissiveIntensity: 1.3, roughness: .2 }));
  dots.add(hero); scene.add(dots);
  // 新しい「それっぽい話」のカード
  const card = new THREE.Mesh(new THREE.BoxGeometry(5.2, 2.6, .08), [0, 0, 0, 0].map(() => new THREE.MeshStandardMaterial({ color: 0x1b2c48 })).concat([
    new THREE.MeshStandardMaterial({ map: texText(["人は1日に", "3万5000回", "決断している"], 1024, 512, "#eaf2ff", "#14243c", 110), roughness: .45, emissive: 0x0b1424 }),
    new THREE.MeshStandardMaterial({ color: 0x14243c })]));
  scene.add(card);
  const tag = new THREE.Mesh(new THREE.PlaneGeometry(2.6, .7), new THREE.MeshBasicMaterial({ map: texText(["出典：見つからない"], 1024, 276, "#ffb648", "#2a1606", 120), transparent: true }));
  scene.add(tag);
  function show(which) { stampG.visible = which === "stamp"; dots.visible = which === "dots"; card.visible = tag.visible = which === "card"; }
  return {
    canvas,
    // 冒頭：判子がゆっくり迫り、最後に振り下ろす直前で止まる
    stamp(k) {
      show("stamp"); floor.visible = true;
      const e = ease.inOut(k);
      stampG.position.set(0, lerp(1.6, .2, e) + Math.sin(k * 9) * .03, 0); cam.position.set(Math.sin(k * .8) * 1.0, lerp(-.2, -.9, e), lerp(13, 8.0, e)); cam.lookAt(0, stampG.position.y + 1.7, 0);
      stampG.rotation.set(lerp(.35, .55, e), lerp(-.5, .15, e), lerp(.06, -.04, e));
      key.target.position.copy(stampG.position); R.render(scene, cam);
    },
    // 第 2 章：消えた点が周りを漂い、1 つが目の前で止まる
    dots(k) {
      show("dots"); floor.visible = false;
      cam.position.set(0, 0, 8); cam.lookAt(0, 0, 0);
      dots.children.forEach((m, i) => {
        if (m === hero) return;
        const u = m.userData, ang = u.a + k * u.s * 2.2;
        m.position.set(Math.cos(ang) * u.r, u.y + Math.sin(k * 3 + i) * .2, Math.sin(ang) * u.r - 2);
        m.scale.setScalar(.6 + .4 * Math.sin(k * 4 + i));
      });
      const e = ease.out(k * 1.25);
      hero.position.set(lerp(-6, 0, e), lerp(2.4, 0, e), lerp(-6, 4.2, e)); hero.scale.setScalar(lerp(.5, 1.25, e));
      R.render(scene, cam);
    },
    // 最後：カードが浮かび、虫眼鏡で照らすと「出典：見つからない」の札が出る
    card(k, tagK) {
      show("card"); floor.visible = true;
      cam.position.set(Math.sin(k * 1.1) * .8, .4, lerp(9, 7.2, ease.out(k))); cam.lookAt(0, .5, 0);
      card.position.set(0, .7 + Math.sin(k * 5) * .06, 0); card.rotation.set(-.06, lerp(-.5, .12, ease.inOut(k)), .02);
      tag.position.set(1.3, -.45, .35); tag.scale.setScalar(Math.max(.001, ease.back(tagK))); tag.rotation.z = -.08;
      key.target.position.set(0, .7, 0); R.render(scene, cam);
    },
    clear() { R.setClearColor(0x000000, 0); R.clear(); },
  };
})();
