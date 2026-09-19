// Step 02 - the page: a prompt box, an SSE reader, and <Renderer>.
//
// React without JSX. The model's OpenUI Lang text accumulates in one string
// state; <Renderer> from @openuidev/react-lang re-parses it on every change
// and renders the catalog components from library.mjs. While isStreaming is
// true, forward references that have no definition yet render as nothing;
// the shell around them is already there.
//
// esbuild bundles this file and its imports into static/bundle.js
// (`npm run build`); see README for why a bundler is needed here.

import { Renderer } from "@openuidev/react-lang";
import { createElement as h, useState } from "react";
import { createRoot } from "react-dom/client";
import { library } from "./library.mjs";

// Read the SSE stream from /generate; call onDelta with every text piece.
// Resolves on `event: done`, rejects on `event: error` or a non-200 answer.
async function generate(prompt, onDelta) {
  const response = await fetch("/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  if (!response.ok) throw new Error(`server answered ${response.status}: ${(await response.text()).slice(0, 200)}`);
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let end;
    while ((end = buffer.indexOf("\n\n")) >= 0) {
      const event = buffer.slice(0, end);
      buffer = buffer.slice(end + 2);
      const data = event.split("\n").filter((l) => l.startsWith("data: ")).map((l) => l.slice(6)).join("\n");
      if (event.startsWith("event: done")) return;
      if (event.startsWith("event: error")) throw new Error(data ? JSON.parse(data) : "the model call failed");
      if (data) onDelta(JSON.parse(data));
    }
  }
}

function App() {
  const [prompt, setPrompt] = useState("show me a dashboard for a lemonade stand");
  const [response, setResponse] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [parse, setParse] = useState(null);
  const [error, setError] = useState("");

  async function run(text) {
    setResponse("");
    setError("");
    setStreaming(true);
    let program = "";
    try {
      await generate(text, (delta) => { program += delta; setResponse(program); });
    } catch (failure) {
      setError(failure.message);  // the stream ended early: say so next to what did arrive
    } finally {
      setStreaming(false);
      window.openui.lastResponse = program;
    }
  }
  window.openui.run = run;

  const status = parse
    ? `${parse.meta.statementCount} statements, ${parse.meta.unresolved.length} unresolved` +
      (parse.meta.errors.length ? `, ${parse.meta.errors.length} errors` : "")
    : "";

  return h("div", null,
    h("header", null,
      h("h1", null, "OpenUI Lang with @openuidev/react-lang"),
      h("input", { id: "prompt", value: prompt, onChange: (e) => setPrompt(e.target.value) }),
      h("button", { id: "generate", onClick: () => run(prompt), disabled: streaming }, streaming ? "Streaming" : "Generate"),
      h("span", { id: "status", "data-streaming": String(streaming) }, status),
      error ? h("span", { id: "error" }, error) : null),
    h("main", null,
      h("section", { id: "ui" },
        h(Renderer, { response, library, isStreaming: streaming, onParseResult: setParse,
          onAction: (event) => console.log("action", event) })),
      h("aside", null,
        h("h2", null, "OpenUI Lang from the model"),
        h("pre", { id: "source" }, response),
        h("h2", null, "Unresolved references"),
        h("pre", { id: "unresolved" }, parse && parse.meta.unresolved.length ? parse.meta.unresolved.join("\n") : "(none)"))));
}

window.openui = { lastResponse: "" };
createRoot(document.getElementById("app")).render(h(App));
