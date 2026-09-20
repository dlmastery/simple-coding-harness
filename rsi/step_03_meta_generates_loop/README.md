# Lesson 03 - A meta skill generates the loop harness, under human approval

A meta harness is a harness whose output is a harness. This one, the
`loop-writer` pack, never fits a model: given the intent of a problem it
writes the five files of lesson 02's pack by filling a template, lints them
against the intent by the checklist of lesson 00, writes them down as a
proposal, shows the whole pack to the human and asks *approve / edit /
reject*. Nothing lands until the human answers, and the lesson's hook
enforces the last step mechanically: no Bash command containing `apply` runs
before a `proposals/<id>.approved` file exists - the file the agent writes
with the human's exact words. This is the framework paper's L1: the human
specified what, how and success (the intent), the system executes a
generation procedure, the human accepts. Most "agent builds agent" demos stop
here. It is not RSI yet: generating twice gives the same bytes (the template
is the mechanism, nothing is random, nothing is read from a run), and
running the generated pack never changes it.

## Getting started

Prerequisites: lesson 02 (the pack the writer produces is lesson 02's, and
the offline test checks the filled template against it). This lesson adds
the writer pack under `.claude/skills/loop-writer/` with its `template/`
(five files with `{{placeholders}}`), and three contracts - `lint_pack`,
`propose`, `apply` - that the agent implements as helpers under
`runs/loop-writer/helpers/`. After an approved run, the generated pack sits
at `.claude/skills/adult-income-loop/` and `.agents/skills/adult-income-loop/`.

## How to execute it

1. Open your agent in this directory and type the prompt:

   ```text
   Use the loop-writer skill: generate the loop pack for ../tasks/01_adult_income and propose it.
   ```

   The agent reads the intent, fills the template, lints the five files,
   records the proposal under `runs/loop-writer/adult_income/proposals/`
   (`p001/` the files, `p001.json` the record) and shows you the whole pack.
   Then it asks **approve / edit / reject** and stops.

2. Answer in the chat. `approve` (any wording that approves) lands the pack:
   the agent writes your words to `p001.approved`, then runs `apply`, which
   snapshots nothing (there is no previous pack), writes the five files into
   both mirrors and records `{"event": "apply", "approved": "<your words>"}`
   in the trace. `edit: <a change>` lands your version: the agent makes
   exactly that change, lints again, and applies with `--edited`. `reject`
   writes `p001.rejected`; nothing lands.

3. Headless, as recorded, in two turns:

   ```bash
   claude -p "Use the loop-writer skill: generate the loop pack for ../tasks/01_adult_income and propose it." \
     --allowedTools "Bash,Read,Write,Edit,Skill" --setting-sources project --strict-mcp-config
   claude -p --continue "approve" \
     --allowedTools "Bash,Read,Write,Edit,Skill" --setting-sources project --strict-mcp-config
   ```

4. Tests: `python run_tests.py rsi`. Offline: the template has the five
   files and every placeholder the fill covers; the filled template lints
   against the intent and *is* lesson 02's pack (same `loop.json` bytes,
   same 24 recipes); the writer's procedure proposes before it applies and
   waits for the user. `RSI_LIVE=1`: after turn one the proposal exists and
   the pack has not landed; after `approve` the five files are byte-identical
   to the filled template in both mirrors and the trace holds the word.

5. To reset: `rm -rf runs .claude/skills/adult-income-loop .agents/skills/adult-income-loop`.

## What it looks like

`.claude/skills/loop-writer/SKILL.md` - the front matter carries a
`patches:` glob, the files this pack may write, and the procedure stops in
the middle:

