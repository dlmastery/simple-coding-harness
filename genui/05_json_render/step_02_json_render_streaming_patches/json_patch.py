"""RFC 6902 JSON Patch and RFC 6901 JSON Pointer, in Python, for the server and
the tests. The page uses createSpecStreamCompiler from @json-render/core; this
module is the same idea on the other side of the wire.

    apply_patch(doc, {"op": "add", "path": "/elements/card-1", "value": {...}})

    stream = SpecStream()
    for chunk in model_output:      # any split, lines may arrive in pieces
        for patch in stream.push(chunk):
            ...                     # one complete, applied patch at a time
    stream.spec                     # the document so far

The six operations are add, remove, replace, move, copy and test. Two
departures from the RFC, copied from the library's compiler so both sides
build the same spec: add creates a missing parent object (or array, when
the next segment is an index), and replace creates a missing target. The
model's first element patch is "/elements/card-1" with no "/elements" patch
before it, and a later turn may "replace" a state key it never added. remove,
move, copy and test stay strict: the target must exist.
"""

import copy
import json

OPS = {"add", "remove", "replace", "move", "copy", "test"}


class PatchError(ValueError):
    pass


def parse_pointer(pointer):
    """'/elements/card-1/props/title' -> ['elements', 'card-1', 'props', 'title']."""
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise PatchError(f"pointer must start with '/': {pointer!r}")
    return [part.replace("~1", "/").replace("~0", "~") for part in pointer[1:].split("/")]


def _step(container, key, pointer):
    if isinstance(container, list):
        if key == "-":
            return len(container)
        if not key.isdigit():
            raise PatchError(f"{pointer}: {key!r} is not an array index")
        return int(key)
    return key


def get_path(doc, pointer):
    node = doc
    for key in parse_pointer(pointer):
        key = _step(node, key, pointer)
        try:
            node = node[key]
        except (KeyError, IndexError, TypeError):
            raise PatchError(f"{pointer}: not found") from None
    return node


def _parent(doc, pointer, create=False):
    parts = parse_pointer(pointer)
    if not parts:
        raise PatchError("the root cannot be a target of this operation")
    parent = doc
    for index, key in enumerate(parts[:-1]):
        key = _step(parent, key, pointer)
        missing = key not in parent if isinstance(parent, dict) else not (isinstance(parent, list) and key < len(parent))
        if missing and create:
            following = parts[index + 1]
            child = [] if following == "-" or following.isdigit() else {}
            if isinstance(parent, list):
                parent.insert(key, child)
            else:
                parent[key] = child
        try:
            parent = parent[key]
        except (KeyError, IndexError, TypeError):
            raise PatchError(f"{pointer}: parent not found") from None
    return parent, _step(parent, parts[-1], pointer)


def _add(doc, pointer, value):
    parent, key = _parent(doc, pointer, create=True)
    if isinstance(parent, list):
        if key > len(parent):
            raise PatchError(f"{pointer}: index past the end")
        parent.insert(key, value)
    elif isinstance(parent, dict):
        parent[key] = value
    else:
        raise PatchError(f"{pointer}: parent is not a container")


def _remove(doc, pointer):
    parent, key = _parent(doc, pointer)
    try:
        return parent.pop(key)
    except (KeyError, IndexError, TypeError):
        raise PatchError(f"{pointer}: not found") from None


def apply_patch(doc, patch):
    """Apply one operation in place. Returns doc."""
    op = patch.get("op")
    if op not in OPS:
        raise PatchError(f"unknown op {op!r}")
    path = patch.get("path")
    if not isinstance(path, str):
        raise PatchError("patch needs a path")
    if op in {"add", "replace", "test"} and "value" not in patch:
        raise PatchError(f"{op} needs a value")
    if op in {"move", "copy"} and not isinstance(patch.get("from"), str):
        raise PatchError(f"{op} needs a from")

    if op == "add":
        if path == "":
            doc.clear()
            doc.update(patch["value"])
        else:
            _add(doc, path, copy.deepcopy(patch["value"]))
    elif op == "remove":
        _remove(doc, path)
    elif op == "replace":
        parent, key = _parent(doc, path, create=True)
        if isinstance(parent, list) and key < len(parent):
            parent[key] = copy.deepcopy(patch["value"])
        else:
            _add(doc, path, copy.deepcopy(patch["value"]))
    elif op == "move":
        value = _remove(doc, patch["from"])
        _add(doc, path, value)
    elif op == "copy":
        _add(doc, path, copy.deepcopy(get_path(doc, patch["from"])))
    elif op == "test":
        if get_path(doc, path) != patch["value"]:
            raise PatchError(f"test failed at {path}")
    return doc


def apply_patches(doc, patches):
    for patch in patches:
        apply_patch(doc, patch)
    return doc


class SpecStream:
    """Feed text chunks in; complete patch lines come out, applied to .spec."""

    def __init__(self):
        self.spec = {}
        self.patches = []
        self.buffer = ""
        self.skipped = []

    def push(self, chunk):
        self.buffer += chunk
        lines = self.buffer.split("\n")
        self.buffer = lines.pop()
        return self._apply_lines(lines)

    def finish(self):
        """Apply the last line when the stream ended without a newline."""
        rest, self.buffer = self.buffer, ""
        return self._apply_lines([rest]) if rest.strip() else []

    def _apply_lines(self, lines):
        applied = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                patch = json.loads(line)
                apply_patch(self.spec, patch)
            except (ValueError, PatchError) as error:
                self.skipped.append((line, str(error)))
                continue
            self.patches.append(patch)
            applied.append(patch)
        return applied

    def has_root(self):
        """True once the page has something to paint: /root and its element."""
        return self.spec.get("root") in self.spec.get("elements", {})
