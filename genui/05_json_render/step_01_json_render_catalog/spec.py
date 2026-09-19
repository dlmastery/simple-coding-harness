"""Check a spec against the catalog before the page sees it.

The shape is json-render's flat element map, plus an optional state model:

    {"root": "card-1",
     "elements": {"card-1": {"type": "Card", "props": {...}, "children": ["metric-1"]}},
     "state": {"sales": {"total": 500}}}

check_spec() returns a list of problems, empty when the spec is fine. It checks
the things the renderer would otherwise fail on quietly: an unknown type, a
child id that does not exist, and props that do not match the Zod schema
(exported as JSON Schema in catalog.json).

Two allowances match the renderer. A prop whose schema accepts null may be
left out (the prompt shows it as `subtitle?`). A prop may be a dynamic
expression such as {"$state": "/sales/total"}; the renderer resolves those
before the component sees them, so they are not checked against the type.
"""

import jsonschema


def is_expression(value):
    return isinstance(value, dict) and any(key.startswith("$") for key in value)


def props_schema(component, skip):
    """The component's props schema with nullable props, and the names in
    `skip`, made optional."""
    schema = dict(component["props"])
    properties = schema.get("properties", {})

    def accepts_null(prop):
        options = prop.get("anyOf", [prop])
        return any(o.get("type") == "null" or (isinstance(o.get("type"), list) and "null" in o["type"]) for o in options)

    schema["required"] = [
        name for name in schema.get("required", [])
        if name not in skip and not accepts_null(properties.get(name, {}))
    ]
    return schema


def check_spec(spec, catalog):
    problems = []
    if not isinstance(spec, dict) or "root" not in spec or not isinstance(spec.get("elements"), dict):
        return ["spec needs a root id and an elements map"]
    elements = spec["elements"]
    if spec["root"] not in elements:
        problems.append(f"root {spec['root']!r} is not in elements")
    components = catalog["components"]
    for element_id, element in elements.items():
        # the model writes the elements: every shape is checked before it is trusted, and a wrong
        # shape is a sentence in the list, never an exception out of the check
        if not isinstance(element, dict):
            problems.append(f"{element_id}: an element must be an object")
            continue
        kind = element.get("type")
        if kind not in components:
            problems.append(f"{element_id}: unknown type {kind!r}")
            continue
        children = element.get("children") or []
        if not isinstance(children, list) or not all(isinstance(c, str) for c in children):
            problems.append(f"{element_id}: children must be a list of element ids")
            children = []
        for child in children:
            if child not in elements:
                problems.append(f"{element_id}: child {child!r} is not in elements")
        if not isinstance(element.get("props", {}), dict):
            problems.append(f"{element_id}: props must be an object")
            continue
        props = {k: v for k, v in element.get("props", {}).items() if not is_expression(v)}
        expressions = set(element.get("props", {})) - set(props)
        validator = jsonschema.Draft202012Validator(props_schema(components[kind], expressions))
        for error in validator.iter_errors(props):
            where = "/".join(str(p) for p in error.path) or "props"
            problems.append(f"{element_id}: {kind}.{where}: {error.message}")
    if not problems:
        problems += cycles(spec)
    return problems


def cycles(spec):
    """An element that contains itself: the renderer would nest it until it gives up."""

    def visit(element_id, path):
        if element_id in path:
            return [f"{element_id}: element contains itself"]
        found = []
        for child in spec["elements"].get(element_id, {}).get("children") or []:
            found += visit(child, path | {element_id})
        return found

    return visit(spec["root"], frozenset()) if isinstance(spec.get("root"), str) else []


def walk(spec):
    """Yield (depth, id, element) from the root down, in render order; a cycle is visited once."""

    def visit(element_id, depth, path):
        element = spec["elements"].get(element_id)
        if element is None or element_id in path:
            return
        yield depth, element_id, element
        for child in element.get("children") or []:
            yield from visit(child, depth + 1, path | {element_id})

    yield from visit(spec["root"], 0, frozenset())
