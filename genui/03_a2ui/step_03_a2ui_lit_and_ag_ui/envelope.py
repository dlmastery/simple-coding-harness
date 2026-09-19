"""A2UI v0.9.1 by hand: the four envelope messages, schema validation, JSON
Pointer, and the surface state a renderer keeps.

The schema files in schema/ are the ones the a2ui-agent-sdk package bundles
for v0.9.1 (Apache-2.0). server_to_client.json refers to "catalog.json" for
the component definitions; the registry below maps that name to the Basic
Catalog, which is how the spec says a validator plugs a catalog in.
"""

import json
from pathlib import Path

HERE = Path(__file__).parent
SCHEMA_DIR = HERE / "schema"
VERSION = "v0.9.1"
BASIC_CATALOG_ID = "https://a2ui.org/specification/v0_9_1/catalogs/basic/catalog.json"


# ------------------------------------------------------------ the four messages


def create_surface(surface_id, catalog_id=BASIC_CATALOG_ID, theme=None, send_data_model=None):
    """A createSurface message. A surface must exist before anything else targets it."""
    body = {"surfaceId": surface_id, "catalogId": catalog_id}
    if theme is not None:
        body["theme"] = theme
    if send_data_model is not None:
        body["sendDataModel"] = send_data_model
    return {"version": VERSION, "createSurface": body}


def update_components(surface_id, components):
    """An updateComponents message: a flat list; one component must have id 'root'."""
    return {"version": VERSION, "updateComponents": {"surfaceId": surface_id, "components": list(components)}}


def update_data_model(surface_id, path="/", value=None, remove=False):
    """An updateDataModel message. Omit value (remove=True) to delete the key at path."""
    body = {"surfaceId": surface_id, "path": path}
    if not remove:
        body["value"] = value
    return {"version": VERSION, "updateDataModel": body}


def delete_surface(surface_id):
    """A deleteSurface message: the client drops the surface and its state."""
    return {"version": VERSION, "deleteSurface": {"surfaceId": surface_id}}


def message_type(message):
    """Which of the four keys a message carries, or None."""
    for key in ("createSurface", "updateComponents", "updateDataModel", "deleteSurface"):
        if key in message:
            return key
    return None


# ------------------------------------------------------------ schema validation

_schemas = None


def load_schema(name):
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def schemas():
    """The envelope validator plus a registry with the catalog wired in under the
    placeholder name the envelope uses ("catalog.json" next to server_to_client.json)."""
    global _schemas
    if _schemas is None:
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource

        envelope = load_schema("server_to_client.json")
        common = load_schema("common_types.json")
        catalog = load_schema("catalog.json")
        placeholder = envelope["$id"].rsplit("/", 1)[0] + "/catalog.json"
        registry = Registry().with_resources([
            (envelope["$id"], Resource.from_contents(envelope)),
            (common["$id"], Resource.from_contents(common)),
            (catalog["$id"], Resource.from_contents(catalog)),
            (placeholder, Resource.from_contents(catalog)),
        ])
        _schemas = {
            "envelope": Draft202012Validator(envelope, registry=registry),
            "registry": registry,
            "catalog": catalog,
        }
    return _schemas


def component_error(component):
    """Validate one component against its own catalog entry, for a readable message.

    The envelope's anyComponent is a oneOf over every catalog entry, so its
    error only says "not valid under any of the given schemas". The entry
    picked by the component name says what is wrong.
    """
    from jsonschema import Draft202012Validator

    name = component.get("component")
    catalog = schemas()["catalog"]
    if name not in catalog["components"]:
        return [], f"{name!r} is not a component of the Basic Catalog"
    entry = Draft202012Validator({"$ref": f"{catalog['$id']}#/components/{name}"}, registry=schemas()["registry"])
    errors = list(entry.iter_errors(component))
    if not errors:
        return [], None
    # the deepest error names the cause; "unevaluated properties" is its symptom one level up
    weak = ("unevaluatedProperties", "additionalProperties")
    error = max(errors, key=lambda e: (len(e.absolute_path), e.validator not in weak))
    return list(error.absolute_path), error.message


def validate(message):
    """The spec's standard error shape ({code, surfaceId, path, message}) or None when valid."""
    from jsonschema.exceptions import best_match

    error = best_match(schemas()["envelope"].iter_errors(message))
    if error is None:
        return None
    body = message.get(message_type(message) or "", {})
    surface_id = body.get("surfaceId", "") if isinstance(body, dict) else ""
    path, text = list(error.absolute_path), error.message
    if path[:2] == ["updateComponents", "components"] and len(path) == 3:
        inner_path, inner_text = component_error(body["components"][path[2]])
        path, text = path + inner_path, inner_text or text
    return {"code": "VALIDATION_FAILED", "surfaceId": surface_id, "path": "/" + "/".join(str(p) for p in path), "message": text[:200]}


def repair_checks(message):
    """The spec's Example Stream writes a check as {call, args, message}; the schema's
    CheckRule wants {condition: {call, args}, message}. Rewrite in place, return the count."""
    fixed = 0
    for component in message.get("updateComponents", {}).get("components", []):
        for rule in component.get("checks", []):
            if "condition" not in rule and "call" in rule:
                rule["condition"] = {"call": rule.pop("call"), "args": rule.pop("args", {})}
                fixed += 1
    return fixed


# ------------------------------------------------------------ JSON Pointer (RFC 6901)


