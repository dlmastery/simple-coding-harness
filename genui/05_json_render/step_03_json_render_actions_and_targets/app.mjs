// The page: stream the first spec as in step 2, then keep the compiler alive.
// A Button press becomes an action. setState is handled by the library inside
// the page; the two catalog actions go to the server (POST /action), and the
// model's answer is more JSON Patch lines, pushed into the same compiler, so
// the spec on screen changes in place. Every action is written to #log.
import React from "react";
import { createRoot } from "react-dom/client";
import htm from "htm";
import { createSpecStreamCompiler } from "@json-render/core";
import { Renderer, JSONUIProvider } from "@json-render/react";
import { registry } from "./registry.mjs";

const html = htm.bind(React.createElement);
const { useState, useEffect, useMemo, useRef } = React;

async function* chunks(response) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  while (true) {
    const { value, done } = await reader.read();
    if (done) return;
    yield decoder.decode(value, { stream: true });
  }
}

function App() {
  const [prompt, setPrompt] = useState("Show me a dashboard for a lemonade stand: this week's sales, the best days, and what sold.");
  const [spec, setSpec] = useState(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const [log, setLog] = useState([]);
  const compiler = useRef(createSpecStreamCompiler());
  // State patches mutate spec.state in place, so StateProvider would see the
  // same object and skip the update. A fresh copy per spec version fixes that.
  const state = useMemo(() => ({ ...(spec?.state ?? {}) }), [spec]);

  function note(line) {
    setLog((lines) => [...lines, line]);
  }

  // Read one JSONL stream into the shared compiler. Returns the patch count.
  async function consume(response) {
    const before = compiler.current.getPatches().length;
    for await (const chunk of chunks(response)) {
      const { result, newPatches } = compiler.current.push(chunk);
      if (newPatches.length === 0) continue;
      setSpec(result.elements ? result : { ...result, elements: {} });
    }
    setSpec(compiler.current.getResult());
    return compiler.current.getPatches().length - before;
  }

  async function run() {
    const started = performance.now();
    compiler.current.reset();
    setLoading(true);
    setStatus("streaming...");
    const response = await fetch("/stream", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ prompt }),
    });
    const patches = await consume(response);
    setLoading(false);
    setStatus(`complete at ${((performance.now() - started) / 1000).toFixed(2)} s, ${patches} patches`);
  }

  // A catalog action: tell the server which button was pressed, then apply
  // the model's patches to the spec that is already on screen.
  async function serverAction(action, params) {
    const started = performance.now();
    note(`${action} ${JSON.stringify(params)} -> server`);
    setLoading(true);
    const response = await fetch("/action", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ action, params }),
    });
    const patches = await consume(response);
    setLoading(false);
    note(`${action}: ${patches} patches applied in ${((performance.now() - started) / 1000).toFixed(2)} s`);
  }

  const handlers = {
    refresh_numbers: (params) => serverAction("refresh_numbers", params ?? {}),
    show_details: (params) => serverAction("show_details", params ?? {}),
  };

  // setState never reaches a handler; onStateChange is the only trace of it.
  function onStateChange(changes) {
    for (const { path, value } of changes) note(`setState ${path} = ${JSON.stringify(value)} (handled in the page)`);
  }

  // ?last=1 shows the spec the server streamed most recently; ?auto=1 starts a stream on load.
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (params.get("last")) fetch("/spec").then((r) => r.json()).then(setSpec);
    if (params.get("auto")) run();
  }, []);

  return html`
    <div className="toolbar">
      <input value=${prompt} onChange=${(e) => setPrompt(e.target.value)} />
      <button onClick=${run}>Generate</button>
      <span className="status" id="status">${status}</span>
    </div>
    <main id="surface">
      <${JSONUIProvider} registry=${registry} initialState=${state} handlers=${handlers} onStateChange=${onStateChange}>
        <${Renderer} spec=${spec} registry=${registry} loading=${loading} />
      <//>
    </main>
    <pre id="log">${log.join("\n")}</pre>`;
}

createRoot(document.getElementById("app")).render(html`<${App} />`);
