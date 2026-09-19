"""Step 02 - what a page can paint at each point of a streamed layout.

Two questions, asked after every chunk of the model's JSON:

  complete: how many catalog components are closed and reachable from the
            root, so a renderer can draw them for good
  skeleton: is the list of the root's direct children final, so the page
            knows the layout and can reserve every slot

The nested tree closes its root last, so the skeleton is only known at the
end. The flat map writes the root element first, so the skeleton is known
after a few dozen characters. That is the whole argument for the flat shape.
"""

from catalog import CATALOG
from partial_json import is_partial, parse_partial


def is_component(node):
    return isinstance(node, dict) and node.get("type") in CATALOG and isinstance(node.get("props"), dict)


def complete_in_tree(node):
    """Closed catalog nodes in a nested tree, counting the closed ones inside open parents."""
    if not is_component(node):
        return 0
    count = 0 if is_partial(node) or is_partial(node["props"]) else 1
    return count + sum(complete_in_tree(child) for child in node.get("children") or [])


def complete_in_flat(spec, element_id=None, seen=None):
    """Closed catalog elements reachable from the root by id."""
    if not isinstance(spec, dict) or not isinstance(spec.get("elements"), dict):
        return 0
    seen = set() if seen is None else seen
    element_id = spec.get("root") if element_id is None else element_id
    node = spec["elements"].get(element_id)
    if element_id in seen or not is_component(node):
        return 0
    seen.add(element_id)
    count = 0 if is_partial(node) or is_partial(node["props"]) else 1
    children = [c for c in node.get("children") or [] if isinstance(c, str)]  # a nested node here is a shape mix-up
    return count + sum(complete_in_flat(spec, child, seen) for child in children)


def skeleton_known(spec, shape):
    """Is the root's list of direct children final?"""
    if shape == "tree":
        return is_component(spec) and not is_partial(spec) and not is_partial(spec.get("children", []))
    if not isinstance(spec, dict) or not isinstance(spec.get("elements"), dict):
        return False
    root = spec["elements"].get(spec.get("root"))
    return is_component(root) and not is_partial(root) and not is_partial(root.get("children", []))


def measure(spec, shape):
    complete = complete_in_tree(spec) if shape == "tree" else complete_in_flat(spec)
    return {"complete": complete, "skeleton": skeleton_known(spec, shape)}


def replay(chunks, shape):
    """Feed the chunks one by one; report the chunk index of the first paint and of the skeleton."""
    text = ""
    first_paint = skeleton = None
    for index, chunk in enumerate(chunks, 1):
        text += chunk
        try:
            spec = parse_partial(text)
        except ValueError:
            spec = None  # not JSON (a fence, prose): nothing to paint yet
        got = measure(spec, shape)
        if first_paint is None and got["complete"]:
            first_paint = index
        if skeleton is None and got["skeleton"]:
            skeleton = index
    return {"chunks": len(chunks), "first_paint_chunk": first_paint, "skeleton_chunk": skeleton, "chars": len(text)}