```markdown
---
name: loop-writer
description: "A meta skill whose output is a loop harness: from a problem's intent.md write the five files of a loop pack (SKILL.md, tools.md, loop.json, recipes.json, schema.json) by filling the template, lint them against the intent, propose them, and land them only with the user's words. Use in rsi/step_03_meta_generates_loop; never fits a model."
metadata:
  type: workflow
  version: "3.0"
  rsi: "off"
  patches: ["adult-income-loop/*"]
---
# Loop writer: a meta skill whose output is a loop harness

## Procedure
1. Build `lint_pack`, `propose` and `apply` under `runs/loop-writer/helpers/` if they are not there yet.
2. Read `T/intent.md`: `name` (`{{task}}`), `title`, the task directory (`{{task_dir}}`), `metric`, `budget_fits`, `models`. `{{task_slug}}` is the name with `_` as `-`.
3. Write the pack from `template/`: the five files with every `{{placeholder}}` replaced and nothing else changed. ...
4. `lint_pack` the five files against `T/intent.md` by the checklist in `tools.md`: ... If a rule fails, the pack is refused: fix your substitution and lint again. Nothing is proposed that does not lint.
5. `propose W T --target adult-income-loop --files runs/loop-writer/adult_income/proposals/p001 --summary "<one line>"`: the helper records `p001.json` with the five files. Then show the user the whole proposed pack - every file, in full - and ask: **approve / edit / reject**. Stop and wait. Run nothing else until the answer arrives.
6. When the answer arrives, quoting their words verbatim:
   - approve (any wording that approves): write their exact words to `runs/loop-writer/adult_income/proposals/p001.approved`, then `apply W T p001 --approved "<their words>"`. The pack lands in both mirrors.
   - `edit: <a change>`: make exactly that change to the proposal's files (nothing else), lint again, write `.approved` with their words, `apply ... --edited runs/loop-writer/adult_income/proposals/p001-edited`. Their version lands.
   - reject: write `p001.rejected` with their words. Nothing lands.
```

`.claude/skills/loop-writer/tools.md` - the two contracts of the approval
cycle. `propose` writes; `apply` refuses without the words:

```markdown
- `propose(pack, task, target, files, summary, visit=1)` - refuse when this visit already has a proposal (one per visit: `proposals/p<visit>*.json` exists); refuse a file outside the pack's `patches:` globs (this pack's front matter); refuse a patch that changes more than 20 % of the target pack's lines or removes the test-rule line from its `SKILL.md`; `lint_pack` the result against the intent. Write `runs/<pack name>/<task name>/proposals/<id>.json` (`{"id", "visit", "target", "files": {path: text}, "summary", "diff"}`, ids `p001`, `p002`, ...), append `{"event": "propose", "id"}` and print the id and the unified diff. Nothing lands.
- `apply(pack, task, id, approved, edited=None)` - refuse without `approved` (non-empty: the user's exact words, which you write to `proposals/<id>.approved` first - the lesson's hook lets no `apply` command run before that file exists); refuse when `proposals/<id>.rejected` exists. Snapshot every file of the target pack under `runs/<target name>/versions/gen_NNN/` (the next number), write the proposal's files (or the `edited` ones, the user's version) into both mirrors, append `{"event": "apply", "id", "approved", "version", "files"}` and print the version label. A `reject` answer: write `proposals/<id>.rejected` holding the words; nothing lands and nothing is snapshotted.
```

`.claude/skills/loop-writer/template/schema.json` - the intent's facts as
placeholders; the rest is lesson 02's file:

```json
{
 "task": "{{task}}",
 "target": "target",
 "metric": "{{metric}}",
 "n_fits": {{budget_fits}},
 "test_rule": "locked, scored once after FREEZE",
```

`test_step.py` - the offline claim that the writer's output is lesson 02's
pack:

```python
    lesson_02 = RSI / "step_02_loop_harness" / ".claude" / "skills" / "adult-income-loop"
    assert json.loads((lesson_02 / "recipes.json").read_text(encoding="utf-8")) == recipes
    assert (lesson_02 / "loop.json").read_text(encoding="utf-8") == f["loop.json"]
```

