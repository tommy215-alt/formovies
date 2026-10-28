// 各話の renderer.html を Playwright で 1 コマずつ撮影し、ffmpeg で動画にする。
//   node render_frames.js                  全コマを書き出す
//   node render_frames.js --stills 3,40.5  指定した秒のコマを work/stills/ に PNG で保存（確認用）
//   node render_frames.js --thumb          サムネイル thumbnail.png を書き出す
//   node render_frames.js --segments job.json  指定したコマの範囲を場面ごとの mp4 に（production_script.py render が使う）
//   node render_frames.js --clip 58,66 out.mp4  指定した秒の範囲だけを mp4 に（音なし。比較・試し書き出し用）
//   --renderer <ファイル名>  renderer.html の代わりに別の描画ファイルを使う（比較用。省略時は renderer.html）
// GPU：既定（REVERSE_GPU=auto）は GPU で WebGL が動けば GPU、動かなければソフトウェア描画（SwiftShader）。
//   REVERSE_GPU=off でいつも SwiftShader、REVERSE_GPU=on で GPU が使えなければ止める。
const { chromium } = require("playwright");
const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");

// 第 3 話以降の共通版。node ../common/render_frames.js --dir <各話のフォルダ> [--stills … | --thumb | --segments …]
const argv = process.argv.slice(2);
const di = argv.indexOf("--dir");
const HERE = di >= 0 ? path.resolve(argv[di + 1]) : process.cwd(), WORK = path.join(HERE, "work");
const tl = JSON.parse(fs.readFileSync(path.join(WORK, "timeline.json"), "utf8"));
let args = di >= 0 ? argv.filter((_, i) => i !== di && i !== di + 1) : argv;
const ri = args.indexOf("--renderer");
const RENDERER = ri >= 0 ? args[ri + 1] : "renderer.html";
if (ri >= 0) args = args.filter((_, i) => i !== ri && i !== ri + 1);

async function open(browser) {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on("pageerror", e => { console.error("page error:", e.message); process.exit(1); });
  await page.goto(pathToFileURL(path.join(HERE, RENDERER)).href); // Windows のパスでも正しい URL にする
  await page.evaluate(async t => {
    await Promise.all(["900 52px \"Noto Sans CJK JP\"", "800 52px \"Noto Sans CJK JP\"", "700 52px \"Noto Sans CJK JP\"", "500 40px \"Noto Sans CJK JP\""]
      .map(f => document.fonts.load(f, "あ漢A−×")));
    window.setTimeline(t);
  }, tl);
  const ok = await page.evaluate(() => document.fonts.check("700 52px \"Noto Sans CJK JP\"", "あ"));
  if (!ok) throw new Error("Noto Sans CJK JP が読み込めない");
  return page;
}

const SOFTWARE = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"];

async function renderer(browser) {
  const page = await browser.newPage();
  const r = await page.evaluate(() => {
    const g = document.createElement("canvas").getContext("webgl2") || document.createElement("canvas").getContext("webgl");
    if (!g) return "";
    const e = g.getExtension("WEBGL_debug_renderer_info");
    return String(e ? g.getParameter(e.UNMASKED_RENDERER_WEBGL) : g.getParameter(g.RENDERER));
  });
  await page.close();
  return r;
}

// GPU を試し、WebGL がソフトウェア描画（SwiftShader・llvmpipe）になったら SwiftShader の設定で開き直す
async function launch() {
  const mode = (process.env.REVERSE_GPU || "auto").toLowerCase();
  if (mode !== "off") {
    try {
      // channel "chromium" は通常版の Chromium（新しいヘッドレス）。ヘッドレス専用版は GPU を使わない
      const b = await chromium.launch({ channel: "chromium", args: ["--ignore-gpu-blocklist", "--enable-gpu-rasterization"] });
      const r = await renderer(b);
      if (r && !/swiftshader|llvmpipe|software/i.test(r)) {
        console.error("WebGL: GPU（" + r + "）");
        return b;
      }
      await b.close();
      if (mode === "on") throw new Error("GPU で WebGL が動かない（" + (r || "WebGL なし") + "）");
    } catch (e) {
      if (mode === "on") throw e;
    }
  }
  const b = await chromium.launch({ args: SOFTWARE });
  console.error("WebGL: ソフトウェア描画（" + await renderer(b) + "）");
  return b;
}

