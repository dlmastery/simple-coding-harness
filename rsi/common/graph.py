"""Graph engineering: the job as a DAG whose nodes are legal operators, a
recipe as a path with bindings, and the loop walking paths in order.

`graph.json` names nodes (operators), edges (hard dependencies) and
constraints (one scale, one encode, one model per path; no cycles;
`score_test` is a sink behind `gate: freeze_only`). `paths.json` lists the
paths the loop walks. Both are `mutable: false`: a run may not add a path,
so an illegal path is skipped and counted, never repaired or invented.
"""

from common import recipe

ONE_OF = ("scale", "encode", "model")


def has_cycle(nodes, edges):
    out = {n: [] for n in nodes}
    for a, b in edges:
        out.setdefault(a, []).append(b)
    state = {}

    def visit(n):
        if state.get(n) == 1:
            return True
        if state.get(n) == 2:
            return False
        state[n] = 1
        if any(visit(m) for m in out.get(n, [])):
            return True
        state[n] = 2
        return False

    return any(visit(n) for n in out)


def path_recipe(path):
    """The recipe a path binds, or None when the bindings are not a recipe."""
    b = path.get("bindings", {})
    rec = {f: b.get(f) for f in recipe.FIELDS}
    try:
        return recipe.validate(rec)
    except ValueError:
        return None


def why_illegal(graph, path):
    """The first rule this path breaks, or None when it is legal."""
    nodes, edges = graph["nodes"], [tuple(e) for e in graph["edges"]]
    seq = path.get("nodes", [])
    if not seq or any(n not in nodes for n in seq):
        return "names a node that is not in the graph"
    for a, b in zip(seq, seq[1:]):
        if (a, b) not in edges:
            return f"edge {a} -> {b} is not in the graph"
    for n in ONE_OF:
        if seq.count(n) != 1:
            return f"visits {n} {seq.count(n)} times; a path visits it once"
    if any(nodes[n].get("gate") == "freeze_only" for n in seq):
        return "reaches score_test, a sink that opens only after FREEZE"
    if path_recipe(path) is None:
        return "bindings are not a recipe"
    return None


def lint_graph(graph, paths, task):
    problems = []
    nodes = graph.get("nodes", {})
    edges = [tuple(e) for e in graph.get("edges", [])]
    for a, b in edges:
        if a not in nodes or b not in nodes:
            problems.append(f"edge {a} -> {b} names an unknown node")
    if has_cycle(nodes, edges):
        problems.append("graph.json has a cycle")
    if graph.get("mutable", True):
        problems.append("graph.json must be mutable: false")
    sinks = [n for n, spec in nodes.items() if spec.get("gate") == "freeze_only"]
    if "score_test" in nodes and "score_test" not in sinks:
        problems.append("score_test must be a sink with gate: freeze_only")
    for n in ONE_OF:
        if n not in nodes:
            problems.append(f"graph.json lacks the {n} node")
    ids = [p.get("id") for p in paths]
    if len(set(ids)) != len(ids):
        problems.append("paths.json has duplicate ids")
    for p in paths:
        reason = why_illegal(graph, p)
        if reason:
            problems.append(f"path {p.get('id')}: {reason}")
        r = path_recipe(p)
        if r and r["model"] not in task["allowed_models"]:
            problems.append(f"path {p.get('id')} binds a model the task does not allow")
    return problems
