// The page: the official Lit renderer fed by AG-UI events.
//
// @a2ui/lit is thin: A2uiSurface (the element), basicCatalog (a Catalog over
// the Lit components that @a2ui/web_core defines) and Context (the markdown
// injection point). The state machine, MessageProcessor, is @a2ui/web_core's.
import { MessageProcessor, Catalog } from '@a2ui/web_core/v0_9';
import { injectBasicCatalogStyles } from '@a2ui/web_core/v0_9/basic_catalog';
import { A2uiSurface, basicCatalog, Context } from '@a2ui/lit/v0_9';
import { ContextProvider } from '@lit/context';
import { renderMarkdown } from '@a2ui/markdown-it';
import { runAgent, runAgentInput, newId } from './agui.mjs';

const app = document.getElementById('app');
const prose = document.getElementById('prose');
const log = document.getElementById('log');
const form = document.getElementById('prompt-form');
const t0 = performance.now();
const THREAD = newId('thread');
const history = []; // AG-UI messages so far; the server sees the whole thread each run

window.a2uiLog = [];
function note(line) {
  const stamped = `${((performance.now() - t0) / 1000).toFixed(2)}s ${line}`;
  window.a2uiLog.push(stamped);
  log.append(Object.assign(document.createElement('div'), { textContent: stamped }));
}

// The renderer answers createSurface with a catalog lookup by id. The Lit
// basic catalog is registered under the v0_9 id; the spec's v0_9_1 id gets an alias.
const V0_9_1 = 'https://a2ui.org/specification/v0_9_1/catalogs/basic/catalog.json';
const alias = new Catalog(V0_9_1, [...basicCatalog.components.values()], [...basicCatalog.functions.values()]);
const processor = new MessageProcessor([basicCatalog, alias], onAction);
injectBasicCatalogStyles();
new ContextProvider(app, { context: Context.markdown, initialValue: renderMarkdown }); // Text renders markdown
processor.onSurfaceCreated((surface) => {
  const element = new A2uiSurface();
  element.surface = surface;
  element.id = `surface-${surface.id}`;
  app.append(element);
});
processor.onSurfaceDeleted((id) => document.getElementById(`surface-${id}`)?.remove());

// A2UI over AG-UI: every A2UI envelope is the value of a CUSTOM event named "a2ui".
function onEvent(event) {
  switch (event.type) {
    case 'CUSTOM':
      if (event.name === 'a2ui') {
        processor.processMessages([event.value]);
        const kind = Object.keys(event.value).find((k) => k !== 'version');
        const count = event.value.updateComponents?.components.length;
        note(`CUSTOM a2ui ${kind}${count ? ` (${count} components)` : ''}`);
      } else {
        note(`CUSTOM ${event.name} ${JSON.stringify(event.value).slice(0, 120)}`);
      }
      break;
    case 'TEXT_MESSAGE_CONTENT':
      prose.textContent += event.delta;
      break;
    case 'RUN_STARTED':
    case 'RUN_FINISHED':
    case 'STEP_STARTED':
    case 'STEP_FINISHED':
    case 'RUN_ERROR':
      note(`${event.type} ${JSON.stringify(event.result ?? event.stepName ?? event.message ?? '')}`);
      break;
  }
}

// One run at a time: the button is disabled and actions are ignored while a
// run is open, and a2uiDone flips whatever happens (a dead server, a 422, a
// message the processor refuses), so nothing waits forever.
let running = false;
async function run(messages, forwardedProps = {}) {
  window.a2uiDone = false;
  running = true;
  form.elements.go.disabled = true;
  try {
    await runAgent('/agent', runAgentInput({ threadId: THREAD, messages, forwardedProps }), onEvent);
  } catch (error) {
    note(`run failed: ${error.message}`);
  } finally {
    running = false;
    form.elements.go.disabled = false;
    window.a2uiDone = true;
  }
}

// The renderer resolved the action's context from its data model; AG-UI has
// no message type for it, so it travels in forwardedProps, with the data
// model alongside, the way the spec's sendDataModel describes.
function onAction(action) {
  if (running) return note(`action ${action.name} ignored: a run is still open`);
  note(`action ${action.name} from ${action.sourceComponentId} ${JSON.stringify(action.context)}`);
  const dataModel = processor.getClientDataModel('v0.9.1') ?? { version: 'v0.9.1', surfaces: {} };
  run(history, { a2ui: { action, a2uiClientDataModel: dataModel } });
}

form.onsubmit = (event) => {
  event.preventDefault();
  if (running) return;
  prose.textContent = '';
  history.push({ id: newId('msg'), role: 'user', content: form.elements.prompt.value });
  note(`POST /agent run with ${history.length} message(s)`);
  run(history);
};

window.processor = processor;
window.dataModel = (id) => processor.model.getSurface(id)?.dataModel.get('/');
