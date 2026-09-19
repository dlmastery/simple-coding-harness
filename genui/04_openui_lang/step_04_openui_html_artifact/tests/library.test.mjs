import { test } from "node:test";
import assert from "node:assert/strict";
import { createElement as h } from "react";
import { renderToString } from "react-dom/server";
import { Renderer, createStreamingParser } from "@openuidev/react-lang";
import { library, PROMPT_OPTIONS } from "../library.mjs";
import { META } from "../sandbox.mjs";

const schema = library.toJSONSchema();
const DOC = "<!doctype html><html><head><style>body{font:14px system-ui}</style></head><body><button id='b'>0</button><script>let n=0;document.querySelector('#b').onclick=e=>{e.target.textContent=String(++n)}</script></body></html>";
const PROGRAM = `root = Stack([intro, art])\nintro = Markdown("A **counter**:")\nart = HtmlArtifact("Counter", ${JSON.stringify(DOC)})\n`;

test("the catalog is step 02's eight components plus Markdown and HtmlArtifact", () => {
  assert.deepEqual(Object.keys(schema.$defs), ["Stack", "Text", "Metric", "Table", "BarChart", "Card", "Button", "Input", "Markdown", "HtmlArtifact"]);
  assert.deepEqual(Object.keys(schema.$defs.HtmlArtifact.properties), ["title", "document"]);
  assert.deepEqual(schema.$defs.HtmlArtifact.required, ["title", "document"]);
});

test("library.prompt() carries the html-artifact rules and both examples", () => {
  const prompt = library.prompt(PROMPT_OPTIONS);
  assert.match(prompt, /^HtmlArtifact\(title: string, document: string\)/m);
  assert.match(prompt, /^Markdown\(text: string\)/m);
  for (const rule of PROMPT_OPTIONS.additionalRules) assert.ok(prompt.includes(rule), rule);
  assert.ok(prompt.includes("Only use HtmlArtifact when the user explicitly asks"));
  assert.ok(prompt.includes("inline CSS and JavaScript only"));
  assert.ok(prompt.includes('artifact = HtmlArtifact("Interactive counter"'));
  assert.ok(prompt.includes("Example 1 - a normal reply"));
});

test("the streaming parser exposes the partial document while the string is still open", () => {
  const sp = createStreamingParser(schema, "Stack");
  const cut = PROGRAM.indexOf("<button");
  let result = sp.push(PROGRAM.slice(0, cut));
  const art = result.root.props.children[1];
  assert.equal(art.typeName, "HtmlArtifact");
  assert.equal(art.partial, true);
  assert.ok(art.props.document.endsWith("<body>"));
  assert.equal(result.meta.incomplete, true);
  result = sp.push(PROGRAM.slice(cut));
  assert.equal(result.meta.incomplete, false);
  assert.equal(result.root.props.children[1].props.document, DOC);
});

test("<Renderer> shows the status line and the raw source while streaming", () => {
  const html = renderToString(h(Renderer, { response: PROGRAM, library, isStreaming: true }));
  assert.match(html, /Generating artifact \.\.\. \d+ characters so far/);
  assert.match(html, /data-state="streaming"/);
  assert.ok(html.includes('<pre class="artifact-raw">'));
  assert.ok(!html.includes("<iframe"));
});

test("<Renderer> mounts the sandboxed iframe with the CSP before any element once streaming ends", () => {
  const html = renderToString(h(Renderer, { response: PROGRAM, library, isStreaming: false }));
  assert.ok(html.includes('<div class="markdown"><p class="md-p">A <strong>counter</strong>:</p></div>'));
  const iframe = /<iframe[^>]*>/.exec(html)[0];
  assert.match(iframe, /sandbox="allow-scripts"/);
  assert.match(iframe, /referrerpolicy="no-referrer"/i);  // React writes the camelCase name; HTML attributes are case-insensitive
  const srcdoc = /srcdoc="([^"]*)"/i.exec(iframe)[1].replace(/&quot;/g, '"').replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&#x27;/g, "'").replace(/&amp;/g, "&");
  assert.ok(srcdoc.startsWith("<!doctype html>" + META + "<html><head><style>"), srcdoc.slice(0, 160));
  assert.ok(html.includes('class="tab active" data-view="rendered"'));
});

test("a dashboard program renders catalog components and no iframe", () => {
  const response = 'root = Stack([m, c])\nm = Metric("Cups", 241, "+8%")\nc = BarChart("Sales", ["Mon"], [3])\n';
  const html = renderToString(h(Renderer, { response, library, isStreaming: false }));
  assert.match(html, /<div class="value">241<\/div>/);
  assert.ok(!html.includes("<iframe") && !html.includes("artifact"));
});
