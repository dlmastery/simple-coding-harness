// Three hand-written renderers, one per component the state can hold, in
// the spirit of sub-theme 01 step 01: the page owns the components and the
// agent fills their props. Input is the `dashboard` object from the
// shared state; output is a DOM subtree, rebuilt on every state change.

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

export function renderMetric({ title, value, delta }) {
  const card = el("div", "metric");
  card.appendChild(el("div", "metric-title", title));
  card.appendChild(el("div", "metric-value", value));
  if (delta) card.appendChild(el("div", "metric-delta", delta));
  return card;
}

export function renderTable({ columns, rows }) {
  const table = el("table");
  const head = table.createTHead().insertRow();
  for (const column of columns) head.appendChild(el("th", "", column));
  const body = table.createTBody();
  for (const row of rows) {
    const tr = body.insertRow();
    for (const cell of row) tr.appendChild(el("td", "", String(cell)));
  }
  return table;
}

export function renderChart({ kind, labels, values }) {
  const max = Math.max(...values, 1);
  const chart = el("div", `chart chart-${kind}`);
  values.forEach((value, i) => {
    const column = el("div", "bar-column");
    const bar = el("div", "bar");
    bar.style.height = `${Math.round((value / max) * 100)}%`;
    bar.title = `${labels[i]}: ${value}`;
    column.appendChild(bar);
    column.appendChild(el("div", "bar-label", labels[i]));
    chart.appendChild(column);
  });
  return chart;
}

export function renderDashboard(dashboard) {
  const root = el("div", "dashboard");
  const metrics = el("div", "metrics");
  for (const metric of dashboard.metrics || []) metrics.appendChild(renderMetric(metric));
  root.appendChild(metrics);
  if (dashboard.table) root.appendChild(renderTable(dashboard.table));
  if (dashboard.chart) root.appendChild(renderChart(dashboard.chart));
  if (dashboard.purchases && dashboard.purchases.length) {
    const list = el("ul", "purchases");
    for (const p of dashboard.purchases) list.appendChild(el("li", "", `${p.item}: $${p.cost}`));
    root.appendChild(list);
  }
  return root;
}
