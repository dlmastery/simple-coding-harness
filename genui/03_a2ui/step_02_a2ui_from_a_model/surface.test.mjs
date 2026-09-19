// node --test: the DOM-free half of the renderer.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { SurfaceStore, Surface, pointerGet, pointerSet, pointerDelete } from './static/surface.mjs';

const CATALOG = 'https://a2ui.org/specification/v0_9_1/catalogs/basic/catalog.json';

test('JSON Pointer: get, set creates parents, delete keeps array length, escapes', () => {
  const doc = {};
  pointerSet(doc, '/contact/email', 'a@b.c');
  assert.equal(pointerGet(doc, '/contact/email'), 'a@b.c');
  assert.equal(pointerGet(doc, '/contact/phone'), undefined);
  pointerSet(doc, '/tags', ['x', 'y']);
  pointerDelete(doc, '/tags/0');
  assert.equal(doc.tags.length, 2);
  pointerSet(doc, '/a~1b/c~0d', 1);
  assert.equal(pointerGet(doc, '/a~1b/c~0d'), 1);
  pointerSet(doc, '/', { fresh: true });
  assert.deepEqual(doc, { fresh: true });
});

test('a child id may arrive before its component: tree shows a placeholder, then fills in', () => {
  const store = new SurfaceStore();
  store.apply({ version: 'v0.9.1', createSurface: { surfaceId: 's', catalogId: CATALOG } });
  const surface = store.apply({ version: 'v0.9.1', updateComponents: { surfaceId: 's', components: [
    { id: 'root', component: 'Column', children: ['title', 'later'] },
    { id: 'title', component: 'Text', text: 'Hi' },
  ] } });
  assert.deepEqual(surface.missingIds(), ['later']);
  assert.deepEqual(surface.tree().children[1], { id: 'later', missing: true });
  surface.apply({ version: 'v0.9.1', updateComponents: { surfaceId: 's', components: [{ id: 'later', component: 'Text', text: 'Now' }] } });
  assert.deepEqual(surface.missingIds(), []);
  assert.equal(surface.tree().children[1].component, 'Text');
});

test('data binding resolves paths, two-way set writes back, action context is resolved at click time', () => {
  const surface = new Surface('s', CATALOG);
  surface.apply({ version: 'v0.9.1', updateComponents: { surfaceId: 's', components: [
    { id: 'root', component: 'Column', children: ['field', 'send'] },
    { id: 'field', component: 'TextField', label: 'Email', value: { path: '/contact/email' } },
    { id: 'send', component: 'Button', child: 'label', action: { event: { name: 'submit', context: { email: { path: '/contact/email' }, formId: 'f1' } } } },
    { id: 'label', component: 'Text', text: 'Send' },
  ] } });
  assert.equal(surface.resolve({ path: '/contact/email' }), undefined);
  surface.apply({ version: 'v0.9.1', updateDataModel: { surfaceId: 's', path: '/contact', value: { email: 'a@b.c' } } });
  assert.equal(surface.resolve({ path: '/contact/email' }), 'a@b.c');
  surface.set('/contact/email', 'new@b.c');
  const action = surface.action('send', 't0');
  assert.deepEqual(action, { name: 'submit', surfaceId: 's', sourceComponentId: 'send', timestamp: 't0', context: { email: 'new@b.c', formId: 'f1' } });
});

test('updateDataModel without value removes the key; deleteSurface drops the surface', () => {
  const store = new SurfaceStore();
  store.apply({ version: 'v0.9.1', createSurface: { surfaceId: 's', catalogId: CATALOG } });
  store.apply({ version: 'v0.9.1', updateDataModel: { surfaceId: 's', value: { user: { name: 'Ada', temp: 1 } } } });
  const surface = store.apply({ version: 'v0.9.1', updateDataModel: { surfaceId: 's', path: '/user/temp' } });
  assert.deepEqual(surface.data, { user: { name: 'Ada' } });
  store.apply({ version: 'v0.9.1', deleteSurface: { surfaceId: 's' } });
  assert.equal(store.surfaces.size, 0);
  assert.throws(() => store.apply({ version: 'v0.9.1', updateDataModel: { surfaceId: 's', value: {} } }), /never created/);
});

test('a repeated createSurface is a reset: what EventSource replays after a reconnect', () => {
  const store = new SurfaceStore();
  store.apply({ version: 'v0.9.1', createSurface: { surfaceId: 's', catalogId: CATALOG } });
  store.apply({ version: 'v0.9.1', updateDataModel: { surfaceId: 's', path: '/stale', value: true } });
  const again = store.apply({ version: 'v0.9.1', createSurface: { surfaceId: 's', catalogId: CATALOG } });
  assert.deepEqual(again.data, {});
  assert.equal(store.surfaces.size, 1);
});

test('a component inside itself is a cycle, not a stack overflow', () => {
  const surface = new Surface('s', CATALOG);
  surface.apply({ version: 'v0.9.1', updateComponents: { surfaceId: 's', components: [
    { id: 'root', component: 'Column', children: ['root', 'card'] },
    { id: 'card', component: 'Card', child: 'root' },
  ] } });
  const tree = surface.tree();
  assert.deepEqual(tree.children[0], { id: 'root', cycle: true });
  assert.deepEqual(tree.children[1].children[0], { id: 'root', cycle: true });
  assert.deepEqual(surface.missingIds(), []);
});

test('a path cannot reach Object.prototype and a list index must be digits', () => {
  const doc = { tags: ['x'] };
  for (const path of ['/__proto__/polluted', '/constructor/prototype/polluted', '/a/__proto__']) {
    assert.throws(() => pointerSet(doc, path, 1), /refused/);
    assert.throws(() => pointerGet(doc, path), /refused/);
  }
  assert.equal({}.polluted, undefined);
  assert.equal(pointerGet(doc, '/toString'), undefined); // own properties only
  assert.equal(pointerGet(doc, '/tags/x'), undefined);
  assert.throws(() => pointerSet(doc, '/tags/x', 1), /not an array index/);
  pointerDelete(doc, '/tags/x');
  assert.deepEqual(doc, { tags: ['x'] });
});
