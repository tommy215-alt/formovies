// アイコンとヘッダーを PNG に書き出す: node anatomy_room/branding/render.js
const { chromium } = require("playwright");
const path = require("path");
const { cubeMark } = require("./mark");

const C = { bg: "#0A1424", bg2: "#10203A", grid: "#1C3150", line: "#46D3F0", text: "#EEF4FA", sub: "#9FC3D9" };
const FONT = "'Noto Sans CJK JP','Noto Sans JP',sans-serif";
const MONO = "'Noto Sans Mono CJK JP',monospace";

function page(w, h, svg) {
  return `<!doctype html><meta charset="utf-8"><style>html,body{margin:0;background:${C.bg}}svg{display:block}</style>
  <svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${svg}</svg>`;
}

function dotGrid(w, h, step, r, color, op) {
  return `<defs><pattern id="dots" width="${step}" height="${step}" patternUnits="userSpaceOnUse">
    <circle cx="${step / 2}" cy="${step / 2}" r="${r}" fill="${color}" opacity="${op}"/></pattern></defs>
    <rect width="${w}" height="${h}" fill="url(#dots)"/>`;
}

function icon() {
  const w = 800;
  return page(w, w, `
    <defs><radialGradient id="g" cx="50%" cy="45%" r="60%">
      <stop offset="0" stop-color="${C.bg2}"/><stop offset="1" stop-color="${C.bg}"/></radialGradient></defs>
    <rect width="${w}" height="${w}" fill="url(#g)"/>
    ${dotGrid(w, w, 40, 2, C.grid, 0.9).replace('id="dots"', 'id="dots"')}
    ${cubeMark({ cx: 378, cy: 404, s: 215, line: C.line, bg: C.bg })}`);
}

function header(safeGuide = false) {
  const W = 2560, H = 1440;
  // YouTube の安全領域（全デバイスで表示）: 1546×423 を中央に
  const sx = (W - 1546) / 2, sy = (H - 423) / 2;
  // 定規の目盛り（「解剖・計測」のモチーフ）
  let ticks = "";
  for (let x = 0; x <= W; x += 16) {
    const long = x % 160 === 0, midT = x % 80 === 0;
    const len = long ? 26 : midT ? 16 : 9;
    ticks += `<line x1="${x}" y1="${sy + 423 + 40}" x2="${x}" y2="${sy + 423 + 40 + len}" stroke="${C.line}" stroke-opacity="${long ? 0.55 : 0.28}" stroke-width="2"/>`;
  }
  const guide = safeGuide ? `
    <rect x="${sx}" y="${sy}" width="1546" height="423" fill="none" stroke="#FF5A7A" stroke-width="4" stroke-dasharray="16 10"/>
    <text x="${sx + 12}" y="${sy - 14}" fill="#FF5A7A" font-family="${MONO}" font-size="28">safe area 1546×423（全デバイスで表示）</text>
    <rect x="${(W - 2560) / 2}" y="${(H - 423) / 2}" width="2560" height="423" fill="none" stroke="#FFC24A" stroke-width="3" stroke-dasharray="8 8"/>
    <text x="16" y="${sy - 14}" fill="#FFC24A" font-family="${MONO}" font-size="28">desktop 2560×423</text>` : "";
  return page(W, H, `
    <defs><linearGradient id="hg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="${C.bg2}"/><stop offset="0.6" stop-color="${C.bg}"/></linearGradient></defs>
    <rect width="${W}" height="${H}" fill="url(#hg)"/>
    ${dotGrid(W, H, 48, 2.2, C.grid, 0.85)}
    <line x1="0" y1="${sy - 40}" x2="${W}" y2="${sy - 40}" stroke="${C.line}" stroke-opacity="0.18" stroke-width="2"/>
    ${ticks}
    ${cubeMark({ cx: sx + 205, cy: sy + 215, s: 150, line: C.line, bg: C.bg })}
    <text x="${sx + 440}" y="${sy + 150}" fill="${C.sub}" font-family="${MONO}" font-size="34" letter-spacing="10">THE ANATOMY ROOM</text>
    <text x="${sx + 432}" y="${sy + 268}" fill="${C.text}" font-family="${FONT}" font-weight="700" font-size="128" letter-spacing="6">世界の解剖室</text>
    <text x="${sx + 440}" y="${sy + 345}" fill="${C.line}" font-family="${FONT}" font-weight="500" font-size="48" letter-spacing="4">見えない仕組みを、CGで解き明かす。</text>
    ${guide}`);
}

(async () => {
  const out = __dirname;
  const browser = await chromium.launch();
  const shots = [
    ["icon_800.png", 800, 800, icon()],
    ["header_2560x1440.png", 2560, 1440, header(false)],
    ["header_safe_area_guide.png", 2560, 1440, header(true)],
  ];
  for (const [name, w, h, html] of shots) {
    const p = await browser.newPage({ viewport: { width: w, height: h } });
    await p.setContent(html);
    await p.evaluate(() => document.fonts.ready);
    await p.screenshot({ path: path.join(out, name) });
    await p.close();
    console.log("wrote", name);
  }
  // 小さく表示したときの見え方の確認用（丸く切り抜き、実寸に近いサイズ）
  const b64 = require("fs").readFileSync(path.join(out, "icon_800.png")).toString("base64");
  const p = await browser.newPage({ viewport: { width: 420, height: 180 } });
  await p.setContent(`<body style="margin:0;background:#fff;display:flex;gap:28px;align-items:center;padding:20px;font-family:sans-serif">
    ${[160, 88, 48, 32].map(s => `<img src="data:image/png;base64,${b64}" style="width:${s}px;height:${s}px;border-radius:50%">`).join("")}</body>`);
  await p.screenshot({ path: path.join(out, "icon_preview_sizes.png") });
  await browser.close();
  console.log("wrote icon_preview_sizes.png");
})();
