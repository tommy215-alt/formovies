// テンプレートの外に足す画面の部品（2026-10-29〜、pilot_015 の修正事項。案 A：production/common/stage.js は変えない）。
// 注目・拡大のときのテクノロジー感のあるアイコンと、冒頭の大きな見出し。文字は Stage.text で描くので、文字の自動検査（textcheck）の対象になる。
//   HUD.title(ctx, rows, cx, cy, k, t)          冒頭の見出し：太い大きな文字に、光の帯が横切る。rows＝[[文字, 大きさ, 色], …]
//   HUD.lens(ctx, cx, cy, r, k, t, label, draw) 拡大鏡の枠（目盛り・十字・倍率の札）。draw(ctx) を円の中だけに描く
//   HUD.tag(ctx, x0, y0, x1, y1, sym, name, k)  対象 (x0,y0) から札 (x1,y1) へ線を引き、元素記号と名前を出す
//   HUD.scanBox(ctx, x0, y0, x1, y1, k, t)      四隅の枠＋中を往復するスキャンの線＋細かい目盛り
//   HUD.readout(ctx, x, y, rows, k, size)        データ表示：左から文字が打ち出される（rows＝文字列の配列）
//   HUD.ring(ctx, x, y, k, r)                    波紋のように広がる輪（k＝0→1）
//   HUD.ink(ctx, x0, y0, x1, y1, k)              赤いインクの丸と下線（判を押したような強調）
//   HUD.route(ctx, pts, k, t)                    点線の経路が伸び、先頭に光る点
(function (root) {
  const S = root.Stage, { W, H, clamp, lerp, easeOut, easeInOut } = S;
  const CY = "143,220,255";
  const off = document.createElement("canvas"); off.width = W; off.height = H;

  function title(ctx, rows, cx, cy, k, t) {
    if (k <= 0) return;
    const o = off.getContext("2d"); o.setTransform(1, 0, 0, 1, 0, 0); o.clearRect(0, 0, W, H);
    let tot = rows.reduce((a, r) => a + r[1] * 1.12, 0), y = cy - tot / 2;
    S.group(() => rows.forEach(([s, size, col]) => { y += size * .56; S.text(o, s, cx, y, size, col, { weight: 900, stroke: "#040a14", sw: Math.round(size * .14) }); y += size * .56; }));
    // 光の帯：左から右へ一度横切る（文字の形の中だけ）
    const sx = lerp(-300, W + 300, easeInOut(clamp((t % 99) / 1.4))), g = o.createLinearGradient(sx - 160, 0, sx + 160, 0);
    g.addColorStop(0, "rgba(255,255,255,0)"); g.addColorStop(.5, "rgba(255,246,220,.85)"); g.addColorStop(1, "rgba(255,255,255,0)");
    o.save(); o.globalCompositeOperation = "source-atop"; o.fillStyle = g; o.fillRect(0, cy - tot, W, tot * 2); o.restore();
    const e = easeOut(clamp(k));
    ctx.save(); ctx.globalAlpha *= clamp(k * 1.4);
    ctx.shadowColor = "rgba(255,200,120,.55)"; ctx.shadowBlur = 40 * e;
    const s = 1.18 - .18 * e;                                   // 少し大きい所から、ぐっと定位置へ
    ctx.translate(cx, cy); ctx.scale(s, s); ctx.translate(-cx, -cy); ctx.drawImage(off, 0, 0);
    ctx.restore();
  }

  function lens(ctx, cx, cy, r, k, t, label, draw) {
    if (k <= 0) return;
    const e = easeOut(clamp(k)), rr = r * (.6 + .4 * e);
    if (draw) { ctx.save(); ctx.beginPath(); ctx.arc(cx, cy, rr, 0, 6.283); ctx.clip(); ctx.globalAlpha *= clamp(k * 1.3); draw(ctx, rr); ctx.restore(); }
    ctx.save(); ctx.globalAlpha *= clamp(k * 1.5); ctx.strokeStyle = `rgba(${CY},.95)`; ctx.shadowColor = `rgba(${CY},.6)`; ctx.shadowBlur = 12;
    ctx.lineWidth = 4; ctx.beginPath(); ctx.arc(cx, cy, rr, 0, 6.283); ctx.stroke();
    ctx.lineWidth = 2; ctx.globalAlpha *= .7; ctx.beginPath(); ctx.arc(cx, cy, rr + 14, -1.2 + t * .4, .6 + t * .4); ctx.stroke();
    for (let i = 0; i < 36; i++) { const a = i / 36 * 6.283, l = i % 9 === 0 ? 16 : 7; ctx.beginPath(); ctx.moveTo(cx + Math.cos(a) * (rr - 2), cy + Math.sin(a) * (rr - 2)); ctx.lineTo(cx + Math.cos(a) * (rr - 2 - l), cy + Math.sin(a) * (rr - 2 - l)); ctx.stroke(); }
    ctx.globalAlpha *= .6; ctx.beginPath(); ctx.moveTo(cx - 22, cy); ctx.lineTo(cx + 22, cy); ctx.moveTo(cx, cy - 22); ctx.lineTo(cx, cy + 22); ctx.stroke();
    ctx.restore();
    if (label && k > .5) { ctx.save(); ctx.globalAlpha *= clamp((k - .5) * 2); const lx = cx + rr * .72, ly = cy - rr * .82;
      S.rrect(ctx, lx - 58, ly - 26, 116, 52, 10); ctx.fillStyle = "rgba(6,14,26,.82)"; ctx.fill(); ctx.strokeStyle = `rgba(${CY},.8)`; ctx.lineWidth = 2; ctx.stroke();
      S.group(() => S.text(ctx, label, lx, ly + 2, 34, `rgb(${CY})`, { weight: 800 })); ctx.restore(); }
  }

  function tag(ctx, x0, y0, x1, y1, sym, name, k, col = CY) {
    if (k <= 0) return;
    const e = easeOut(clamp(k * 1.4));
    ctx.save(); ctx.strokeStyle = `rgba(${col},.9)`; ctx.lineWidth = 2.5; ctx.shadowColor = `rgba(${col},.55)`; ctx.shadowBlur = 8;
    ctx.beginPath(); ctx.arc(x0, y0, 7, 0, 6.283); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(lerp(x0, x1, Math.min(1, e * 1.6)), lerp(y0, y1, Math.min(1, e * 1.6))); ctx.stroke(); ctx.restore();
    if (k < .45) return;
    ctx.save(); ctx.font = `900 48px ${S.FONT}`; const sw_ = ctx.measureText(sym).width; ctx.restore();   // 記号が長い札（「化石」など）は幅を広げる（1 文字の札は 84 のまま）
    const a = clamp((k - .45) / .35), w = name ? Math.max(150, sw_ + 40) : Math.max(84, sw_ + 24), h = name ? 104 : 74;
    ctx.save(); ctx.globalAlpha *= a; ctx.translate(x1, y1); ctx.scale(.85 + .15 * a, .85 + .15 * a);
    S.rrect(ctx, -w / 2, -h / 2, w, h, 12); ctx.fillStyle = "rgba(6,14,26,.86)"; ctx.fill(); ctx.strokeStyle = `rgba(${col},.95)`; ctx.lineWidth = 2.5; ctx.stroke();
    ctx.fillStyle = `rgba(${col},.95)`; ctx.fillRect(-w / 2, -h / 2 + 12, 4, h - 24);
    ctx.restore();
    ctx.save(); ctx.globalAlpha *= a; S.group(() => {
      S.text(ctx, sym, x1, y1 - (name ? 14 : 0), 48, `rgb(${col})`, { weight: 900 });
      if (name) S.text(ctx, name, x1, y1 + 30, 26, "#D8E6F2", { weight: 700 });
    }, [x1 - w / 2, y1 - h / 2, x1 + w / 2, y1 + h / 2]); ctx.restore();
  }

  function scanBox(ctx, x0, y0, x1, y1, k, t) {
    if (k <= 0) return;
    S.hudBox(ctx, x0, y0, x1, y1, k);
    if (k < .4) return;
    const a = clamp((k - .4) / .4), y = lerp(y0 + 6, y1 - 6, .5 + .5 * Math.sin(t * 2.4));
    ctx.save(); ctx.globalAlpha *= a;
    const g = ctx.createLinearGradient(0, y - 30, 0, y + 2); g.addColorStop(0, `rgba(${CY},0)`); g.addColorStop(1, `rgba(${CY},.18)`);
    ctx.fillStyle = g; ctx.fillRect(x0 + 4, y - 30, x1 - x0 - 8, 32); ctx.fillStyle = `rgba(${CY},.85)`; ctx.fillRect(x0 + 4, y, x1 - x0 - 8, 2);
    ctx.fillStyle = `rgba(${CY},.35)`; for (let x = x0 + 24; x < x1 - 10; x += 40) ctx.fillRect(x, y1 + 10, 2, 8);
    ctx.restore();
  }

  function readout(ctx, x, y, rows, k, size = 30) {
    if (k <= 0) return;
    const total = rows.reduce((a, r) => a + r.length, 0); let left = Math.floor(total * clamp(k));
    ctx.save(); S.group(() => rows.forEach((r, i) => { const n = Math.min(r.length, left); left -= n; if (n <= 0) return;
      S.text(ctx, r.slice(0, n), x, y + i * size * 1.35, size, i === 0 ? `rgb(${CY})` : "#D8E6F2", { weight: 700, align: "left", stroke: "#040a14", sw: 6 }); }));
    ctx.restore();
  }

  function ring(ctx, x, y, k, r = 140, col = CY) {
    if (k <= 0 || k >= 1) return;
    ctx.save(); ctx.strokeStyle = `rgba(${col},${.8 * (1 - k)})`; ctx.lineWidth = 3;
    for (let i = 0; i < 2; i++) { const kk = clamp(k * 1.3 - i * .25); if (kk <= 0) continue; ctx.beginPath(); ctx.arc(x, y, r * (.3 + kk), 0, 6.283); ctx.stroke(); }
    ctx.restore();
  }

  function ink(ctx, x0, y0, x1, y1, k) {
    if (k <= 0) return;
    const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2, rx = (x1 - x0) / 2 + 26, ry = (y1 - y0) / 2 + 22, e = easeOut(clamp(k * 1.25));
    ctx.save(); ctx.strokeStyle = "rgba(230,70,60,.92)"; ctx.lineCap = "round"; ctx.shadowColor = "rgba(255,80,60,.35)"; ctx.shadowBlur = 6;
    for (let p = 0; p < 2; p++) {                              // 二重の線で、手で描いた丸に見せる
      ctx.lineWidth = p ? 3 : 6; ctx.beginPath();
      const a0 = -2.6 + p * .3, a1 = a0 + 6.6 * e;
      for (let a = a0; a <= a1; a += .04) { const w = 1 + .04 * Math.sin(a * 3 + p); const px = cx + Math.cos(a) * rx * w, py = cy + Math.sin(a) * ry * (1 + .05 * Math.cos(a * 2 + p)); a === a0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py); }
      ctx.stroke();
    }
    if (k > .7) { const u = easeOut(clamp((k - .7) / .3)); ctx.lineWidth = 5; ctx.beginPath(); ctx.moveTo(x0 - 6, y1 + 14); ctx.lineTo(lerp(x0 - 6, x1 + 6, u), y1 + 10); ctx.stroke(); }
    ctx.restore();
  }

  function route(ctx, pts, k, t) {
    if (k <= 0 || pts.length < 2) return;
    const seg = pts.slice(1).map((p, i) => Math.hypot(p[0] - pts[i][0], p[1] - pts[i][1])), L = seg.reduce((a, b) => a + b, 0);
    let left = L * clamp(k), end = pts[0];
    ctx.save(); ctx.strokeStyle = `rgba(${CY},.9)`; ctx.lineWidth = 4; ctx.setLineDash([14, 12]); ctx.lineDashOffset = -t * 40; ctx.beginPath(); ctx.moveTo(...pts[0]);
    for (let i = 0; i < seg.length && left > 0; i++) { const u = Math.min(1, left / seg[i]); end = [lerp(pts[i][0], pts[i + 1][0], u), lerp(pts[i][1], pts[i + 1][1], u)]; ctx.lineTo(...end); left -= seg[i]; }
    ctx.stroke(); ctx.setLineDash([]);
    const g = ctx.createRadialGradient(end[0], end[1], 0, end[0], end[1], 26); g.addColorStop(0, "rgba(220,245,255,1)"); g.addColorStop(1, `rgba(${CY},0)`);
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(end[0], end[1], 26, 0, 6.283); ctx.fill(); ctx.restore();
  }

  // 共通エンディングの短い版（2026-10-29〜、案 2）：本編の最後の画の上に、ロゴ・決めゼリフ・音声のクレジットを重ねる。
  //   t は ending_start からの秒、o = { end1, end2（決めゼリフの 2 句の始まり、ending_start からの秒）, credits }
  function endingOverlay(ctx, t, o) {
    const k = easeOut(clamp(t / .35)), k2 = easeOut(clamp((t - o.end2) / .35));
    ctx.save(); const g = ctx.createLinearGradient(0, 600, 0, 1400); g.addColorStop(0, "rgba(4,8,14,0)"); g.addColorStop(.3, `rgba(4,8,14,${.72 * k})`); g.addColorStop(.7, `rgba(4,8,14,${.72 * k})`); g.addColorStop(1, "rgba(4,8,14,0)");
    ctx.fillStyle = g; ctx.fillRect(0, 600, W, 800); ctx.restore();
    ctx.save(); ctx.globalAlpha = k; const s = .9 + .1 * k;
    ctx.translate(540, 900); ctx.scale(s, s); ctx.translate(-540, -900);
    S.rewindIcon(ctx, 540, 790, 46, "#8FDCFF");
    S.group(() => S.text(ctx, "リバース", 540, 905, 120, "#FFFFFF", { weight: 900, stroke: "#04101c", sw: 14 }));
    ctx.restore();
    if (k2 > 0) { ctx.save(); ctx.globalAlpha = k2; S.group(() => S.text(ctx, "世界の仕組みを、はじめから。", 540, 1030, 50, "#A8E6FF", { weight: 800, stroke: "#04101c", sw: 8 })); ctx.restore(); }
    if (o.credits && o.credits.length) { ctx.save(); ctx.globalAlpha = k * .9; S.group(() => S.text(ctx, "音声：" + o.credits.join("／"), 540, 1150, 28, "#B8C7D6", { weight: 500 })); ctx.restore(); }
  }

  root.HUD = { title, lens, tag, scanBox, readout, ring, ink, route, endingOverlay };
})(window);
