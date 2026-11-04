// YouTube の予約投稿（2026-11-01〜、ユーザーの承認：完成して video_qa を通った回を、anatomy_room/publish/queue.json の順に予約公開で上げてよい）。
// YouTube Studio の画面を Playwright で操作する（API は使わない）。ブラウザは PC の Google Chrome、プロフィールはリポジトリの外
// （%LOCALAPPDATA%\reverse_yt_profile）。ログイン状態はそこにだけ残る。パスワードはこのスクリプトでは扱わない（ユーザーが画面で一度ログインする）。
//   node anatomy_room/tools/yt_upload.js login          ログイン用に Chrome を開く（YouTube Studio のチャンネル画面に入ったら自動で閉じる）
//   node anatomy_room/tools/yt_upload.js next           queue.json の status が queued の回を順に全部上げて、予約公開まで入れる。
//       公開の時刻を過ぎていた回（PC が切れていたなど）や publish_at が空の回は、次に空いている 8:00・19:00 に振り直す。
//       Windows のタスク スケジューラ「Reverse-YouTube-Upload」が、ログオン時と 3 時間ごとにこれを動かす（tools/yt_task.ps1）
//   node anatomy_room/tools/yt_upload.js upload pilot_024   指定した回を上げる
//   --show を付けると画面を表示したまま操作する（最初の数回の確認用）
// 入れる項目：動画・タイトル・説明文（youtube_metadata.md の「## タイトル」と「## 説明文」のコードブロック）・子ども向けではない・
//   改変または合成されたコンテンツ「いいえ」（ユーザーの指示）・予約公開の日時（日本時間）。各段階の画面は anatomy_room/publish/log/ に保存する。
const fs = require("fs"), path = require("path");
const { chromium } = require(path.join(__dirname, "..", "node_modules", "playwright"));
const ROOT = path.join(__dirname, "..", ".."), PUB = path.join(__dirname, "..", "publish"), QUEUE = path.join(PUB, "queue.json"), LOG = path.join(PUB, "log");
const PROFILE = path.join(process.env.LOCALAPPDATA || process.env.HOME, "reverse_yt_profile");
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const argv = process.argv.slice(2), SHOW = argv.includes("--show"), args = argv.filter(a => !a.startsWith("--"));
fs.mkdirSync(LOG, { recursive: true });
const stamp = () => new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
const say = s => console.log(s);

async function open(headless) {
  return chromium.launchPersistentContext(PROFILE, {
    // 画面を出さない形（ヘッドレス）は YouTube Studio に「対応していないブラウザ」として弾かれるため、ふつうの Chrome を窓だけ画面の外に置いて動かす
    headless: false, executablePath: fs.existsSync(CHROME) ? CHROME : undefined, viewport: { width: 1400, height: 1000 }, locale: "ja-JP", timezoneId: "Asia/Tokyo",
    ignoreDefaultArgs: ["--enable-automation"], args: ["--disable-blink-features=AutomationControlled", ...(headless ? ["--window-position=-32000,-32000"] : [])],
  });
}
function meta(file) {   // youtube_metadata.md からタイトルと説明文
  const s = fs.readFileSync(path.join(ROOT, file), "utf-8");
  const title = s.split("## タイトル")[1].split("\n").map(x => x.trim()).find(x => x && !x.startsWith("#"));
  const desc = s.split("## 説明文")[1].split("```")[1].replace(/^\n/, "").replace(/\n$/, "");
  if (!title || title.length > 100) throw new Error("タイトルがない、または 100 文字を超える");
  if (/[<>]/.test(title + desc) || desc.length > 5000) throw new Error("説明文に使えない文字（< >）があるか、5000 文字を超える");
  return { title, desc };
}
let page, shotN = 0;
async function shot(name) { const f = path.join(LOG, `${stamp()}_${String(++shotN).padStart(2, "0")}_${name}.png`); await page.screenshot({ path: f }).catch(() => {}); return f; }
async function clickFirst(sels, timeout = 15000) {   // 候補のどれか見つかったものを押す（日本語と英語の画面の両方に対応）
  const t0 = Date.now();
  while (Date.now() - t0 < timeout) { for (const s of sels) { const l = page.locator(s).first(); if (await l.isVisible().catch(() => false)) { await l.click(); return s; } } await page.waitForTimeout(300); }
  throw new Error("見つからない：" + sels.join(" / "));
}
async function dismiss() {   // 「YouTube Studio へようこそ」などの案内が出ていたら閉じる
  for (const s of ["ytcp-button:has-text('続行')", "ytcp-button:has-text('Continue')", "ytcp-button:has-text('閉じる')", "#dismiss-button"]) { const l = page.locator(s).first(); if (await l.isVisible().catch(() => false)) { await l.click().catch(() => {}); await page.waitForTimeout(800); } }
}
async function typeInto(sel, text) { const box = page.locator(sel).first(); await box.waitFor({ timeout: 60000 }); await box.click(); await page.keyboard.press("Control+A"); await page.keyboard.press("Delete"); await page.keyboard.insertText(text); }

