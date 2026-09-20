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

```text
[Skill graph-writer]
[Read tools.md]  [Read template/* (six files)]  [Read bad_paths.json]  [Read ../tasks/01_adult_income/intent.md]
agent> Six template files, the intent, the bad paths file and the contracts are read; no helpers exist yet under runs/graph-writer/helpers/, so I'll build them first.
[Write runs/graph-writer/helpers/common.py (197 lines)]   [Write .../lint_pack.py (21 lines)]   [Write .../propose.py (68 lines)]   [Write .../apply.py (77 lines)]
agent> Now fill the template into proposals/p001/ (byte-for-byte, only the placeholders replaced), then the self-check against bad_paths.json and the real lint.
$ python - <<'EOF'
fill = {"task": "adult_income", "task_slug": "adult-income", "task_dir": "01_adult_income", "title": "Adult Census Income (> 50k)", "metric": "roc_auc", "budget_fits": "24"}
... (fill the six files; lint with bad_paths.json in place of paths.json; lint the real pack)
graph.json 1194
loop.json 479
paths.json 5862
schema.json 3412
SKILL.md 2751
--- self-check: bad_paths.json must be refused
{"ok": false, "error": "refused: 6 problem(s)", "problems": [
  "graph.json: cycle through load (edges into it: fit -> load)",
  "p02: encode -> scale is not an edge of the graph",
  "p02: one scale per path (2 found)",
  "p02: one encode per path (2 found)",
  "p03: model -> score_test is not an edge of the graph",
  "p03: score_test as a step (the test sink may only be the last node, after FREEZE)"]}
--- the real pack
{"ok": true, "problems": []}
agent> The self-check refused the bad paths naming the cycle fit -> load, the two-scale path (p02) and the path stepping through score_test (p03); the real pack passes. Now propose.
$ python runs/graph-writer/helpers/propose.py .claude/skills/graph-writer ../tasks/01_adult_income --target adult-income-graph --files runs/graph-writer/adult_income/proposals/p001 --summary "adult-income-graph: the six-file graph pack filled from the template for Adult Census Income (roc_auc, 24 fits, 7-node DAG, 24 paths)"; ls runs/graph-writer/adult_income/proposals; cat runs/graph-writer/adult_income/traces.jsonl
{"id": "p001", "target": "adult-income-graph", "summary": "...", "files": ["SKILL.md", "graph.json", "loop.json", "paths.json", "schema.json", "tools.md"], "lint": "ok", "diff_lines": 876}
p001  p001.json
{"event": "propose", "id": "p001", ...}
agent> ## Proposal p001 - adult-income-graph
Lint self-check - bad_paths.json refused (6 problems): (the six lines above)
Lint of the real pack against T/intent.md: ok: true, problems: [].
propose -> id p001, lint ok, 876 diff lines (all additions: the target pack does not exist yet). Nothing has landed.

### graph.json - nodes / edges
NODES
  load          source
  scale         operator  field=scale         values=[yes, no]
  encode        operator  field=encode        values=[onehot, ordinal]
  class_weight  operator  field=class_weight  values=[none, balanced]
  model         operator  field=model         values=[logreg, rf, hgb]   hyper = the model's middle value
  fit           sink      counts=true
  FREEZE        gate      when: fits_used == N
  score_test    sink      gate=freeze_only, once=true
EDGES
  load -> scale -> encode -> class_weight -> model -> fit -> FREEZE -> score_test
CONSTRAINTS  one scale / one encode / one model per path; no cycles; score_test only as the last node, after FREEZE, once
mutable: false

### paths.json - baseline p01; every path walks load, scale, encode, class_weight, model, fit
p01: scale=yes, encode=onehot,  class_weight=none,     model=logreg
p02: scale=yes, encode=onehot,  class_weight=balanced, model=logreg
... (20 more)
p23: scale=no,  encode=ordinal, class_weight=none,     model=hgb
p24: scale=no,  encode=ordinal, class_weight=balanced, model=hgb

### SKILL.md   ### loop.json   ### schema.json   ### tools.md
... (79 more lines)

approve / edit / reject?
[24 turns, 190 s]

--- turn 2: claude -p --continue "edit: remove path p24"
$ python - <<'EOF'
(copy proposals/p001 to proposals/p001-edited; drop the path with id p24 from paths.json; lint the edited pack)
paths: 24 -> 23 | baseline: p01
other five files: byte-identical to p001
--- lint the edited pack
{"ok": true, "problems": [], "files": ["SKILL.md", "graph.json", "loop.json", "paths.json", "schema.json", "tools.md"]}
agent> The edited pack lints clean (23 paths, DAG untouched). Writing your words to p001.approved, then applying the edited version.
$ printf '%s' 'edit: remove path p24' > runs/graph-writer/adult_income/proposals/p001.approved && python runs/graph-writer/helpers/apply.py ... --approved "edit: remove path p24" --edited runs/graph-writer/adult_income/proposals/p001-edited
PreToolUse:Bash hook error: gate: apply needs proposals/<id>.approved holding the user's exact words - show the proposal and ask first
agent> The hook checks for the .approved file before the command runs, so it must exist in a separate step first.
$ printf '%s' 'edit: remove path p24' > runs/graph-writer/adult_income/proposals/p001.approved && cat runs/graph-writer/adult_income/proposals/p001.approved
edit: remove path p24
$ python runs/graph-writer/helpers/apply.py .claude/skills/graph-writer ../tasks/01_adult_income p001 --approved "edit: remove path p24" --edited runs/graph-writer/adult_income/proposals/p001-edited
{"id": "p001", "version": "gen_001", "approved": "edit: remove path p24", "edited": true, "files": ["SKILL.md", "graph.json", "loop.json", "paths.json", "schema.json", "tools.md"], "landed": [...]}
$ python - <<'EOF'  (compare the two mirrors; count the landed paths; list the trace events)
mirrors identical: True ['SKILL.md', 'graph.json', 'loop.json', 'paths.json', 'schema.json', 'tools.md']
landed paths: 23 last: p23
['propose', 'apply']
['p001', 'p001-edited', 'p001.approved', 'p001.json']
agent> Done - your version landed.
- Proposal: p001 (target adult-income-graph)
- Lint: bad_paths.json refused with the cycle fit -> load, p02's two scale nodes, and p03 stepping through score_test; the filled pack passed; the edited pack (p24 removed) passed too.
- Decision: edit: remove path p24 - written verbatim to runs/graph-writer/adult_income/proposals/p001.approved; the edit made on a copy under proposals/p001-edited/ (only paths.json changed: 24 -> 23 paths, baseline still p01; the other five files byte-identical to the proposal).
- Landed (apply, version gen_001): SKILL.md, tools.md, graph.json, paths.json, loop.json, schema.json into both .claude/skills/adult-income-graph/ and .agents/skills/adult-income-graph/ (mirrors verified identical). Trace: propose, apply with approved: "edit: remove path p24".
[6 turns, 53 s]
```

What to notice: the writer's own lint found six problems in the planted
file - more than the three the test computes, because it also names the
edges the illegal steps break - and zero in its output, before the human saw
anything. The proposal was shown as a node / edge list and 24 `id: bindings`
lines, not as JSON. The edit landed as the human's version: 23 paths, five
files untouched, the words in `p001.approved` and in the trace. And the hook
fired again on the combined write-and-apply command, exactly as in lesson 03.

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
