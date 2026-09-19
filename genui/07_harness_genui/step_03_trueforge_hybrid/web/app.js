// Generative UI step 03 - the page: one SSE chunk at a time into the parser,
// the tree re-rendered after every chunk, the program shown beside it. The
// parser commits a statement when its line balances; an HtmlArtifact line
// still open shows up in the tree as a partial node, which the renderer
// draws as the raw source growing, until the line ends and it becomes an
// iframe.

import { Parser } from "./openui-parse.mjs";
import { render } from "./render.mjs";

const surface = document.getElementById("surface");
const program = document.getElementById("program");
const status = document.getElementById("status");
const parser = new Parser();
let chunks = 0;
let drawn = "";

// Redraw when a statement committed or the artifact document grew. A chunk
// that only lengthens an unfinished catalog line changes nothing on screen,
// and skipping it keeps a mounted iframe from reloading for no reason.
function redraw() {
  const partial = parser.partial();
  const key = `${parser.statements.size}:${partial && partial.type === "HtmlArtifact" ? parser.buffer.length : 0}`;
  if (key === drawn) return;
  drawn = key;
  surface.replaceChildren(render(parser.tree()));
  const pending = parser.pending();
  const artifacts = surface.querySelectorAll(".artifact").length;
  const part = artifacts ? `, ${artifacts} artifact${artifacts > 1 ? "s" : ""}` : "";
  status.textContent = pending.length
    ? `${chunks} chunks, waiting for ${pending.join(", ")}${part}`
    : `${chunks} chunks, ${parser.statements.size} statements, nothing pending${part}`;
}

const source = new EventSource("/events");
source.onopen = () => {  // a reconnect replays the program from the start: begin again, do not append
  if (parser.statements.size || parser.buffer) { parser.statements.clear(); parser.buffer = ""; parser.errors.length = 0; program.replaceChildren(); }
};
source.onmessage = (event) => {
  const piece = JSON.parse(event.data);
  if (piece === null) {
    parser.close();
    redraw();
    surface.dataset.done = "1";
    source.close();
    return;
  }
  chunks += 1;
  const span = document.createElement("span");
  span.className = "new";
  span.textContent = piece;
  for (const old of program.querySelectorAll(".new")) old.className = "";
  program.append(span);
  parser.feed(piece);
  redraw();
};
source.onerror = () => { status.textContent = "disconnected"; };
