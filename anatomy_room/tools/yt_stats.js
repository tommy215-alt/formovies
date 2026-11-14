// 読み取り専用：YouTube Studio の一覧と各動画のアナリティクスの文字を保存する（何も変更しない。2026-11-15、新もしも設計の確認用）
//   node anatomy_room/tools/yt_stats.js   → anatomy_room/publish/stats/<日付>/（rows.json・各動画の画面の文字）。表は python anatomy_room/tools/yt_stats_table.py <日付>
const fs = require("fs"), path = require("path");
const REPO = path.join(__dirname, "..");
const { chromium } = require(path.join(REPO, "node_modules", "playwright"));
const PROFILE = path.join(process.env.LOCALAPPDATA, "reverse_yt_profile");
const OUT = path.join(REPO, "publish", "stats", new Date().toISOString().slice(0, 10));
fs.mkdirSync(OUT, { recursive: true });
const wait = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const ctx = await chromium.launchPersistentContext(PROFILE, {
    headless: false, executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", viewport: { width: 1600, height: 1200 },
    locale: "ja-JP", timezoneId: "Asia/Tokyo", ignoreDefaultArgs: ["--enable-automation"],
    args: ["--disable-blink-features=AutomationControlled", "--window-position=-32000,-32000"] });
  const page = ctx.pages()[0] || await ctx.newPage();
  try {
    await page.goto("https://studio.youtube.com/"); await wait(5000);
    const ch = page.url().match(/channel\/([^/?#]+)/)[1];
    // チャンネル全体（28 日・90 日）
    for (const [name, u] of [["ch_overview", `https://studio.youtube.com/channel/${ch}/analytics/tab-overview/period-default`],
                             ["ch_content", `https://studio.youtube.com/channel/${ch}/analytics/tab-content/period-default`],
                             ["ch_content_shorts", `https://studio.youtube.com/channel/${ch}/analytics/tab-content/period-default/explore?entity_type=CHANNEL&entity_id=${ch}&r_content_type=SHORTS`],
                             ["ch_audience", `https://studio.youtube.com/channel/${ch}/analytics/tab-build_audience/period-default`]]) {
      if (fs.existsSync(path.join(OUT, name + ".txt"))) continue;
      await page.goto(u); await wait(8000);
      fs.writeFileSync(path.join(OUT, name + ".txt"), await page.locator("body").innerText());
      await page.screenshot({ path: path.join(OUT, name + ".png"), fullPage: true });
    }
    // 一覧（ショート・動画）
    const rows = [];
    for (const tab of ["short", "upload"]) {
      await page.goto(`https://studio.youtube.com/channel/${ch}/videos/${tab}?filter=%5B%5D&sort=%7B%22columnType%22%3A%22date%22%2C%22sortOrder%22%3A%22DESCENDING%22%7D`); await wait(7000);
      // ページの行数を増やす
      for (let k = 0; k < 3; k++) {
        const n = await page.locator("ytcp-video-row").count();
        for (const r of await page.locator("ytcp-video-row").all()) {
          const href = await r.locator("a[href*='/video/']").first().getAttribute("href").catch(() => null); if (!href) continue;
          const id = href.match(/video\/([^/]+)/)[1];
          if (rows.find(x => x.id === id)) continue;
          rows.push({ tab, id, text: (await r.innerText()).replace(/\s*\n\s*/g, " | ") });
        }
        const next = page.locator("#navigate-after:not([disabled])").first();
        if (n && await next.isVisible().catch(() => false)) { if (!(await next.click({ timeout: 5000 }).then(() => true).catch(() => false))) break; await wait(5000); } else break;
      }
    }
    fs.writeFileSync(path.join(OUT, "rows.json"), JSON.stringify(rows, null, 1));
    // 各動画のアナリティクス（公開済みのもの）
    for (const r of rows) {
      if (/予約|非公開|Private|Scheduled/.test(r.text) && !/公開/.test(r.text.replace(/非公開/g, ""))) continue;
      for (const tab of ["tab-overview", "tab-reach_viewers", "tab-interest_viewers"]) {
        await page.goto(`https://studio.youtube.com/video/${r.id}/analytics/${tab}/period-default`); await wait(7000);
        fs.writeFileSync(path.join(OUT, `${r.id}_${tab}.txt`), await page.locator("body").innerText());
        if (tab === "tab-interest_viewers") await page.screenshot({ path: path.join(OUT, `${r.id}_${tab}.png`) });
      }
      console.log("ok", r.id);
    }
  } finally { await ctx.close(); }
})().catch(e => { console.error(e); process.exit(1); });