(async () => {
  const browser = await launch();
  const page = await open(browser);
  const stage = await page.$("#stage"); // 背景・3D・文字の 3 層を重ねた画面全体
  // 撮影は画面の範囲を決めて撮る（要素の撮影は「動きが止まるまで待つ」確認が 30 秒で切れて止まることがあった：Windows・GPU）
  const box = await stage.boundingBox();
  const canvas = {
    async screenshot(o) {
      for (let k = 0; ; k++) {
        try {
          return await page.screenshot({ ...o, clip: box, timeout: 120000 });
        } catch (e) {
          if (k >= 2) throw e;
          console.error("screenshot: 撮り直し（" + e.message.split("\n")[0] + "）");
        }
      }
    },
  };
  if (args[0] === "--stills") {
    fs.mkdirSync(path.join(WORK, "stills"), { recursive: true });
    const ts = args[1].split(","), t0 = Date.now();
    for (const s of ts) {
      await page.evaluate(t => window.renderFrame(t), parseFloat(s));
      await canvas.screenshot({ path: path.join(WORK, "stills", `t${parseFloat(s).toFixed(2).padStart(6, "0")}.png`) });
    }
    console.log(`stills: ${args[1]}（1 コマあたり ${((Date.now() - t0) / 1000 / ts.length).toFixed(2)} 秒）`);
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
  } else if (args[0] === "--clip") {
    const [a, b] = args[1].split(",").map(parseFloat), out = path.resolve(args[2]), t0 = Date.now();
    const ff = spawn("ffmpeg", ["-y", "-hide_banner", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(tl.fps),
      "-c:v", "png", "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", String(tl.fps), out], { stdio: ["pipe", "inherit", "inherit"] });
    const i0 = Math.round(a * tl.fps), i1 = Math.round(b * tl.fps);
    for (let i = i0; i < i1; i++) {
      await page.evaluate(t => window.renderFrame(t), i / tl.fps);
      const buf = await canvas.screenshot({ type: "png" });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
    }
    ff.stdin.end();
    await new Promise((res, rej) => ff.on("close", c => c === 0 ? res() : rej(new Error("ffmpeg " + c))));
    console.log(`clip: ${i1 - i0} frames in ${((Date.now() - t0) / 1000).toFixed(0)}s（1 コマ ${((Date.now() - t0) / 1000 / (i1 - i0)).toFixed(2)} 秒）`);
  } else if (args[0] === "--textcheck") {
    // 文字の自動検査：step 秒ごとに 1 コマ描き、stage.js の checkText() の結果と、使った文字の一覧を work/textcheck.json に保存
    const step = parseFloat(args[1] || "0.1"), n = Math.floor(tl.duration / step);
    const res = await page.evaluate(({ n, step }) => {
      const issues = [], chars = new Set();
      for (let i = 0; i <= n; i++) {
        const t = +(i * step).toFixed(3);
        Stage.clearTextLog(); window.renderFrame(t);
        for (const e of Stage.TEXTLOG) for (const ch of e.s) chars.add(ch);
        issues.push(...Stage.checkText(t));
      }
      return { issues, chars: [...chars].join("") };
    }, { n, step });
    fs.writeFileSync(path.join(WORK, "textcheck.json"), JSON.stringify({ step, frames: n + 1, ...res }, null, 1));
    console.log(`textcheck: ${n + 1} コマ、問題 ${res.issues.length} 件`);
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
