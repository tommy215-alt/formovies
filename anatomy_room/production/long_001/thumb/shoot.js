// thumb.html を撮って thumbnail_youtube.png（1280×720）にする。node thumb/shoot.js（long_001 のフォルダで）
const { chromium } = require("playwright");
const path = require("path");
const { pathToFileURL } = require("url");
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 2560, height: 1440 } });
  await p.goto(pathToFileURL(path.join(__dirname, "thumb.html")).href);
  await p.waitForFunction(() => window.DONE === true, null, { timeout: 60000 });
  const png = await p.screenshot({ clip: { x: 0, y: 0, width: 2560, height: 1440 } });
  const p2 = await b.newPage({ viewport: { width: 1280, height: 720 } });
  await p2.setContent(`<body style="margin:0"><img src="data:image/png;base64,${png.toString("base64")}" style="width:1280px;height:720px;display:block"></body>`);
  await p2.screenshot({ path: path.join(__dirname, "..", "thumbnail_youtube.png"), clip: { x: 0, y: 0, width: 1280, height: 720 } });
  await b.close();
  console.log("thumbnail_youtube.png");
})().catch(e => { console.error(e); process.exit(1); });