The recorded run (Claude Code 2.1.278, headless, two turns; the proposal
the agent showed is trimmed to its head):

```text
[Skill loop-writer]
[Read .claude/skills/loop-writer/tools.md]  [Glob .claude/skills/**/*]  [Read ../tasks/01_adult_income/intent.md]
[Read template/SKILL.md]  [Read template/tools.md]  [Read template/loop.json]  [Read template/schema.json]  [Read template/recipes.json]
[Read .claude/skills/loop-writer/SKILL.md]  [Read test_step.py]
$ ls -la && ls -R runs 2>/dev/null | head -50; ls .agents/skills .claude/skills; cat .claude/settings.json 2>/dev/null
.agents/skills:
loop-writer
.claude/skills:
loop-writer
$ python -c "import yaml, sys; print(sys.version)" && file .claude/skills/loop-writer/template/* && ls ../step_02_loop_harness/runs 2>/dev/null | head
3.12.3 | packaged by conda-forge | (main, Apr 15 2024, 18:20:11) [MSC v.1938 64 bit (AMD64)]
.claude/skills/loop-writer/template/SKILL.md:     ASCII text, with very long lines (526)
...
agent> Templates are LF/ASCII, PyYAML is available. Building the three helpers (step 1).
[Write runs/loop-writer/helpers/common.py (69 lines)]   [Write runs/loop-writer/helpers/lint_pack.py (153 lines)]
[Write runs/loop-writer/helpers/propose.py (91 lines)]  [Write runs/loop-writer/helpers/apply.py (81 lines)]
[Write runs/loop-writer/adult_income/proposals/p001/SKILL.md (34 lines)]   [Write .../p001/loop.json (25 lines)]
[Write .../p001/schema.json (225 lines)]   [Write .../p001/recipes.json (170 lines)]   [Write .../p001/tools.md (70 lines)]
agent> Step 4: lint the five files against the intent, and confirm they are exactly the filled template (nothing else changed).
$ python runs/loop-writer/helpers/lint_pack.py runs/loop-writer/adult_income/proposals/p001 ../tasks/01_adult_income && python - <<'EOF'
from pathlib import Path
T = Path(".claude/skills/loop-writer/template"); P = Path("runs/loop-writer/adult_income/proposals/p001")
fill = {"task":"adult_income","task_slug":"adult-income","task_dir":"01_adult_income","title":"Adult Census Income (> 50k)","metric":"roc_auc","budget_fits":"24"}
... (compare each filled template file to the proposal, byte for byte)
{"files": ["SKILL.md", "loop.json", "recipes.json", "schema.json", "tools.md"], "problems": [], "ok": true}
loop.json identical | no CRLF
recipes.json identical | no CRLF
schema.json identical | no CRLF
SKILL.md identical | no CRLF
tools.md identical | no CRLF
agent> Lint is clean and all five files are byte-identical to the filled template. Step 5: record the proposal.
$ python runs/loop-writer/helpers/propose.py .claude/skills/loop-writer ../tasks/01_adult_income --target adult-income-loop --files runs/loop-writer/adult_income/proposals/p001 --summary "adult-income-loop: the five files of the loop pack filled from the template for 01_adult_income (roc_auc, 24 fits, 24 static recipes, test locked until FREEZE)"; ls runs/loop-writer/adult_income/proposals; cat runs/loop-writer/adult_income/traces.jsonl; ls .claude/skills .agents/skills
{"id": "p001", "target": "adult-income-loop", "files": ["adult-income-loop/SKILL.md", "adult-income-loop/loop.json", "adult-income-loop/recipes.json", "adult-income-loop/schema.json", "adult-income-loop/tools.md"], "summary": "...", "lines_changed": 524, "recorded": "runs/loop-writer/adult_income/proposals/p001.json", "diff": "<539 diff lines: every file is new>"}
p001
p001.json
{"event": "propose", "id": "p001", "target": "adult-income-loop", "files": [...], "summary": "..."}
loop-writer
loop-writer
agent> # Proposal p001 - the adult-income-loop pack

Recorded at runs/loop-writer/adult_income/proposals/p001.json. Nothing has landed: .claude/skills/ and .agents/skills/ still hold only loop-writer.
- Source: ../tasks/01_adult_income/intent.md -> task=adult_income, task_slug=adult-income, task_dir=01_adult_income, title=Adult Census Income (> 50k), metric=roc_auc, budget_fits=24.
- Lint: 0 problems (n_fits = N = 24 recipes = budget_fits; test rule locked, scored once after FREEZE; metric and models match the intent; front matter, four headings, ## Allowed / ## Forbidden present).
- Byte check: each file is identical to the template with only the six placeholders replaced (LF line endings); recipes.json is the template's 24 static recipes, untouched.
- Would land at: .claude/skills/adult-income-loop/ and, byte-identical, .agents/skills/adult-income-loop/.

Below is the whole pack, every file in full.
## 1. adult-income-loop/SKILL.md
---
name: adult-income-loop
description: "Train a classifier for the Adult Census Income (> 50k) problem by running the counted loop declared in loop.json over recipes.json - 24 fits, a freeze, one test score - with helpers you build from the contracts in tools.md. Use in the lesson that landed it, when the pack has loop.json and no graph or memory file."
...
## 2. adult-income-loop/loop.json
{"kind": "counted_while", "N": 24, "counter": "t", "error_still_counts": true, ...}
## 3. adult-income-loop/recipes.json  (24 recipes)   ## 4. adult-income-loop/schema.json   ## 5. adult-income-loop/tools.md
... (511 more lines)

approve / edit / reject?
[26 turns, 286 s]

--- turn 2: claude -p --continue "approve"
$ printf '%s' "approve" > runs/loop-writer/adult_income/proposals/p001.approved && python runs/loop-writer/helpers/apply.py .claude/skills/loop-writer ../tasks/01_adult_income p001 --approved "approve"
PreToolUse:Bash hook error: gate: apply needs proposals/<id>.approved holding the user's exact words - show the proposal and ask first
agent> The hook checks for the .approved file before the command runs, so the file must exist first - writing it in a separate step.
[Write runs/loop-writer/adult_income/proposals/p001.approved (1 lines)]
$ python runs/loop-writer/helpers/apply.py .claude/skills/loop-writer ../tasks/01_adult_income p001 --approved "approve" && diff -r .claude/skills/adult-income-loop .agents/skills/adult-income-loop && echo "mirrors identical" && diff -r runs/loop-writer/adult_income/proposals/p001 .claude/skills/adult-income-loop && echo "landed == proposal" && cat runs/loop-writer/adult_income/traces.jsonl
{"id": "p001", "version": "gen_001", "label": "proposed", "approved": "approve", "files": [".claude/skills/adult-income-loop/loop.json", ".claude/skills/adult-income-loop/recipes.json", ".claude/skills/adult-income-loop/schema.json", ".claude/skills/adult-income-loop/SKILL.md", ".claude/skills/adult-income-loop/tools.md", ".agents/skills/adult-income-loop/loop.json", ...]}
mirrors identical
landed == proposal
{"event": "propose", "id": "p001", ...}
{"event": "apply", "id": "p001", "approved": "approve", "version": "gen_001", "files": [...]}
agent> Proposal p001 - approved - landed as version gen_001 (the proposed version, unedited).
Your words `approve` are in runs/loop-writer/adult_income/proposals/p001.approved; the trace at
runs/loop-writer/adult_income/traces.jsonl holds the two events, propose then apply (with "approved": "approve").
The pre-landing snapshot is runs/adult-income-loop/versions/gen_001/ (empty: the pack did not exist before).
Files landed, byte-identical in both mirrors and identical to the proposal:
- .claude/skills/adult-income-loop/SKILL.md, tools.md, loop.json, recipes.json, schema.json
- .agents/skills/adult-income-loop/SKILL.md, tools.md, loop.json, recipes.json, schema.json
Done.
[4 turns, 33 s]
```

