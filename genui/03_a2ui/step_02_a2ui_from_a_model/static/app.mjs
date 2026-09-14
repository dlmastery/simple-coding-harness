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

const handlers = {
  onChange: () => paint(store, app, handlers),
  onAction: async (action) => {
    note(`action -> POST /action ${JSON.stringify(action.context)}`);
    const response = await fetch('/action', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(action) });
    for (const message of await response.json()) receive(message);
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
async function generate(promptText) {
  note(`POST /generate ${JSON.stringify(promptText)}`);
  const response = await fetch('/generate', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ prompt: promptText }) });
  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = '';
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += value;
    let end;
    while ((end = buffer.indexOf('\n\n')) >= 0) {
      const frame = buffer.slice(0, end);
      buffer = buffer.slice(end + 2);
      const event = frame.match(/^event: (.*)$/m)?.[1];
      const data = JSON.parse(frame.match(/^data: (.*)$/m)[1]);
      if (event === 'note') note(`note ${JSON.stringify(data)}`);
      else if (event === 'done') note('done');
      else receive(data);
    }
  }
  window.a2uiDone = true;
}

form.onsubmit = (event) => {
  event.preventDefault();
  window.a2uiDone = false;
  generate(form.elements.prompt.value);
};
window.store = store;
