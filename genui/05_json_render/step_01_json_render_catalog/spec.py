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
        kind = element.get("type")
        if kind not in components:
            problems.append(f"{element_id}: unknown type {kind!r}")
            continue
        for child in element.get("children", []):
            if child not in elements:
                problems.append(f"{element_id}: child {child!r} is not in elements")
        props = {k: v for k, v in element.get("props", {}).items() if not is_expression(v)}
        expressions = set(element.get("props", {})) - set(props)
        validator = jsonschema.Draft202012Validator(props_schema(components[kind], expressions))
        for error in validator.iter_errors(props):
            where = "/".join(str(p) for p in error.path) or "props"
            problems.append(f"{element_id}: {kind}.{where}: {error.message}")
    return problems


def walk(spec):
    """Yield (depth, id, element) from the root down, in render order."""

    def visit(element_id, depth):
        element = spec["elements"].get(element_id)
        if element is None:
            return
        yield depth, element_id, element
        for child in element.get("children", []):
            yield from visit(child, depth + 1)

    yield from visit(spec["root"], 0)
