// Step 04 - the catalog renderers, two tree walkers, and the escape hatch.
// Each renderer turns props into an HTML string; the walkers put the strings
// together. Nothing here touches the DOM, so `node --test` can run it all.
import { isPartial } from "./partial-json.mjs";
import { sandboxed } from "./sandbox.mjs";

export function esc(value) {
  // Every prop the model wrote goes through here before it becomes markup.
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

export function list(value) {
  // A prop that should be an array. The schema says so, but the page renders
  // the document before it is validated, and not every endpoint enforces it.
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

// Layout components take the rendered children as a second argument.
export function Card({ title }, children = "") {
  return `<div class="card box"><div class="heading">${esc(title)}</div>${children}</div>`;
}

export function Row(props, children = "") {
  return `<div class="row">${children}</div>`;
}

export function Column(props, children = "") {
  return `<div class="column">${children}</div>`;
}

export function Text({ text }) {
  return `<p class="text">${esc(text)}</p>`;
}

export function Button({ label, action }) {
  return `<button class="action" data-action="${esc(action)}">${esc(label)}</button>`;
}

const PENDING = `<div class="card pending"></div>`;

export function GeneratedView(props) {
  // The escape hatch: model-written HTML in the step 03 sandbox. The document
  // goes through esc() because it is an attribute value here; the browser
  // unescapes it when it reads srcdoc. While the html prop is still being
  // written the slot stays pending: a half document is not mounted, and not
  // mounted again on every delta.
  if (isPartial(props)) return PENDING;
  return `<iframe class="card generated" sandbox="allow-scripts" srcdoc="${esc(sandboxed(String(props.html ?? "")))}"></iframe>`;
}

export const RENDERERS = { Card, Row, Column, Text, Metric, Table, Chart, Button, GeneratedView };

export function render(component, props, children = "") {
  // The page never trusts the name: an unknown component becomes a visible stub.
  // hasOwn, not `in`: "constructor" and "toString" are not components.
  if (!Object.hasOwn(RENDERERS, component)) return `<div class="card unknown">unknown component: ${esc(component)}</div>`;
  return RENDERERS[component](props ?? {}, children);
}

function isComponent(node) {
  return node !== null && typeof node === "object" && Object.hasOwn(RENDERERS, node.type) && typeof node.props === "object";
}

export function renderTree(node) {
  // A nested tree. A node still open in the stream renders as pending, with
  // whatever closed children it already has inside it.
  if (!isComponent(node)) return node ? PENDING : "";
  const children = list(node.children).map(renderTree).join("");
  const html = render(node.type, node.props, children);
  return isPartial(node) ? `<div class="pending-wrap">${html}</div>` : html;
}

export function renderFlat(spec, id = spec?.root, seen = new Set()) {
  // A flat element map. A child id whose element has not arrived yet renders
  // as a pending slot, so the layout holds still while the details stream in.
  const elements = spec?.elements;
  const node = typeof id === "string" && elements && typeof elements === "object" && Object.hasOwn(elements, id) ? elements[id] : undefined;
  if (node === undefined || seen.has(id)) return PENDING;
  seen.add(id);
  if (!isComponent(node)) return PENDING;
  const children = list(node.children).map((child) => renderFlat(spec, child, seen)).join("");
  const html = render(node.type, node.props, children);
  return isPartial(node) ? `<div class="pending-wrap">${html}</div>` : html;
}

export function renderSpec(spec, shape) {
  if (spec === null || spec === undefined) return "";
  return shape === "flat" ? renderFlat(spec) : renderTree(spec);
}
