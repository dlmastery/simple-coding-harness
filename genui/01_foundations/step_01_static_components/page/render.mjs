// Step 01 - three hand-written renderers, keyed by component name.
// Each one turns props into an HTML string. Nothing here touches the DOM,
// so `node --test` can run these without a browser.

export function esc(value) {
  // Every prop the model wrote goes through here before it becomes markup.
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

export function list(value) {
  // A prop that should be an array. The schema says so, but not every endpoint enforces it.
  return Array.isArray(value) ? value : [];
}

export function Metric({ title, value, delta }) {
  const sign = String(delta ?? "").trim().startsWith("-") ? "down" : "up";
  return `<div class="card metric">
    <div class="title">${esc(title)}</div>
    <div class="value">${esc(value)}</div>
    <div class="delta ${sign}">${esc(delta)}</div>
  </div>`;
}

export function Table({ columns, rows }) {
  const head = list(columns).map((c) => `<th>${esc(c)}</th>`).join("");
  const body = list(rows)
    .map((row) => `<tr>${list(row).map((cell) => `<td>${esc(cell)}</td>`).join("")}</tr>`)
    .join("");
  return `<div class="card table"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
}

export function Chart({ kind = "bar", labels, values }) {
  // A small inline SVG: bars or a polyline, scaled to the largest value.
  const width = 420, height = 160, pad = 24;
  const numbers = list(values).map((v) => Math.max(0, Number(v) || 0)); // a bar cannot have a negative height
  const max = Math.max(1, ...numbers);
  const step = (width - 2 * pad) / Math.max(1, numbers.length);
  const y = (v) => height - pad - ((height - 2 * pad) * v) / max;
  let marks;
  if (kind === "line") {
    const points = numbers.map((v, i) => `${pad + step * (i + 0.5)},${y(v)}`).join(" ");
    marks = `<polyline points="${points}" fill="none" stroke="currentColor" stroke-width="2"/>`;
  } else {
    marks = numbers
      .map((v, i) => `<rect x="${pad + step * i + step * 0.15}" y="${y(v)}" width="${step * 0.7}" height="${height - pad - y(v)}" rx="2"/>`)
      .join("");
  }
  const axis = list(labels)
    .map((label, i) => `<text x="${pad + step * (i + 0.5)}" y="${height - 6}" text-anchor="middle">${esc(label)}</text>`)
    .join("");
  return `<div class="card chart"><svg viewBox="0 0 ${width} ${height}" class="${esc(kind)}">${marks}${axis}</svg></div>`;
}

export const RENDERERS = { Metric, Table, Chart };

export function render(component, props) {
  // The page never trusts the name: an unknown component becomes a visible stub.
  // hasOwn, not `in`: "constructor" and "toString" are not components.
  if (!Object.hasOwn(RENDERERS, component)) return `<div class="card unknown">unknown component: ${esc(component)}</div>`;
  return RENDERERS[component](props ?? {});
}
