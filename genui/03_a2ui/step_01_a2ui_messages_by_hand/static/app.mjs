// The page: read the message stream, feed the store, repaint after every message.
import { SurfaceStore, messageType } from './surface.mjs';
import { paint } from './render.mjs';

const store = new SurfaceStore();
const app = document.getElementById('app');
const log = document.getElementById('log');

// What the page saw, for the demo script and for the eye: one line per message or event.
window.a2uiLog = [];
function note(line) {
  window.a2uiLog.push(line);
  log.append(Object.assign(document.createElement('div'), { textContent: line }));
}

const handlers = {
  onChange: (surface) => {
    paint(store, app, handlers); // a bound Text updates as the user types
    note(`data model of ${surface.id}: ${JSON.stringify(surface.data)}`);
  },
  onAction: (action) => note(`action ${JSON.stringify(action)}`), // step 02 posts this to the server
};

export function receive(message) {
  const kind = messageType(message);
  const surface = store.apply(message);
  paint(store, app, handlers);
  const detail = kind === 'updateComponents'
    ? `${message.updateComponents.components.length} components, missing refs: ${surface.missingIds().length}`
    : kind === 'updateDataModel' ? `path ${message.updateDataModel.path ?? '/'}` : `surface ${message[kind].surfaceId}`;
  note(`${kind}: ${detail}`);
}

const params = new URLSearchParams(location.search);
const source = new EventSource(`/stream${params.get('all') ? '?all=1' : ''}`);
source.onmessage = (event) => receive(JSON.parse(event.data));
source.addEventListener('done', () => source.close());
window.store = store;
