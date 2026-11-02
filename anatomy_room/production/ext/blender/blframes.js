// Blender で描いた 3D の場面のコマを bg に敷く（ext/blender/blkit.py、2026-11-02〜）。テンプレートの外の部品。
// renderer.html：<script src="work/blender/index.js"></script> と <script src="../ext/blender/blframes.js"></script> を kit.js のあとに。
// SHOTS の 3D のショットを { at: "l01", kind: "3d", draw: blShot("l01") } にし、kitStart(...) のあとに BL.install()。
// コマは work/blender/<ショット>/f_0001.js（bl_pack.py）。読み込みは非同期なので、renderFrame がまだ読んでいないコマに当たったら、
// 一度描いてから（文字の検査はこの 1 回目を使う）読み込みを待って描き直す Promise を返す（render_frames.js は await する）。
const BL = { meta: window.BL_META || {}, cache: new Map(), pending: new Map(), wait: new Map(), missing: null, MAX: 16 };
function BLF(name, i, uri) { const f = BL.wait.get(name + ":" + i); if (f) f(uri); }
BL.frameAt = function (name, t) {
  const m = BL.meta[name]; if (!m) return 0;
  if (CUE && CUE[name] !== undefined && Math.abs(CUE[name] - m.start) > .02 && !BL.warned) { BL.warned = true; console.error(`blender: ${name} の開始時刻が描いたときと違う（${m.start} → ${CUE[name]}）。scene.py を描き直す`); }
  return Math.max(1, Math.min(m.frames, Math.round((t - (CUE[name] !== undefined ? CUE[name] : m.start)) * 30) + 1));
};
BL.load = function (name, i) {
  const k = name + ":" + i; if (BL.cache.has(k)) return Promise.resolve(BL.cache.get(k)); if (BL.pending.has(k)) return BL.pending.get(k);
  const p = new Promise((res, rej) => {
    BL.wait.set(k, uri => { const im = new Image(); im.onload = () => { BL.cache.set(k, im); res(im); }; im.onerror = () => rej(new Error("decode " + k)); im.src = uri; });
    const s = document.createElement("script"); s.src = `work/blender/${name}/f_${String(i).padStart(4, "0")}.js`;
    s.onload = () => s.remove(); s.onerror = () => { s.remove(); rej(new Error("no " + s.src)); }; document.head.appendChild(s);
  }).finally(() => { BL.pending.delete(k); BL.wait.delete(k); while (BL.cache.size > BL.MAX) BL.cache.delete(BL.cache.keys().next().value); });
  BL.pending.set(k, p); return p;
};
function blShot(name) {
  return (t) => { const i = BL.frameAt(name, t), im = BL.cache.get(name + ":" + i);
    if (im) { BL.cache.delete(name + ":" + i); BL.cache.set(name + ":" + i, im);
      // カットイン（kit の camFX は three のカメラを傾けて寄せる）を、絵の回転と拡大で同じように。回して角が見えない大きさより小さくしない
      const P = typeof ciPhase === "function" ? ciPhase(t) : null;
      if (P && P.c === name) { const [roll, z] = KIT.ci[P.c][P.p], a = P.p ? CUT[P.p - 1] : 0, k = easeOut(clamp((P.d - a) / ((CUT[P.p] - a) * .85))), r = roll * (1 - k);
        const s = Math.max(1 / (z + (1 - z) * k), Math.cos(r) + H / W * Math.abs(Math.sin(r)));
        bg.save(); bg.translate(W / 2, H / 2); bg.rotate(r); bg.scale(s, s); bg.drawImage(im, -W / 2, -H / 2, W, H); bg.restore(); }
      else bg.drawImage(im, 0, 0, W, H); }
    else { bg.fillStyle = "#000"; bg.fillRect(0, 0, W, H); BL.missing = [name, i]; }
    BL.last = [name, i]; };
}
BL.install = function () {
  const rf = window.renderFrame;
  window.renderFrame = function (t) {
    BL.missing = null; BL.last = null; rf(t);
    const pre = () => { if (BL.last) { const [n, i] = BL.last, m = BL.meta[n]; for (let j = i + 1; j <= Math.min(m.frames, i + 4); j++) BL.load(n, j).catch(() => {}); } };
    if (!BL.missing) { pre(); return; }
    const [n, i] = BL.missing; return BL.load(n, i).then(() => { BL.missing = null; rf(t); pre(); });
  };
};
