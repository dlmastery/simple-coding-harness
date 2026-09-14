// Step 04 - the page: a prompt box, an SSE reader, <Renderer>, and the
// host side of the iframe boundary.
//
// React without JSX. The model's OpenUI Lang text accumulates in one string
// state; <Renderer> from @openuidev/react-lang re-parses it on every change
// and renders the catalog components from library.mjs. The HtmlArtifact
// renderer reads the same streaming flag through useIsStreaming(), so it can
// hold the iframe back until the whole document has arrived.
//
// esbuild bundles this file and its imports into static/bundle.js
// (`npm run build`); see the step 02 README for why a bundler is needed.

import { Renderer } from "@openuidev/react-lang";
import { createElement as h, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { library } from "./library.mjs";
import { isEvent } from "./sandbox.mjs";

// Read the SSE stream from /generate; call onDelta with every text piece.
// The final `event: done` carries the API's token usage.
async function generate(prompt, onDelta) {
  const response = await fetch("/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
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
      if (event.startsWith("event: done")) return data ? JSON.parse(data) : {};
      if (data) onDelta(JSON.parse(data));
    }
  }
  return {};
}

function App() {
  const [prompt, setPrompt] = useState("build me an interactive lemonade price calculator I can play with");
  const [response, setResponse] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [parse, setParse] = useState(null);
  const [usage, setUsage] = useState(null);
  const [events, setEvents] = useState([]);

  // Messages from the artifact iframe: keep the one accepted shape, drop the rest.
  useEffect(() => {
    const onMessage = (e) => {
      if (!isEvent(e.data)) return;
      setEvents((list) => [...list, e.data.name]);
    };
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, []);

  async function run(text) {
    setResponse("");
    setUsage(null);
    setEvents([]);
    setStreaming(true);
    let program = "";
    try {
      const done = await generate(text, (delta) => { program += delta; setResponse(program); });
      setUsage(done.usage ?? null);
    } finally {
      setStreaming(false);
      window.openui.lastResponse = program;
    }
  }
  window.openui.run = run;

  const status = parse
    ? `${parse.meta.statementCount} statements, ${parse.meta.unresolved.length} unresolved` +
      (parse.meta.errors.length ? `, ${parse.meta.errors.length} errors` : "") +
      (usage ? `, ${usage.prompt_tokens} prompt + ${usage.completion_tokens} completion tokens` : "")
    : "";

  return h("div", null,
    h("header", null,
      h("h1", null, "OpenUI html artifact"),
      h("input", { id: "prompt", value: prompt, onChange: (e) => setPrompt(e.target.value) }),
      h("button", { id: "generate", onClick: () => run(prompt), disabled: streaming }, streaming ? "Streaming" : "Generate"),
      h("span", { id: "status", "data-streaming": String(streaming) }, status)),
    h("main", null,
      h("section", { id: "ui" },
        h(Renderer, { response, library, isStreaming: streaming, onParseResult: setParse,
          onAction: (event) => console.log("action", event) })),
      h("aside", null,
        h("h2", null, "OpenUI Lang from the model"),
        h("pre", { id: "source" }, response),
        h("h2", null, "Events accepted from the iframe"),
        h("pre", { id: "events" }, events.length ? events.join("\n") : "(none)"))));
}

window.openui = { lastResponse: "" };
createRoot(document.getElementById("app")).render(h(App));
