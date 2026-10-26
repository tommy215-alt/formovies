// manual.html を PDF にする: node anatomy_room/docs/manual/build_manual.js
const { chromium } = require("playwright");
const path = require("path");
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto("file://" + path.join(__dirname, "manual.html"));
  await p.evaluate(() => document.fonts.ready);
  await p.pdf({ path: path.join(__dirname, "shorts_manual.pdf"), format: "A4", printBackground: true, preferCSSPageSize: true });
  await b.close();
  console.log("shorts_manual.pdf");
})();
