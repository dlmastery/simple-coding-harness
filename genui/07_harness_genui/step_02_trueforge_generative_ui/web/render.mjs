// Generative UI step 02 - a DOM renderer for the components TrueForge's agent
// emits. Args are positional, in the order the agent writes them. Anything
// the renderer does not know is drawn as a labelled box, so the page never
// goes blank on a new component, and a pending reference is a dashed
// placeholder that fills in when its line arrives.

const RENDERERS = {
  Stack([children, direction = "column", gap = "m", align, justify, wrap]) {
    const box = el("div", `stack ${direction} gap-${gap}`);
    if (align) box.style.alignItems = ALIGN[align] ?? align;
    if (justify) box.style.justifyContent = JUSTIFY[justify] ?? justify;
    if (wrap) box.style.flexWrap = "wrap";
    box.append(...list(children).map(render));
    return box;
  },
  Card([children, variant = "card", direction = "column", gap = "s", align, justify]) {
    const box = el("div", `card ${variant} stack ${direction} gap-${gap}`);
    if (align) box.style.alignItems = ALIGN[align] ?? align;
    if (justify) box.style.justifyContent = JUSTIFY[justify] ?? justify;
    box.append(...list(children).map(render));
    return box;
  },
  CardHeader([title, subtitle]) {
    const box = el("div", "card-header");
    box.append(el("h2", "", title));
    if (subtitle) box.append(el("p", "subtitle", subtitle));
    return box;
  },
  TextContent([text, variant = "default"]) {
    return el("p", `text ${variant}`, String(text));
  },
  Tag([text, icon, size = "md", variant = "default"]) {
    return el("span", `tag ${variant} ${size}`, text);
  },
  Table([columns]) {
    const table = el("table");
    const cols = list(columns).map((c) => (c && c.type === "Col" ? c.args : ["?", []]));
    const head = table.createTHead().insertRow();
    for (const [header] of cols) head.append(el("th", "", String(header)));
    const rows = Math.max(0, ...cols.map(([, values]) => list(values).length));
    const body = table.createTBody();
    for (let r = 0; r < rows; r++) {
      const tr = body.insertRow();
      for (const [, values, kind] of cols) tr.append(el("td", kind === "number" ? "num" : "", String(list(values)[r] ?? "")));
    }
    return table;
  },
  BarChart([categories, series, variant, xLabel, yLabel]) {
    return chart("bar", categories, series, xLabel, yLabel);
  },
  LineChart([categories, series, variant, xLabel, yLabel]) {
    return chart("line", categories, series, xLabel, yLabel);
  },
  PieChart([labels, values, variant = "pie"]) {
    const box = el("div", "chart pie-box");
    const nums = list(values).map(Number);
    const total = nums.reduce((a, b) => a + b, 0) || 1;
    let angle = 0;
    const stops = nums.map((v, i) => {
      const from = angle;
      angle += (v / total) * 360;
      return `${COLORS[i % COLORS.length]} ${from}deg ${angle}deg`;
    });
    const disc = el("div", `pie ${variant}`);
    disc.style.background = `conic-gradient(${stops.join(", ")})`;
    const legend = el("ul", "legend");
    list(labels).forEach((label, i) => {
      const item = el("li", "", `${label}: ${nums[i]}`);
      item.style.setProperty("--swatch", COLORS[i % COLORS.length]);
      legend.append(item);
    });
    box.append(disc, legend);
    return box;
  },
};

const ALIGN = { start: "flex-start", end: "flex-end", center: "center", stretch: "stretch" };
const JUSTIFY = { start: "flex-start", end: "flex-end", center: "center", between: "space-between", around: "space-around", evenly: "space-evenly" };
const COLORS = ["#7aa2f7", "#9ece6a", "#e0af68", "#f7768e", "#bb9af7", "#7dcfff"];

function chart(kind, categories, series, xLabel, yLabel) {
  const box = el("div", "chart");
  const cats = list(categories);
  const lines = list(series).map((s) => (s && s.type === "Series" ? { name: s.args[0], data: list(s.args[1]).map(Number) } : { name: "?", data: [] }));
  const top = Math.max(1, ...lines.flatMap((s) => s.data));
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 320 140");
  svg.setAttribute("class", kind);
  const width = 300 / Math.max(1, cats.length);
  lines.forEach((s, si) => {
    if (kind === "bar") {
      s.data.forEach((v, i) => {
        const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        const w = (width * 0.7) / lines.length;
        rect.setAttribute("x", 10 + i * width + width * 0.15 + si * w);
        rect.setAttribute("y", 110 - (v / top) * 100);
        rect.setAttribute("width", w);
        rect.setAttribute("height", (v / top) * 100);
        rect.setAttribute("fill", COLORS[si % COLORS.length]);
        svg.append(rect);
      });
    } else {
      const poly = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
      poly.setAttribute("points", s.data.map((v, i) => `${10 + i * width + width / 2},${110 - (v / top) * 100}`).join(" "));
      poly.setAttribute("fill", "none");
      poly.setAttribute("stroke", COLORS[si % COLORS.length]);
      poly.setAttribute("stroke-width", "3");
      svg.append(poly);
    }
  });
  cats.forEach((c, i) => {
    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("x", 10 + i * width + width / 2);
    label.setAttribute("y", 128);
    label.setAttribute("text-anchor", "middle");
    label.setAttribute("font-size", "10");
    label.textContent = String(c);
    svg.append(label);
  });
  box.append(svg);
  const caption = [yLabel, xLabel].filter(Boolean).join(" by ");
  const names = lines.map((s) => s.name).join(", ");
  if (caption || names) box.append(el("p", "caption", [caption, names].filter(Boolean).join(" - ")));
  return box;
}

// One resolved node to one DOM node. Scalars become text; unknown components
// become a labelled box; pending references become a placeholder.
export function render(node) {
  if (node === null || typeof node !== "object") return el("span", "", String(node));
  if (Array.isArray(node)) {
    const box = el("div", "stack column gap-s");
    box.append(...node.map(render));
    return box;
  }
  if (node.type === "Pending") return el("div", "pending", `waiting for ${node.ref}`);
  if (node.type === "Cycle") return el("div", "pending", `cycle at ${node.ref}`);
  const draw = RENDERERS[node.type];
  if (draw) return draw(node.args);
  const box = el("div", "unknown");
  box.append(el("strong", "", node.type), el("code", "", JSON.stringify(node.args)));
  return box;
}

function list(value) {
  return Array.isArray(value) ? value : value === undefined || value === null ? [] : [value];
}

function el(tag, className = "", text = "") {
  const node = document.createElement(tag);
  if (className.trim()) node.className = className.trim();
  if (text !== "") node.textContent = text;
  return node;
}
