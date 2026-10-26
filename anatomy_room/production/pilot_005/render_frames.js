// renderer.html を Playwright で 1 コマずつ撮影し、ffmpeg で work/video.mp4 に書き出す。
//   node render_frames.js                  全コマを書き出す
//   node render_frames.js --stills 3,40.5  指定した秒のコマを work/stills/ に PNG で保存（確認用）
//   node render_frames.js --thumb          サムネイル thumbnail.png を書き出す
//   node render_frames.js --segments job.json  指定したコマの範囲を場面ごとの mp4 に（production_script.py render が使う）
const { chromium } = require("playwright");
const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");

const HERE = __dirname, WORK = path.join(HERE, "work");
const tl = JSON.parse(fs.readFileSync(path.join(WORK, "timeline.json"), "utf8"));
const args = process.argv.slice(2);

async function open(browser) {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on("pageerror", e => { console.error("page error:", e.message); process.exit(1); });
  await page.goto("file://" + path.join(HERE, "renderer.html"));
  await page.evaluate(async t => {
    await Promise.all(["700 52px \"Noto Sans CJK JP\"", "500 40px \"Noto Sans CJK JP\"", "400 28px \"Noto Sans CJK JP\""]
      .map(f => document.fonts.load(f, "あ漢A−×")));
    window.setTimeline(t);
  }, tl);
  const ok = await page.evaluate(() => document.fonts.check("700 52px \"Noto Sans CJK JP\"", "あ"));
  if (!ok) throw new Error("Noto Sans CJK JP が読み込めない");
  return page;
}

(async () => {
  const browser = await chromium.launch();
  const page = await open(browser);
  const canvas = await page.$("canvas");
  if (args[0] === "--stills") {
    fs.mkdirSync(path.join(WORK, "stills"), { recursive: true });
    for (const s of args[1].split(",")) {
      await page.evaluate(t => window.renderFrame(t), parseFloat(s));
      await canvas.screenshot({ path: path.join(WORK, "stills", `t${parseFloat(s).toFixed(2).padStart(6, "0")}.png`) });
    }
    console.log("stills:", args[1]);
  } else if (args[0] === "--segments") {
    // 指定されたコマの範囲を、場面ごとに別の mp4 に書き出す（production_script.py render から呼ばれる）
    const jobs = JSON.parse(fs.readFileSync(args[1], "utf8"));
    for (const s of jobs) {
      const tmp = s.out + ".part.mp4";
      const ff = spawn("ffmpeg", ["-y", "-hide_banner", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(tl.fps),
        "-c:v", "png", "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-r", String(tl.fps), tmp], { stdio: ["pipe", "inherit", "inherit"] });
      const t0 = Date.now();
      for (let i = s.a; i < s.b; i++) {
        await page.evaluate(t => window.renderFrame(t), i / tl.fps);
        const buf = await canvas.screenshot({ type: "png" });
        if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
      }
      ff.stdin.end();
      await new Promise((res, rej) => ff.on("close", c => c === 0 ? res() : rej(new Error("ffmpeg " + c))));
      fs.renameSync(tmp, s.out); // 書き終わってから名前を付ける（途中で止まっても壊れた場面を再利用しない）
      console.log(`segment ${s.a}-${s.b} (${s.b - s.a} frames) in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    }
  } else if (args[0] === "--thumb") {
    await page.evaluate(() => window.renderThumb());
    await canvas.screenshot({ path: path.join(HERE, "thumbnail.png") });
    console.log("thumbnail.png");
  } else {
    const n = Math.ceil(tl.duration * tl.fps);
    const ff = spawn("ffmpeg", ["-y", "-hide_banner", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(tl.fps),
      "-c:v", "png", "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
      "-r", String(tl.fps), "-movflags", "+faststart", path.join(WORK, "video.mp4")], { stdio: ["pipe", "inherit", "inherit"] });
    const t0 = Date.now();
    for (let i = 0; i < n; i++) {
      await page.evaluate(t => window.renderFrame(t), i / tl.fps);
      const buf = await canvas.screenshot({ type: "png" });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
      if (i % 150 === 0) console.log(`frame ${i}/${n} (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
    }
    ff.stdin.end();
    await new Promise((res, rej) => ff.on("close", c => c === 0 ? res() : rej(new Error("ffmpeg " + c))));
    console.log(`video: ${n} frames in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