def pointer_tokens(path):
    if path in ("", "/"):
        return []
    if not path.startswith("/"):
        raise ValueError(f"absolute JSON Pointer expected, got {path!r}")
    return [token.replace("~1", "/").replace("~0", "~") for token in path[1:].split("/")]


def pointer_get(doc, path):
    """The value at path, or None when any step is missing (progressive rendering)."""
    node = doc
    for token in pointer_tokens(path):
        if isinstance(node, list) and token.isdigit() and int(token) < len(node):
            node = node[int(token)]
        elif isinstance(node, dict) and token in node:
            node = node[token]
        else:
            return None
    return node


def index(token):
    """A list index: digits only, so '/tags/x' is refused instead of raising deep inside."""
    if not token.isdigit():
        raise ValueError(f"not a list index: {token!r}")
    return int(token)


def pointer_set(doc, path, value):
    """Upsert: create missing objects on the way, then replace the value at path."""
    tokens = pointer_tokens(path)
    if not tokens:
        doc.clear()
        doc.update(value or {})
        return doc
    node = doc
    for token in tokens[:-1]:
        if isinstance(node, list):
            node = node[index(token)]
        else:
            node = node.setdefault(token, {})
    last = tokens[-1]
    if isinstance(node, list):
        node[index(last)] = value
    else:
        node[last] = value
    return doc


def pointer_delete(doc, path):
    tokens = pointer_tokens(path)
    if not tokens:
        doc.clear()
        return doc
    parent = doc
    for token in tokens[:-1]:
        if isinstance(parent, list):
            parent = parent[int(token)] if token.isdigit() and int(token) < len(parent) else None
        else:
            parent = parent.get(token)
        if parent is None:
            return doc
    last = tokens[-1]
    if isinstance(parent, dict):
        parent.pop(last, None)
    elif isinstance(parent, list) and last.isdigit() and int(last) < len(parent):
        parent[int(last)] = None  # arrays keep their length
    return doc


# ------------------------------------------------------------ surface state

CHILD_FIELDS = ("child", "children", "trigger", "content")


class Surface:
    """What a client keeps per surface: a component map and a data model.

    The tree is rebuilt from the map at render time, so components may arrive
    in any order and refer to ids that do not exist yet.
    """

    def __init__(self, surface_id, catalog_id, theme=None, send_data_model=False):
        self.id = surface_id
        self.catalog_id = catalog_id
        self.theme = theme or {}
        self.send_data_model = send_data_model
        self.components = {}
        self.data = {}

    def apply(self, message):
        kind = message_type(message)
        body = message[kind]
        if kind == "updateComponents":
            for component in body["components"]:
                self.components[component["id"]] = component
        elif kind == "updateDataModel":
            if "value" in body:
                pointer_set(self.data, body.get("path", "/"), body["value"])
            else:
                pointer_delete(self.data, body.get("path", "/"))
        else:
            raise ValueError(f"{kind} is not a surface update")

    def resolve(self, value):
        """A literal stays; {"path": ...} reads the data model; a function call is not evaluated here."""
        if isinstance(value, dict) and "path" in value:
            return pointer_get(self.data, value["path"])
        if isinstance(value, dict) and "call" in value:
            return None
        return value

    def set(self, path, value):
        """Two-way binding: an input writes straight into the local data model."""
        pointer_set(self.data, path, value)

    def child_ids(self, component):
        ids = []
        for field in CHILD_FIELDS:
            ref = component.get(field)
            if isinstance(ref, str):
                ids.append(ref)
            elif isinstance(ref, list):
                ids.extend(r for r in ref if isinstance(r, str))
        return ids

    def tree(self, component_id="root", ancestors=frozenset()):
        """The nested view of the flat map. Unknown ids become {"missing": True} placeholders;
        an id that is its own ancestor becomes {"cycle": True}, so a bad map cannot recurse forever."""
        component = self.components.get(component_id)
        if component is None:
            return {"id": component_id, "missing": True}
        if component_id in ancestors:
            return {"id": component_id, "cycle": True}
        inner = ancestors | {component_id}
        return {
            "id": component_id,
            "component": component["component"],
            "children": [self.tree(cid, inner) for cid in self.child_ids(component)],
        }

    def missing_ids(self):
        wanted = {cid for c in self.components.values() for cid in self.child_ids(c)}
        return sorted(wanted - set(self.components))

    def action(self, component_id, timestamp):
        """The client-to-server action message a Button click produces, context resolved."""
        event = self.components[component_id].get("action", {}).get("event", {})
        context = {key: self.resolve(value) for key, value in event.get("context", {}).items()}
        return {"name": event.get("name"), "surfaceId": self.id, "sourceComponentId": component_id,
                "timestamp": timestamp, "context": context}


class SurfaceStore:
    """All surfaces on a page. Routes each envelope message to the right one."""

    def __init__(self):
        self.surfaces = {}

    def apply(self, message):
        kind = message_type(message)
        body = message[kind]
        surface_id = body["surfaceId"]
        if kind == "createSurface":
            # A repeated createSurface is a reset: the surface starts over. (The official
            # MessageProcessor raises here instead, so a server sends deleteSurface first.)
            self.surfaces[surface_id] = Surface(surface_id, body["catalogId"], body.get("theme"), body.get("sendDataModel", False))
        elif kind == "deleteSurface":
            self.surfaces.pop(surface_id, None)
        else:
            if surface_id not in self.surfaces:
                raise ValueError(f"surface {surface_id} was never created")
            self.surfaces[surface_id].apply(message)
        return self.surfaces.get(surface_id)


def read_stream(path):
    """A JSONL file as a list of messages."""
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
