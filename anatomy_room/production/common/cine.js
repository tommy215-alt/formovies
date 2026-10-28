// リバースの映像品質（シネマティック）部品（2026-10-28〜、標準ルール v4）。GPU（RTX 3070・WebGL2）の余力を使う。
// 既存の回（pilot_003〜012 の renderer.html）は読み込まないので影響しない。新しい回の renderer で <script src="../common/cine.js"> を足して使う。
//   Cine.init(THREE, R)                  周りの光（IBL）の下地を作る（PMREM：映り込みのプリセット cold・warm・studio・lamp）
//   Cine.useEnv(scene, name, k)          場面ごとに映り込みを切り替える（k＝強さ）
//   Cine.surface(mat, kind, o)           既存の材質に凹凸（法線）と、つや・ざらつき（ラフネス）の地図を足す：wood・stone・plaster・fabric・metal・paper・skin・porcelain
//   Cine.water(o) / Cine.glass(o)        透過・屈折する水とガラス（MeshPhysicalMaterial）
//   Cine.shaft(o)                        差し込む光の筋（加算合成の円錐。縁と先がやわらかく消え、空気のむらで揺らぐ）
//   Cine.dust(o) → { points, update(t) } 光の中の埃（決まった種で動く。コマごとに同じ結果）
//   Cine.motionBlur(ctx, t, o, draw)     1 コマの露光の間に複数回描いて平均する（動きのぶれ）
//   Cine.bloom(ctx, k, o)                明るい所だけをにじませる（2D、GPU のフィルタ）
// 決定的：乱数はすべて種つき。時刻 t だけで 1 コマが決まる（コマを並列に描いても同じ結果）。
(function (root) {
  const W = 1080, H = 1920;
  let THREE = null, R = null, ENV = {};
  const rng = seed => { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); };

  // ---------------------------------------------------------------- 周りの光（IBL）
  // 部屋の内側に光る面を置いた小さな場面を PMREM でぼかし、scene.environment に使う。値は 1 を超えてよい（半精度で保持）
  const PRESETS = {
    cold:   { base: 0x0a0f16, panels: [[[6, 2, 0], [0.2, 5, 4], 0x9fb8d8, 2.2], [[0, 5, 0], [6, 0.2, 6], 0x6a7a90, 0.8]] },
    warm:   { base: 0x140d08, panels: [[[6, 2, 0], [0.2, 5, 5], 0xffd2a0, 3.4], [[0, 5, 0], [6, 0.2, 6], 0xc89a70, 0.9], [[-6, 1, 0], [0.2, 3, 3], 0x6a5038, 0.6]] },
    studio: { base: 0x2a2e34, panels: [[[0, 5, 0], [8, 0.2, 8], 0xf4f6fa, 3.0], [[6, 2, 2], [0.2, 4, 4], 0xffe6cc, 1.4], [[-6, 2, -2], [0.2, 4, 4], 0xd8e6f6, 1.0]] },
    lamp:   { base: 0x0a0806, panels: [[[-2, 2, -1], [1, 1, 1], 0xffc070, 5.0], [[4, 2, -6], [3, 3, 0.2], 0x5a6a80, 0.6]] },
  };
  function envScene(p) {
    const s = new THREE.Scene();
    s.add(new THREE.Mesh(new THREE.BoxGeometry(14, 10, 14), new THREE.MeshBasicMaterial({ color: new THREE.Color(p.base).convertSRGBToLinear(), side: THREE.BackSide })));
    for (const [pos, size, col, k] of p.panels) {
      const m = new THREE.Mesh(new THREE.BoxGeometry(...size), new THREE.MeshBasicMaterial({ color: new THREE.Color(col).convertSRGBToLinear().multiplyScalar(k) }));
      m.position.set(...pos); s.add(m);
    }
    return s;
  }
  function init(T, renderer) {
    THREE = T; R = renderer;
    const pm = new THREE.PMREMGenerator(R);
    for (const k in PRESETS) ENV[k] = pm.fromScene(envScene(PRESETS[k]), 0.04).texture;
    pm.dispose();
  }
  function useEnv(scene, name, k = 0.6) {
    scene.environment = name ? ENV[name] : null;
    scene.traverse(o => { if (!o.isMesh) return; for (const m of [].concat(o.material)) if (m && "envMapIntensity" in m && !m.userData.envFixed) m.envMapIntensity = k; });
  }

  // ---------------------------------------------------------------- 凹凸とつや（手続き的な地図）
  function noise2(size, seed, oct = 4, sx = 1, sy = 1) {   // 値ノイズの重ね合わせ（0〜1）。端がつながる（タイル状に並べられる）
    const out = new Float32Array(size * size);
    for (let o = 0; o < oct; o++) {
      const g = 4 << o, r = rng(seed + o * 101), grid = new Float32Array(g * g); for (let i = 0; i < grid.length; i++) grid[i] = r();
      const amp = 1 / (1 << o);
      for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
        const fx = (x / size * g * sx) % g, fy = (y / size * g * sy) % g, x0 = Math.floor(fx), y0 = Math.floor(fy), ux = fx - x0, uy = fy - y0;
        const a = grid[y0 * g + x0], b = grid[y0 * g + (x0 + 1) % g], c = grid[((y0 + 1) % g) * g + x0], d = grid[((y0 + 1) % g) * g + (x0 + 1) % g];
        const sx_ = ux * ux * (3 - 2 * ux), sy_ = uy * uy * (3 - 2 * uy);
        out[y * size + x] += amp * ((a * (1 - sx_) + b * sx_) * (1 - sy_) + (c * (1 - sx_) + d * sx_) * sy_);
      }
    }
    let mn = 1e9, mx = -1e9; for (const v of out) { mn = Math.min(mn, v); mx = Math.max(mx, v); }
    for (let i = 0; i < out.length; i++) out[i] = (out[i] - mn) / (mx - mn + 1e-9);
    return out;
  }
  const HEIGHT = {   // 高さの地図（0〜1）。種類ごとの表面の特徴
    wood: (n, s) => { const a = noise2(n, s, 4, 1, 8), b = noise2(n, s + 7, 3, 2, 2); return a.map((v, i) => 0.55 * (0.5 + 0.5 * Math.sin(v * 40 + b[i] * 6)) + 0.45 * b[i]); },
    stone: (n, s) => { const a = noise2(n, s, 5), b = noise2(n, s + 3, 2); return a.map((v, i) => 0.7 * v + 0.3 * b[i] * b[i]); },
    plaster: (n, s) => { const a = noise2(n, s, 5); return a.map(v => v * v); },
    fabric: (n, s) => { const a = noise2(n, s, 3), o = new Float32Array(n * n); for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) o[y * n + x] = 0.5 + 0.25 * Math.sin(x * Math.PI / 2) * Math.sin(y * Math.PI / 2) + 0.25 * (a[y * n + x] - 0.5); return o; },
    metal: (n, s) => { const a = noise2(n, s, 4, 16, 1), o = a.map(v => 0.5 + 0.2 * (v - 0.5)), r = rng(s + 9);
      for (let k = 0; k < 40; k++) { let x = r() * n, y = r() * n; const ang = r() * Math.PI, len = 20 + r() * 120;   // 細かい傷
        for (let i = 0; i < len; i++) { const xi = Math.floor(x + Math.cos(ang) * i + n) % n, yi = Math.floor(y + Math.sin(ang) * i + n) % n; o[yi * n + xi] -= 0.25; } }
      return o; },
    paper: (n, s) => { const a = noise2(n, s, 6), b = noise2(n, s + 5, 3, 1, 6); return a.map((v, i) => 0.6 * v + 0.4 * b[i]); },
    skin: (n, s) => noise2(n, s, 5).map(v => 0.5 + 0.3 * (v - 0.5)),
    porcelain: (n, s) => noise2(n, s, 3).map(v => 0.5 + 0.08 * (v - 0.5)),
  };
  const ROUGH = { wood: [0.55, 0.85], stone: [0.7, 0.98], plaster: [0.8, 1.0], fabric: [0.75, 0.95], metal: [0.25, 0.6], paper: [0.75, 0.95], skin: [0.45, 0.65], porcelain: [0.08, 0.2] };
  const cache = {};
  function maps(kind, seed = 1, size = 512) {
    const key = kind + seed + "_" + size; if (cache[key]) return cache[key];
    const h = HEIGHT[kind](size, seed), nc = document.createElement("canvas"), rc = document.createElement("canvas");
    nc.width = nc.height = rc.width = rc.height = size;
    const nd = nc.getContext("2d").createImageData(size, size), rd = rc.getContext("2d").createImageData(size, size), [r0, r1] = ROUGH[kind];
    for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
      const i = y * size + x, hx = h[y * size + (x + 1) % size] - h[y * size + (x - 1 + size) % size], hy = h[((y + 1) % size) * size + x] - h[((y - 1 + size) % size) * size + x];
      const nx = -hx * 2.5, ny = -hy * 2.5, nz = 1, l = Math.hypot(nx, ny, nz);
      nd.data[i * 4] = (nx / l * 0.5 + 0.5) * 255; nd.data[i * 4 + 1] = (ny / l * 0.5 + 0.5) * 255; nd.data[i * 4 + 2] = (nz / l * 0.5 + 0.5) * 255; nd.data[i * 4 + 3] = 255;
      const rv = (r0 + (r1 - r0) * h[i]) * 255; rd.data[i * 4] = rd.data[i * 4 + 1] = rd.data[i * 4 + 2] = rv; rd.data[i * 4 + 3] = 255;
    }
    nc.getContext("2d").putImageData(nd, 0, 0); rc.getContext("2d").putImageData(rd, 0, 0);
    const mk = c => { const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = 16; return t; };   // 線形（色ではないので sRGB にしない）
    return (cache[key] = { normal: mk(nc), rough: mk(rc) });
  }
  // 既存の材質に凹凸とつやを足す。o.repeat＝並べる回数、o.normal＝凹凸の強さ、o.metal＝金属らしさ、o.sheen＝布の光沢（Physical のみ）
  function surface(mat, kind, o = {}) {
    const m = maps(kind, o.seed || 1, o.size || 512), rep = o.repeat || [1, 1];
    const nm = m.normal.clone(), rm = m.rough.clone(); nm.needsUpdate = rm.needsUpdate = true; nm.repeat.set(...rep); rm.repeat.set(...rep);
    mat.normalMap = nm; mat.normalScale = new THREE.Vector2(o.normal ?? 0.6, o.normal ?? 0.6);
    mat.roughnessMap = rm; mat.roughness = o.roughness ?? 1.0;   // 地図の値がそのまま粗さになる
    if (o.metal !== undefined) mat.metalness = o.metal;
    mat.needsUpdate = true; return mat;
  }
  function physical(base, o = {}) {   // 布の光沢（sheen）や、つやのある塗装（clearcoat）が必要な材質
    const m = new THREE.MeshPhysicalMaterial({ color: base.color ? base.color.clone() : new THREE.Color(1, 1, 1), map: base.map || null, roughness: base.roughness ?? 0.8, metalness: base.metalness ?? 0, ...o });
    return m;
  }
  function water(o = {}) {
    const m = new THREE.MeshPhysicalMaterial({ color: new THREE.Color(o.color ?? 0xdfe8ea).convertSRGBToLinear(), roughness: 0.04, metalness: 0, transmission: 0.92, thickness: o.thickness ?? 0.08, ior: 1.33,
      attenuationColor: new THREE.Color(o.tint ?? 0xb8d0c8).convertSRGBToLinear(), attenuationDistance: o.depth ?? 0.25, transparent: true, envMapIntensity: 1.0 });
    m.normalMap = maps("plaster", 77, 256).normal.clone(); m.normalMap.needsUpdate = true; m.normalScale = new THREE.Vector2(0.15, 0.15); m.userData.envFixed = true;
    return m;
  }
  function glass(o = {}) {
    const m = new THREE.MeshPhysicalMaterial({ color: new THREE.Color(o.color ?? 0xffffff).convertSRGBToLinear(), roughness: o.roughness ?? 0.05, metalness: 0, transmission: 0.95, thickness: o.thickness ?? 0.01, ior: 1.5, transparent: true });
    m.userData.envFixed = true; return m;
  }

  // ---------------------------------------------------------------- 光の筋と埃
  const SHAFT_VS = `varying vec2 vUv; varying vec3 vN; varying vec3 vV; varying vec3 vW;
    void main(){ vUv=uv; vec4 wp=modelMatrix*vec4(position,1.0); vW=wp.xyz; vec4 mv=viewMatrix*wp; vN=normalize(normalMatrix*normal); vV=normalize(-mv.xyz); gl_Position=projectionMatrix*mv; }`;
  const SHAFT_FS = `uniform vec3 uColor; uniform float uOpacity; uniform float uTime; varying vec2 vUv; varying vec3 vN; varying vec3 vV; varying vec3 vW;
    float h(vec3 p){ return fract(sin(dot(p, vec3(12.9898,78.233,37.719)))*43758.5453); }
    float n3(vec3 p){ vec3 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
      return mix(mix(mix(h(i),h(i+vec3(1,0,0)),f.x),mix(h(i+vec3(0,1,0)),h(i+vec3(1,1,0)),f.x),f.y),mix(mix(h(i+vec3(0,0,1)),h(i+vec3(1,0,1)),f.x),mix(h(i+vec3(0,1,1)),h(i+vec3(1,1,1)),f.x),f.y),f.z); }
    void main(){ float edge=pow(abs(dot(normalize(vN),normalize(vV))),1.6); float along=smoothstep(0.0,0.25,vUv.y)*pow(vUv.y,0.6);
      float m=0.65+0.35*n3(vW*1.7+vec3(0.0,-uTime*0.08,uTime*0.05)); gl_FragColor=vec4(uColor*uOpacity*edge*along*m,1.0); }`;
  // from（光源側）から to へ、半径 r0（光源側）→ r1 の円錐
  function shaft(o) {
    const from = new THREE.Vector3(...o.from), to = new THREE.Vector3(...o.to), dir = to.clone().sub(from), len = dir.length();
    const geo = new THREE.CylinderGeometry(o.r0 ?? 0.4, o.r1 ?? 1.0, len, 40, 1, true); geo.translate(0, -len / 2, 0);   // 上端（uv.y＝1、半径 r0）を原点＝光源側に置き、−Y 方向へ伸ばす
    const mat = new THREE.ShaderMaterial({ uniforms: { uColor: { value: new THREE.Color(o.color ?? 0xffd8a8).convertSRGBToLinear() }, uOpacity: { value: o.opacity ?? 0.25 }, uTime: { value: 0 } },
      vertexShader: SHAFT_VS, fragmentShader: SHAFT_FS, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide });
    const m = new THREE.Mesh(geo, mat); m.position.copy(from); m.quaternion.setFromUnitVectors(new THREE.Vector3(0, -1, 0), dir.normalize()); m.renderOrder = 10;
    m.userData.set = (t, k) => { mat.uniforms.uTime.value = t; mat.uniforms.uOpacity.value = (o.opacity ?? 0.25) * k; m.visible = k > 0.001; };
    return m;
  }
  let dustTex = null;
  function dust(o) {
    if (!dustTex) { const c = document.createElement("canvas"); c.width = c.height = 64; const x = c.getContext("2d"), g = x.createRadialGradient(32, 32, 0, 32, 32, 32);
      g.addColorStop(0, "rgba(255,255,255,1)"); g.addColorStop(0.35, "rgba(255,255,255,.45)"); g.addColorStop(1, "rgba(255,255,255,0)"); x.fillStyle = g; x.fillRect(0, 0, 64, 64);
      dustTex = new THREE.CanvasTexture(c); }
    const n = o.count ?? 400, r = rng(o.seed ?? 5), [x0, y0, z0] = o.min, [x1, y1, z1] = o.max, base = new Float32Array(n * 3), ph = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) { base[i * 3] = x0 + r() * (x1 - x0); base[i * 3 + 1] = y0 + r() * (y1 - y0); base[i * 3 + 2] = z0 + r() * (z1 - z0); ph[i * 3] = r() * 6.28; ph[i * 3 + 1] = 0.3 + r() * 0.7; ph[i * 3 + 2] = r() * 6.28; }
    const pos = new Float32Array(n * 3), geo = new THREE.BufferGeometry(); geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    const mat = new THREE.PointsMaterial({ color: new THREE.Color(o.color ?? 0xffe6c0).convertSRGBToLinear(), size: o.size ?? 0.012, map: dustTex, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, opacity: o.opacity ?? 0.8, sizeAttenuation: true });
    const points = new THREE.Points(geo, mat); points.renderOrder = 11;
    function update(t, k = 1) {   // ゆっくり漂い、少し沈む（空気の流れ）。範囲の外に出たら反対側へ回る
      for (let i = 0; i < n; i++) {
        const s = ph[i * 3 + 1];
        let x = base[i * 3] + 0.04 * Math.sin(t * 0.3 * s + ph[i * 3]) + 0.02 * t * s, y = base[i * 3 + 1] - 0.012 * t * s + 0.03 * Math.sin(t * 0.5 * s + ph[i * 3 + 2]), z = base[i * 3 + 2] + 0.03 * Math.cos(t * 0.27 * s + ph[i * 3 + 2]);
        x = x0 + (((x - x0) % (x1 - x0)) + (x1 - x0)) % (x1 - x0); y = y0 + (((y - y0) % (y1 - y0)) + (y1 - y0)) % (y1 - y0);
        pos[i * 3] = x; pos[i * 3 + 1] = y; pos[i * 3 + 2] = z;
      }
      geo.attributes.position.needsUpdate = true; mat.opacity = (o.opacity ?? 0.8) * k; points.visible = k > 0.001;
    }
    return { points, update };
  }

  // ---------------------------------------------------------------- 動きのぶれ・光のにじみ（2D）
  let acc = null;
  // draw(tk) が ctx に 1 コマを描く。n 回描いて平均する（露光 shutter 秒、コマの時刻を中心に）。n<=1 なら 1 回だけ
  function motionBlur(ctx, t, o, draw) {
    const n = Math.max(1, o.n | 0), sh = o.shutter ?? 1 / 60;
    if (n <= 1) { draw(t); return; }
    if (!acc) { acc = document.createElement("canvas"); acc.width = W; acc.height = H; }
    const a = acc.getContext("2d"); a.globalAlpha = 1; a.clearRect(0, 0, W, H);
    for (let k = 0; k < n; k++) {
      const tk = t - sh / 2 + sh * k / (n - 1);
      ctx.clearRect(0, 0, W, H); draw(tk);
      a.globalAlpha = 1 / (k + 1); a.drawImage(ctx.canvas, 0, 0);   // 等しい重みの平均（逐次）
    }
    a.globalAlpha = 1; ctx.clearRect(0, 0, W, H); ctx.drawImage(acc, 0, 0);
  }
  let bl = null;
  // 明るい所だけを取り出してぼかし、加算に近い「スクリーン」で重ねる。thr＝しきい値の強さ（コントラストで暗部を落とす）
  function bloom(ctx, k, o = {}) {
    if (k <= 0.005) return;
    const s = 4, w = W / s, h = H / s;
    if (!bl) { bl = [document.createElement("canvas"), document.createElement("canvas")]; for (const c of bl) { c.width = w; c.height = h; } }
    const [c1, c2] = bl, x1 = c1.getContext("2d"), x2 = c2.getContext("2d");
    x1.clearRect(0, 0, w, h); x1.filter = `brightness(${o.gain ?? 0.85}) contrast(${o.thr ?? 4}) saturate(1.15)`; x1.drawImage(ctx.canvas, 0, 0, w, h); x1.filter = "none";
    x2.clearRect(0, 0, w, h); x2.filter = `blur(${o.radius ?? 10}px)`; x2.drawImage(c1, 0, 0); x2.filter = "none";
    ctx.save(); ctx.globalCompositeOperation = "screen"; ctx.globalAlpha = Math.min(1, k); ctx.imageSmoothingQuality = "high"; ctx.drawImage(c2, 0, 0, W, H); ctx.restore();
  }

  root.Cine = { init, useEnv, surface, physical, water, glass, shaft, dust, motionBlur, bloom, maps, PRESETS };
})(typeof window !== "undefined" ? window : globalThis);
