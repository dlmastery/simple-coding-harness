// The page: send a prompt, feed every streamed message to the store, repaint;
// post a Button's action to the server and apply what comes back.
import { SurfaceStore, messageType } from './surface.mjs';
import { paint } from './render.mjs';

const store = new SurfaceStore();
const app = document.getElementById('app');
const log = document.getElementById('log');
const form = document.getElementById('prompt-form');
const t0 = performance.now();

window.a2uiLog = [];
function note(line) {
  const stamped = `${((performance.now() - t0) / 1000).toFixed(2)}s ${line}`;
  window.a2uiLog.push(stamped);
  log.append(Object.assign(document.createElement('div'), { textContent: stamped }));
}

let running = false; // one generation at a time; the button is disabled meanwhile

const handlers = {
  onChange: () => paint(store, app, handlers),
  onAction: async (action) => {
    if (running) return note('action ignored: a generation is still streaming');
    note(`action -> POST /action ${JSON.stringify(action.context)}`);
    try {
      const response = await fetch('/action', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(action) });
      if (!response.ok) throw new Error(`${response.status} ${await response.text()}`);
      for (const message of await response.json()) receive(message);
    } catch (error) {
      note(`action failed: ${error.message}`);
    }
  },
};

export function receive(message) {
  const kind = messageType(message);
  const surface = store.apply(message);
  paint(store, app, handlers);
  if (kind === 'updateComponents') {
    const ids = message.updateComponents.components.map((c) => c.id);
    const loading = ids.filter((id) => id.startsWith('loading_')).length;
    note(`updateComponents: ${ids.length} components, ${loading} loading placeholders, missing refs ${surface.missingIds().length}`);
  } else if (kind === 'updateDataModel') {
    note(`updateDataModel: ${message.updateDataModel.path ?? '/'} = ${JSON.stringify(message.updateDataModel.value).slice(0, 80)}`);
  } else {
    note(`${kind}: ${message[kind].surfaceId}`);
  }
}

// POST + a hand-parsed SSE body: EventSource cannot send a body, fetch can.
// Frames: `event: note|done` with a JSON data line, or a bare data line
// carrying one A2UI envelope; a frame without a data line (a keepalive
// comment) is skipped. Whatever happens, a2uiDone flips at the end.
async function generate(promptText) {
  note(`POST /generate ${JSON.stringify(promptText)}`);
  try {
    const response = await fetch('/generate', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ prompt: promptText }) });
    if (!response.ok) throw new Error(`${response.status} ${await response.text()}`);
    const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
    let buffer = '';
    let finished = false;
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += value.replaceAll('\r\n', '\n');
      let end;
      while ((end = buffer.indexOf('\n\n')) >= 0) {
        const frame = buffer.slice(0, end);
        buffer = buffer.slice(end + 2);
        const event = frame.match(/^event: (.*)$/m)?.[1];
        const line = frame.match(/^data: (.*)$/m)?.[1];
        if (line === undefined) continue; // a comment, such as the keepalive
        const data = JSON.parse(line);
        if (event === 'note') note(`note ${JSON.stringify(data)}`);
        else if (event === 'done') { note('done'); finished = true; }
        else receive(data);
      }
    }
    if (!finished) note('the stream ended without done');
  } catch (error) {
    note(`generate failed: ${error.message}`); // a dead server, a 422, a message the store refused
  } finally {
    running = false;
    form.elements.go.disabled = false;
    window.a2uiDone = true;
  }
}

form.onsubmit = (event) => {
  event.preventDefault();
  if (running) return;
  running = true;
  form.elements.go.disabled = true;
  window.a2uiDone = false;
  generate(form.elements.prompt.value);
};
window.store = store;
