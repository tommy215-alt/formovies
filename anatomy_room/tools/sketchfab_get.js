// Sketchfab の模型を落とす（2026-11-12〜、ユーザーの承認：052 から Sketchfab の CC0・CC BY の素材を使う）。
// ブラウザは PC の Google Chrome、プロフィールはリポジトリの外（%LOCALAPPDATA%\reverse_sketchfab_profile）。ログインはユーザーが画面で一度だけ行い、
// その状態はそのプロフィールにだけ残る。パスワード・トークンはこのスクリプトでは扱わない・保存しない（YouTube の yt_upload.js と同じ考え方）。
//   node anatomy_room/tools/sketchfab_get.js login                 ログイン用に Chrome を開く（ログインを確かめたら自動で閉じる）
//   node anatomy_room/tools/sketchfab_get.js get <uid> <出力先>     模型を glTF で落として展開し、出力先に credit.json（名前・作者・ライセンス・URL）を書く
// ライセンスは公開の API（ログイン不要）で先に確かめ、CC0（cc0）と CC BY（by）以外は落とさない（ユーザーの決まり：PD・CC0・CC BY だけ）。
const fs = require("fs"), path = require("path"), { execFileSync } = require("child_process");
const { chromium } = require(path.join(__dirname, "..", "node_modules", "playwright"));
const PROFILE = path.join(process.env.LOCALAPPDATA || process.env.HOME, "reverse_sketchfab_profile");
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const ALLOWED = { cc0: "CC0 1.0（パブリックドメイン）", by: "CC BY 4.0（作者名の表示が必要）" };
const say = s => console.log(s);

async function open(hidden) {
  return chromium.launchPersistentContext(PROFILE, {
    headless: false, executablePath: fs.existsSync(CHROME) ? CHROME : undefined, viewport: { width: 1300, height: 900 }, locale: "ja-JP",
    ignoreDefaultArgs: ["--enable-automation"], args: ["--disable-blink-features=AutomationControlled", ...(hidden ? ["--window-position=-32000,-32000"] : [])],
  });
}

async function loggedIn(ctx) {
  const r = await ctx.request.get("https://sketchfab.com/i/users/me", { failOnStatusCode: false });
  return r.ok() ? (await r.json()).username || true : false;
}

async function login() {
  const ctx = await open(false), page = ctx.pages()[0] || await ctx.newPage();
  await page.goto("https://sketchfab.com/login");
  say("Chrome を開きました。Sketchfab にログインしてください（最大 30 分待ちます）。");
  const t0 = Date.now();
  while (Date.now() - t0 < 30 * 60000) {
    const u = await loggedIn(ctx);
    if (u) { say("✅ ログインを確認しました：" + u); await ctx.close(); return; }
    await page.waitForTimeout(3000);
  }
  await ctx.close(); throw new Error("30 分のあいだにログインを確認できなかった");
}

async function get(uid, out) {
  const info = await (await fetch(`https://api.sketchfab.com/v3/models/${uid}`)).json();
  const lic = info.license && (info.license.slug || info.license.label);
  if (!info.license || !ALLOWED[info.license.slug]) throw new Error(`ライセンスが CC0・CC BY ではないので落とさない：${info.name}（${lic}）`);
  if (!info.isDownloadable) throw new Error("ダウンロードできない模型：" + info.name);
  const ctx = await open(true);
  try {
    if (!await loggedIn(ctx)) throw new Error("ログインしていない：先に login を実行して画面でログインしてください");
    const r = await ctx.request.get(`https://sketchfab.com/i/models/${uid}/download`, { headers: { "x-requested-with": "XMLHttpRequest" } });
    if (!r.ok()) throw new Error(`ダウンロードの準備に失敗：${r.status()}`);
    const d0 = await r.json(); if (process.env.SF_DEBUG) say(JSON.stringify(d0).slice(0, 1500));
    const d = d0.latest || d0, pick = v => Array.isArray(v) ? v[0] : v, g = pick(d.gltf) || pick(d.glb);
    if (!g || !g.url) throw new Error("glTF の URL がない：" + JSON.stringify(Object.keys(d)));
    if (g.url.startsWith("/")) g.url = "https://sketchfab.com" + g.url;
    fs.mkdirSync(out, { recursive: true });
    const zip = path.join(out, `${uid}.zip`); let body = await (await ctx.request.get(g.url)).body();
    if (body[0] === 0x7b) { const j = JSON.parse(body.toString()); if (j.url) body = await (await fetch(j.url)).arrayBuffer().then(b => Buffer.from(b)); }   // 一時的な URL（S3）が JSON で返る
    fs.writeFileSync(zip, body);
    execFileSync(process.platform === "win32" ? path.join(process.env.SystemRoot || "C:/Windows", "System32", "tar.exe") : "tar", ["-xf", zip, "-C", out]); fs.unlinkSync(zip);   // Git の tar は「C:」を別の機械の名前と取り違える
    const credit = { name: info.name, author: info.user.displayName || info.user.username, author_url: info.user.profileUrl, license: info.license.label, license_slug: info.license.slug,
                     license_url: info.license.url, url: info.viewerUrl, uid, faces: info.faceCount, animations: info.animationCount, downloaded: new Date().toISOString() };
    fs.writeFileSync(path.join(out, "credit.json"), JSON.stringify(credit, null, 1));
    say(`✅ ${info.name}（${credit.author}、${ALLOWED[info.license.slug]}）→ ${out}（${(body.length / 1e6).toFixed(1)} MB）`);
  } finally { await ctx.close(); }
}

(async () => {
  const [cmd, a, b] = process.argv.slice(2);
  if (cmd === "login") return login();
  if (cmd === "get" && a && b) return get(a, path.resolve(b));
  say("使い方：login ／ get <uid> <出力先>");
})().catch(e => { console.error("❌ " + e.message); process.exit(1); });
