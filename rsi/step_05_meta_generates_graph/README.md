# Lesson 05 - A meta skill generates the graph harness, under human approval

Lesson 03's writer, extended to emit `graph.json`, `paths.json` and the loop
over paths; `lint_pack` now walks the graph (no cycle, every edge names a
node, every path legal, `score_test` a sink behind FREEZE), and the proposal
shows the graph to the human as a node / edge list. `edit` is the
interesting answer: the human's change is what lands - a removed edge, a
changed binding - re-linted first, so a human cannot land an illegal graph
either. The writer never sees the run results: still no feedback loop, still
not RSI, still L1 in the framework's terms. What the lesson buys is the
shape every later "improve" reuses: a structured artefact, a linter that
refuses before a human looks, and an approval whose `edit` branch is real.

## Getting started

Lesson 04 left the graph pack; this lesson generates it. It adds
`.claude/skills/graph-writer/` (`SKILL.md`, `tools.md`, `task.json`,
`template/` with six files), mirrored to `.agents/skills/`. Nothing new under
`../tools/`: `lint_pack.py` already walks graphs (`_lib/graph.py`), and
`propose.py` already renders `graph.json` as nodes and edges. Open your agent
in this directory; the generated pack lands at
`.claude/skills/adult-income-graph/`.

## How to execute it

1. Type the prompt:

   ```text
   Use the graph-writer skill: generate the graph pack for the task in .claude/skills/graph-writer/task.json and propose it to me.
   ```

   The agent renders the six files into `runs/graph-writer/rendered/` and runs:

   ```bash
   python ../tools/lint_pack.py --pack runs/graph-writer/rendered --task .claude/skills/graph-writer/task.json
   python ../tools/propose.py --pack .claude/skills/graph-writer --task .claude/skills/graph-writer/task.json --target .claude/skills/adult-income-graph --kind pack --payload @runs/graph-writer/rendered --summary "graph pack for adult_income: 6 nodes, 5 edges, 24 paths"
   ```