async function login() {
  const ctx = await open(false); page = ctx.pages()[0] || await ctx.newPage();
  await page.goto("https://studio.youtube.com/");
  say("Chrome を開きました。YouTube にログインし、チャンネル「リバース」の YouTube Studio に入ってください（最大 30 分待ちます）。");
  await page.waitForURL(/studio\.youtube\.com\/channel\//, { timeout: 30 * 60000 });
  await page.waitForTimeout(3000); await shot("login_ok"); say("✅ ログインを確認しました：" + page.url()); await ctx.close();
}

async function upload(item) {
  const { title, desc } = meta(item.meta), video = path.join(ROOT, item.video);
  if (!fs.existsSync(video)) throw new Error("動画がない：" + item.video);
  const [d, hm] = item.publish_at.split(" "), [Y, Mo, D] = d.split("-").map(Number);
  if (new Date(`${d}T${hm}:00+09:00`) < new Date(Date.now() + 20 * 60000)) throw new Error("公開日時が近すぎるか過ぎている：" + item.publish_at);   // 振り直しは呼ぶ側（next）で済ませてある
  const ctx = await open(!SHOW); page = ctx.pages()[0] || await ctx.newPage();
  try {
    await page.goto("https://studio.youtube.com/"); await page.waitForTimeout(4000);
    if (!/studio\.youtube\.com\/channel\//.test(page.url())) throw new Error("ログインしていない（node anatomy_room/tools/yt_upload.js login を先に）");
    await dismiss(); await shot("studio");
    const ch = page.url().match(/channel\/([^/?#]+)/)[1];   // アップロードの画面を URL で直接開く（「作成」ボタンの部品は画面の更新で変わるため）
    // 前に途中で止まった下書き（同じタイトル）があれば、その続きから入れる（同じ動画を 2 本上げない）
    let resumed = false;
    // queue.json の "reupload": true の回は、前の版（非公開）が同じタイトルで残っていても、新しい動画として上げる（2026-11-02、声を作り直した 029）。
    // 下書き（ファイル名のままの「reverse 029 moseley」など）が残っていれば、その続きから入れる
    for (const tab of ["short", "upload"]) {
      await page.goto(`https://studio.youtube.com/channel/${ch}/videos/${tab}`); await page.waitForTimeout(5000); await dismiss();
      // タイトルで探し、なければファイル名のままの下書き（上限で止まったときなど。例：reverse 034 bentley）を探す
      let row = page.locator("ytcp-video-row", { hasText: title.replace(/\s*#shorts\s*$/, "") }).first();
      if (item.reupload || !(await row.count())) row = page.locator("ytcp-video-row", { hasText: path.basename(video, ".mp4").replace(/_/g, " ") }).first();
      if (!(await row.count())) continue;
      await row.hover().catch(() => {}); const btn = row.locator("ytcp-button:has-text('ドラフトを編集'), ytcp-button:has-text('下書きを編集'), ytcp-button:has-text('Edit draft'), #edit-draft-button").first();
      if (await btn.count()) { await btn.click(); resumed = true; say("下書きの続きから入れる：" + item.id); break; }
      throw new Error("同じタイトルの動画がすでにある（下書きではない）：" + title);
    }
    if (!resumed) {
      await page.goto(`https://studio.youtube.com/channel/${ch}/videos/upload?d=ud`); await page.waitForTimeout(3000); await shot("upload_dialog");
      const fi = page.locator("input[type=file]").first(); await fi.waitFor({ state: "attached", timeout: 30000 }); await fi.setInputFiles(video);
      say("アップロード中：" + item.id);
    }
    // 上限の表示は少し遅れて出ることがある（2026-11-02：4 秒では見えず、タイトルの欄で止まった）。下書きの続きのときも確かめる
    for (let i = 0; i < 6; i++) {
      await page.waitForTimeout(2000);
      if (await page.locator("text=アップロード数の上限").first().isVisible().catch(() => false)) { await shot("limit"); const e = new Error("1 日のアップロード数の上限（24 時間後に自動で続きを上げる）"); e.limit = true; throw e; }
    }
    await page.locator("#title-textarea #textbox").first().waitFor({ timeout: 120000 }); await page.waitForTimeout(2500);
    await typeInto("#title-textarea #textbox", title); await typeInto("#description-textarea #textbox", desc); await shot("details");
    await clickFirst(["tp-yt-paper-radio-button[name=VIDEO_MADE_FOR_KIDS_NOT_MFK]"]);
    // 「AI の使用」（改変または合成されたコンテンツの申告）：見出しのすぐ下の「いいえ」を選び、選ばれたことを確かめる（ユーザーの指示）
    const aiNo = () => page.evaluate(() => {
      const head = [...document.querySelectorAll("*")].find(e => e.childElementCount === 0 && /^(AI の使用|改変または合成されたコンテンツ|Altered content)/.test(e.textContent.trim()));
      if (!head) return "nohead"; const top = head.getBoundingClientRect().top;
      const r = [...document.querySelectorAll("tp-yt-paper-radio-button")].filter(e => /^(いいえ|No)$/.test(e.innerText.trim()) && e.getBoundingClientRect().top > top).sort((a, b) => a.getBoundingClientRect().top - b.getBoundingClientRect().top)[0];
      if (!r) return "noradio"; r.scrollIntoView({ block: "center" }); if (r.getAttribute("aria-checked") !== "true") r.click(); return "clicked"; });
    const aiChecked = () => page.evaluate(() => { const head = [...document.querySelectorAll("*")].find(e => e.childElementCount === 0 && /^(AI の使用|改変または合成されたコンテンツ|Altered content)/.test(e.textContent.trim())); if (!head) return false;
      const top = head.getBoundingClientRect().top; const r = [...document.querySelectorAll("tp-yt-paper-radio-button")].filter(e => /^(いいえ|No)$/.test(e.innerText.trim()) && e.getBoundingClientRect().top > top).sort((a, b) => a.getBoundingClientRect().top - b.getBoundingClientRect().top)[0]; return !!r && r.getAttribute("aria-checked") === "true"; });
    if ((await aiNo()) === "nohead") { await clickFirst(["#toggle-button", "ytcp-button:has-text('すべて表示')", "ytcp-button:has-text('Show more')"]); await page.waitForTimeout(1000); await aiNo(); }
    await page.waitForTimeout(800); if (!(await aiChecked())) { await aiNo(); await page.waitForTimeout(800); }
    await shot("audience");
    if (!(await aiChecked())) throw new Error("「AI の使用」の「いいえ」を選べなかった");
    for (let i = 0; i < 3; i++) { await clickFirst(["#next-button"]); await page.waitForTimeout(1500); }
    await shot("visibility");
    // 予約公開：日付は欄を全部消してから入れ、時刻は一覧から選ぶ
    const dateStr = `${Y}/${String(Mo).padStart(2, "0")}/${String(D).padStart(2, "0")}`, timeStr = hm.replace(/^0/, "");
    if (!(await page.locator("#datepicker-trigger").first().isVisible().catch(() => false))) { await clickFirst(["#second-container-expand-button", "ytcp-icon-button#second-container-expand-button"]); await page.waitForTimeout(800); }
    await clickFirst(["#datepicker-trigger"]); await page.waitForTimeout(800);
    const dateIn = page.locator("ytcp-date-picker input").first(); await dateIn.waitFor({ timeout: 10000 }); await dateIn.click();
    await page.keyboard.press("Control+A"); await page.keyboard.press("Delete"); await page.keyboard.type(dateStr); await page.keyboard.press("Enter"); await page.waitForTimeout(1000);
    if (await page.locator("ytcp-date-picker input").first().isVisible().catch(() => false)) { await page.locator("text=一般公開としてスケジュール").first().click().catch(() => {}); await page.waitForTimeout(600); }
    await clickFirst(["#time-of-day-trigger", "#time-of-day-container"]); await page.waitForTimeout(800);
    try { await clickFirst([`tp-yt-paper-item:text-is("${timeStr}")`, `ytcp-text-menu tp-yt-paper-item:has-text("${timeStr}")`], 5000); }
    catch { const ti = page.locator("#time-of-day-trigger input, #time-of-day-container input").first(); await ti.click(); await page.keyboard.press("Control+A"); await page.keyboard.type(timeStr); await page.keyboard.press("Enter"); }
    await page.waitForTimeout(1000); await shot("scheduled_input");
    const sched = (await page.locator("#second-container, ytcp-video-visibility-select").first().innerText().catch(() => "")).replace(/\s+/g, " ");
    const shown = await page.evaluate(() => [...document.querySelectorAll("ytcp-date-picker input, #time-of-day-trigger input, #time-of-day-container input, #datepicker-trigger, #time-of-day-trigger")].map(e => (e.value || e.innerText || "").trim()).join(" "));
    say("予約の欄：" + (shown + " " + sched).slice(0, 200));
    if (!(shown + sched).includes(dateStr) || !(shown + sched).includes(timeStr)) throw new Error(`予約の日時が入っていない（${dateStr} ${timeStr}）`);
    // アップロードと処理の完了を待って「スケジュールを設定」を押す
    const done = page.locator("#done-button").first(); const t0 = Date.now();
    while (Date.now() - t0 < 30 * 60000) { if (await done.isEnabled().catch(() => false)) break; await page.waitForTimeout(5000); }
    await shot("before_done"); await done.click(); await page.waitForTimeout(5000); await shot("after_done");
    const link = await page.locator("a.style-scope.ytcp-video-info, #share-url").first().innerText().catch(() => "");
    await clickFirst(["#close-button", "ytcp-button#close-button", "tp-yt-paper-dialog #close-button"], 20000).catch(() => {});
    return link.trim();
  } catch (e) { const f = await shot("error"); e.message += `（画面：${f}）`; throw e; } finally { await ctx.close(); }
}

async function makePrivate(item) {   // 動画の編集画面で、公開設定を「非公開」にして保存する（予約が外れる）
  const { title } = meta(item.meta), stem = title.replace(/\s*#shorts\s*$/, "");
  const ctx = await open(!SHOW); page = ctx.pages()[0] || await ctx.newPage();
  try {
    await page.goto("https://studio.youtube.com/"); await page.waitForTimeout(4000); await dismiss();
    if (!/studio\.youtube\.com\/channel\//.test(page.url())) throw new Error("ログインしていない");
    const ch = page.url().match(/channel\/([^/?#]+)/)[1]; let href = null;
    for (const tab of ["short", "upload", "short"]) { await page.goto(`https://studio.youtube.com/channel/${ch}/videos/${tab}`); await page.waitForTimeout(5000); await dismiss();
      const row = page.locator("ytcp-video-row", { hasText: stem }).first();
      await row.waitFor({ timeout: 10000 }).catch(() => {});   // 一覧の読み込みが遅いことがある（2026-11-02：1 回目は見つからなかった）
      if (!(await row.count())) continue;
      href = await row.locator("a[href*='/video/']").first().getAttribute("href"); if (href) break; }
    if (!href) throw new Error("動画が見つからない：" + stem);
    const id = href.match(/video\/([^/]+)/)[1]; await page.goto(`https://studio.youtube.com/video/${id}/edit`); await page.waitForTimeout(5000); await dismiss(); await shot("edit_" + item.id);
    await clickFirst(["ytcp-video-metadata-visibility", "#visibility-container"]); await page.waitForTimeout(1500);
    if (!(await page.locator("tp-yt-paper-radio-button[name=PRIVATE]").first().isVisible().catch(() => false))) { await clickFirst(["text=保存または公開", "text=Save or publish", "#first-container-expand-button"]); await page.waitForTimeout(1000); }
    await clickFirst(["tp-yt-paper-radio-button[name=PRIVATE]"]); await page.waitForTimeout(800); await shot("private_" + item.id);
    await clickFirst(["ytcp-video-visibility-select #save-button", "tp-yt-paper-dialog #save-button", "ytcp-button:has-text('完了')"]); await page.waitForTimeout(1500);
    await clickFirst(["ytcp-button#save", "#save"]); await page.waitForTimeout(4000); await shot("saved_" + item.id);
    const v = (await page.locator("ytcp-video-metadata-visibility").first().innerText().catch(() => "")).replace(/\s+/g, " ");
    if (!/非公開|Private/.test(v) || /スケジュール|Scheduled/.test(v)) throw new Error("非公開になったか確かめられない：" + v.slice(0, 80));
  } catch (e) { const f = await shot("error"); e.message += `（画面：${f}）`; throw e; } finally { await ctx.close(); }
}
// 公開の枠（日本時間の 8:00・19:00）：PC が切れていて予定の時刻を過ぎた回、または publish_at が空の回は、次に空いている枠に振り直す
const jst = (d, hm) => new Date(`${d}T${hm}:00+09:00`);
function nextSlot(q, after) {
  const taken = new Set(q.items.filter(x => x.status === "scheduled" && x.publish_at).map(x => x.publish_at));
  const t0 = new Date(Date.now() + 9 * 3600000);   // 日本時間の日付
  for (let day = 0; day < 60; day++) { const d = new Date(Date.UTC(t0.getUTCFullYear(), t0.getUTCMonth(), t0.getUTCDate() + day)).toISOString().slice(0, 10);
    for (const hm of q.slots) { const at = `${d} ${hm}`; if (jst(d, hm) > after && !taken.has(at)) return at; } }
  throw new Error("空いている枠が見つからない");
}
function lockOn() {   // タスク スケジューラと手で動かしたのが重ならないように（2 時間たった鍵は古いとみなす）
  const f = path.join(PUB, ".lock"); if (fs.existsSync(f) && Date.now() - fs.statSync(f).mtimeMs < 2 * 3600000) return false;
  fs.writeFileSync(f, String(process.pid)); process.on("exit", () => { try { fs.unlinkSync(f); } catch {} }); return true;
}
function logRun(s) { fs.appendFileSync(path.join(LOG, "run.log"), `${new Date().toISOString()} ${s}\n`, "utf-8"); }

// list：Studio の動画の一覧（ID・題名・公開設定）。delete ID…：指定した動画を完全に削除（元に戻せない。ユーザーの指示があるときだけ。2026-11-04 追加）
async function studioRows() {
  const ch = page.url().match(/channel\/([^/?#]+)/)[1], out = [];
  for (const tab of ["short", "upload"]) { await page.goto(`https://studio.youtube.com/channel/${ch}/videos/${tab}`); await page.waitForTimeout(6000); await dismiss();
    await page.locator("ytcp-video-row").first().waitFor({ timeout: 15000 }).catch(() => {});
    for (const r of await page.locator("ytcp-video-row").all()) {
      const href = await r.locator("a[href*='/video/']").first().getAttribute("href").catch(() => null); if (!href) continue;
      const id = href.match(/video\/([^/]+)/)[1], title = (await r.locator("#video-title").first().innerText().catch(() => "")).trim();
      const vis = (await r.locator(".tablecell-visibility, ytcp-video-row-cell-visibility, #visibility").first().innerText().catch(() => "")).replace(/\s+/g, " ").trim();
      out.push({ tab, id, title, vis, row: r }); } }
  return out;
}
async function listVideos() {
  const ctx = await open(!SHOW); page = ctx.pages()[0] || await ctx.newPage();
  try { await page.goto("https://studio.youtube.com/"); await page.waitForTimeout(4000); await dismiss();
    if (!/studio\.youtube\.com\/channel\//.test(page.url())) throw new Error("ログインしていない");
    for (const r of await studioRows()) say(`${r.tab}	${r.id}	${r.vis}	${r.title}`);
  } finally { await ctx.close(); }
}
async function deleteVideos(ids) {
  const ctx = await open(!SHOW); page = ctx.pages()[0] || await ctx.newPage();
  try { await page.goto("https://studio.youtube.com/"); await page.waitForTimeout(4000); await dismiss();
    if (!/studio\.youtube\.com\/channel\//.test(page.url())) throw new Error("ログインしていない");
    for (const id of ids) {
      const r = (await studioRows()).find(x => x.id === id); if (!r) { say(`❌ 見つからない：${id}`); continue; }
      if (!/非公開|Private/.test(r.vis) || /予約|スケジュール|Scheduled|公開済み|Public/.test(r.vis)) { say(`❌ 非公開ではないので消さない：${id}（${r.vis}）`); continue; }
      const ch = page.url().match(/channel\/([^/?#]+)/)[1]; await page.goto(`https://studio.youtube.com/channel/${ch}/videos/${r.tab}`); await page.waitForTimeout(6000); await dismiss();
      const row = page.locator("ytcp-video-row", { has: page.locator(`a[href*='${id}']`) }).first(); await row.waitFor({ timeout: 15000 });
      await row.hover(); await page.waitForTimeout(800);
      await row.locator("ytcp-icon-button#overflow-menu-button, #hover-items ytcp-icon-button:last-child, ytcp-icon-button[aria-label*='オプション'], ytcp-icon-button[aria-label*='Options']").last().click();
      await page.waitForTimeout(1000); await clickFirst(["tp-yt-paper-item:has-text('完全に削除')", "tp-yt-paper-item:has-text('Delete forever')", "ytcp-text-menu tp-yt-paper-item:has-text('削除')"]);
      await page.waitForTimeout(1500); await shot("delete_" + id);
      await clickFirst(["tp-yt-paper-dialog ytcp-checkbox-lit #checkbox-container", "ytcp-dialog ytcp-checkbox-lit #checkbox-container", "tp-yt-paper-dialog >> text=取り消しできない"]); await page.waitForTimeout(600);
      await clickFirst(["ytcp-button#confirm-button:not([disabled])", "#confirm-button", "ytcp-button:has-text('完全に削除')", "ytcp-button:has-text('Delete forever')"]); await page.waitForTimeout(5000);
      const still = (await studioRows()).find(x => x.id === id);
      if (still) { const f = await shot("delete_fail_" + id); say(`❌ 消えたか確かめられない：${id}（画面：${f}）`); } else { say(`✅ 削除しました：${id}　${r.title}`); logRun(`deleted ${id} ${r.title}`); }
    }
  } catch (e) { const f = await shot("error"); e.message += `（画面：${f}）`; throw e; } finally { await ctx.close(); }
}

(async () => {
  const cmd = args[0];
  if (cmd === "login") return login();
  if (cmd === "list") return listVideos();
  if (cmd === "delete") return deleteVideos(args.slice(1));
  if (!lockOn()) { say("別の投稿が動いているので、今回はやめます"); return; }
  const q = JSON.parse(fs.readFileSync(QUEUE, "utf-8")), save = () => fs.writeFileSync(QUEUE, JSON.stringify(q, null, 1) + "\n", "utf-8");
  // private：予約を外して非公開に戻す（動画は消さない）。回を指定しなければ、まだ公開されていない予約を全部
  if (cmd === "private") {
    const ids = args.slice(1), targets = q.items.filter(x => x.status === "scheduled" && (!ids.length || ids.includes(x.id)) && jst(...x.publish_at.split(" ")) > new Date());
    for (const item of targets) { await makePrivate(item); item.status = "private"; save(); say(`✅ 非公開にしました：${item.id}（予約 ${item.publish_at} を外した）`); logRun(`private ${item.id}`); }
    if (!targets.length) say("非公開にする予約がありません"); return;
  }
  // next：queued の回を上から順に、全部上げる（PC が切れていた間の分も、起動したときにまとめて）
  const items = cmd === "upload" ? q.items.filter(x => x.id === args[1]) : q.items.filter(x => x.status === "queued");
  if (!items.length) { say("上げる回がありません"); return; }
  let last = new Date(Date.now() + 30 * 60000);   // 公開は今から 30 分以上あと
  for (const item of items) {
    if (item.status === "scheduled") throw new Error("すでに予約済み：" + item.id);
    const [d, hm] = (item.publish_at || "").split(" ");
    if (!item.publish_at || jst(d, hm) <= last || q.items.some(x => x !== item && x.status === "scheduled" && x.publish_at === item.publish_at)) {
      const at = nextSlot(q, last); say(`公開の枠を振り直し：${item.id} ${item.publish_at || "（未定）"} → ${at}`); logRun(`reslot ${item.id} ${item.publish_at || "-"} -> ${at}`); item.publish_at = at; save(); }
    try {
      const link = await upload(item);
      item.status = "scheduled"; item.uploaded = new Date().toISOString(); if (link) item.url = link; save();
      say(`✅ 予約しました：${item.id}（公開 ${item.publish_at}）${link ? " " + link : ""}`); logRun(`scheduled ${item.id} ${item.publish_at}`);
      const [d2, hm2] = item.publish_at.split(" "); last = jst(d2, hm2);
    } catch (e) { logRun(`error ${item.id} ${e.message}`); if (e.limit) { say("⏸ " + e.message); return; } throw e; }
  }
})().catch(e => { console.error("❌ " + e.message); process.exit(1); });
