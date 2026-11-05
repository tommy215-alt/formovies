// thumb.html を撮る。node thumb/shoot.js [字体…]（long_001 のフォルダで）
//   字体を指定しない：既定の字体で thumbnail_youtube.png（1280×720）
//   字体を指定する：thumb/out/<字体>.png を字体ごとに書き出す（比較用）
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
(async () => {
  const fonts = process.argv.slice(2);
  const b = await chromium.launch();
  const jobs = fonts.length ? fonts.map(f => [f, path.join(__dirname, "out", f + ".png")]) : [[null, path.join(__dirname, "..", "thumbnail_youtube.png")]];
  fs.mkdirSync(path.join(__dirname, "out"), { recursive: true });
  for (const [font, out] of jobs) {
    const p = await b.newPage({ viewport: { width: 2560, height: 1440 } });
    await p.goto(pathToFileURL(path.join(__dirname, "thumb.html")).href + (font ? "?font=" + font : ""));
    await p.waitForFunction(() => window.DONE === true, null, { timeout: 60000 });
    const png = await p.screenshot({ clip: { x: 0, y: 0, width: 2560, height: 1440 } });
    const p2 = await b.newPage({ viewport: { width: 1280, height: 720 } });
    await p2.setContent(`<body style="margin:0"><img src="data:image/png;base64,${png.toString("base64")}" style="width:1280px;height:720px;display:block"></body>`);
    await p2.screenshot({ path: out, clip: { x: 0, y: 0, width: 1280, height: 720 } });
    await p.close(); await p2.close();
    console.log(path.basename(out));
  }
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
