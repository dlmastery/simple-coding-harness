# Lesson 05 - A meta skill generates the graph harness, under human approval

Lesson 03's writer, extended to emit the graph: `graph.json`, `paths.json`
and a `loop.json` that walks paths, from the same intent and the same
template mechanism. Two things are new. The lint grows the DAG checks - no
cycle, every path built from nodes the graph has and edges it allows, one
`scale` / `encode` / `model` per path, never a step through the test sink -
and the writer proves the lint works before trusting it, by linting a
planted bad paths file (`bad_paths.json`: a cycle `fit -> load`, a path with
two `scale` nodes, a path through `score_test`) and showing the refusal. And
the human's answer that matters is `edit`: the recorded run answers
`edit: remove path p24`, the writer makes exactly that change, lints the
edited pack, and lands the human's version - 23 paths - with the words in the
trace. The writer never sees a run result. There is still no feedback loop,
still no RSI; there is a human whose edit is what lands.

## Getting started

Prerequisites: lesson 04 (the writer's output is that pack, with 24 legal
paths and no planted illegal one) and lesson 03 (the approval cycle:
`propose`, `apply`, the `.approved` file, the hook). This lesson adds
`.claude/skills/graph-writer/` with its `template/` (six files) and
`bad_paths.json`.

## How to execute it

1. Open your agent in this directory and type the prompt:

   ```text
   Use the graph-writer skill: generate the graph pack for ../tasks/01_adult_income and propose it.
   ```

   The agent fills the template, lints the bad paths (refused: cycle, two
   scales, a step through the test sink), lints the real pack (passes),
   records the proposal, shows you the graph as a node / edge list and the
   24 paths as `id: bindings` lines, and asks **approve / edit / reject**.

2. Answer `edit: remove path p24` (as recorded), or `approve`, or
   `reject`. An edit is made to a copy under `proposals/p001-edited/`,
   linted again - an edit that breaks the DAG or a constraint is refused
   and you are asked again - and landed with `apply --edited`.

3. Headless, as recorded, two turns:

   ```bash
   claude -p "Use the graph-writer skill: generate the graph pack for ../tasks/01_adult_income and propose it." \
     --allowedTools "Bash,Read,Write,Edit,Skill" --setting-sources project --strict-mcp-config
   claude -p --continue "edit: remove path p24" \
     --allowedTools "Bash,Read,Write,Edit,Skill" --setting-sources project --strict-mcp-config
   ```

4. Tests: `python run_tests.py rsi`. Offline: the filled template is a legal
   graph pack whose `graph.json` is lesson 04's byte for byte; the bad paths
   are refused by the DAG lint (written in the test the way the contract
   states it); the procedure lints before it proposes and lands the edit.
   `RSI_LIVE=1`: after turn one a proposal, the refusal named, nothing
   landed; after the edit, 23 paths (the fill minus `p24`) in both mirrors,
   the other five files identical to the fill, the trace `propose` then
   `apply` with the words.

5. To reset: `rm -rf runs .claude/skills/adult-income-graph .agents/skills/adult-income-graph`.

## What it looks like

`.claude/skills/graph-writer/SKILL.md` - steps 3 and 5 are the lesson:

```markdown
3. Self-check the lint before you trust it: `lint_pack` the same pack with `paths.json` replaced by `bad_paths.json` (a cycle `fit -> load` under `edges_added`, a path with two `scale` nodes, a path that steps through the test sink). It must be refused with those three problems named. Show the refusal. Then `lint_pack` the real pack against `T/intent.md`: it must pass.
4. `propose W T --target adult-income-graph --files runs/graph-writer/adult_income/proposals/p001 --summary "<one line>"`. Show the user the graph as a node / edge list, the 24 paths as `id: bindings` lines, and the other four files in full, and ask: **approve / edit / reject**. Stop and wait.
5. When the answer arrives, quoting their words verbatim:
   - approve: write their words to `runs/graph-writer/adult_income/proposals/p001.approved`, then `apply W T p001 --approved "<their words>"`.
   - `edit: <a change>` (for example `edit: remove path p24`, or a changed binding): make exactly that change to a copy of the proposal's files under `runs/graph-writer/adult_income/proposals/p001-edited/`, lint the edited pack (an edit that breaks the DAG or a constraint is refused: tell the user and ask again), write `.approved` with their words, `apply ... --edited runs/graph-writer/adult_income/proposals/p001-edited`. Their version lands.
   - reject: write `p001.rejected`; nothing lands.
```

`.claude/skills/graph-writer/bad_paths.json` - what the lint must refuse:

```json
{
 "baseline": "p01",
 "paths": [
  {"id": "p01", "steps": ["load", "scale", "encode", "class_weight", "model", "fit"], "bindings": {"scale": "yes", "encode": "onehot", "class_weight": "none", "model": "logreg"}},
  {"id": "p02", "steps": ["load", "scale", "encode", "scale", "encode", "class_weight", "model", "fit"], "bindings": {"scale": "yes", "encode": "onehot", "class_weight": "none", "model": "rf"}, "note": "two scale nodes: breaks 'one scale per path' and walks an edge the graph lacks"},
  {"id": "p03", "steps": ["load", "scale", "encode", "class_weight", "model", "score_test", "fit"], "bindings": {"scale": "no", "encode": "ordinal", "class_weight": "none", "model": "hgb"}, "note": "score_test before FREEZE: a sink used as a step"}
 ],
 "edges_added": [["fit", "load"]],
 "note": "a proposal built from this file must be refused by lint_pack before any human sees it: a cycle (fit -> load) and two illegal paths"
}
```

`.claude/skills/graph-writer/tools.md` - the graph part of the `lint_pack`
contract, shared by every later writer:

```markdown
`graph.json`, when present, has a cycle, or a path in `paths.json` uses a node that is not in the graph, walks an edge the graph does not have, or breaks a constraint (one `encode`, one `scale`, one `model` per path, `score_test` only as the last node)
```

`test_step.py` - the DAG lint as the test implements it from the contract,
run on the bad file:

```python
def test_bad_paths_are_refused_before_the_human():
    graph = json.loads(filled()["graph.json"])
    bad = json.loads((SKILLS / "graph-writer" / "bad_paths.json").read_text(encoding="utf-8"))
    problems = lint_graph(graph, bad)
    assert "cycle" in problems and any("one scale per path" in p for p in problems) and any("score_test as a step" in p for p in problems)
```

The recorded run (Claude Code 2.1.278, headless, two turns; the proposal
trimmed):

<!-- transcript -->

Files:

```text
step_05_meta_generates_graph/
├── README.md
├── test_step.py
├── .claude/
│   ├── settings.json
│   └── skills/graph-writer/
│       ├── SKILL.md                    fill, lint the bad file (refused), lint the real one, propose, wait, land the edit
│       ├── tools.md                    lint_pack (with the DAG checks), propose, apply
│       ├── bad_paths.json              a cycle and two illegal paths: refused before the human
│       └── template/                   lesson 04's six files with {{placeholders}}; paths.json without the planted p17
├── .agents/skills/graph-writer/        the same
├── .claude/skills/adult-income-graph/  (after the edit) the landed pack, 23 paths, both mirrors
└── runs/graph-writer/                  helpers/, adult_income/{proposals/p001/, p001-edited/, p001.json, p001.approved, traces.jsonl}
```

## Governance considerations

- **Who approves what.** The human sees the graph and the paths before
  anything lands, and what lands is the human's version when they edit.
  The writer cannot land an edit that breaks the DAG: it lints the edited
  pack and asks again.
- **The hook.** No `apply` command runs before `p001.approved` exists.
- **What the helper refuses.** `lint_pack`: a cycle, an unknown node, a
  non-edge, a constraint broken, a step through the test sink, plus
  lesson 03's intent checks; `propose`: a file outside `patches:`; `apply`:
  no words. The self-check on `bad_paths.json` is the writer proving its
  own gate works before it uses it on its own output.
- **What is and is not self-modified.** Nothing. The writer never reads a
  run result; the generated pack never changes the writer.
- **Rung.** L1: the human accepts, and here also amends.

## How to measure it

| Claim | Test |
|---|---|
| the filled template is a legal graph pack (no cycle, 24 legal paths, the intent's budget and test rule) and its `graph.json` is lesson 04's | `test_template_fills_into_a_legal_graph_pack` |
| the planted bad paths are refused by the DAG lint before any human sees them (cycle, two scales, a step through the test sink) | `test_bad_paths_are_refused_before_the_human` |
| the writer lints before it proposes, proposes before it applies, and lands an edit with `--edited` | `test_writer_lints_before_it_proposes_and_lands_the_edit` |
| the pack contract | `test_front_matter` .. `test_no_python_shipped` |
| the recorded run: the refusal shown, nothing landed after turn one; after `edit: remove path p24` 23 paths in both mirrors, the other files equal to the fill, the words in the trace (`RSI_LIVE=1`) | `test_live_claude_code` |

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 06 - the RSI harness](../step_06_rsi_harness/README.md): the first
file a later run reads that an earlier run wrote. Previous:
[lesson 04 - graph engineering](../step_04_graph_harness/README.md).
