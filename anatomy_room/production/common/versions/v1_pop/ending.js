// 全動画共通のエンディング（docs/ENDING_SPEC.md）。2D Canvas に描く。
//   drawEnding(ctx, t, opts)
//     t    : エンディング開始からの秒（0 = 本編からの切り替え）
//     opts : { end1, end2 : 「リバース。」「世界の仕組みを、はじめから。」の音声の開始（エンディング開始からの秒）,
//              credits : ["VOICEVOX:…", …], brand : 下部のブランド名（省略時「世界の解剖室」）, W, H : 画面の大きさ（既定 1080×1920） }
// 毎回同じ基本演出を使う（変えてよいのはクレジットだけ）。
(function (root) {
  const C = { navy: "#0A1424", navy2: "#13284A", cyan: "#1AA7CF", cyanL: "#8FDDF2", orange: "#FF8A2A", white: "#FFFFFF" };
  const FONT = '"Noto Sans CJK JP", sans-serif';
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const easeOut = k => 1 - Math.pow(1 - clamp(k), 3);
  const easeInOut = k => { k = clamp(k); return k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2; };
  const prog = (t, a, d) => clamp((t - a) / d);

  function cubeMark(ctx, cx, cy, s, alpha) {
    ctx.save(); ctx.globalAlpha *= alpha;
    const k = .8660254, P = (x, y) => [cx + x, cy + y];
    const top = P(0, -s), ur = P(k * s, -s / 2), bot = P(0, s), ll = P(-k * s, s / 2), ul = P(-k * s, -s / 2), c = P(0, 0);
    const poly = (pts, fill) => { ctx.beginPath(); pts.forEach((p, i) => i ? ctx.lineTo(...p) : ctx.moveTo(...p)); ctx.closePath(); ctx.fillStyle = fill; ctx.fill(); };
    poly([top, ur, c, ul], "#EAF1F8"); poly([ul, c, bot, ll], "#A9BDD3");
    const dx = s * .1, dy = s * .058;
    const R = (u, v) => [c[0] + dx + u * (ur[0] - c[0]) + v * (bot[0] - c[0]), c[1] + dy + u * (ur[1] - c[1]) + v * (bot[1] - c[1])];
    ctx.strokeStyle = C.cyan; ctx.lineWidth = s * .04; ctx.lineCap = "round";
    ctx.beginPath(); ctx.moveTo(...c); ctx.lineTo(...bot); ctx.moveTo(...c); ctx.lineTo(...ur); ctx.stroke();
    ctx.beginPath(); [R(0, 0), R(1, 0), R(1, 1), R(0, 1)].forEach((p, i) => i ? ctx.lineTo(...p) : ctx.moveTo(...p)); ctx.closePath();
    ctx.fillStyle = "rgba(26,167,207,.12)"; ctx.fill(); ctx.stroke();
    ctx.restore();
  }

  function text(ctx, s, x, y, size, color, { weight = 900, align = "center", alpha = 1, spacing = 0 } = {}) {
    ctx.save(); ctx.globalAlpha *= alpha; ctx.font = `${weight} ${size}px ${FONT}`; ctx.fillStyle = color;
    ctx.textAlign = align; ctx.textBaseline = "middle";
    if ("letterSpacing" in ctx) ctx.letterSpacing = spacing + "px";
    ctx.fillText(s, x, y); ctx.restore();
  }

  function drawEnding(ctx, t, opts = {}) {
    const W = opts.W || 1080, H = opts.H || 1920;
    const e1 = opts.end1 ?? 0.35, e2 = opts.end2 ?? 1.6;
    const cx = W / 2, cy = H * 0.44;
    // 明るい背景（白 → 淡い水色 → 淡い橙）と、中央の光
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, "#FFFFFF"); g.addColorStop(.5, "#E2F6FC"); g.addColorStop(1, "#FFF0E0");
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    const glow = ctx.createRadialGradient(cx, cy, 40, cx, cy, 620);
    glow.addColorStop(0, "rgba(143,221,242,.55)"); glow.addColorStop(1, "rgba(143,221,242,0)");
    ctx.fillStyle = glow; ctx.fillRect(0, 0, W, H);
    // 細かい格子（ブランドの質感）
    ctx.fillStyle = "rgba(19,40,74,.07)";
    for (let y = 30; y < H; y += 48) for (let x = 30; x < W; x += 48) { ctx.beginPath(); ctx.arc(x, y, 2.2, 0, 7); ctx.fill(); }

    // 巻き戻しの円弧（反時計回り。最初は速く、だんだん落ち着く）
    const spin = easeOut(prog(t, 0.05, 2.2));
    const rings = [[360, C.cyan, 14, 1.55], [420, C.orange, 10, 1.15], [480, C.navy2, 6, .8]];
    rings.forEach(([r, col, w, sp], i) => {
      const k = easeOut(prog(t, 0.08 + i * .08, .7));
      if (k <= 0) return;
      const a0 = -Math.PI / 2 - spin * Math.PI * 2 * sp - i * 1.1;
      const len = Math.PI * (1.25 - i * .2) * k;
      ctx.save(); ctx.strokeStyle = col; ctx.lineWidth = w; ctx.lineCap = "round"; ctx.globalAlpha = .9;
      ctx.beginPath(); ctx.arc(cx, cy, r, a0, a0 - len, true); ctx.stroke();
      // 矢じり（反時計回りの向き）
      const ae = a0 - len, px = cx + r * Math.cos(ae), py = cy + r * Math.sin(ae);
      const tx = Math.sin(ae), ty = -Math.cos(ae); // 反時計回りの接線
      ctx.fillStyle = col; ctx.beginPath();
      ctx.moveTo(px + tx * w * 2.6, py + ty * w * 2.6);
      ctx.lineTo(px - ty * w * 1.9, py + tx * w * 1.9);
      ctx.lineTo(px + ty * w * 1.9, py - tx * w * 1.9);
      ctx.closePath(); ctx.fill();
      ctx.restore();
    });

    // 「REVERSE」と「リバース」：右から左へ巻き戻るように現れる
    const k1 = easeInOut(prog(t, e1 - 0.05, 0.55));
    ctx.save();
    ctx.beginPath(); ctx.rect(W - (W + 40) * k1, 0, (W + 40) * k1 + 40, H); ctx.clip();
    text(ctx, "R E V E R S E", cx, cy - 175, 44, C.cyan, { weight: 700, spacing: 6 });
    text(ctx, "リバース", cx + 6, cy + 8, 200, "rgba(26,167,207,.35)");
    text(ctx, "リバース", cx, cy, 200, C.navy);
    ctx.restore();
    if (k1 > 0 && k1 < 1) { ctx.fillStyle = C.orange; ctx.fillRect(W - (W + 40) * k1, cy - 150, 8, 300); }

    // サブタイトル（2 句目の音声と同時）
    const k2 = easeOut(prog(t, e2 - 0.05, 0.6));
    if (k2 > 0) {
      ctx.save(); ctx.globalAlpha = .82 * k2; ctx.fillStyle = "#FFFFFF"; ctx.beginPath();
      if (ctx.roundRect) ctx.roundRect(cx - 430, cy + 165 + 24 * (1 - k2), 860, 92, 46); else ctx.rect(cx - 430, cy + 165 + 24 * (1 - k2), 860, 92);
      ctx.fill(); ctx.restore();
      text(ctx, "世界の仕組みを、はじめから", cx, cy + 210 + 24 * (1 - k2), 62, C.navy2, { weight: 700, alpha: k2 });
      const bw = 640 * easeOut(prog(t, e2 + 0.15, 0.8));
      ctx.fillStyle = C.orange; ctx.fillRect(cx + 320 - bw, cy + 262, bw, 7);
    }

    // ブランドとクレジット（小さく）
    const k3 = easeOut(prog(t, 0.6, 0.6));
    // ブランド名（opts.brand。省略時は第 1・2 話と同じ「世界の解剖室」、空文字なら出さない）
    const brand = opts.brand ?? "世界の解剖室";
    if (brand) {
      ctx.save(); ctx.font = `700 40px ${FONT}`; const bw = ctx.measureText(brand).width; ctx.restore();
      const x0 = brand === "世界の解剖室" ? cx - 180 : cx - (bw + 75) / 2; // 第 1・2 話と同じ位置を保つ
      cubeMark(ctx, x0 + 30, H * 0.80, 30, k3);
      text(ctx, brand, x0 + 75, H * 0.80, 40, C.navy2, { weight: 700, align: "left", alpha: k3 });
    }
    if (opts.credits && opts.credits.length)
      text(ctx, "音声：" + opts.credits.join("／"), cx, H * 0.80 + 70, 28, "#4A5B70", { weight: 500, alpha: k3 });

    // 本編からの切り替え：白い閃光
    const flash = 1 - prog(t, 0, 0.35);
    if (flash > 0) { ctx.fillStyle = `rgba(255,255,255,${flash})`; ctx.fillRect(0, 0, W, H); }
  }

  root.drawEnding = drawEnding;
})(typeof window !== "undefined" ? window : globalThis);