2. **You will be asked**: approve / edit / reject, with the graph shown as
   nodes and edges and the 24 paths as a table. Try `edit`: say what to
   change (in the recording: "edit: change the binding of p07 to hyper 0.25
   (logreg C=0.25); keep everything else"). The agent applies your change to
   a copy under `runs/graph-writer/edited/`, lints it, and runs:

   ```bash
   python ../tools/apply.py --pack .claude/skills/graph-writer --task .claude/skills/graph-writer/task.json --proposal p1 --approved "edit: change the binding of p07 to hyper 0.25 (logreg C=0.25); keep everything else" --edited @runs/graph-writer/edited
   ```

   An edit that removes the edge `scale -> encode` makes every path illegal:
   `apply.py` answers `the edited pack does not lint: [... edge scale -> encode
   is not in the graph ...]; nothing lands`. An edit that drops a path and
   lowers `N` to 23 is refused too (`loop.json N 23 != task budget 24`): the
   human may reshape the graph, not the budget.

3. Run what landed with the `adult-income-graph` skill (lesson 04's prompt).
   Reset: `rm -rf runs .claude/skills/adult-income-graph`. Headless: two
   turns, `claude -p "<the prompt>"` then `claude -p --continue "<your answer>"`,
   both with `--allowedTools "Bash,Read,Write,Edit,Skill"`. Tests:
   `python run_tests.py rsi`.

## What it looks like

`.claude/skills/graph-writer/SKILL.md` - step 6's `edit` branch:

```markdown
---
name: graph-writer
description: Write a graph harness pack (SKILL.md, tools.md, schema.json, graph.json, paths.json, loop.json) for the task in task.json and propose it for human approval; the user sees the graph as nodes and edges and may edit it before it lands. Use in rsi/step_05_meta_generates_graph when a task.json exists and no graph pack does. You do not fit models.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# Graph writer: a meta skill whose output is a graph harness

## Procedure
5. Show the user the node / edge list and every file, then ask: **approve / edit / reject**. An edit may remove an edge or a path, or change a binding; what lands is the user's version, linted again. Wait for the answer; run nothing until it arrives.
6. Land exactly what was decided, quoting the user's words verbatim:
   - approve: `python ../tools/apply.py --pack W --task T --proposal <id> --approved "<the user's exact words>"`
   - edit: apply the user's change to a copy of the rendered files under `runs/graph-writer/edited/` (their words say what to change; if a removed edge makes a path illegal, leave the path - the linter will say so and nothing lands until the user resolves it), then `python ../tools/apply.py --pack W --task T --proposal <id> --approved "<their words>" --edited @runs/graph-writer/edited`
```

`../tools/_lib/graph.py` - what the linter walks before a human sees a
proposal, and again before an edit lands:

```python
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
```

`../tools/_lib/proposals.py` - the graph rendered for the human, on top of
the files:

```python
        for name, text in payload.items():
            if name.endswith("graph.json"):
                g = json.loads(text)
                out.append(f"### {name} as a graph\nnodes: {', '.join(g['nodes'])}\nedges: " + "; ".join(f"{a} -> {b}" for a, b in g["edges"]))
```

`../tools/apply.py` - an edited pack is linted again; the human's version is
what lands:

```python
    if decision == "edit":
        if a.edited is None:
            raise ValueError("--approved edit needs --edited <the user's version>; nothing lands")
        payload = cli.value(a.edited)
        if record["kind"] == "pack":
            problems = lint_payload(payload, run.task)
            if problems:
                raise ValueError(f"the edited pack does not lint: {problems}; nothing lands")
```

The recorded run (Claude Code 2.1.278, headless, two turns; the agent's
rendering and the 24-row path table it showed are trimmed):

```text
[Skill graph-writer]
agent> Using the graph-writer skill. Boot order: tools.md, task.json, then the templates.
[Read task.json] [Read template/*]  [Write runs/graph-writer/rendered/{SKILL.md,graph.json,loop.json,paths.json,schema.json,tools.md}]
$ python ../tools/lint_pack.py --pack runs/graph-writer/rendered --task .claude/skills/graph-writer/task.json
{"ok": true, "problems": [], ...}
agent> Lint is ok. Proposing:
$ python ../tools/propose.py --pack .claude/skills/graph-writer --task .claude/skills/graph-writer/task.json --target .claude/skills/adult-income-graph --kind pack --payload @runs/graph-writer/rendered --summary "graph pack for adult_income: 6 nodes, 5 edges, 24 paths"
{"id": "p1", "diff": "### graph.json as a graph\nnodes: load, scale, encode, model, fit, score_test\nedges: load -> scale; scale -> encode; encode -> model; model -> fit; fit -> score_test\n### SKILL.md ...", ...}
agent> ## Proposal p1 - graph pack for adult_income
Target: .claude/skills/adult-income-graph - lint: ok (0 problems) - nothing has landed yet.
The graph: nodes load, scale, encode, model, fit, score_test; edges load -> scale -> encode -> model -> fit -> score_test.
score_test: sink, gate: freeze_only. Constraints: one_of [scale, encode, model], no_cycles. mutable: false.
The paths: 24, every one load -> scale -> encode -> model -> fit; p00 logreg 1 yes onehot none (baseline) ...
p07 logreg 1 no ordinal balanced ... p23 hgb 0.1 no ordinal balanced.
approve / edit / reject? An edit may remove an edge or a path, or change a binding - tell me what
to change and I'll re-lint your version before it lands. I'll run nothing until you answer.
[20 turns, 117 s]
=== user> edit: change the binding of p07 to hyper 0.25 (logreg C=0.25); keep everything else
agent> Applying your edit to a copy under runs/graph-writer/edited/, then linting it before it lands.
$ mkdir -p runs/graph-writer/edited && cp runs/graph-writer/rendered/* runs/graph-writer/edited/
[Edit runs/graph-writer/edited/paths.json]
$ python ../tools/lint_pack.py --pack runs/graph-writer/edited --task .claude/skills/graph-writer/task.json
{"ok": true, "problems": [], ...}
agent> Edited version lints ok. Landing it with your words:
$ python ../tools/apply.py --pack .claude/skills/graph-writer --task .claude/skills/graph-writer/task.json --proposal p1 --approved "edit: change the binding of p07 to hyper 0.25 (logreg C=0.25); keep everything else" --edited @runs/graph-writer/edited
{"id": "p1", "decision": "edit", "landed": true, "target": ".claude/skills/adult-income-graph", "files": ["SKILL.md", "graph.json", "loop.json", "paths.json", "schema.json", "tools.md"], "approved_by": "human", "words": "edit: change the binding of p07 to hyper 0.25 (logreg C=0.25); keep everything else"}
agent> Proposal p1 - decision: edit - landed. The only difference from the proposed pack is
paths.json's p07: hyper 1 -> 0.25. The edited pack was re-linted before landing: ok, 0 problems
(0.25 is in logreg's hyper list [0.25, 1, 4], so the path is still a valid recipe).
I did not fit, score, or run the generated pack; that's for the adult-income-graph skill itself.
[6 turns, 51 s]
```

What to notice: what landed is the human's version (`p07` at `C=0.25`,
checked after the recording), the human's words are in the trace, and the
agent re-linted before landing without being told twice - the rule is in
its procedure and in the script.

Files:

```text
step_05_meta_generates_graph/
├── README.md, test_step.py, .claude/settings.json
├── .claude/skills/graph-writer/
│   ├── SKILL.md, tools.md, task.json
│   └── template/                  SKILL.md, tools.md, schema.json, graph.json, paths.json ({{paths}}), loop.json
├── .agents/skills/graph-writer/
├── .claude/skills/adult-income-graph/   (after approval / edit)
└── runs/graph-writer/{rendered/, edited/, adult_income/proposals/p1.json, adult_income/traces.jsonl}
```

## Governance considerations

- **Who approves what.** The human approves the graph and the paths, and
  may edit them; the writer decides nothing about the task. The linter
  stands between both of them and the disk: neither the writer's nor the
  human's version lands unless it lints against `task.json`.
- **The hook.** Blocks `apply.py` without the user's words.
- **What the script refuses.** A cyclic graph, an unknown node, a path that
  visits `scale` / `encode` / `model` other than once, a path that reaches
  the sink, a binding that is not a recipe, a changed budget - before the
  human sees the proposal and again on an edit; `walk_path.py` /
  `fit_recipe.py` for the writer.
- **What is and is not self-modified.** Nothing. The generated pack is
  immutable while it runs (lesson 04's checksums), and the writer never
  reads a run.

## How to measure it

| Claim | Test |
|---|---|
| the writer cannot walk or fit | `test_writer_cannot_walk_or_fit` |
| a cycle or an illegal path is refused before the human sees the proposal (no proposal file is written) | `test_cycle_and_bad_path_refused_before_the_human_sees_them` |
| the proposal shows the graph as nodes and edges | `test_proposal_shows_the_graph_as_nodes_and_edges` |
| an edit that changes a binding lands and the pack still runs; one that lowers `N` does not lint | `test_edit_removing_a_path_lands_and_the_pack_still_runs` |
| an edit that removes an edge every path needs does not land | `test_edit_removing_a_needed_edge_does_not_land` |
| the generated pack equals lesson 04's graph and paths and passes its checks | `test_generated_pack_passes_lesson_04_checks` |
| the pack contract | `test_pack_contract` |
| the recorded run reproduces (`RSI_LIVE=1`) | `test_live_claude_code` |

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 06 - the RSI harness](../step_06_rsi_harness/README.md): the first
file a later run reads that an earlier run wrote. Previous:
[Lesson 04 - graph engineering](../step_04_graph_harness/README.md).
