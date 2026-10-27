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
  // ---------------------------------------------------------------- 文字の自動検査（2026-10-26）
  // text() で描いた文字の画面上の範囲を記録し、checkText() で「安全領域の外」「文字どうしの重なり」「小さすぎる文字」「入れ物からのはみ出し」を調べる。
  const TEXTLOG = [], CHARLOG = [], OBSLOG = []; let GROUP = 0, CONTAINER = null, NOCHAR = false;
  const SAFE = { x0: 40, x1: 1040, y0: 170, y1: 1650 };       // 縦型ショートの安全領域（上：検索・メニュー、下：タイトル・説明欄）
  const RIGHT_UI = { x0: 950, y0: 880, y1: 1650 };              // 右側のボタン列（いいね・コメントなど）
  function screenBox(ctx, x0, y0, x1, y1) {
    const m = ctx.getTransform(), pts = [[x0, y0], [x1, y0], [x0, y1], [x1, y1]].map(([x, y]) => [m.a * x + m.c * y + m.e, m.b * x + m.d * y + m.f]);
    return [Math.min(...pts.map(p => p[0])), Math.min(...pts.map(p => p[1])), Math.max(...pts.map(p => p[0])), Math.max(...pts.map(p => p[1]))];
  }
  function logText(ctx, s, x, y, size, align, base) {
    if (ctx.globalAlpha < .35 || !s.trim()) return;
    const w = ctx.measureText(s).width, h = size * 1.15;
    const x0 = align === "left" ? x : align === "right" ? x - w : x - w / 2;
    const y0 = base === "middle" ? y - h / 2 : base === "top" ? y : y - h;
    const m = ctx.getTransform(), scale = Math.hypot(m.a, m.b);
    TEXTLOG.push({ s, box: screenBox(ctx, x0, y0, x0 + w, y0 + h), size: size * scale, group: GROUP, container: CONTAINER, ignore: !!ctx.__noCheck });
  }
  function group(fn, container = null) { const g = GROUP, c = CONTAINER; GROUP = ++GROUP_SEQ; CONTAINER = container; try { fn(); } finally { GROUP = g; CONTAINER = c; } }
  let GROUP_SEQ = 0;
  function checkText(t) {
    const out = [], L = TEXTLOG.filter(e => !e.ignore);
    const ov = (a, b) => Math.max(0, Math.min(a[2], b[2]) - Math.max(a[0], b[0])) * Math.max(0, Math.min(a[3], b[3]) - Math.max(a[1], b[1]));
    for (const e of L) {
      if (e.small_sub) { out.push({ t, kind: "small_subtitle", s: e.s, size: Math.round(e.size) }); continue; }
      const [x0, y0, x1, y1] = e.box;
      if (x0 < SAFE.x0 - 1 || x1 > SAFE.x1 + 1 || y0 < SAFE.y0 - 1 || y1 > SAFE.y1 + 1) out.push({ t, kind: "safe", s: e.s, box: e.box.map(Math.round) });
      else if (x1 > RIGHT_UI.x0 && y1 > RIGHT_UI.y0 && y0 < RIGHT_UI.y1) out.push({ t, kind: "right_ui", s: e.s, box: e.box.map(Math.round) });
      if (e.size < 26) out.push({ t, kind: "small", s: e.s, size: Math.round(e.size) });
      if (e.container) { const c = e.container; if (x0 < c[0] - 1 || x1 > c[2] + 1 || y0 < c[1] - 1 || y1 > c[3] + 1) out.push({ t, kind: "overflow", s: e.s, box: e.box.map(Math.round), container: c.map(Math.round) }); }
    }
    for (const e of L) for (const c of CHARLOG) { // 文字がキャラクター（オモテ）にかぶっていないか
      if (e.small_sub) continue;
      const area = (e.box[2] - e.box[0]) * (e.box[3] - e.box[1]);
      const bh = e.box[3] - e.box[1], o = ov(e.box, c); // 文字の 10% 以上、または 1 文字の半分ほど以上が隠れたら
      if (area > 0 && (o / area > .1 || o > .5 * bh * bh)) out.push({ t, kind: "over_character", s: e.s });
    }
    for (const o of OBSLOG) for (let i = 0; i < L.length; i++) { // 声の波形・大きな × など、文字を隠すもの
      const e = L[i]; if (e.small_sub || (o.before && i >= o.n)) continue;
      const area = (e.box[2] - e.box[0]) * (e.box[3] - e.box[1]);
      const lim = o.kind === "over_wave" ? .02 : .05; // 声の波形は、端が触れる程度（2%）でも拾う
      if (area > 0 && ov(e.box, o.box) / area > lim) out.push({ t, kind: o.kind, s: e.s });
    }
    for (let i = 0; i < L.length; i++) for (let j = i + 1; j < L.length; j++) {
      const a = L[i], b = L[j];
      if (a.group && a.group === b.group) continue;
      const o = ov(a.box, b.box), m = Math.min((a.box[2] - a.box[0]) * (a.box[3] - a.box[1]), (b.box[2] - b.box[0]) * (b.box[3] - b.box[1]));
      if (m > 0 && o / m > .12) out.push({ t, kind: "overlap", s: a.s + " ／ " + b.s });
    }
    return out;
  }
  function text(ctx, s, x, y, size, color, { weight = 800, align = "center", alpha = 1, base = "middle", stroke = null, sw = 10, shadow = false } = {}) {
    if (alpha <= 0 || size <= 0) return;
    ctx.save(); ctx.globalAlpha *= alpha; ctx.font = `${weight} ${size}px ${FONT}`;
    ctx.textAlign = align; ctx.textBaseline = base;
    logText(ctx, s, x, y, size, align, base);
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
    if (ctx.globalAlpha >= .35) TEXTLOG.push({ s, box: screenBox(ctx, x - w / 2, y - h / 2, x + w / 2, y + h / 2), size: size * Math.hypot(ctx.getTransform().a, ctx.getTransform().b), group: ++GROUP_SEQ, container: null, ignore: !!ctx.__noCheck });
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
    if (ctx.globalAlpha >= .35) TEXTLOG.push({ s, box: screenBox(ctx, x - w / 2, y - h / 2, x + w / 2, y + h / 2), size, group: ++GROUP_SEQ, container: null, ignore: !!ctx.__noCheck });
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
    NOCHAR = true; omote3(p, w / 2, h - 30, 1, { ...o, noShadow: true }); NOCHAR = false;
    if ((o.alpha ?? 1) > .35) CHARLOG.push(screenBox(ctx, x - 110 * s, y - 560 * s, x + 110 * s, y));
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
    if (label) { // 文字が必ずギザギザの内側に収まるよう、大きさを文字に合わせる
      ctx.save(); ctx.font = `900 ${size}px ${FONT}`; const lw = ctx.measureText(label).width; ctx.restore();
      r = Math.max(r, lw / (2 * .72 * .82), size * .75 / (.8 * .72 * .82));
    }
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s);
    ctx.beginPath();
    for (let i = 0; i < spikes * 2; i++) {
      const a = i / (spikes * 2) * Math.PI * 2, rr = i % 2 ? r * .72 : r;
      ctx[i ? "lineTo" : "moveTo"](Math.cos(a) * rr, Math.sin(a) * rr * .8);
    }
    ctx.closePath(); ctx.fillStyle = fill; ctx.fill(); ctx.lineWidth = 10; ctx.strokeStyle = stroke; ctx.lineJoin = "round"; ctx.stroke();
    if (s >= .85 && !ctx.__noCheck && ctx.globalAlpha >= .35) // ギザギザの本体（内側の円）が、先に描いた文字を隠していないか
      OBSLOG.push({ kind: "under_mark", box: screenBox(ctx, -r * .72, -r * .8 * .72, r * .72, r * .8 * .72), before: true, n: TEXTLOG.filter(e => !e.ignore).length });
    if (label) { // 飛び出す途中（小さいうち）は検査しない
      const inner = screenBox(ctx, -r * .72, -r * .8 * .72, r * .72, r * .8 * .72), nc = ctx.__noCheck; ctx.__noCheck = nc || s < .85;
      group(() => text(ctx, label, 0, 4, size, color, { weight: 900 }), inner); ctx.__noCheck = nc;
    }
    ctx.restore();
  }
  // 複数行の札（自動で大きさを決める）：lines = [[文字, 大きさ, 色], ...]
  function panel(ctx, lines, x, y, k = 1, { bgc = "rgba(255,255,255,.95)", edge = C.orange, pad = 34, gap = 14 } = {}) {
    if (k <= 0) return;
    ctx.save(); ctx.globalAlpha *= clamp(k);
    const ws = lines.map(([s, sz]) => { ctx.font = `900 ${sz}px ${FONT}`; return ctx.measureText(s).width; });
    const w = Math.max(...ws) + pad * 2, h = lines.reduce((a, [, sz]) => a + sz * 1.2, 0) + gap * (lines.length - 1) + pad * 1.4;
    const sc = back(k);
    ctx.translate(x, y); ctx.scale(sc, sc);
    ctx.shadowColor = "rgba(0,0,0,.2)"; ctx.shadowBlur = 20; ctx.shadowOffsetY = 8;
    rrect(ctx, -w / 2, -h / 2, w, h, 26); ctx.fillStyle = bgc; ctx.fill(); ctx.shadowColor = "transparent";
    ctx.strokeStyle = edge; ctx.lineWidth = 6; ctx.stroke();
    const box = screenBox(ctx, -w / 2, -h / 2, w / 2, h / 2);
    let yy = -h / 2 + pad * .7;
    group(() => lines.forEach(([s, sz, col, opt]) => { text(ctx, s, 0, yy + sz * .6, sz, col, { weight: 900, ...(opt || {}) }); yy += sz * 1.2 + gap; }), box);
    ctx.restore();
  }
  function bigX(ctx, x, y, r, k, col = C.red) {
    if (k <= 0) return;
    const s = back(k);
    if (k > .5 && !ctx.__noCheck) { const rr = r * 1.21 * s; // 線の太さを含めた範囲。これより前に描いた文字を隠していないか
      OBSLOG.push({ kind: "under_mark", box: screenBox(ctx, x - rr, y - rr, x + rr, y + rr), before: true, n: TEXTLOG.filter(e => !e.ignore).length }); }
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
    text(ctx, "◀◀ REWIND", 70, 400, 64, "#FFFFFF", { align: "left", weight: 900, stroke: "rgba(14,26,48,.8)", sw: 10 });
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

  // ================================================================ テクノ改修（2026-10-26）
  // ---------------------------------------------------------------- オモテ（3D ピクトグラム）
  // three.js で描く立体のピクトグラム。頭（球）＋胴（カプセル）＋手足（カプセル）、頭のてっぺんにアンテナのような 1 本の毛（シルエットの目印）、
  // 胸に光るリング。表情は目・まゆ・口の形だけで出す。呼び出し方は旧版（2D）の omote(ctx, x, y, s, o) と同じ。
  const O3W = 640, O3H = 760;
  let O3 = null;
  function o3init() {
    const THREE = root.THREE;
    const can = document.createElement("canvas"); can.width = O3W; can.height = O3H;
    const r = new THREE.WebGLRenderer({ canvas: can, antialias: true, alpha: true, preserveDrawingBuffer: true });
    r.setPixelRatio(1); r.setSize(O3W, O3H, false); r.setClearColor(0x000000, 0); r.outputEncoding = THREE.sRGBEncoding;
    const scene = new THREE.Scene();
    const cam = new THREE.PerspectiveCamera(24, O3W / O3H, .1, 100);
    cam.position.set(0, 2.35, 14.6); cam.lookAt(0, 2.2, 0); cam.updateMatrixWorld();
    scene.add(new THREE.HemisphereLight(0xffffff, 0x7f94b8, .7));
    const key = new THREE.DirectionalLight(0xffffff, .95); key.position.set(4, 7, 9); scene.add(key);
    const rim = new THREE.DirectionalLight(0x49e3ff, .9); rim.position.set(-7, 3, -6); scene.add(rim);
    const rim2 = new THREE.DirectionalLight(0xff4fd8, .35); rim2.position.set(7, 2, -5); scene.add(rim2);
    const M = (c, o = {}) => new THREE.MeshStandardMaterial({ color: new THREE.Color(c).convertSRGBToLinear(), roughness: .3, metalness: .05, ...o });
    const skin = M(0xff5410), dark = M(0x101225, { roughness: .5 }), white = M(0xffffff, { roughness: .25 });
    const glow = new THREE.MeshBasicMaterial({ color: 0x3ff0ff });
    const g = new THREE.Group(); scene.add(g);
    const body = new THREE.Group(); g.add(body);
    const torso = new THREE.Mesh(new THREE.CapsuleGeometry(.62, .78, 8, 24), skin); torso.position.y = 1.78; body.add(torso);
    const ring = new THREE.Mesh(new THREE.TorusGeometry(.26, .045, 10, 40), glow); ring.position.set(0, 1.92, .6); body.add(ring);
    const head = new THREE.Group(); head.position.y = 3.25; body.add(head);
    head.add(new THREE.Mesh(new THREE.SphereGeometry(.95, 40, 28), skin));
    // アンテナ毛（曲がった円錐）＋光る先端
    const hair = new THREE.Group(); hair.position.set(.1, .88, 0); head.add(hair);
    const hc = new THREE.Mesh(new THREE.ConeGeometry(.13, .75, 16), skin); hc.position.y = .35; hc.rotation.z = -.35; hair.add(hc);
    const tip = new THREE.Mesh(new THREE.SphereGeometry(.1, 16, 12), glow); tip.position.set(.26, .72, 0); hair.add(tip);
    // 顔：目（白）・ひとみ（黒）・まゆ・口・×目・笑い目
    const face = new THREE.Group(); head.add(face);
    const eyes = [], pupils = [], brows = [], xs = [], arcs = [];
    for (const sd of [-1, 1]) {
      const e = new THREE.Mesh(new THREE.SphereGeometry(.25, 24, 16), white); e.position.set(sd * .34, .12, .8); e.scale.set(1, 1.2, .5); face.add(e); eyes.push(e);
      const p = new THREE.Mesh(new THREE.SphereGeometry(.12, 16, 12), dark); p.position.set(sd * .34, .12, .93); p.scale.set(1, 1.1, .4); face.add(p); pupils.push(p);
      const b = new THREE.Mesh(new THREE.CapsuleGeometry(.04, .24, 4, 8), dark); b.rotation.z = Math.PI / 2; b.position.set(sd * .33, .45, .86); face.add(b); brows.push(b);
      const xg = new THREE.Group(); xg.position.set(sd * .33, .12, .92);
      for (const a of [.8, -.8]) { const m = new THREE.Mesh(new THREE.BoxGeometry(.34, .06, .04), dark); m.rotation.z = a; xg.add(m); }
      face.add(xg); xs.push(xg);
      const ar = new THREE.Mesh(new THREE.TorusGeometry(.14, .035, 8, 20, Math.PI), dark); ar.position.set(sd * .33, .08, .9); face.add(ar); arcs.push(ar);
    }
    const mouth = new THREE.Mesh(new THREE.SphereGeometry(.16, 20, 14), dark); mouth.position.set(0, -.36, .84); mouth.scale.set(1, .25, .4); face.add(mouth);
    const sweat = [];
    for (const [x, y] of [[.95, .3], [-1.0, .05]]) { const d = new THREE.Mesh(new THREE.SphereGeometry(.11, 12, 10), M(0x7fd8ff, { transparent: true, opacity: .9 })); d.position.set(x, y, .4); d.scale.set(1, 1.5, 1); head.add(d); sweat.push(d); }
    // 腕・脚：肩／ひじ（腰／ひざ）の位置を軸にした入れ子
    function limb(len1, len2, rad, shoulder) {
      const a = new THREE.Group(); a.position.set(...shoulder); body.add(a);
      const u = new THREE.Mesh(new THREE.CapsuleGeometry(rad, len1, 6, 14), skin); u.position.y = -len1 / 2; a.add(u);
      const el = new THREE.Group(); el.position.y = -len1; a.add(el);
      const l = new THREE.Mesh(new THREE.CapsuleGeometry(rad, len2, 6, 14), skin); l.position.y = -len2 / 2; el.add(l);
      const h = new THREE.Mesh(new THREE.SphereGeometry(rad * 1.35, 16, 12), skin); h.position.y = -len2 - rad * .6; el.add(h);
      return { a, el };
    }
    const armL = limb(.55, .55, .17, [-.72, 2.3, 0]), armR = limb(.55, .55, .17, [.72, 2.3, 0]);
    const legL = limb(.5, .45, .22, [-.32, 1.1, 0]), legR = limb(.5, .45, .22, [.32, 1.1, 0]);
    O3 = { THREE, r, can, scene, cam, g, body, head, hair, eyes, pupils, brows, xs, arcs, mouth, sweat, armL, armR, legL, legR, face };
    return O3;
  }
  function omote3(ctx, x, y, s, o = {}) {
    if (!root.THREE) return omote(ctx, x, y, s, o); // three.js が無いレンダラーでは旧 2D 版
    const Q = O3 || o3init();
    const ex = o.expr || "normal", tk = clamp(o.talk || 0), lk = o.look || [0, 0];
    const big = ex === "shock" || ex === "panic";
    const yaw = o.yaw ?? (lk[0] >= 0 ? .32 : -.32);
    Q.g.rotation.set(0, yaw, -(o.rot || 0)); Q.g.scale.set(o.sx || 1, o.sy || 1, o.sx || 1);
    Q.body.rotation.set(0, 0, -(o.lean || 0));
    Q.head.rotation.set(lk[1] * .18, lk[0] * .25, 0);
    const al = o.armL ?? .25, ar = o.armR ?? .25;
    Q.armL.a.rotation.z = -al; Q.armL.el.rotation.z = -(o.elbowL ?? .2);
    Q.armR.a.rotation.z = ar; Q.armR.el.rotation.z = (o.elbowR ?? .2);
    Q.armL.a.visible = !o.noArmL;
    const lp = o.legs || 0;
    Q.legL.a.rotation.z = -.06 + .22 * Math.sin(lp); Q.legR.a.rotation.z = .06 + .22 * Math.sin(lp + Math.PI);
    Q.legL.el.rotation.z = Q.legR.el.rotation.z = 0;
    Q.hair.rotation.z = -(o.wind || 0) * .7;
    // 表情
    const eyeY = ex === "smug" ? .5 : ex === "deadpan" ? .38 : ex === "think" ? .8 : big ? 1.35 : 1.2;
    Q.eyes.forEach(e => { e.visible = ex !== "happy" && ex !== "dizzy"; e.scale.set(big ? 1.25 : 1, eyeY, .5); });
    Q.pupils.forEach((p, i) => {
      p.visible = ex !== "happy" && ex !== "dizzy";
      const sc = big ? .6 : 1;
      p.scale.set(sc, sc * Math.min(1.1, eyeY), .4);
      p.position.set((i ? .34 : -.34) + lk[0] * .08, .12 + lk[1] * -.07 + (ex === "think" ? .07 : 0), .95);
    });
    Q.xs.forEach(m => m.visible = ex === "dizzy");
    Q.arcs.forEach(m => m.visible = ex === "happy");
    const bh = big ? .6 : ex === "smug" ? .4 : ex === "deadpan" ? .36 : .46;
    Q.brows.forEach((b, i) => {
      const sd = i ? 1 : -1;
      b.position.y = bh + (ex === "smug" && sd > 0 ? .1 : 0);
      b.rotation.z = Math.PI / 2 + (ex === "think" ? sd * .25 : ex === "smug" ? (sd > 0 ? -.35 : .1) : big ? -sd * .25 : 0);
    });
    let mw = 1, mh = .25, mx = 0;
    if (big) { mw = .9 + .3 * tk; mh = .9 + .5 * tk + (ex === "panic" ? .3 : 0); }
    else if (ex === "happy") { mw = 1.5; mh = .7 + .3 * tk; }
    else if (tk > .08) { mw = 1.05; mh = .3 + 1.0 * tk; mx = ex === "smug" ? .1 : 0; }
    else if (ex === "smug") { mw = 1.1; mh = .18; mx = .12; }
    else if (ex === "deadpan" || ex === "think") { mw = 1.0; mh = .1; }
    Q.mouth.scale.set(mw, mh, .4); Q.mouth.position.x = mx;
    Q.sweat.forEach(d => d.visible = !!o.sweat);
    Q.r.render(Q.scene, Q.cam);
    // 足もと（原点）が (x, y) に来るように貼る。s＝1 で身長 約 560px
    const p = new Q.THREE.Vector3(0, 0, 0).project(Q.cam);
    const fx = (p.x + 1) / 2 * O3W, fy = (1 - p.y) / 2 * O3H;
    ctx.save(); ctx.globalAlpha *= (o.alpha ?? 1);
    if (!o.noShadow) { ctx.fillStyle = "rgba(10,30,60,.16)"; ctx.beginPath(); ctx.ellipse(x, y + 4 * s, 120 * s * (o.sx || 1), 18 * s, 0, 0, 7); ctx.fill(); }
    ctx.drawImage(Q.can, x - fx * s, y - fy * s, O3W * s, O3H * s);
    if (!NOCHAR && (o.alpha ?? 1) > .35) CHARLOG.push(screenBox(ctx, x - 110 * s * (o.sx || 1), y - 560 * s * (o.sy || 1), x + 110 * s * (o.sx || 1), y));
    ctx.restore();
  }

  // ---------------------------------------------------------------- ウラ：姿は出さない（声の波形だけ）
  function wipe2(ctx, t, who, cx, cy, r, o = {}) {
    if (who !== "W") return wipe(ctx, t, who, cx, cy, r, o);
    if (!speaking(t, "W")) return;
    r = Math.min(r, 125);
    const k = talk(t, "W"), w = r * 2.1, h = Math.max(50, r * .55);
    if ((o.alpha ?? 1) > .35) OBSLOG.push({ kind: "over_wave", box: screenBox(ctx, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2) });
    ctx.save(); ctx.globalAlpha *= clamp(o.alpha ?? 1);
    rrect(ctx, cx - w / 2, cy - h / 2, w, h, h / 2); ctx.fillStyle = "rgba(12,18,40,.72)"; ctx.fill();
    ctx.strokeStyle = C.ura; ctx.lineWidth = 3; ctx.stroke();
    const n = 18;
    for (let i = 0; i < n; i++) {
      const e = (.25 + .75 * k) * (.45 + .55 * Math.abs(Math.sin(i * 1.7 + t * 23)));
      const bh = (h - 18) * e, bx = cx - w / 2 + 26 + i * (w - 52) / (n - 1);
      ctx.fillStyle = i % 3 ? "#9B86FF" : "#3FF0FF"; ctx.fillRect(bx - 3, cy - bh / 2, 6, bh);
    }
    ctx.restore();
  }

  // ---------------------------------------------------------------- テクノの背景・HUD・カメラ・切り替え
  function mixHex(a, b, k) {
    const pa = parseInt(a.slice(1), 16), pb = parseInt(b.slice(1), 16);
    const ch = s => Math.round(((pa >> s) & 255) * (1 - k) + ((pb >> s) & 255) * k);
    return `rgb(${ch(16)},${ch(8)},${ch(0)})`;
  }
  // 明るいテクノの背景：白〜淡い寒色の地に、場面の色をわずかに混ぜ、遠近の格子と光
  function techBG(ctx, c1, c2, c3) {
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, mixHex("#F6FBFF", c1 || "#F6FBFF", .35)); g.addColorStop(.6, mixHex("#E4EEFF", c2 || c1 || "#E4EEFF", .35));
    g.addColorStop(1, mixHex("#D6E4FF", c3 || c2 || c1 || "#D6E4FF", .4));
    ctx.fillStyle = g; ctx.fillRect(-200, -200, W + 400, H + 400);
    const t = (TL && root.__t) || 0;
    ctx.save(); ctx.strokeStyle = "rgba(25,140,255,.13)"; ctx.lineWidth = 2;
    const hy = 1180, vx = W / 2;
    for (let i = -12; i <= 12; i++) { ctx.beginPath(); ctx.moveTo(vx + i * 30, hy); ctx.lineTo(vx + i * 260, H + 100); ctx.stroke(); }
    for (let k = 0; k < 9; k++) { const y = hy + Math.pow((k + (t * 1.2) % 1) / 9, 2) * (H - hy + 100); ctx.beginPath(); ctx.moveTo(-100, y); ctx.lineTo(W + 100, y); ctx.stroke(); }
    ctx.strokeStyle = "rgba(25,140,255,.07)";
    for (let x = 0; x <= W; x += 90) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, hy); ctx.stroke(); }
    for (let y = 0; y <= hy; y += 90) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
    const rg = ctx.createRadialGradient(W * .5, 620, 40, W * .5, 620, 760);
    rg.addColorStop(0, "rgba(63,240,255,.20)"); rg.addColorStop(1, "rgba(63,240,255,0)"); ctx.fillStyle = rg; ctx.fillRect(0, 0, W, H);
    ctx.restore();
  }
  // 画面の四隅の細い枠（テクノの世界観で全場面をそろえる）
  function hud(ctx, t) {
    ctx.save(); ctx.strokeStyle = "rgba(25,160,255,.55)"; ctx.lineWidth = 4; const m = 28, L = 70;
    for (const [x, y, dx, dy] of [[m, m, 1, 1], [W - m, m, -1, 1], [m, H - m, 1, -1], [W - m, H - m, -1, -1]]) {
      ctx.beginPath(); ctx.moveTo(x, y + dy * L); ctx.lineTo(x, y); ctx.lineTo(x + dx * L, y); ctx.stroke();
    }
    const sy = (t * 520) % (H + 300) - 150;
    const g = ctx.createLinearGradient(0, sy - 60, 0, sy + 60); g.addColorStop(0, "rgba(63,240,255,0)"); g.addColorStop(.5, "rgba(63,240,255,.10)"); g.addColorStop(1, "rgba(63,240,255,0)");
    ctx.fillStyle = g; ctx.fillRect(0, sy - 60, W, 120);
    ctx.restore();
  }
  // カメラ：場面ごとのゆっくりした寄り＋衝撃の瞬間のパンチズームと揺れ。bg と ui の両方に同じ変換をかける
  function camera(ctxs, t, sceneStart, sceneEnd, hits = [], focus = [W / 2, 760]) {
    const push = 1 + .035 * easeInOut(clamp((t - sceneStart) / Math.max(.5, sceneEnd - sceneStart)));
    let punch = 0, shake = 0;
    for (const h of hits) { const d = t - h; if (d >= 0 && d < .6) { punch = Math.max(punch, .07 * Math.exp(-d / .12)); shake = Math.max(shake, 14 * Math.exp(-d / .1)); } }
    const z = push + punch, sx = shake * Math.sin(t * 91), sy = shake * Math.cos(t * 73);
    for (const c of ctxs) { c.setTransform(z, 0, 0, z, focus[0] * (1 - z) + sx, focus[1] * (1 - z) + sy); }
  }
  function resetCam(ctxs) { for (const c of ctxs) c.setTransform(1, 0, 0, 1, 0, 0); }
  // 場面の切り替え：横に流れる光の筋（ホワイトフラッシュの代わり）
  function whip(ctx, k, seed = 1) {
    if (k <= 0) return;
    const r = rng(seed);
    ctx.save(); ctx.globalAlpha = clamp(k);
    ctx.fillStyle = "rgba(255,255,255,.55)"; ctx.fillRect(0, 0, W, H);
    for (let i = 0; i < 22; i++) {
      const y = r() * H, h = 4 + r() * 26, x = (1 - k) * W * (r() < .5 ? 1 : -1) * 0.6;
      ctx.fillStyle = i % 3 ? "rgba(63,240,255,.75)" : "rgba(255,79,216,.6)"; ctx.fillRect(x - 200, y, W + 400, h);
    }
    ctx.restore();
  }
  // 字幕（テクノ版）：暗いガラスの帯に、話者の色の細い発光線
  function subtitles2(ctx, t, cy = 1475) {  // オモテの足もと（y≈1330）と重ならない高さ
    const line = currentLine(t);
    if (!line || t >= TL.ending_start) return;
    const rows = subChunk(line, t).split(" / ");
    let size = 58;
    const cx = 490, maxW = 780; // 右側のボタン列（x≥950）と画面の端を避ける
    ctx.font = `800 ${size}px ${FONT}`;
    let wmax = Math.max(...rows.map(r => ctx.measureText(r.replace(/\*\*/g, "")).width));
    if (wmax > maxW) { size = Math.floor(size * maxW / wmax); ctx.font = `800 ${size}px ${FONT}`; wmax = maxW; }
    if (size < 44) TEXTLOG.push({ s: rows.join(""), box: [0, 0, 0, 0], size, group: -1, container: null, ignore: false, small_sub: true });
    const lh = size * 1.34, bw = Math.min(850, wmax + 64), bh = rows.length * lh + 30;
    const k = easeOut(prog(t, line.start - .04, .1));
    const col = line.who === "M" ? C.omote : "#8C74FF";
    ctx.save(); ctx.globalAlpha = k; ctx.translate(0, 12 * (1 - k));
    ctx.shadowColor = hexA(col, .55); ctx.shadowBlur = 26;
    rrect(ctx, cx - bw / 2, cy - bh / 2, bw, bh, 18); ctx.fillStyle = "rgba(10,16,34,.86)"; ctx.fill();
    ctx.shadowColor = "transparent"; ctx.strokeStyle = col; ctx.lineWidth = 3; ctx.stroke();
    group(() => rows.forEach((r, i) => rich(ctx, r, cx, cy - (rows.length - 1) * lh / 2 + i * lh + 2, size, "#FFFFFF", "#3FF0FF")),
      screenBox(ctx, cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2));
    const name = (TL.names || {})[line.who] || line.who;
    ctx.font = `900 30px ${FONT}`; const tw = ctx.measureText(name).width + 40;
    rrect(ctx, cx - bw / 2 + 18, cy - bh / 2 - 22, tw, 44, 10); ctx.fillStyle = col; ctx.fill();
    group(() => text(ctx, name, cx - bw / 2 + 18 + tw / 2, cy - bh / 2 + 1, 30, "#FFFFFF", { weight: 900 }));
    ctx.restore();
  }
  function header2(ctx) {
    // 左上の固定ロゴ：2026-10-27 の標準（REVERSE_STANDARD_RULES v2）から表示しない。制作設定の "logo"（既定 False）が
    // タイムラインに入る。"logo" のない旧版のタイムライン（pilot_009 まで・pilot_010）は従来どおり表示する
    if (TL && TL.logo === false) return;
    ctx.__noCheck = true; try { header2_(ctx); } finally { ctx.__noCheck = false; }
  }
  function header2_(ctx) {
    ctx.save(); rrect(ctx, 40, 92, 250, 62, 14); ctx.fillStyle = "rgba(10,16,34,.78)"; ctx.fill();
    ctx.strokeStyle = "#3FF0FF"; ctx.lineWidth = 2.5; ctx.stroke(); ctx.restore();
    rewindIcon(ctx, 82, 123, 17, "#3FF0FF");
    text(ctx, "リバース", 112, 124, 34, "#FFFFFF", { align: "left", weight: 900 });
  }


  // ---------------------------------------------------------------- オモテ（顔のない、もちもちした人型ピクトグラム）2026-10-27〜
  // 目・口・鼻・眉・耳は一切つけない。感情は全身の動き（傾き・うなずき・乗り出し・硬直）と、立体の汗のしずくで出す。
  // 3D の場面に直接置くための部品：mochi3D(THREE) → { g, pose(o), box(camera, W, H) }。単位はメートル（身長 約 1.6 m）。原点は足もと。
  function mochi3D(THREE, opt = {}) {
    const col = new THREE.Color(opt.color || 0xd5dbe4).convertSRGBToLinear();
    const mat = new THREE.MeshStandardMaterial({ color: col, roughness: .62, metalness: 0, emissive: col, emissiveIntensity: .03 });
    const cap = (r, l) => { const m = new THREE.Mesh(new THREE.CapsuleGeometry(r, l, 10, 24), mat); m.castShadow = true; m.receiveShadow = true; return m; };
    const g = new THREE.Group(), body = new THREE.Group(); g.add(body);
    const hips = new THREE.Group(); hips.position.y = .62; body.add(hips);              // 上半身はここを軸に傾く
    const torso = cap(.235, .3); torso.position.y = .3; torso.scale.set(1.05, 1, .9); hips.add(torso);
    const neck = new THREE.Group(); neck.position.y = .66; hips.add(neck);
    const head = new THREE.Group(); head.position.y = .2; neck.add(head);
    const skull = new THREE.Mesh(new THREE.SphereGeometry(.205, 40, 30), mat); skull.scale.set(1.04, .98, 1); skull.castShadow = true; head.add(skull);
    const limb = (parent, x, y, r, l1, l2) => {                                       // 付け根 → 上 → 関節 → 下（先は丸い）
      const a = new THREE.Group(); a.position.set(x, y, 0); parent.add(a);
      const u = cap(r, l1); u.position.y = -l1 / 2 - r * .3; a.add(u);
      const el = new THREE.Group(); el.position.y = -l1 - r * .5; a.add(el);
      const d = cap(r * .95, l2); d.position.y = -l2 / 2 - r * .2; el.add(d);
      return { a, el };
    };
    const armL = limb(hips, -.29, .56, .075, .2, .2), armR = limb(hips, .29, .56, .075, .2, .2);
    const legL = limb(body, -.11, .64, .095, .22, .2), legR = limb(body, .11, .64, .095, .22, .2);
    // 立体の汗のしずく（頭の横に現れて落ちる）
    const dropMat = new THREE.MeshStandardMaterial({ color: 0xbfe6ff, roughness: .1, metalness: 0, transparent: true, opacity: .85 });
    const drop = new THREE.Group(); head.add(drop);
    const ds = new THREE.Mesh(new THREE.SphereGeometry(.035, 16, 12), dropMat); drop.add(ds);
    const dc = new THREE.Mesh(new THREE.ConeGeometry(.033, .06, 16), dropMat); dc.position.y = .04; drop.add(dc);
    function pose(o = {}) {
      g.position.set(o.x || 0, o.y || 0, o.z || 0); g.rotation.set(0, o.yaw || 0, 0);
      g.scale.set(o.sx || 1, o.sy || 1, o.sx || 1);
      hips.rotation.set(o.lean || 0, 0, o.side || 0);                                  // lean＞0：前に乗り出す
      head.rotation.set(o.nod || 0, o.look || 0, o.tilt || 0);                          // tilt：首をかしげる
      const ph = o.walk || 0, st = o.stride ?? .35;
      legL.a.rotation.x = Math.sin(ph) * st; legR.a.rotation.x = -Math.sin(ph) * st;
      legL.el.rotation.x = Math.max(0, -Math.sin(ph)) * st * 1.2; legR.el.rotation.x = Math.max(0, Math.sin(ph)) * st * 1.2;
      body.position.y = o.walk ? Math.abs(Math.cos(ph)) * .02 : 0;
      const sw = o.walk ? Math.sin(ph) * .3 : 0;
      armL.a.rotation.set(-(o.armFL ?? 0) + sw, 0, -(o.armL ?? .12)); armR.a.rotation.set(-(o.armFR ?? 0) - sw, 0, (o.armR ?? .12));
      armL.el.rotation.x = -(o.elbowL ?? .15); armR.el.rotation.x = -(o.elbowR ?? .15);
      const k = o.sweat || 0; drop.visible = k > 0 && k < 1;                           // 0→1：現れて、頬の横を落ちる
      drop.position.set(.22, .1 - .25 * Math.max(0, k - .35) / .65, .05); dropMat.opacity = .85 * Math.min(1, k * 4, (1 - k) * 5);
    }
    const tmp = new THREE.Vector3();
    function box(camera, W, H) {                                                       // 画面上のおおよその範囲（文字の検査用）
      g.updateMatrixWorld(true);
      const pts = [[0, 0, 0], [0, 1.62, 0], [-.4, .9, 0], [.4, .9, 0], [0, .9, .3], [0, .9, -.3]];
      let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
      for (const p of pts) { tmp.set(...p).applyMatrix4(g.matrixWorld).project(camera); if (tmp.z > 1) return null;
        const x = (tmp.x + 1) / 2 * W, y = (1 - tmp.y) / 2 * H; x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); }
      return [x0, y0, x1, y1];
    }
    pose({});
    return { g, pose, box, mat };
  }

  root.Stage = {
    W, H, FONT, C, clamp, lerp, easeOut, easeIn, easeInOut, back, elastic, prog, win, rng, hexA,
    text, rrect, pill, rich, note, setup, sceneRange, sceneAt, currentLine, talk, speaking, subtitles: subtitles2, header: header2, rewindIcon,
    omote: omote3, omote2d: omote, omotePixel, uraBust, wipe: wipe2, speedLines, burst, bigX, bigO, arrow, vhs, glitch, flash, gradientBG: techBG, dots, rays,
    techBG, hud, camera, resetCam, whip, mixHex, panel, group, checkText, mochi3D, TEXTLOG, CHARLOG, clearTextLog: () => { TEXTLOG.length = 0; CHARLOG.length = 0; OBSLOG.length = 0; }, subtitlesOld: subtitles, headerOld: header, gradientOld: gradientBG,
    get TL() { return TL; }, get CUE() { return CUE; },
  };
})(typeof window !== "undefined" ? window : globalThis);
