// The page: read the model's JSONL as it streams, push every chunk into
// createSpecStreamCompiler, and render after each complete patch. The
// compiler buffers partial lines, so a chunk boundary in the middle of a
// patch is not a problem. JSONUIProvider supplies the contexts Renderer
// needs; spec.state seeds the state model that {"$state": "/path"} props read.
import React from "react";
import { createRoot } from "react-dom/client";
import htm from "htm";
import { createSpecStreamCompiler } from "@json-render/core";
import { Renderer, JSONUIProvider } from "@json-render/react";
import { registry } from "./registry.mjs";

const html = htm.bind(React.createElement);
const { useState, useEffect, useMemo } = React;

async function* chunks(response) {
  if (!response.ok) throw new Error(`server answered ${response.status}: ${(await response.text()).slice(0, 200)}`);
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  while (true) {
    const { value, done } = await reader.read();
    if (done) return;
    yield decoder.decode(value, { stream: true });
  }
}

// The server ends a failed stream with one line {"error": "..."}: not a patch, so
// the compiler skips it; the page reads it and stops with the reason.
function errorLine(text) {
  const last = text.trimEnd().split("\n").at(-1) ?? "";
  if (!last.startsWith('{"error"')) return null;
  try { return JSON.parse(last).error; } catch { return null; }
}

function App() {
  const [prompt, setPrompt] = useState("Show me a dashboard for a lemonade stand: this week's sales, the best days, and what sold.");
  const [spec, setSpec] = useState(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  // State patches mutate spec.state in place, so StateProvider would see the
  // same object and skip the update. A fresh copy per spec version fixes that.
  const state = useMemo(() => ({ ...(spec?.state ?? {}) }), [spec]);

  async function run() {
    if (loading) return;
    const started = performance.now();
    const seconds = () => ((performance.now() - started) / 1000).toFixed(2);
    let firstPaint = null;
    let text = "";
    setLoading(true);
    setStatus("streaming...");
    const compiler = createSpecStreamCompiler();
    try {
      const response = await fetch("/stream", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      for await (const chunk of chunks(response)) {
        text += chunk;
        const { result, newPatches } = compiler.push(chunk);
        if (newPatches.length === 0) continue;
        // The first patch sets /root alone; Renderer reads spec.elements[spec.root]
        // with no guard, so give it an empty map until /elements arrives.
        setSpec(result.elements ? result : { ...result, elements: {} });
        if (firstPaint === null && result.root && result.elements?.[result.root]) {
          firstPaint = seconds();
          setStatus(`first paint at ${firstPaint} s`);
        }
      }
      setSpec(compiler.getResult()); // applies a last line that had no newline
      const failed = errorLine(text);
      setStatus(failed
        ? `stopped after ${compiler.getPatches().length} patches: ${failed}`
        : `first paint at ${firstPaint} s, complete at ${seconds()} s, ${compiler.getPatches().length} patches`);
    } catch (error) {
      setStatus(`stream failed: ${error.message}`); // a dead server or a lost connection: a terminal state, not "streaming..." forever
    } finally {
      setLoading(false);
    }
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
      <button onClick=${run} disabled=${loading}>Generate</button>
      <span className="status" id="status">${status}</span>
    </div>
    <main id="surface">
      <${JSONUIProvider} registry=${registry} initialState=${state}>
        <${Renderer} spec=${spec} registry=${registry} loading=${loading} />
      <//>
    </main>`;
}

createRoot(document.getElementById("app")).render(html`<${App} />`);
