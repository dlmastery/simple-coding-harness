// Step 03 - the view's catalog: four renderers keyed by component name.
//
// The server's `components` list has the shape of sub-theme 01's static
// step: `{"component": "Metric", "props": {...}}`. Each renderer turns props
// into an HTML string, so `node --test` covers it without a browser. Every
// prop goes through `esc` before it becomes markup: the spec is data, and
// the only place markup is trusted to run is the generated region, which
// has its own frame (sandbox.mjs).

export function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

export function Metric({ title, value, delta }) {
  return `<div class="card"><div class="muted">${esc(title)}</div><div class="value">${esc(value)}</div><div class="muted">${esc(delta)}</div></div>`;
}

// The spec is the server's data: a prop that should be a list but is not becomes a list, never a thrown error.
const list = (value) => (Array.isArray(value) ? value : value === undefined || value === null ? [] : [value]);

export function Table({ columns = [], rows = [] }) {
  const head = list(columns).map((c, i) => `<th class="${i ? "num" : ""}">${esc(c)}</th>`).join("");
  const body = list(rows).map((row) => `<tr>${list(row).map((cell, i) => `<td class="${i ? "num" : ""}">${esc(cell)}</td>`).join("")}</tr>`).join("");
  return `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

export function BarChart({ labels = [], values = [] }) {
  labels = list(labels);
  const numbers = list(values).map((v) => Number(v) || 0);
  const most = Math.max(1, ...numbers);
  const bars = numbers.map((v, i) => {
    const label = labels.length <= 14 ? `<span>${esc(labels[i] ?? "")}</span>` : "";
    return `<div class="bar" style="height:${Math.round(100 * v / most)}%" title="${esc(labels[i] ?? "")}: ${v}">${label}</div>`;
  });
  return `<div class="bars">${bars.join("")}</div>`;
}

export function Text({ text }) {
  return `<p class="text">${esc(text)}</p>`;
}

export const RENDERERS = { Metric, Table, BarChart, Text };

export function render(component, props) {
  // The view never trusts the name: an unknown component becomes a visible stub.
  const renderer = RENDERERS[component];
  if (!renderer) return `<div class="card unknown">unknown component: ${esc(component)}</div>`;
  return renderer(props ?? {});
}

export function renderComponents(components = []) {
  // Metrics sit in one row of cards; everything else stacks in order.
  components = list(components);
  const metrics = components.filter((c) => c?.component === "Metric");
  const rest = components.filter((c) => c?.component !== "Metric");
  const cards = metrics.length ? `<div class="cards">${metrics.map((c) => render(c.component, c.props)).join("")}</div>` : "";
  return cards + rest.map((c) => render(c?.component, c?.props)).join("");
}
