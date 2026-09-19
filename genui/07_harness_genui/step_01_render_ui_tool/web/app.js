// Generative UI step 01 - the browser surface: one renderer per catalog type,
// keyed by element type, walking the element map from root.

const surface = document.getElementById("surface");
const status = document.getElementById("status");

const RENDERERS = {
  Card(props, children) {
    const box = el("div", "card");
    if (props.title) box.append(el("h2", "", props.title));
    box.append(...children);
    return box;
  },
  Stack(props, children) {
    const box = el("div", props.direction === "row" ? "stack-row" : "stack-column");
    box.append(...children);
    return box;
  },
  Text(props) {
    return el("p", "", props.text);
  },
  Metric(props) {
    const box = el("div", "metric");
    box.append(el("div", "label", props.label));
    const value = el("div", "value", String(props.value));
    if (props.delta) {
      const up = /^[+▲]/.test(String(props.delta));
      value.append(el("span", up ? "delta" : "delta down", props.delta));
    }
    box.append(value);
    return box;
  },
  Table(props) {
    const table = el("table");
    const head = table.createTHead().insertRow();
    for (const column of props.columns) head.append(el("th", "", String(column)));
    const body = table.createTBody();
    for (const row of props.rows) {
      const tr = body.insertRow();
      for (const cell of Array.isArray(row) ? row : [row]) tr.append(el("td", "", String(cell)));
    }
    return table;
  },
  Chart(props) {
    const box = el("div", "chart");
    if (props.title) box.append(el("h3", "", props.title));
    const values = props.values.map(Number);
    const top = Math.max(...values, 1);
    if (props.kind === "line") {
      box.append(linePath(values, top));
      return box;
    }
    values.forEach((value, i) => {
      const row = el("div", "bar-row");
      const bar = el("div", "bar");
      bar.style.width = `${(value / top) * 100}%`;
      row.append(el("span", "", String(props.labels[i])), bar, el("span", "", String(value)));
      box.append(row);
    });
    return box;
  },
};

function linePath(values, top) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 300 100");
  svg.setAttribute("class", "line");
  const step = values.length > 1 ? 300 / (values.length - 1) : 0;
  const points = values.map((v, i) => `${i * step},${100 - (v / top) * 90}`).join(" ");
  const path = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
  path.setAttribute("points", points);
  path.setAttribute("fill", "none");
  path.setAttribute("stroke", "#7aa2f7");
  path.setAttribute("stroke-width", "3");
  svg.append(path);
  return svg;
}

// Walk the element map from root: children are rendered first, then handed
// to the parent's renderer. Unknown types get a visible placeholder.
export function render(spec, id = spec.root) {
  const element = spec.elements[id];
  const children = (element.children || []).map((child) => render(spec, child));
  const draw = RENDERERS[element.type];
  if (!draw) return el("p", "", `(${element.type}: no web renderer)`);
  const node = draw(element.props || {}, children);
  node.dataset.id = id;
  return node;
}

function el(tag, className = "", text = "") {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}

// One SSE event per render_ui call; the newest spec replaces the surface.
const source = new EventSource("/events");
source.onopen = () => { status.textContent = "connected, waiting for render_ui"; };
source.onmessage = (event) => {
  const spec = JSON.parse(event.data);
  surface.replaceChildren(render(spec));
  status.textContent = `rendered ${Object.keys(spec.elements).length} elements from root "${spec.root}"`;
};
source.onerror = () => { status.textContent = "disconnected"; };
