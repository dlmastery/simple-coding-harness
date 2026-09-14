// The page: send the prompt, receive one complete spec, hand it to Renderer.
// JSONUIProvider supplies the state, action and visibility contexts Renderer
// needs; spec.state seeds the state model that {"$state": "/path"} props read.
import React from "react";
import { createRoot } from "react-dom/client";
import htm from "htm";
import { Renderer, JSONUIProvider } from "@json-render/react";
import { registry } from "./registry.mjs";

const html = htm.bind(React.createElement);
const { useState, useEffect } = React;
const NO_STATE = {};

async function generate(prompt) {
  const response = await fetch("/generate", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

function App() {
  const [prompt, setPrompt] = useState("Show me a dashboard for a lemonade stand: this week's sales, the best days, and what sold.");
  const [spec, setSpec] = useState(null);
  const [status, setStatus] = useState("");

  async function run() {
    setStatus("asking the model for a complete spec...");
    try {
      const { spec, usage, seconds } = await generate(prompt);
      setSpec(spec);
      setStatus(`${Object.keys(spec.elements).length} elements, ${usage.completion_tokens} output tokens, ${seconds} s`);
    } catch (error) {
      setStatus(String(error));
    }
  }

  // ?last=1 shows the spec the server generated most recently, with no model call.
  useEffect(() => {
    if (new URLSearchParams(location.search).get("last")) {
      fetch("/spec").then((r) => r.json()).then(setSpec);
    }
  }, []);

  return html`
    <div className="toolbar">
      <input value=${prompt} onChange=${(e) => setPrompt(e.target.value)} />
      <button onClick=${run}>Generate</button>
      <span className="status">${status}</span>
    </div>
    <main id="surface">
      <${JSONUIProvider} registry=${registry} initialState=${spec?.state ?? NO_STATE}>
        <${Renderer} spec=${spec} registry=${registry} />
      <//>
    </main>`;
}

createRoot(document.getElementById("app")).render(html`<${App} />`);
