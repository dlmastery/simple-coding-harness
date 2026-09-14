// Generative UI step 02 - the page: one SSE line at a time into the parser,
// the tree re-rendered after every line, the program shown beside it.

import { Parser } from "./openui-parse.mjs";
import { render } from "./render.mjs";

const surface = document.getElementById("surface");
const program = document.getElementById("program");
const status = document.getElementById("status");
const parser = new Parser();
let lines = 0;

function redraw() {
  surface.replaceChildren(render(parser.tree()));
  const pending = parser.pending();
  status.textContent = pending.length
    ? `${lines} lines, waiting for ${pending.join(", ")}`
    : `${lines} lines, ${parser.statements.size} statements, nothing pending`;
}

const source = new EventSource("/events");
source.onmessage = (event) => {
  const line = JSON.parse(event.data);
  if (line === null) {
    parser.close();
    redraw();
    surface.dataset.done = "1";
    source.close();
    return;
  }
  lines += 1;
  const span = document.createElement("span");
  span.className = "new";
  span.textContent = line + "\n";
  for (const old of program.querySelectorAll(".new")) old.className = "";
  program.append(span);
  parser.feed(line + "\n");
  redraw();
};
source.onerror = () => { status.textContent = "disconnected"; };
