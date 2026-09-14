// Step 04 - the catalog: step 02's eight components plus Markdown and HtmlArtifact.
//
// Each defineComponent() pairs a name, a description, a Zod props schema and
// a React renderer. The key order of the z.object() is the positional
// argument order the model must use, and library.prompt() reads it to write
// the component signatures into the system prompt. No JSX: the renderers use
// React.createElement, so this file runs in Node (prompt.mjs, tests) and in
// the browser bundle without a transform.
//
// The pattern is the State of Generative UI report's hybrid: catalog
// primitives by default, one open-ended component (HtmlArtifact) where the
// catalog does not reach. The rules and examples in PROMPT_OPTIONS come from
// OpenUI's examples/miscellaneous/html-artifact (src/lib/prompt-options.ts),
// adapted to this catalog.

import { createLibrary, defineComponent } from "@openuidev/react-lang";
import { createElement as h } from "react";
import { z } from "zod";
import { HtmlArtifact } from "./html-artifact.mjs";
import { renderMarkdown } from "./markdown.mjs";

// Renderers receive { props, renderNode }. renderNode turns a child element
// node (or a list of them) into React nodes; the library resolves references.
const Stack = defineComponent({
  name: "Stack",
  description: "Lays children out in a column or a row",
  props: z.object({
    children: z.array(z.any()).describe("child components"),
    direction: z.enum(["column", "row"]).optional().describe("default column"),
    gap: z.enum(["s", "m", "l"]).optional().describe("default m"),
  }),
  component: ({ props, renderNode }) =>
    h("div", { className: `stack ${props.direction ?? "column"} gap-${props.gap ?? "m"}` }, renderNode(props.children)),
});

const Text = defineComponent({
  name: "Text",
  description: "A run of text",
  props: z.object({
    text: z.string(),
    size: z.enum(["small", "body", "heading"]).optional().describe("default body"),
  }),
  component: ({ props }) => h("p", { className: `text ${props.size ?? "body"}` }, props.text),
});

const Metric = defineComponent({
  name: "Metric",
  description: "One number with a label and an optional change",
  props: z.object({
    label: z.string(),
    value: z.union([z.string(), z.number()]),
    delta: z.string().optional().describe('such as "+12%"'),
  }),
  component: ({ props }) =>
    h("div", { className: "metric" },
      h("div", { className: "label" }, props.label),
      h("div", { className: "value" }, String(props.value)),
      h("div", { className: `delta ${String(props.delta ?? "").startsWith("-") ? "down" : "up"}` }, props.delta ?? "")),
});

const Table = defineComponent({
  name: "Table",
  description: "A table with column headers and rows of cells",
  props: z.object({
    columns: z.array(z.string()),
    rows: z.array(z.array(z.union([z.string(), z.number()]))),
  }),
  component: ({ props }) =>
    h("table", { className: "table" },
      h("thead", null, h("tr", null, props.columns.map((c, i) => h("th", { key: i }, c)))),
      h("tbody", null, props.rows.map((row, i) =>
        h("tr", { key: i }, row.map((cell, j) => h("td", { key: j }, String(cell))))))),
});

const BarChart = defineComponent({
  name: "BarChart",
  description: "A bar chart with one series",
  props: z.object({
    title: z.string(),
    labels: z.array(z.string()),
    values: z.array(z.number()),
  }),
  component: ({ props }) => {
    const max = Math.max(1, ...props.values);
    return h("div", { className: "chart" },
      h("div", { className: "chart-title" }, props.title),
      h("div", { className: "bars" }, props.values.map((v, i) =>
        h("div", { key: i, className: "bar", title: String(v), style: { height: `${Math.round((v / max) * 100)}%` } },
          h("span", { className: "bar-label" }, props.labels[i] ?? "")))));
  },
});

const Card = defineComponent({
  name: "Card",
  description: "A bordered box with a title and children",
  props: z.object({
    title: z.string(),
    children: z.array(z.any()).describe("child components"),
  }),
  component: ({ props, renderNode }) =>
    h("section", { className: "card" }, h("h3", null, props.title), renderNode(props.children)),
});

const Button = defineComponent({
  name: "Button",
  description: "A button that fires an action name",
  props: z.object({
    label: z.string(),
    action: z.string().describe("snake_case action name"),
    variant: z.enum(["primary", "secondary"]).optional(),
  }),
  component: ({ props }) =>
    h("button", { className: `button ${props.variant ?? "secondary"}`, "data-action": props.action }, props.label),
});

const Input = defineComponent({
  name: "Input",
  description: "A single-line text field",
  props: z.object({
    name: z.string(),
    placeholder: z.string().optional(),
    type: z.enum(["text", "email", "number"]).optional(),
  }),
  component: ({ props }) =>
    h("input", { className: "input", name: props.name, placeholder: props.placeholder ?? "", type: props.type ?? "text" }),
});

const Markdown = defineComponent({
  name: "Markdown",
  description: "Conversational text in Markdown. Use this for normal replies and to introduce an artifact",
  props: z.object({
    text: z.string(),
  }),
  component: ({ props }) => h("div", { className: "markdown" }, renderMarkdown(props.text)),
});

export const library = createLibrary({
  components: [Stack, Text, Metric, Table, BarChart, Card, Button, Input, Markdown, HtmlArtifact],
  root: "Stack",
});

// The prompt rules from OpenUI's html-artifact example, with two additions
// for this catalog: dashboards and forms stay in catalog components, and the
// one message shape the host accepts from inside the iframe.
export const PROMPT_OPTIONS = {
  preamble: "You answer with OpenUI Lang only, no prose outside the program.",
  additionalRules: [
    "Use the catalog components (Metric, BarChart, Table, Card, Input, Button, Text) for dashboards, reports and forms. Never put a dashboard into an HtmlArtifact.",
    "Use Markdown for normal conversation. A reply that needs no components is a Stack with a single Markdown child.",
    "Only use HtmlArtifact when the user explicitly asks you to build something interactive: an app, game, simulation, calculator, visualization, or similar experience. Introduce it with a short Markdown child first.",
    "When you use HtmlArtifact, generate a self-contained HTML/CSS/JavaScript experience in the document argument. It may be a complete HTML document or a fragment.",
    "Inside an HtmlArtifact document: use inline CSS and JavaScript only. Do not depend on external scripts, stylesheets, fonts, images, or network requests.",
    "Do not wrap the document in Markdown fences.",
    "Keep each statement on one line. Encode line breaks as \\n inside the document string.",
    "The document is a double-quoted openui-lang string. Prefer single quotes inside HTML and JavaScript, and escape any double quotes or backslashes.",
    "The document may tell the host about a user action with parent.postMessage({type: 'event', name: 'some_name'}, '*'); nothing else crosses the iframe boundary.",
    "Put numbers in Metric values and BarChart values, not in Text.",
  ],
  examples: [
    `Example 1 - a normal reply:

root = Stack([answer])
answer = Markdown("Hi! I can chat, build a dashboard from the catalog, or build you an interactive HTML experience. Try asking for a calculator, a game or a simulator.")`,
    `Example 2 - an interactive artifact:

root = Stack([intro, artifact])
intro = Markdown("Here's a simple click counter:")
artifact = HtmlArtifact("Interactive counter", "<!doctype html><html><head><style>body{font-family:system-ui;padding:2rem}button{padding:.5rem 1rem}</style></head><body><h1>Counter</h1><button id='count'>0</button><script>let count=0;document.querySelector('#count').addEventListener('click',event=>{event.currentTarget.textContent=String(++count)})</script></body></html>")`,
  ],
};
