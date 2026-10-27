// この PC で「リバース」の動画を書き出せるかを調べる。anatomy_room で node tools/check_pc.js
// 調べるもの：Node.js・Playwright（Chromium）・GPU で WebGL が動くか・Python 3（numpy・Pillow）・ffmpeg・Noto Sans CJK JP・VOICEVOX ENGINE
const { spawnSync } = require("child_process");
const http = require("http");

const ok = [], ng = [];
const report = (good, name, detail) => { (good ? ok : ng).push(name); console.log(`${good ? "OK  " : "NG  "} ${name}：${detail}`); };
const cmd = (c, a) => { const r = spawnSync(c, a, { encoding: "utf8" }); return r.status === 0 ? (r.stdout + r.stderr).trim() : null; };

(async () => {
  report(true, "Node.js", process.version);

  const py = ["python3", "python", "py"].find(c => cmd(c, ["--version"]));
  const lib = py && cmd(py, ["-c", "import numpy, PIL; print('numpy', numpy.__version__, '/ Pillow', PIL.__version__)"]);
  report(!!lib, "Python 3（numpy・Pillow）", lib ? `${py}：${lib}` : py ? `${py} はあるが numpy か Pillow がない → pip install numpy pillow` : "見つからない");

  const ff = cmd("ffmpeg", ["-version"]);
  report(!!ff, "ffmpeg", ff ? ff.split("\n")[0] : "見つからない（インストール後、PC を再起動すると見つかることがある）");

  let chromium;
  try { ({ chromium } = require("playwright")); } catch { report(false, "Playwright", "ない → anatomy_room で npm install"); }
  if (chromium) {
    let b;
    try { b = await chromium.launch({ channel: "chromium", args: ["--ignore-gpu-blocklist", "--enable-gpu-rasterization"] }); }
    catch (e) { report(false, "Chromium", "起動できない → npx playwright install chromium"); }
    if (b) {
      report(true, "Playwright（Chromium）", require("playwright/package.json").version);
      const p = await b.newPage();
      const gl = await p.evaluate(() => {
        const g = document.createElement("canvas").getContext("webgl2");
        if (!g) return "";
        const e = g.getExtension("WEBGL_debug_renderer_info");
        return String(e ? g.getParameter(e.UNMASKED_RENDERER_WEBGL) : g.getParameter(g.RENDERER));
      });
      const gpu = gl && !/swiftshader|llvmpipe|software/i.test(gl);
      report(gpu, "GPU で WebGL", gpu ? gl : `GPU が使えない（${gl || "WebGL なし"}）。書き出しはできるが遅い → GPU のドライバを最新にする`);
      await p.setContent("<span>あ</span>");
      const font = await p.evaluate(async () => { await document.fonts.load('700 52px "Noto Sans CJK JP"', "あ"); return document.fonts.check('700 52px "Noto Sans CJK JP"', "あ"); });
      report(font, "フォント Noto Sans CJK JP", font ? "あり" : "ない → docs/PC_SETUP.md の手順 4");
      await b.close();
    }
  }

  const vv = await new Promise(r => http.get("http://127.0.0.1:50021/version", res => { let d = ""; res.on("data", c => d += c); res.on("end", () => r(d)); })
    .on("error", () => r(null)).setTimeout(3000, function () { this.destroy(); }));
  report(!!vv, "VOICEVOX ENGINE（127.0.0.1:50021）", vv ? `版 ${vv.replace(/"/g, "")}` : "応答なし → VOICEVOX（アプリ）を起動しておく");

  console.log(ng.length ? `\n足りないもの ${ng.length} 個：${ng.join("、")}` : "\nすべてそろっています。書き出しの準備ができました。");
})();
