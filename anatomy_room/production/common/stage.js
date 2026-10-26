// チャンネル「リバース」新構成（第 3 話以降）の共通の描画部品。各話の renderer.html が読み込む。
//   ・文字・札・字幕（話者名：オモテ／ウラ）・ブランド表示
//   ・キャラクター：オモテ（全身。表情とポーズで反応）とウラ（ワイプの胸像。話すと口が動く）
//   ・効果：集中線、漫画の爆発、注記、巻き戻し（VHS 風）、グリッチ
// すべて決定的（同じ時刻なら同じ絵）。
(function (root) {
  const W = 1080, H = 1920;
  const FONT = '"Noto Sans CJK JP", sans-serif';
  const C = {
    navy: "#0E1A30", navy2: "#1C2D4E", ink: "#18202E", white: "#FFFFFF",
    orange: "#FF7A2A", yellow: "#FFC83D", red: "#EF4136", green: "#20B26B", cyan: "#19B4E0", sky: "#4FC3F7",
    omote: "#FF7A2A", ura: "#7B5CFF", skin: "#FFD9BC", skinS: "#F2BE98", hair: "#2A2440", jeans: "#33507F",
    uraHair: "#3A2C6E", uraTop: "#14B8A6",
  };
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const lerp = (a, b, k) => a + (b - a) * k;
  const easeOut = k => 1 - Math.pow(1 - clamp(k), 3);
  const easeIn = k => Math.pow(clamp(k), 3);
  const easeInOut = k => { k = clamp(k); return k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2; };
  const back = k => { k = clamp(k); const s = 1.7; return 1 + (s + 1) * Math.pow(k - 1, 3) + s * Math.pow(k - 1, 2); };
  const elastic = k => { k = clamp(k); return k === 0 || k === 1 ? k : Math.pow(2, -10 * k) * Math.sin((k * 10 - .75) * 2 * Math.PI / 3) + 1; };
  const prog = (t, a, d) => clamp((t - a) / d);
  const win = (t, a, b, fi = .3, fo = .3) => Math.min(prog(t, a, fi), 1 - prog(t, b - fo, fo));
  function rng(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }
  function hexA(hex, a) { const n = parseInt(hex.slice(1), 16); return `rgba(${n >> 16},${(n >> 8) & 255},${n & 255},${a})`; }

  // ---------------------------------------------------------------- 文字
  function text(ctx, s, x, y, size, color, { weight = 800, align = "center", alpha = 1, base = "middle", stroke = null, sw = 10, shadow = false } = {}) {
    if (alpha <= 0 || size <= 0) return;
    ctx.save(); ctx.globalAlpha *= alpha; ctx.font = `${weight} ${size}px ${FONT}`;
    ctx.textAlign = align; ctx.textBaseline = base;
    if (shadow) { ctx.shadowColor = "rgba(0,0,0,.25)"; ctx.shadowBlur = 16; ctx.shadowOffsetY = 6; }
    if (stroke) { ctx.lineJoin = "round"; ctx.strokeStyle = stroke; ctx.lineWidth = sw; ctx.strokeText(s, x, y); ctx.shadowColor = "transparent"; }
    ctx.fillStyle = color; ctx.fillText(s, x, y); ctx.restore();
  }
  function rrect(ctx, x, y, w, h, r) {
    r = Math.min(r, w / 2, h / 2);
    ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
  }
  function pill(ctx, s, x, y, size, fg, bgc, alpha = 1, pad = 26, weight = 800) {
    if (alpha <= 0) return 0;
    ctx.save(); ctx.globalAlpha *= alpha; ctx.font = `${weight} ${size}px ${FONT}`;
    const w = ctx.measureText(s).width + pad * 2, h = size * 1.55;
    ctx.shadowColor = "rgba(0,0,0,.18)"; ctx.shadowBlur = 18; ctx.shadowOffsetY = 6;
    rrect(ctx, x - w / 2, y - h / 2, w, h, h / 2); ctx.fillStyle = bgc; ctx.fill();
    ctx.shadowColor = "transparent";
    ctx.fillStyle = fg; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(s, x, y + 2);
    ctx.restore();
    return w;
  }
  // **強調** を色分けして 1 行を中央揃え
  function rich(ctx, s, cx, y, size, base, emph, weight = 800) {
    const parts = s.split("**");
    ctx.font = `${weight} ${size}px ${FONT}`;
    const ws = parts.map(p => ctx.measureText(p).width), tot = ws.reduce((a, b) => a + b, 0);
    let x = cx - tot / 2;
    parts.forEach((p, i) => { text(ctx, p, x, y, size, i % 2 ? emph : base, { align: "left", weight }); x += ws[i]; });
    return tot;
  }
  // 画面の端の注記（事実と演出の区別など）
  function note(ctx, s, x, y, alpha = 1, size = 30, dark = false) {
    if (alpha <= 0) return;
    ctx.save(); ctx.globalAlpha *= alpha; ctx.font = `700 ${size}px ${FONT}`;
    const w = ctx.measureText(s).width + 36, h = size * 1.6;
    rrect(ctx, x - w / 2, y - h / 2, w, h, 12); ctx.fillStyle = dark ? "rgba(14,26,48,.78)" : "rgba(255,255,255,.88)"; ctx.fill();
    ctx.fillStyle = dark ? "#FFFFFF" : C.navy2; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(s, x, y + 1);
    ctx.restore();
  }

  // ---------------------------------------------------------------- 場面
  let TL = null, CUE = {}, SCN = [];
  function setup(tl, scenes) { TL = tl; CUE = { ...tl.cues, endcard: tl.ending_start }; SCN = scenes; }
  function sceneRange(name) {
    const i = SCN.indexOf(name);
    const a = i === 0 ? 0 : CUE[name];
    const b = i + 1 < SCN.length ? CUE[SCN[i + 1]] : TL.ending_start;
    return [a, b];
  }
  function sceneAt(t) {
    for (let i = SCN.length - 1; i >= 0; i--) if (t >= sceneRange(SCN[i])[0]) return SCN[i];
    return SCN[0];
  }
  // いま話しているセリフ（字幕・口パク用）
  function currentLine(t) {
    const L = TL.lines.filter(x => !x.ending);
    for (let i = 0; i < L.length; i++) {
      const nextStart = i + 1 < L.length ? L[i + 1].start : Infinity;
      if (t >= L[i].start - .05 && t < Math.min(nextStart - .02, L[i].end + .4)) return L[i];
    }
    return null;
  }
  // その話者の口の開き（0〜1）。話していなければ 0
  function talk(t, who) {
    const L = TL.lines;
    for (const x of L) {
      if (x.who === who && t >= x.start && t < x.end) {
        const fi = Math.floor((t - x.start) * TL.fps), e = x.env || [];
        return fi < e.length ? e[fi] : 0;
      }
    }
    return 0;
  }
  function speaking(t, who) { return TL.lines.some(x => x.who === who && !x.ending && t >= x.start - .05 && t < x.end + .1); }

  // ---------------------------------------------------------------- 字幕
  function plain(s) { return s.replace(/\*\*/g, "").replace(/ \/ /g, ""); }
  function subChunk(line, t) {
    if (!Array.isArray(line.sub)) return line.sub;
    const lens = line.sub.map(s => plain(s).length), tot = lens.reduce((a, b) => a + b, 0);
    const k = clamp((t - line.start) / (line.end - line.start)) * tot;
    let acc = 0;
    for (let i = 0; i < lens.length; i++) { acc += lens[i]; if (k < acc) return line.sub[i]; }
    return line.sub[line.sub.length - 1];
  }
  function subtitles(ctx, t, cy = 1430) {
    const line = currentLine(t);
    if (!line || t >= TL.ending_start) return;
    const rows = subChunk(line, t).split(" / ");
    let size = 62;
    const cx = 505;
    ctx.font = `800 ${size}px ${FONT}`;
    let wmax = Math.max(...rows.map(r => ctx.measureText(r.replace(/\*\*/g, "")).width));
    if (wmax > 860) { size = Math.floor(size * 860 / wmax); ctx.font = `800 ${size}px ${FONT}`; wmax = 860; }
    const lh = size * 1.36, bw = Math.min(930, wmax + 70), bh = rows.length * lh + 34;
    const k = easeOut(prog(t, line.start - .05, .14));
    const col = line.who === "M" ? C.omote : C.ura;
    ctx.save(); ctx.globalAlpha = k;
    ctx.translate(0, 18 * (1 - k));
    ctx.shadowColor = "rgba(0,0,0,.28)"; ctx.shadowBlur = 24; ctx.shadowOffsetY = 8;
    rrect(ctx, cx - bw / 2, cy - bh / 2, bw, bh, 26); ctx.fillStyle = "rgba(12,20,38,.88)"; ctx.fill();
    ctx.shadowColor = "transparent";
    ctx.fillStyle = col; rrect(ctx, cx - bw / 2, cy - bh / 2, 12, bh, 6); ctx.fill();
    rows.forEach((r, i) => rich(ctx, r, cx, cy - (rows.length - 1) * lh / 2 + i * lh + 2, size, "#FFFFFF", C.yellow));
    // 話者タグ：名前と、声の大きさで動くバー
    const name = (TL.names || {})[line.who] || line.who;
    const tx = cx - bw / 2, ty = cy - bh / 2 - 64;
    ctx.font = `900 34px ${FONT}`;
    const tw = ctx.measureText(name).width + 140;
    rrect(ctx, tx, ty, tw, 54, 27); ctx.fillStyle = col; ctx.fill();
    text(ctx, name, tx + 24, ty + 28, 34, "#FFFFFF", { align: "left", weight: 900 });
    const fi = Math.floor((t - line.start) * TL.fps), env = line.env || [];
    for (let b = 0; b < 5; b++) {
      const e = fi >= 0 && fi < env.length ? env[Math.max(0, Math.min(env.length - 1, fi - b))] : 0;
      const h = 8 + 28 * e * (.6 + .4 * Math.sin(b * 1.7 + 1));
      ctx.fillStyle = "#FFFFFF"; ctx.fillRect(tx + tw - 104 + b * 17, ty + 27 - h / 2, 9, h);
    }
    ctx.restore();
  }

  // ---------------------------------------------------------------- ブランド
  function rewindIcon(ctx, x, y, r, col) {
    ctx.save(); ctx.strokeStyle = col; ctx.lineWidth = r * .22; ctx.lineCap = "round";
    ctx.beginPath(); ctx.arc(x, y, r, -Math.PI * .2, Math.PI * 1.45); ctx.stroke();
    const a = Math.PI * 1.45, px = x + r * Math.cos(a), py = y + r * Math.sin(a);
    ctx.fillStyle = col; ctx.beginPath();
    ctx.moveTo(px - r * .45, py - r * .05); ctx.lineTo(px + r * .2, py - r * .45); ctx.lineTo(px + r * .25, py + r * .3); ctx.closePath(); ctx.fill();
    ctx.beginPath(); ctx.moveTo(x - r * .28, y); ctx.lineTo(x + r * .2, y - r * .32); ctx.lineTo(x + r * .2, y + r * .32); ctx.closePath(); ctx.fill();
    ctx.restore();
  }
  function header(ctx, dark = false) {
    ctx.save(); rrect(ctx, 40, 92, 250, 62, 31); ctx.fillStyle = dark ? "rgba(14,26,48,.55)" : "rgba(255,255,255,.85)"; ctx.fill(); ctx.restore();
    rewindIcon(ctx, 82, 123, 17, dark ? "#FFFFFF" : C.cyan);
    text(ctx, "リバース", 112, 124, 34, dark ? "#FFFFFF" : C.navy2, { align: "left", weight: 900 });
  }

  // ---------------------------------------------------------------- オモテ（全身）
  // (x, y) = 足もと中央、s = 大きさ（1 で身長 約 560px）
  // o: expr（normal/smug/shock/panic/dizzy/think/deadpan/happy）, talk（0〜1 口の開き）, armL/armR（腕の角度。0＝下、+＝外へ上がる、ラジアン）,
  //    elbowL/elbowR（ひじの曲げ）, lean（体の傾き）, rot（全体の回転）, sx/sy（伸び縮み）, look（[x,y] 視線 -1〜1）, wind（髪のなびき）,
  //    sweat（汗）, noArmL（左腕なし）, alpha, legs（歩く位相）, blush
  function omote(ctx, x, y, s, o = {}) {
    const ex = o.expr || "normal";
    ctx.save();
    ctx.globalAlpha *= (o.alpha ?? 1);
    ctx.translate(x, y); ctx.rotate(o.rot || 0); ctx.scale(s * (o.sx || 1), s * (o.sy || 1));
    // 影
    if (!o.noShadow) { ctx.save(); ctx.fillStyle = "rgba(0,0,0,.14)"; ctx.beginPath(); ctx.ellipse(0, 4, 120, 18, 0, 0, 7); ctx.fill(); ctx.restore(); }
    ctx.rotate(o.lean || 0);
    const lw = (c, w) => { ctx.strokeStyle = c; ctx.lineWidth = w; ctx.lineCap = "round"; ctx.lineJoin = "round"; };
    // 脚
    const lp = o.legs || 0;
    for (const sd of [-1, 1]) {
      const sw = Math.sin(lp + (sd > 0 ? Math.PI : 0)) * 18;
      lw(C.jeans, 46); ctx.beginPath(); ctx.moveTo(sd * 40, -205); ctx.lineTo(sd * 46 + sw, -22); ctx.stroke();
      ctx.fillStyle = "#FFFFFF"; rrect(ctx, sd * 46 + sw - 34 + sd * 8, -36, 68, 34, 16); ctx.fill();
      ctx.fillStyle = C.red; ctx.fillRect(sd * 46 + sw - 34 + sd * 8, -10, 68, 8);
    }
    // 腕（後ろ側に描く部分なし。肩から 2 本の線＋手）
    function arm(sd, ang, elbow) {
      const sx = sd * 100, sy = -395;
      const a1 = ang * sd, l1 = 105, l2 = 100;
      const ex_ = sx + Math.sin(a1) * l1, ey = sy + Math.cos(a1) * l1;
      const a2 = a1 + elbow * sd;
      const hx = ex_ + Math.sin(a2) * l2, hy = ey + Math.cos(a2) * l2;
      lw(C.omote, 44); ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(ex_, ey); ctx.lineTo(hx, hy); ctx.stroke();
      lw("#E8641A", 44); ctx.globalAlpha *= 1; // 袖口
      ctx.fillStyle = C.skin; ctx.beginPath(); ctx.arc(hx, hy, 27, 0, 7); ctx.fill();
      ctx.strokeStyle = C.skinS; ctx.lineWidth = 3; ctx.stroke();
    }
    if (!o.noArmL) arm(-1, o.armL ?? .25, o.elbowL ?? .2);
    arm(1, o.armR ?? .25, o.elbowR ?? .2);
    // 胴体（オレンジのパーカー）
    ctx.fillStyle = C.omote; rrect(ctx, -110, -430, 220, 245, 60); ctx.fill();
    ctx.fillStyle = "#E8641A"; rrect(ctx, -70, -300, 140, 70, 24); ctx.fill(); // ポケット
    ctx.strokeStyle = "#FFFFFF"; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(-28, -425); ctx.lineTo(-34, -360); ctx.moveTo(28, -425); ctx.lineTo(34, -360); ctx.stroke();
    ctx.fillStyle = "#E8641A"; ctx.beginPath(); ctx.ellipse(0, -425, 85, 26, 0, 0, 7); ctx.fill(); // フード
    // 頭
    const hy = -540;
    ctx.fillStyle = C.skin; ctx.beginPath(); ctx.ellipse(-92, hy + 6, 18, 24, 0, 0, 7); ctx.ellipse(92, hy + 6, 18, 24, 0, 0, 7); ctx.fill();
    ctx.beginPath(); ctx.ellipse(0, hy, 96, 104, 0, 0, 7); ctx.fill();
    // 髪（とがった前髪。wind でなびく）
    const wd = o.wind || 0;
    ctx.fillStyle = C.hair; ctx.beginPath();
    ctx.moveTo(-100, hy - 10);
    const spikes = [[-110, -95], [-70, -150], [-30, -120], [5, -165], [40, -125], [80, -150], [108, -90]];
    spikes.forEach(([sx, sy], i) => ctx.lineTo(sx + wd * (30 + i * 6), hy + sy - Math.abs(wd) * 10 * Math.sin(i)));
    ctx.lineTo(104, hy - 10); ctx.quadraticCurveTo(80, hy - 70, 30, hy - 58); ctx.quadraticCurveTo(-20, hy - 40, -50, hy - 70);
    ctx.quadraticCurveTo(-80, hy - 50, -100, hy - 10); ctx.closePath(); ctx.fill();
    // 顔
    face(ctx, ex, hy, o);
    // 汗
    if (o.sweat) {
      ctx.fillStyle = "#7FD3FF";
      for (const [sx, sy, r] of [[112, hy - 40, 16], [-120, hy - 10, 12]]) {
        ctx.beginPath(); ctx.moveTo(sx, sy - r * 1.8); ctx.quadraticCurveTo(sx + r, sy, sx, sy + r); ctx.quadraticCurveTo(sx - r, sy, sx, sy - r * 1.8); ctx.fill();
      }
    }
    ctx.restore();
  }
  function face(ctx, ex, hy, o) {
    const lk = o.look || [0, 0], tk = clamp(o.talk || 0);
    const eyeY = hy + 2;
    ctx.lineCap = "round";
    const brow = (y1, y2, sd) => { ctx.strokeStyle = C.hair; ctx.lineWidth = 9; ctx.beginPath(); ctx.moveTo(sd * 18, hy - 42 + y1); ctx.lineTo(sd * 58, hy - 42 + y2); ctx.stroke(); };
    for (const sd of [-1, 1]) {
      const cx = sd * 36;
      if (ex === "happy") { ctx.strokeStyle = C.ink; ctx.lineWidth = 8; ctx.beginPath(); ctx.arc(cx, eyeY + 6, 16, Math.PI * 1.1, Math.PI * 1.9); ctx.stroke(); brow(-4, -8, sd); continue; }
      if (ex === "dizzy") {
        ctx.strokeStyle = C.ink; ctx.lineWidth = 5; ctx.beginPath();
        for (let a = 0; a < Math.PI * 5; a += .2) { const r = 2 + a * 1.4; ctx.lineTo(cx + r * Math.cos(a * sd), eyeY + r * Math.sin(a * sd)); }
        ctx.stroke(); brow(-2, -10, sd); continue;
      }
      const big = ex === "shock" || ex === "panic";
      const ry = big ? 31 : 25, rx = big ? 25 : 21;
      ctx.fillStyle = "#FFFFFF"; ctx.beginPath(); ctx.ellipse(cx, eyeY, rx, ry, 0, 0, 7); ctx.fill();
      ctx.strokeStyle = C.ink; ctx.lineWidth = 4; ctx.stroke();
      const pr = big ? 7 : 12;
      ctx.fillStyle = C.ink; ctx.beginPath(); ctx.arc(cx + lk[0] * 8, eyeY + lk[1] * 9 + 2, pr, 0, 7); ctx.fill();
      ctx.fillStyle = "#FFFFFF"; ctx.beginPath(); ctx.arc(cx + lk[0] * 8 + 4, eyeY + lk[1] * 9 - 3, pr * .32, 0, 7); ctx.fill();
      // まぶた
      const lid = ex === "smug" ? .5 : ex === "deadpan" ? .55 : ex === "think" ? .25 : 0;
      if (lid > 0) {
        ctx.fillStyle = C.skin; ctx.fillRect(cx - rx - 3, eyeY - ry - 3, rx * 2 + 6, (ry * 2 + 6) * lid);
        ctx.strokeStyle = C.ink; ctx.lineWidth = 5; ctx.beginPath(); ctx.moveTo(cx - rx, eyeY - ry + (ry * 2) * lid); ctx.lineTo(cx + rx, eyeY - ry + (ry * 2) * lid); ctx.stroke();
      }
      if (ex === "smug") brow(sd < 0 ? 4 : -10, sd < 0 ? 0 : -16, sd);
      else if (big) brow(-14, -20, sd);
      else if (ex === "think") brow(4, -6, sd);
      else if (ex === "deadpan") brow(0, 0, sd);
      else brow(-2, -6, sd);
    }
    // 口
    const my = hy + 52;
    ctx.fillStyle = "#7A2E2E"; ctx.strokeStyle = C.ink; ctx.lineWidth = 5;
    if (ex === "shock" || ex === "panic") {
      const r = 14 + 14 * tk + (ex === "panic" ? 8 : 0);
      ctx.beginPath(); ctx.ellipse(0, my + 6, r * .8, r, 0, 0, 7); ctx.fill(); ctx.stroke();
    } else if (ex === "happy") {
      ctx.beginPath(); ctx.moveTo(-34, my - 4); ctx.quadraticCurveTo(0, my + 40 + 10 * tk, 34, my - 4); ctx.closePath(); ctx.fill(); ctx.stroke();
    } else if (tk > .08) {
      const h = 6 + 22 * tk, w = ex === "smug" ? 26 : 30;
      ctx.beginPath(); ctx.ellipse(ex === "smug" ? 8 : 0, my, w, h, 0, 0, 7); ctx.fill(); ctx.stroke();
    } else if (ex === "smug") {
      ctx.beginPath(); ctx.moveTo(-22, my + 2); ctx.quadraticCurveTo(10, my + 10, 32, my - 10); ctx.stroke();
    } else if (ex === "deadpan" || ex === "think") {
      ctx.beginPath(); ctx.moveTo(-22, my); ctx.lineTo(22, my); ctx.stroke();
    } else if (ex === "dizzy") {
      ctx.beginPath(); for (let i = 0; i <= 6; i++) ctx.lineTo(-30 + i * 10, my + (i % 2 ? 6 : -4)); ctx.stroke();
    } else {
      ctx.beginPath(); ctx.moveTo(-24, my - 2); ctx.quadraticCurveTo(0, my + 16, 24, my - 2); ctx.stroke();
    }
  }
  // ドット絵のオモテ（QR の回など）。block＝ドットの大きさ（画面の px）
  let pixCan = null, smallCan = null;
  function omotePixel(ctx, x, y, s, o, block) {
    const w = 640, h = 720;
    if (!pixCan) { pixCan = document.createElement("canvas"); smallCan = document.createElement("canvas"); }
    pixCan.width = w; pixCan.height = h;
    const p = pixCan.getContext("2d");
    p.clearRect(0, 0, w, h);
    omote(p, w / 2, h - 30, 1, { ...o, noShadow: true });
    const bs = Math.max(1, block / s);
    smallCan.width = Math.ceil(w / bs); smallCan.height = Math.ceil(h / bs);
    const q = smallCan.getContext("2d");
    q.imageSmoothingEnabled = true; q.clearRect(0, 0, smallCan.width, smallCan.height);
    q.drawImage(pixCan, 0, 0, smallCan.width, smallCan.height);
    ctx.save(); ctx.imageSmoothingEnabled = false; ctx.globalAlpha *= (o.alpha ?? 1);
    ctx.drawImage(smallCan, x - w / 2 * s, y - (h - 30) * s, w * s, h * s);
    ctx.restore();
  }

  // ---------------------------------------------------------------- ウラ（ワイプの胸像）
  // o: expr（smirk/amused/stern/excited）, talk, alpha, pop（出てくる 0〜1）
  function uraBust(ctx, x, y, s, o = {}) {
    const ex = o.expr || "smirk", tk = clamp(o.talk || 0);
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
    // 肩（青緑のタートルネック）
    ctx.fillStyle = C.uraTop; ctx.beginPath(); ctx.moveTo(-150, 210); ctx.quadraticCurveTo(-140, 95, -40, 80); ctx.lineTo(40, 80);
    ctx.quadraticCurveTo(140, 95, 150, 210); ctx.closePath(); ctx.fill();
    ctx.fillStyle = "#0E9A8B"; rrect(ctx, -40, 55, 80, 50, 18); ctx.fill();
    // 後ろ髪（ボブ）
    ctx.fillStyle = C.uraHair; ctx.beginPath(); ctx.ellipse(0, -10, 112, 120, 0, Math.PI, 0); ctx.lineTo(112, 70); ctx.quadraticCurveTo(80, 92, 60, 60);
    ctx.lineTo(-60, 60); ctx.quadraticCurveTo(-80, 92, -112, 70); ctx.closePath(); ctx.fill();
    // 顔
    ctx.fillStyle = "#FFE3CF"; ctx.beginPath(); ctx.ellipse(0, 0, 80, 92, 0, 0, 7); ctx.fill();
    // 前髪（まっすぐ）
    ctx.fillStyle = C.uraHair; ctx.beginPath(); ctx.moveTo(-88, -10); ctx.quadraticCurveTo(-90, -100, 0, -104); ctx.quadraticCurveTo(90, -100, 88, -10);
    ctx.lineTo(70, -30); ctx.lineTo(40, -38); ctx.lineTo(10, -30); ctx.lineTo(-25, -40); ctx.lineTo(-60, -30); ctx.closePath(); ctx.fill();
    // 目（半目で涼しい）
    for (const sd of [-1, 1]) {
      const cx = sd * 33, cy = 12;
      if (ex === "amused") { ctx.strokeStyle = C.ink; ctx.lineWidth = 6; ctx.beginPath(); ctx.arc(cx, cy + 6, 13, Math.PI * 1.15, Math.PI * 1.85); ctx.stroke(); }
      else {
        const open = ex === "excited" ? 1 : ex === "stern" ? .45 : .6;
        ctx.fillStyle = "#FFFFFF"; ctx.beginPath(); ctx.ellipse(cx, cy, 17, 17 * open, 0, 0, 7); ctx.fill();
        ctx.fillStyle = "#4B2E83"; ctx.beginPath(); ctx.arc(cx + 2, cy + 1, 9 * Math.min(1, open + .3), 0, 7); ctx.fill();
        ctx.strokeStyle = C.ink; ctx.lineWidth = 5; ctx.beginPath(); ctx.moveTo(cx - 19, cy - 17 * open + 2); ctx.lineTo(cx + 19, cy - 17 * open - (ex === "stern" ? sd * 5 : 0)); ctx.stroke();
        if (ex === "excited") { ctx.fillStyle = "#FFFFFF"; ctx.beginPath(); ctx.arc(cx + 6, cy - 5, 3.5, 0, 7); ctx.fill(); }
      }
      // 丸めがね
      ctx.strokeStyle = "#2B2140"; ctx.lineWidth = 4.5; ctx.beginPath(); ctx.arc(cx, cy + 2, 27, 0, 7); ctx.stroke();
    }
    ctx.beginPath(); ctx.moveTo(-6, 14); ctx.lineTo(6, 14); ctx.stroke();
    // 口（片方だけ上がる笑み。話すと開く）
    ctx.strokeStyle = C.ink; ctx.lineWidth = 5; ctx.fillStyle = "#9C3A4A";
    if (tk > .08) { ctx.beginPath(); ctx.ellipse(4, 56, 16, 4 + 13 * tk, 0, 0, 7); ctx.fill(); ctx.stroke(); }
    else if (ex === "amused" || ex === "excited") { ctx.beginPath(); ctx.moveTo(-20, 50); ctx.quadraticCurveTo(2, 70, 24, 48); ctx.stroke(); }
    else if (ex === "stern") { ctx.beginPath(); ctx.moveTo(-14, 56); ctx.lineTo(16, 54); ctx.stroke(); }
    else { ctx.beginPath(); ctx.moveTo(-16, 56); ctx.quadraticCurveTo(6, 60, 22, 46); ctx.stroke(); }
    ctx.fillStyle = "rgba(255,120,140,.25)"; ctx.beginPath(); ctx.ellipse(-46, 40, 14, 8, 0, 0, 7); ctx.ellipse(46, 40, 14, 8, 0, 0, 7); ctx.fill();
    ctx.restore();
  }
  // ワイプ：丸い枠の中の胸像と名前（who＝"W" ならウラ、"M" ならオモテ）
  function wipe(ctx, t, who, cx, cy, r, o = {}) {
    const k = o.alpha ?? 1;
    if (k <= 0) return;
    const pop = back(o.pop ?? 1);
    ctx.save(); ctx.globalAlpha *= clamp(k); ctx.translate(cx, cy); ctx.scale(pop, pop);
    ctx.shadowColor = "rgba(0,0,0,.25)"; ctx.shadowBlur = 20; ctx.shadowOffsetY = 8;
    ctx.fillStyle = "#FFFFFF"; ctx.beginPath(); ctx.arc(0, 0, r + 8, 0, 7); ctx.fill();
    ctx.shadowColor = "transparent";
    ctx.save(); ctx.beginPath(); ctx.arc(0, 0, r, 0, 7); ctx.clip();
    const g = ctx.createLinearGradient(0, -r, 0, r);
    if (who === "W") { g.addColorStop(0, "#EDE7FF"); g.addColorStop(1, "#C9BBFF"); } else { g.addColorStop(0, "#FFF1E3"); g.addColorStop(1, "#FFC9A0"); }
    ctx.fillStyle = g; ctx.fillRect(-r, -r, 2 * r, 2 * r);
    const tk = talk(t, who);
    if (who === "W") uraBust(ctx, 0, r * .12, r / 165, { expr: o.expr, talk: tk });
    else omote(ctx, 0, r * 4.85, r / 112, { expr: o.expr || "normal", talk: tk, noShadow: true, armL: .2, armR: .2 });
    ctx.restore();
    const col = who === "W" ? C.ura : C.omote;
    ctx.strokeStyle = col; ctx.lineWidth = 7; ctx.beginPath(); ctx.arc(0, 0, r + 4, 0, 7); ctx.stroke();
    pill(ctx, (TL.names || {})[who] || who, 0, r + 14, 30, "#FFFFFF", col, 1, 18, 900);
    ctx.restore();
  }

  // ---------------------------------------------------------------- 効果
  function speedLines(ctx, cx, cy, t, col = "rgba(255,255,255,.75)", n = 48, inner = 330, seed = 3) {
    const r = rng(seed + Math.floor(t * 12));
    ctx.save(); ctx.fillStyle = col;
    for (let i = 0; i < n; i++) {
      const a = (i / n) * Math.PI * 2 + r() * .1, w = .012 + r() * .02, r0 = inner + r() * 120, r1 = 1500;
      ctx.beginPath(); ctx.moveTo(cx + Math.cos(a - w) * r1, cy + Math.sin(a - w) * r1); ctx.lineTo(cx + Math.cos(a) * r0, cy + Math.sin(a) * r0);
      ctx.lineTo(cx + Math.cos(a + w) * r1, cy + Math.sin(a + w) * r1); ctx.closePath(); ctx.fill();
    }
    ctx.restore();
  }
  // 漫画の爆発（ギザギザの吹き出し）＋文字
  function burst(ctx, x, y, r, k, label, { fill = C.yellow, stroke = C.navy, size = 96, color = C.navy, rot = -.08, spikes = 14 } = {}) {
    if (k <= 0) return;
    const s = back(k);
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s);
    ctx.beginPath();
    for (let i = 0; i < spikes * 2; i++) {
      const a = i / (spikes * 2) * Math.PI * 2, rr = i % 2 ? r * .72 : r;
      ctx[i ? "lineTo" : "moveTo"](Math.cos(a) * rr, Math.sin(a) * rr * .8);
    }
    ctx.closePath(); ctx.fillStyle = fill; ctx.fill(); ctx.lineWidth = 10; ctx.strokeStyle = stroke; ctx.lineJoin = "round"; ctx.stroke();
    if (label) text(ctx, label, 0, 4, size, color, { weight: 900 });
    ctx.restore();
  }
  function bigX(ctx, x, y, r, k, col = C.red) {
    if (k <= 0) return;
    const s = back(k);
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.strokeStyle = "#FFFFFF"; ctx.lineCap = "round";
    for (const [w, c] of [[r * .42, "#FFFFFF"], [r * .26, col]]) {
      ctx.strokeStyle = c; ctx.lineWidth = w; ctx.beginPath(); ctx.moveTo(-r, -r); ctx.lineTo(r, r); ctx.moveTo(r, -r); ctx.lineTo(-r, r); ctx.stroke();
    }
    ctx.restore();
  }
  function bigO(ctx, x, y, r, k, col = C.green) {
    if (k <= 0) return;
    const s = back(k);
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
    for (const [w, c] of [[r * .42, "#FFFFFF"], [r * .26, col]]) { ctx.strokeStyle = c; ctx.lineWidth = w; ctx.beginPath(); ctx.arc(0, 0, r, 0, 7); ctx.stroke(); }
    ctx.restore();
  }
  function arrow(ctx, x1, y1, x2, y2, col, w = 18, head = 46, alpha = 1) {
    if (alpha <= 0) return;
    const a = Math.atan2(y2 - y1, x2 - x1);
    ctx.save(); ctx.globalAlpha *= alpha; ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = w; ctx.lineCap = "round";
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2 - Math.cos(a) * head * .6, y2 - Math.sin(a) * head * .6); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(x2, y2); ctx.lineTo(x2 - Math.cos(a - .45) * head, y2 - Math.sin(a - .45) * head);
    ctx.lineTo(x2 - Math.cos(a + .45) * head, y2 - Math.sin(a + .45) * head); ctx.closePath(); ctx.fill();
    ctx.restore();
  }
  // 巻き戻し（VHS 風）：走査線・色ずれ・「◀◀ REWIND」
  function vhs(ctx, t, k) {
    if (k <= 0) return;
    ctx.save(); ctx.globalAlpha = k;
    ctx.fillStyle = "rgba(20,40,90,.12)"; ctx.fillRect(0, 0, W, H);
    for (let y = (t * 900) % 12; y < H; y += 12) { ctx.fillStyle = "rgba(255,255,255,.10)"; ctx.fillRect(0, y, W, 3); }
    const by = (t * 1400) % (H + 200) - 100;
    ctx.fillStyle = "rgba(255,255,255,.35)"; ctx.fillRect(0, by, W, 60);
    text(ctx, "◀◀ REWIND", 70, 250, 64, "#FFFFFF", { align: "left", weight: 900, stroke: "rgba(14,26,48,.8)", sw: 10 });
    ctx.restore();
  }
  // グリッチ：画面の横の帯をずらす（そのキャンバス自身を使う）
  function glitch(ctx, t, amount, seed = 1) {
    if (amount <= 0) return;
    const r = rng(seed + Math.floor(t * 20));
    const can = ctx.canvas;
    for (let i = 0; i < 9 * amount; i++) {
      const y = r() * H, h = 20 + r() * 120, dx = (r() - .5) * 160 * amount;
      ctx.drawImage(can, 0, y, W, h, dx, y, W, h);
    }
    ctx.save(); ctx.globalCompositeOperation = "screen"; ctx.globalAlpha = .25 * amount;
    ctx.fillStyle = r() < .5 ? "#FF00AA" : "#00E5FF"; ctx.fillRect(0, r() * H, W, 30 + r() * 80); ctx.restore();
  }
  function flash(ctx, k, col = "255,255,255") { if (k > 0) { ctx.fillStyle = `rgba(${col},${clamp(k)})`; ctx.fillRect(0, 0, W, H); } }
  function gradientBG(ctx, c1, c2, c3) {
    const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, c1); g.addColorStop(.55, c2 || c1); g.addColorStop(1, c3 || c2 || c1);
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  }
  function dots(ctx, col = "rgba(255,255,255,.18)", step = 48, off = 0) {
    ctx.fillStyle = col;
    for (let y = 30 + off % step; y < H; y += step) for (let x = 30; x < W; x += step) { ctx.beginPath(); ctx.arc(x, y, 2.4, 0, 7); ctx.fill(); }
  }
  function rays(ctx, cx, cy, t, col, n = 18) {
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(t * .15); ctx.fillStyle = col;
    for (let i = 0; i < n; i++) { ctx.rotate(Math.PI * 2 / n); ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(-90, -1500); ctx.lineTo(90, -1500); ctx.closePath(); ctx.fill(); }
    ctx.restore();
  }

  root.Stage = {
    W, H, FONT, C, clamp, lerp, easeOut, easeIn, easeInOut, back, elastic, prog, win, rng, hexA,
    text, rrect, pill, rich, note, setup, sceneRange, sceneAt, currentLine, talk, speaking, subtitles, header, rewindIcon,
    omote, omotePixel, uraBust, wipe, speedLines, burst, bigX, bigO, arrow, vhs, glitch, flash, gradientBG, dots, rays,
    get TL() { return TL; }, get CUE() { return CUE; },
  };
})(typeof window !== "undefined" ? window : globalThis);
