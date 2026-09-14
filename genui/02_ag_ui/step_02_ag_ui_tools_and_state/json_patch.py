"""JSON Patch (RFC 6902), the three operations AG-UI state deltas use:
add, replace and remove, with JSON Pointer paths such as
/dashboard/metrics/- (append) or /dashboard/table.

The server applies each patch to its own copy of the state before sending
it, so server and page hold the same object after every STATE_DELTA.
json-patch.mjs is the same code for the page.
"""


def split_pointer(path):
    """'/a/b~1c/0' -> ['a', 'b/c', '0']. An empty path means the root."""
    if path == "":
        return []
    return [part.replace("~1", "/").replace("~0", "~") for part in path[1:].split("/")]


def walk(document, parts):
    """The container the last part points into, and that last part."""
    target = document
    for part in parts[:-1]:
        target = target[int(part)] if isinstance(target, list) else target[part]
    return target, parts[-1]


def apply_patch(document, operations):
    """Apply the operations in order, in place. Returns the document."""
    for operation in operations:
        op, parts = operation["op"], split_pointer(operation["path"])
        if not parts:
            raise ValueError("the root cannot be patched in place")
        parent, key = walk(document, parts)
        if isinstance(parent, list):
            if op == "add":
                if key == "-":
                    parent.append(operation["value"])
                else:
                    parent.insert(int(key), operation["value"])
            elif op == "replace":
                parent[int(key)] = operation["value"]
            elif op == "remove":
                del parent[int(key)]
            else:
                raise ValueError(f"unsupported op {op}")
        else:
            if op in ("add", "replace"):
                parent[key] = operation["value"]
            elif op == "remove":
                del parent[key]
            else:
                raise ValueError(f"unsupported op {op}")
    return document