What to notice: the writer read the intent, filled the template and
checked its own output against the fill byte for byte before it linted -
and the lint is the agent's own `lint_pack`, built from the checklist of
lesson 00. It stopped at the question, and the artifacts prove it: after
turn one `.claude/skills/` holds only `loop-writer`. In turn two the agent
first tried to write the approval file and run `apply` in one command, and
the lesson's hook blocked it: the `.approved` file did not exist yet when
the hook checked. It wrote the file, then applied. That is the advisory
skill and the deterministic gate in one exchange.

Files:

```text
step_03_meta_generates_loop/
├── README.md
├── test_step.py
├── .claude/
│   ├── settings.json                  the hook: no `apply` command without a proposals/*.approved file
│   └── skills/loop-writer/
│       ├── SKILL.md                   read the intent, fill, lint, propose, wait, apply with the words
│       ├── tools.md                   lint_pack, propose, apply; never fit_recipe
│       └── template/                  lesson 02's five files with {{placeholders}}
│           ├── SKILL.md  loop.json  recipes.json  schema.json  tools.md
├── .agents/skills/loop-writer/        the same
├── .claude/skills/adult-income-loop/  (after `approve`) the generated pack, both mirrors
└── runs/loop-writer/                  helpers/, adult_income/{proposals/p001/, p001.json, p001.approved, traces.jsonl}
```

