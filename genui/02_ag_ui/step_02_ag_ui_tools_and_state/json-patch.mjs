// JSON Patch (RFC 6902) for the page: add, replace and remove, with JSON
// Pointer paths. The same code as json_patch.py, so server and page agree.

export function splitPointer(path) {
  if (path === "") return [];
  return path.slice(1).split("/").map((part) => part.replace(/~1/g, "/").replace(/~0/g, "~"));
}

export function applyPatch(document, operations) {
  for (const operation of operations) {
    const parts = splitPointer(operation.path);
    if (parts.length === 0) throw new Error("the root cannot be patched in place");
    let parent = document;
    for (const part of parts.slice(0, -1)) parent = Array.isArray(parent) ? parent[Number(part)] : parent[part];
    const key = parts[parts.length - 1];
    if (Array.isArray(parent)) {
      if (operation.op === "add") key === "-" ? parent.push(operation.value) : parent.splice(Number(key), 0, operation.value);
      else if (operation.op === "replace") parent[Number(key)] = operation.value;
      else if (operation.op === "remove") parent.splice(Number(key), 1);
      else throw new Error(`unsupported op ${operation.op}`);
    } else if (operation.op === "add" || operation.op === "replace") parent[key] = operation.value;
    else if (operation.op === "remove") delete parent[key];
    else throw new Error(`unsupported op ${operation.op}`);
  }
  return document;
}
