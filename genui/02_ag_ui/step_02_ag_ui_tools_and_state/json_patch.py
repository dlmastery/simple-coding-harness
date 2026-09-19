"""JSON Patch (RFC 6902), the three operations this step's state deltas
use: add, replace and remove, with JSON Pointer paths such as
/dashboard/metrics/- (append) or /dashboard/table. An unknown op, a path
into nothing or a list index that is not a number raises ValueError.

The server applies each patch to its own copy of the state before sending
it, so server and page hold the same object after every STATE_DELTA.
json-patch.mjs is the same code for the page.
"""


def split_pointer(path):
    """'/a/b~1c/0' -> ['a', 'b/c', '0']. An empty path means the root."""
    if path == "":
        return []
    return [part.replace("~1", "/").replace("~0", "~") for part in path[1:].split("/")]


OPS = ("add", "replace", "remove")


def index(part):
    """A list index: digits only, so 'x' is refused instead of being coerced."""
    if not part.isdigit():
        raise ValueError(f"not a list index: {part!r}")
    return int(part)


def walk(document, parts):
    """The container the last part points into, and that last part."""
    target = document
    for part in parts[:-1]:
        try:
            target = target[index(part)] if isinstance(target, list) else target[part]
        except (KeyError, IndexError, TypeError):
            raise ValueError(f"no such path: {part!r}") from None
    return target, parts[-1]


def apply_patch(document, operations):
    """Apply the operations in order, in place. Returns the document."""
    for operation in operations:
        op, parts = operation.get("op"), split_pointer(operation.get("path", ""))
        if op not in OPS:
            raise ValueError(f"unsupported op {op}")
        if not parts:
            raise ValueError("the root cannot be patched in place")
        parent, key = walk(document, parts)
        if isinstance(parent, list):
            if op == "add":
                if key == "-":
                    parent.append(operation["value"])
                else:
                    parent.insert(index(key), operation["value"])
            elif op == "replace":
                parent[index(key)] = operation["value"]
            else:
                del parent[index(key)]
        elif isinstance(parent, dict):
            if op == "remove":
                parent.pop(key, None)
            else:
                parent[key] = operation["value"]
        else:
            raise ValueError(f"no such path: {operation.get('path')!r}")
    return document
