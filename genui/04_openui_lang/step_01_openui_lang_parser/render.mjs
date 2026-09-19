// Step 01 - a hand-written DOM renderer for the eight catalog components.
//
// The renderer walks the tree from resolve(). Element nodes go to one
// function per component name; placeholder nodes become grey skeleton boxes,
// which is what the reader sees while a forward reference waits for its
// definition to stream in.

function el(tag, className, ...children) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  for (const child of children) node.append(child);
  return node;
}

const RENDERERS = {
  Stack: (p) => el("div", `stack ${p.direction ?? "column"} gap-${p.gap ?? "m"}`, ...renderList(p.children)),
  Text: (p) => el("p", `text ${p.size ?? "body"}`, String(p.text ?? "")),
  Metric: (p) => el("div", "metric",
    el("div", "label", String(p.label ?? "")),
    el("div", "value", String(p.value ?? "")),
    el("div", `delta ${String(p.delta ?? "").startsWith("-") ? "down" : "up"}`, String(p.delta ?? ""))),
  Table: (p) => {
    const table = el("table", "table");
    table.append(el("thead", "", el("tr", "", ...(p.columns ?? []).map((c) => el("th", "", String(c))))));
    // a row that is not a list (the model wrote a string) becomes a one-cell row instead of a thrown error
    table.append(el("tbody", "", ...(p.rows ?? []).map((row) => el("tr", "", ...(Array.isArray(row) ? row : [row]).map((cell) => el("td", "", String(cell)))))));
    return table;
  },
  BarChart: (p) => {
    const values = (p.values ?? []).map(Number);
    const max = Math.max(1, ...values);
    const bars = values.map((v, i) => {
      const bar = el("div", "bar", el("span", "bar-label", String((p.labels ?? [])[i] ?? "")));
      bar.style.height = `${Math.round((v / max) * 100)}%`;
      bar.title = String(v);
      return bar;
    });
    return el("div", "chart", el("div", "chart-title", String(p.title ?? "")), el("div", "bars", ...bars));
  },
  Card: (p) => el("section", "card", el("h3", "", String(p.title ?? "")), ...renderList(p.children)),
  Button: (p) => {
    const button = el("button", `button ${p.variant ?? "secondary"}`, String(p.label ?? ""));
    button.dataset.action = String(p.action ?? "");
    return button;
  },
  Input: (p) => {
    const input = el("input", "input");
    input.name = String(p.name ?? "");
    input.placeholder = String(p.placeholder ?? "");
    input.type = String(p.type ?? "text");
    return input;
  },
};

function renderList(children) {
  return (Array.isArray(children) ? children : []).map(renderNode);
}

export function renderNode(node) {
  if (node && node.type === "placeholder") {
    const box = el("div", "skeleton");
    box.dataset.ref = node.name;
    return box;
  }
  if (node && node.type === "element") {
    const render = RENDERERS[node.typeName];
    if (!render) return el("div", "error", `no renderer for ${node.typeName}`);
    const dom = render(node.props ?? {});
    if (node.statementId) dom.dataset.statement = node.statementId;
    return dom;
  }
  return el("span", "", node == null ? "" : String(node));
}

// Replace the container's content with the tree from one parse result.
export function render(result, container) {
  container.replaceChildren(result.root ? renderNode(result.root) : el("div", "skeleton"));
}
