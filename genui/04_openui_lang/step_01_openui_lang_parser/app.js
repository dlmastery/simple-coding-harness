// Step 01 - the page. One StreamingParser, one render() call per pushed line.
import { StreamingParser, catalogFromSchema, parse } from "/openui-parse.mjs";
import { render } from "/render.mjs";

const ui = document.getElementById("ui");
const source = document.getElementById("source");
const unresolvedBox = document.getElementById("unresolved");
const status = document.getElementById("status");

const catalog = catalogFromSchema(await (await fetch("/catalog.json")).json());
let parser = new StreamingParser(catalog);

function show(result) {
  render(result, ui);
  source.textContent = parser.buffer;
  unresolvedBox.textContent = result.unresolved.join("\n") || "(none)";
  status.textContent = `${result.statementCount} statements, ${result.unresolved.length} unresolved` +
    (result.incomplete ? ", one line pending" : "");
}

// The demo script and the SSE reader both go through these two functions.
window.openui = {
  reset() { parser = new StreamingParser(catalog); ui.replaceChildren(); },
  push(chunk) { show(parser.push(chunk)); },
  finish() { show(parser.finish()); },
};

document.getElementById("render-all").onclick = async () => {
  window.openui.reset();
  const text = await (await fetch("/program.oui")).text();
  parser.buffer = text;
  show(parse(text, catalog));
};

document.getElementById("stream").onclick = () => {
  window.openui.reset();
  const events = new EventSource("/stream?delay=400");
  events.onopen = () => { if (parser.buffer) window.openui.reset(); };  // a reconnect replays from line 1: start over, do not append
  events.onmessage = (event) => window.openui.push(JSON.parse(event.data) + "\n");
  events.addEventListener("done", () => { events.close(); window.openui.finish(); });
  events.onerror = () => { status.textContent = "stream lost, reconnecting"; };
};
