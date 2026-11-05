// layouts.html の 10 案を thumb/out/L<番号>.png に書き出し、一覧 compare_layouts.jpg 用の素材にする。node thumb/shoot_layouts.js
const { chromium } = require("playwright");
const path = require("path");
const fs = require("fs");
const { pathToFileURL } = require("url");
(async () => {
  const b = await chromium.launch();
  fs.mkdirSync(path.join(__dirname, "out"), { recursive: true });
  for (let l = 1; l <= 10; l++) {
    const p = await b.newPage({ viewport: { width: 2560, height: 1440 } });
    await p.goto(pathToFileURL(path.join(__dirname, "layouts.html")).href + "?l=" + l);
    await p.waitForFunction(() => window.DONE === true, null, { timeout: 60000 });
    const png = await p.screenshot({ clip: { x: 0, y: 0, width: 2560, height: 1440 } });
    const p2 = await b.newPage({ viewport: { width: 1280, height: 720 } });
    await p2.setContent(`<body style="margin:0"><img src="data:image/png;base64,${png.toString("base64")}" style="width:1280px;height:720px;display:block"></body>`);
    await p2.screenshot({ path: path.join(__dirname, "out", `L${l}.png`), clip: { x: 0, y: 0, width: 1280, height: 720 } });
    await p.close(); await p2.close(); console.log("L" + l);
  }
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
