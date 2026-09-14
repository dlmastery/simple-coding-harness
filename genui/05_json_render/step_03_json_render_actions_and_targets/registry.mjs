// One React implementation per catalog entry. defineRegistry builds the map
// Renderer reads and types the props. No JSX: htm gives the same tagged
// template in the browser and in Node, so tests render this registry with
// react-dom/server. Button is the one component that emits an event; the
// renderer looks up on.press in the element and dispatches the action.
import React from "react";
import htm from "htm";
import { defineRegistry } from "@json-render/react";
import { catalog } from "./catalog.mjs";

const html = htm.bind(React.createElement);

export const { registry } = defineRegistry(catalog, {
  components: {
    Card: ({ props, children }) => html`
      <section className="card">
        <h2>${props.title}</h2>
        ${props.subtitle ? html`<p className="subtitle">${props.subtitle}</p>` : null}
        ${children}
      </section>`,
    Row: ({ props, children }) => html`
      <div className=${"row " + (props.gap === "large" ? "gap-large" : "gap-small")}>${children}</div>`,
    Text: ({ props }) => html`<p className=${"text " + (props.tone ?? "normal")}>${props.text}</p>`,
    Metric: ({ props }) => html`
      <div className="metric">
        <div className="label">${props.label}</div>
        <div className="value">${props.value}</div>
        ${props.delta ? html`<div className="delta">${props.delta}</div>` : null}
      </div>`,
    // A prop may be a {"$state": "/path"} expression whose state has not
    // arrived yet; it resolves to undefined until then, so arrays get a default.
    Table: ({ props }) => html`
      <table>
        <thead><tr>${(props.columns ?? []).map((c) => html`<th key=${c}>${c}</th>`)}</tr></thead>
        <tbody>
          ${(props.rows ?? []).map((row, i) => html`<tr key=${i}>${row.map((cell, j) => html`<td key=${j}>${cell}</td>`)}</tr>`)}
        </tbody>
      </table>`,
    Button: ({ props, emit }) => html`
      <button className=${"button " + (props.variant ?? "primary")} onClick=${() => emit("press")}>${props.label}</button>`,
    Chart: ({ props }) => {
      const labels = props.labels ?? [];
      const values = props.values ?? [];
      const max = Math.max(...values, 1);
      return html`
        <div className=${"chart " + props.kind}>
          ${labels.map((label, i) => html`
            <div className="bar-slot" key=${label}>
              <div className="bar" style=${{ height: `${(100 * (values[i] ?? 0)) / max}%` }} title=${String(values[i] ?? "")} />
              <div className="bar-label">${label}</div>
            </div>`)}
        </div>`;
    },
  },
});
