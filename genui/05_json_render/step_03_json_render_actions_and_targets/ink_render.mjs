// The second target: the same catalog and the same spec, rendered in the
// terminal by @json-render/ink. One implementation per catalog entry again,
// written with ink's Box and Text instead of HTML. createRenderer wraps the
// providers; the state prop seeds the {"$state": "/path"} expressions.
//
//     node ink_render.mjs demo_spec.json        # print the spec as text
//
// renderSpecToText() renders into a fake stdout and returns the last frame,
// which is what the CLI prints and what the tests compare.
import { readFileSync } from "node:fs";
import { EventEmitter } from "node:events";
import React from "react";
import { render, Box, Text } from "ink";
import { createRenderer } from "@json-render/ink";
import { catalog } from "./catalog.mjs";

const h = React.createElement;

function bars(labels, values, width = 24) {
  const max = Math.max(...values, 1);
  const label = Math.max(...labels.map((l) => l.length));
  return labels.map((name, i) => {
    const filled = Math.round((width * values[i]) / max);
    return `${name.padEnd(label)} ${"█".repeat(filled).padEnd(width)} ${values[i]}`;
  });
}

function tableLines(columns, rows) {
  const widths = columns.map((c, i) => Math.max(c.length, ...rows.map((r) => String(r[i] ?? "").length)));
  const line = (cells) => cells.map((cell, i) => String(cell ?? "").padEnd(widths[i])).join("  ");
  return [line(columns), widths.map((w) => "-".repeat(w)).join("  "), ...rows.map(line)];
}

export const components = {
  Card: ({ element, children }) =>
    h(Box, { flexDirection: "column", borderStyle: "round", paddingX: 1, marginBottom: 0 },
      h(Text, { bold: true }, element.props.title),
      element.props.subtitle ? h(Text, { dimColor: true }, element.props.subtitle) : null,
      children),
  Row: ({ children }) => h(Box, { flexDirection: "row", gap: 2 }, children),
  Text: ({ element }) =>
    h(Text, { dimColor: element.props.tone === "muted", bold: element.props.tone === "strong" }, element.props.text),
  Metric: ({ element }) =>
    h(Box, { flexDirection: "column", marginRight: 2 },
      h(Text, { dimColor: true }, element.props.label.toUpperCase()),
      h(Text, { bold: true }, String(element.props.value)),
      element.props.delta ? h(Text, { color: "green" }, element.props.delta) : null),
  Table: ({ element }) =>
    h(Box, { flexDirection: "column" },
      ...tableLines(element.props.columns ?? [], element.props.rows ?? []).map((line, i) => h(Text, { key: i }, line))),
  Chart: ({ element }) =>
    h(Box, { flexDirection: "column" },
      ...bars(element.props.labels ?? [], element.props.values ?? []).map((line, i) => h(Text, { key: i, color: "blue" }, line))),
  Button: ({ element }) => h(Text, { color: "cyan" }, `[ ${element.props.label} ]`),
};

export const InkRenderer = createRenderer(catalog, components);

class FakeStdout extends EventEmitter {
  constructor(columns) {
    super();
    this.columns = columns;
    this.frames = [];
  }
  write(text) {
    this.frames.push(text);
    return true;
  }
}

class FakeStdin extends EventEmitter {
  isTTY = true;
  setRawMode() {}
  setEncoding() {}
  resume() {}
  pause() {}
  ref() {}
  unref() {}
  read() {
    return null;
  }
}

export async function renderSpecToText(spec, { columns = 88, onAction } = {}) {
  const stdout = new FakeStdout(columns);
  const instance = render(h(InkRenderer, { spec, state: spec.state ?? {}, onAction }), {
    stdout,
    stdin: new FakeStdin(),
    debug: true,
    patchConsole: false,
    exitOnCtrlC: false,
  });
  await new Promise((resolve) => setTimeout(resolve, 30));
  instance.unmount();
  // On a CI runner Ink unmounts with one more, empty write: keep the last frame that has content.
  return stdout.frames.filter((frame) => frame.trim()).at(-1) ?? "";
}

if (process.argv[1] && import.meta.url.endsWith(process.argv[1].replace(/\\/g, "/").split("/").pop())) {
  const file = process.argv[2] ?? "demo_spec.json";
  const spec = JSON.parse(readFileSync(file, "utf-8"));
  process.stdout.write(await renderSpecToText(spec) + "\n");
}
