// 「解剖された立方体」マーク（SVG 文字列を返す）。
// 上面・左面は不透明な「外側」、右面は少し外へずらして回路状の「内側」を見せる。
function cubeMark({ cx, cy, s, light = "#EAF1F8", mid = "#A9BDD3", line = "#46D3F0", bg = "#0A1424" }) {
  const k = 0.8660254;
  const P = (x, y) => [cx + x, cy + y];
  const top = P(0, -s), ur = P(k * s, -s / 2), lr = P(k * s, s / 2);
  const bot = P(0, s), ll = P(-k * s, s / 2), ul = P(-k * s, -s / 2), c = P(0, 0);
  const pts = (...a) => a.map(p => p.join(",")).join(" ");
  // 右面をずらす量（切り離した感じ）
  const dx = s * 0.10, dy = s * 0.058;
  const R = (u, v) => [c[0] + dx + u * (ur[0] - c[0]) + v * (bot[0] - c[0]),
                       c[1] + dy + u * (ur[1] - c[1]) + v * (bot[1] - c[1])];
  const traces = [
    [[0.18, 0.2], [0.5, 0.2], [0.5, 0.45], [0.82, 0.45]],
    [[0.18, 0.55], [0.32, 0.55], [0.32, 0.82], [0.68, 0.82]],
    [[0.5, 0.45], [0.5, 0.65], [0.82, 0.65]],
  ];
  const nodes = [[0.18, 0.2], [0.82, 0.45], [0.18, 0.55], [0.68, 0.82], [0.82, 0.65], [0.5, 0.45]];
  const sw = s * 0.028;
  const tr = traces.map(t => `<polyline points="${t.map(([u, v]) => R(u, v).join(",")).join(" ")}" fill="none" stroke="${line}" stroke-width="${sw}" stroke-linecap="round" stroke-linejoin="round"/>`).join("");
  const nd = nodes.map(([u, v]) => { const [x, y] = R(u, v); return `<circle cx="${x}" cy="${y}" r="${s * 0.045}" fill="${bg}" stroke="${line}" stroke-width="${sw}"/>`; }).join("");
  const face = pts(R(0, 0), R(1, 0), R(1, 1), R(0, 1));
  return `
  <polygon points="${pts(top, ur, c, ul)}" fill="${light}"/>
  <polygon points="${pts(ul, c, bot, ll)}" fill="${mid}"/>
  <line x1="${c[0]}" y1="${c[1]}" x2="${bot[0]}" y2="${bot[1]}" stroke="${line}" stroke-width="${sw * 1.4}" stroke-linecap="round"/>
  <line x1="${c[0]}" y1="${c[1]}" x2="${ur[0]}" y2="${ur[1]}" stroke="${line}" stroke-width="${sw * 1.4}" stroke-linecap="round"/>
  <polygon points="${face}" fill="${line}" fill-opacity="0.08" stroke="${line}" stroke-width="${sw}" stroke-linejoin="round"/>
  ${tr}${nd}`;
}
module.exports = { cubeMark };
