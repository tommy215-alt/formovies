// 当事者設計（シリーズ「あなたならどうする？」、2026-11-02〜）の目線の演出。テンプレートの外の部品（kit.js のあとに読む）。
// bg に場面の画（Blender のコマなど）を描いたあと、renderer の fxEp(t, name) から呼ぶ。閃光は使わない（全設計の決まり）。
//   POV.shake(t, amt)     手持ちの揺れ（画を少し拡大してずらす。amt は画素）
//   POV.blur(px)          視界のぼけ（メガネをなくした・意識が遠のく）
//   POV.breath(t, rate, k) 息づかいに合わせて周辺が暗くなる（rate：1 秒あたりの呼吸、k：強さ 0〜1）
//   POV.heart(t, bpm, k)  心拍に合わせて周辺が赤黒く脈打つ
//   POV.blink(t, t0, d)   t0 から d 秒のまばたき（閉じて開く）。POV.eyes(k)：まぶたの閉じ具合 0〜1
//   POV.rain(t, k)        雨の筋。POV.sand(t, k, dir)：砂嵐（黄色いかすみと横に流れる砂）
const POV = (() => {
  let tmp = null;
  const copy = () => { if (!tmp) { tmp = document.createElement("canvas"); tmp.width = W; tmp.height = H; } const x = tmp.getContext("2d"); x.clearRect(0, 0, W, H); x.drawImage(bg.canvas, 0, 0); return tmp; };
  const n1 = (t, f, s) => Math.sin(t * f + s) * .6 + Math.sin(t * f * 2.13 + s * 1.7) * .3 + Math.sin(t * f * 4.7 + s * .3) * .1;
  function shake(t, amt) { if (amt <= 0) return; const c = copy(), sc = 1 + 2.4 * amt / W, dx = n1(t, 2.1, 1) * amt, dy = n1(t, 1.7, 4) * amt, r = n1(t, 1.3, 7) * amt * .0006;
    bg.save(); bg.translate(W / 2 + dx, H / 2 + dy); bg.rotate(r); bg.scale(sc, sc); bg.drawImage(c, -W / 2, -H / 2); bg.restore(); }
  function blur(px) { if (px <= .2) return; const c = copy(); bg.save(); bg.filter = `blur(${px}px)`; bg.drawImage(c, 0, 0); bg.restore(); }
  function vig(k, col) { if (k <= 0) return; const g = bg.createRadialGradient(W / 2, H / 2, H * .18, W / 2, H / 2, H * .62); g.addColorStop(0, `rgba(${col},0)`); g.addColorStop(1, `rgba(${col},${Math.min(.95, k)})`); bg.fillStyle = g; bg.fillRect(0, 0, W, H); }
  function breath(t, rate = .45, k = .5) { vig(k * (.55 + .45 * (.5 + .5 * Math.sin(t * rate * 2 * Math.PI))), "0,0,0"); }
  function heart(t, bpm = 110, k = .5) { const p = (t * bpm / 60) % 1, b = Math.exp(-p * 9) + .6 * Math.exp(-Math.max(0, p - .22) * 11) * (p > .22 ? 1 : 0); vig(k * (.35 + .65 * b), "40,0,0"); }
  function eyes(k) { if (k <= 0) return; const h = H / 2 * Math.min(1, k) * 1.08; bg.fillStyle = "#000";
    bg.beginPath(); bg.moveTo(0, 0); bg.lineTo(W, 0); bg.lineTo(W, h); bg.quadraticCurveTo(W / 2, h + 140 * k, 0, h); bg.fill();
    bg.beginPath(); bg.moveTo(0, H); bg.lineTo(W, H); bg.lineTo(W, H - h); bg.quadraticCurveTo(W / 2, H - h - 140 * k, 0, H - h); bg.fill(); }
  function blink(t, t0, d = .32) { const u = (t - t0) / d; if (u < 0 || u > 1) return; eyes(Math.sin(u * Math.PI)); }
  function rain(t, k = .5) { if (k <= 0) return; const r = S.rng(Math.floor(t * 30) * 7 + 3); bg.save(); bg.strokeStyle = `rgba(200,215,230,${.35 * k})`; bg.lineWidth = 2;
    for (let i = 0; i < 160 * k; i++) { const x = r() * W, y = r() * H, L = 60 + r() * 90; bg.beginPath(); bg.moveTo(x, y); bg.lineTo(x - L * .12, y + L); bg.stroke(); } bg.restore(); }
  function sand(t, k = .5, dir = 1) { if (k <= 0) return; bg.fillStyle = `rgba(196,150,82,${.75 * Math.min(1, k)})`; bg.fillRect(0, 0, W, H);
    const r = S.rng(Math.floor(t * 30) * 13 + 5); bg.save(); bg.strokeStyle = `rgba(235,200,140,${.45 * k})`; bg.lineWidth = 2;
    for (let i = 0; i < 260 * k; i++) { const y = r() * H, x = r() * W, L = 40 + r() * 160; bg.beginPath(); bg.moveTo(x, y); bg.lineTo(x + dir * L, y + (r() - .5) * 12); bg.stroke(); } bg.restore(); }
  return { shake, blur, breath, heart, eyes, blink, rain, sand };
})();