## Governance considerations

- **Who approves what.** The human approves the whole pack (every file, in
  full, shown before the question). `n` means nothing lands; `edit` means
  the human's text lands, not the writer's. The trace records the words.
- **The hook.** The second gate of the series appears here: a Bash command
  containing `apply` is blocked until a `proposals/*.approved` file exists
  under `runs/`. The agent writes that file only after the user answers,
  with their exact words. Agents without hooks get the same refusal from the
  contract (`apply` refuses without `approved`).
- **What the helper refuses.** `lint_pack`: a pack that widens the intent
  (`n_fits`, the test rule, `metric`, `models`), a `loop.json` whose `N` is
  not the budget, a `SKILL.md` without the front matter or the four
  headings. `propose`: a file outside `patches:`, a second proposal in the
  same visit. `apply`: no words, a rejected proposal.
- **What is and is not self-modified.** Nothing self-modifies. The writer
  writes a *different* pack; the writer's own files never change; the
  written pack has no feedback path to the writer. Twice from the same
  intent gives the same bytes: the offline test compares the fill to
  lesson 02, the live test compares the landed files to the fill.
- **Rung.** L1: humans specify what / how / success; the system executes;
  the human accepts.

## How to measure it

| Claim | Test |
|---|---|
| the template holds the five files and every placeholder the fill covers | `test_template_has_the_five_files_and_placeholders` |
| the filled template lints against the intent and is lesson 02's pack (same `loop.json` bytes, same 24 recipes) | `test_filled_template_lints_against_the_intent` |
| the writer proposes before it applies, asks approve / edit / reject, waits, and may write only `adult-income-loop/*` | `test_writer_waits_for_the_user` |
| the pack contract; `fit_recipe`, `load_splits`, `score_test` forbidden and absent from the procedure | `test_forbidden_tools_absent_from_procedure` and the rest |
| the recorded run: after turn one a proposal and no landed pack; after `approve` the five files byte-identical to the fill in both mirrors, the trace `propose` then `apply` with the word (`RSI_LIVE=1`) | `test_live_claude_code` |

Scorecard fields: none produced here (nothing is fitted); the generated pack
reports lesson 02's.

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 04 - graph engineering with loops](../step_04_graph_harness/README.md):
the job as a DAG, a recipe as a path, the loop walking paths. Previous:
[lesson 02 - loop engineering](../step_02_loop_harness/README.md).
