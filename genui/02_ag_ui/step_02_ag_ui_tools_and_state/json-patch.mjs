// JSON Patch (RFC 6902) for the page: add, replace and remove, with JSON
// Pointer paths. The same code as json_patch.py, so server and page agree.
// The patch is data from the wire, so the path is checked before it is
// followed: no prototype keys, list indexes are digits, a missing parent
// is an error rather than a crash further down.

const OPS = new Set(["add", "replace", "remove"]);
const FORBIDDEN = new Set(["__proto__", "constructor", "prototype"]); // would reach Object.prototype

export function splitPointer(path) {
  if (path === "") return [];
  return path.slice(1).split("/").map((part) => part.replace(/~1/g, "/").replace(/~0/g, "~"));
}

function index(part) {
  if (!/^\d+$/.test(part)) throw new Error(`not a list index: ${part}`);
  return Number(part);
}

function step(parent, part) {
  if (FORBIDDEN.has(part)) throw new Error(`refused path segment ${part}`);
  const child = Array.isArray(parent) ? parent[index(part)] : Object.hasOwn(parent, part) ? parent[part] : undefined;
  if (child === undefined || child === null || typeof child !== "object") throw new Error(`no such path: ${part}`);
  return child;
}

export function applyPatch(document, operations) {
  for (const operation of operations) {
    if (!OPS.has(operation.op)) throw new Error(`unsupported op ${operation.op}`);
    const parts = splitPointer(operation.path ?? "");
    if (parts.length === 0) throw new Error("the root cannot be patched in place");
    let parent = document;
    for (const part of parts.slice(0, -1)) parent = step(parent, part);
    const key = parts[parts.length - 1];
    if (FORBIDDEN.has(key)) throw new Error(`refused path segment ${key}`);
    if (Array.isArray(parent)) {
      if (operation.op === "add") key === "-" ? parent.push(operation.value) : parent.splice(index(key), 0, operation.value);
      else if (operation.op === "replace") parent[index(key)] = operation.value;
      else parent.splice(index(key), 1);
    } else if (operation.op === "remove") delete parent[key];
    else parent[key] = operation.value;
  }
  return document;
}
