// node --test: the AG-UI client's frame parser and input shape, and the
// official state machine (@a2ui/web_core's MessageProcessor) without a DOM.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseSse, runAgentInput, runAgent } from './src/agui.mjs';
import { MessageProcessor, Catalog } from '@a2ui/web_core/v0_9';
import { BASIC_FUNCTIONS, TextApi, ColumnApi, CardApi, ButtonApi, TextFieldApi } from '@a2ui/web_core/v0_9/basic_catalog';

const CATALOG = 'https://a2ui.org/specification/v0_9_1/catalogs/basic/catalog.json';

test('parseSse splits complete frames and keeps the remainder', () => {
  const wire = 'data: {"type":"RUN_STARTED","threadId":"t","runId":"r"}\n\n'
    + 'data: {"type":"CUSTOM","name":"a2ui","value":{"version":"v0.9.1","deleteSurface":{"surfaceId":"s"}}}\n\n'
    + 'data: {"type":"RUN_FIN';
  const { events, rest } = parseSse(wire);
  assert.equal(events.length, 2);
  assert.equal(events[1].name, 'a2ui');
  assert.equal(events[1].value.deleteSurface.surfaceId, 's');
  assert.equal(rest, 'data: {"type":"RUN_FIN');
  assert.deepEqual(parseSse(rest + 'ISHED"}\n\n').events[0].type, 'RUN_FINISHED');
});

test('runAgentInput carries the thread, a fresh run id and forwardedProps', () => {
  const messages = [{ id: 'm1', role: 'user', content: 'a form' }];
  const a = runAgentInput({ threadId: 't1', messages, forwardedProps: { a2ui: { action: { name: 'submit' } } } });
  const b = runAgentInput({ threadId: 't1', messages });
  assert.equal(a.threadId, 't1');
  assert.notEqual(a.runId, b.runId);
  assert.deepEqual(a.messages, messages);
  assert.deepEqual(a.forwardedProps.a2ui.action, { name: 'submit' });
  assert.deepEqual(b.forwardedProps, {});
});

test('runAgent posts the input and hands every event to the handler', async () => {
  const body = new ReadableStream({
    start(controller) {
      const encoder = new TextEncoder();
      controller.enqueue(encoder.encode('data: {"type":"RUN_STARTED","threadId":"t","runId":"r"}\n\ndata: {"type":"CUS'));
      controller.enqueue(encoder.encode('TOM","name":"a2ui","value":{"x":1}}\n\n'));
      controller.close();
    },
  });
  const calls = [];
  const fakeFetch = async (url, init) => { calls.push({ url, init }); return { body }; };
  const seen = [];
  await runAgent('/agent', runAgentInput({ threadId: 't', messages: [] }), (e) => seen.push(e.type), fakeFetch);
  assert.deepEqual(seen, ['RUN_STARTED', 'CUSTOM']);
  assert.equal(calls[0].init.method, 'POST');
  assert.equal(JSON.parse(calls[0].init.body).threadId, 't');
});

test('web_core MessageProcessor keeps the surface state and dispatches actions', async () => {
  const catalog = new Catalog(CATALOG, [TextApi, ColumnApi, CardApi, ButtonApi, TextFieldApi], BASIC_FUNCTIONS);
  const actions = [];
  const processor = new MessageProcessor([catalog], (a) => actions.push(a));
  processor.processMessages([
    { version: 'v0.9.1', createSurface: { surfaceId: 'main', catalogId: CATALOG, sendDataModel: true } },
    { version: 'v0.9.1', updateComponents: { surfaceId: 'main', components: [
      { id: 'root', component: 'Column', children: ['email', 'send'] },
      { id: 'email', component: 'TextField', label: 'Email', value: { path: '/form/email' } },
      { id: 'send', component: 'Button', child: 'label', action: { event: { name: 'submit', context: { email: { path: '/form/email' } } } } },
      { id: 'label', component: 'Text', text: 'Send' },
    ] } },
    { version: 'v0.9.1', updateDataModel: { surfaceId: 'main', path: '/form', value: { email: 'ada@example.com' } } },
  ]);
  const surface = processor.model.getSurface('main');
  assert.equal(surface.componentsModel.get('root').type, 'Column');
  assert.equal(surface.dataModel.get('/form/email'), 'ada@example.com');
  assert.deepEqual(processor.getClientDataModel('v0.9.1'), { version: 'v0.9.1', surfaces: { main: { form: { email: 'ada@example.com' } } } });
  await surface.dispatchAction({ event: { name: 'submit', context: { email: 'ada@example.com' } } }, 'send'); // the resolved action
  assert.deepEqual(actions[0].context, { email: 'ada@example.com' });
  assert.equal(actions.length, 1);
  assert.equal(actions[0].name, 'submit');
  assert.equal(actions[0].sourceComponentId, 'send');
  assert.equal(actions[0].surfaceId, 'main');
  assert.throws(() => processor.processMessages([{ version: 'v0.9.1', createSurface: { surfaceId: 'x', catalogId: 'unknown' } }]), /Catalog not found/);
});
