// The state an A2UI client keeps, with no DOM in it: JSON Pointer, one Surface
// (component map + data model), and the store that routes envelope messages.
// render.mjs paints this; node --test exercises it directly.

export function messageType(message) {
  for (const key of ['createSurface', 'updateComponents', 'updateDataModel', 'deleteSurface']) {
    if (key in message) return key;
  }
  return null;
}

// ------------------------------------------------------------ JSON Pointer (RFC 6901)

// A path in a message is data from the wire. These three tokens would reach
// Object.prototype through pointerSet, so they are refused everywhere.
const FORBIDDEN = new Set(['__proto__', 'constructor', 'prototype']);

export function pointerTokens(path) {
  if (path === '' || path === '/') return [];
  if (!path.startsWith('/')) throw new Error(`absolute JSON Pointer expected, got ${path}`);
  const tokens = path.slice(1).split('/').map((t) => t.replaceAll('~1', '/').replaceAll('~0', '~'));
  for (const token of tokens) if (FORBIDDEN.has(token)) throw new Error(`refused JSON Pointer token ${token}`);
  return tokens;
}

function index(token) {
  if (!/^\d+$/.test(token)) throw new Error(`not an array index: ${token}`);
  return Number(token);
}

export function pointerGet(doc, path) {
  let node = doc;
  for (const token of pointerTokens(path)) {
    if (Array.isArray(node) && /^\d+$/.test(token) && Number(token) < node.length) node = node[Number(token)];
    else if (node && typeof node === 'object' && Object.hasOwn(node, token)) node = node[token];
    else return undefined; // not there yet: progressive rendering treats it as empty
  }
  return node;
}

export function pointerSet(doc, path, value) {
  const tokens = pointerTokens(path);
  if (tokens.length === 0) {
    for (const key of Object.keys(doc)) delete doc[key];
    Object.assign(doc, value ?? {});
    return doc;
  }
  let node = doc;
  for (const token of tokens.slice(0, -1)) {
    if (Array.isArray(node)) node = node[index(token)];
    else node = node[token] ??= {};
  }
  const last = tokens.at(-1);
  if (Array.isArray(node)) node[index(last)] = value;
  else node[last] = value;
  return doc;
}

export function pointerDelete(doc, path) {
  const tokens = pointerTokens(path);
  if (tokens.length === 0) {
    for (const key of Object.keys(doc)) delete doc[key];
    return doc;
  }
  let parent = doc;
  for (const token of tokens.slice(0, -1)) {
    parent = Array.isArray(parent) ? parent[Number(token)] : parent?.[token];
    if (parent == null) return doc;
  }
  const last = tokens.at(-1);
  if (Array.isArray(parent)) {
    if (/^\d+$/.test(last) && Number(last) < parent.length) parent[Number(last)] = undefined; // arrays keep their length
  } else delete parent[last];
  return doc;
}

// ------------------------------------------------------------ surface state

const CHILD_FIELDS = ['child', 'children', 'trigger', 'content'];

export class Surface {
  constructor(id, catalogId, theme = {}, sendDataModel = false) {
    this.id = id;
    this.catalogId = catalogId;
    this.theme = theme;
    this.sendDataModel = sendDataModel;
    this.components = new Map();
    this.data = {};
  }

  apply(message) {
    const kind = messageType(message);
    const body = message[kind];
    if (kind === 'updateComponents') {
      for (const component of body.components) this.components.set(component.id, component);
    } else if (kind === 'updateDataModel') {
      if ('value' in body) pointerSet(this.data, body.path ?? '/', body.value);
      else pointerDelete(this.data, body.path ?? '/');
    } else {
      throw new Error(`${kind} is not a surface update`);
    }
  }

  // A literal stays; {path} reads the data model; a function call is not evaluated here.
  resolve(value) {
    if (value && typeof value === 'object' && 'path' in value) return pointerGet(this.data, value.path);
    if (value && typeof value === 'object' && 'call' in value) return undefined;
    return value;
  }

  // Two-way binding: an input writes straight into the local data model.
  set(path, value) {
    pointerSet(this.data, path, value);
  }

  childIds(component) {
    const ids = [];
    for (const field of CHILD_FIELDS) {
      const ref = component[field];
      if (typeof ref === 'string') ids.push(ref);
      else if (Array.isArray(ref)) ids.push(...ref.filter((r) => typeof r === 'string'));
    }
    return ids;
  }

  // The nested view of the flat map. Unknown ids become {missing: true} placeholders;
  // an id that is its own ancestor becomes {cycle: true}, so a bad map cannot overflow the stack.
  tree(id = 'root', ancestors = new Set()) {
    const component = this.components.get(id);
    if (!component) return { id, missing: true };
    if (ancestors.has(id)) return { id, cycle: true };
    const inner = new Set(ancestors).add(id);
    return { id, component: component.component, children: this.childIds(component).map((c) => this.tree(c, inner)) };
  }

  missingIds() {
    const wanted = new Set();
    for (const c of this.components.values()) for (const id of this.childIds(c)) wanted.add(id);
    return [...wanted].filter((id) => !this.components.has(id)).sort();
  }

  // The client-to-server action message a Button click produces, context resolved now.
  action(componentId, timestamp = new Date().toISOString()) {
    const event = this.components.get(componentId)?.action?.event ?? {};
    const context = {};
    for (const [key, value] of Object.entries(event.context ?? {})) context[key] = this.resolve(value) ?? null;
    return { name: event.name, surfaceId: this.id, sourceComponentId: componentId, timestamp, context };
  }
}

export class SurfaceStore {
  constructor() {
    this.surfaces = new Map();
  }

  apply(message) {
    const kind = messageType(message);
    const body = message[kind];
    const id = body.surfaceId;
    if (kind === 'createSurface') {
      // A repeated createSurface is a reset: the surface starts over. (The official
      // MessageProcessor throws here instead, so a server sends deleteSurface first.)
      this.surfaces.set(id, new Surface(id, body.catalogId, body.theme ?? {}, body.sendDataModel ?? false));
    } else if (kind === 'deleteSurface') {
      this.surfaces.delete(id);
    } else {
      if (!this.surfaces.has(id)) throw new Error(`surface ${id} was never created`);
      this.surfaces.get(id).apply(message);
    }
    return this.surfaces.get(id);
  }
}
