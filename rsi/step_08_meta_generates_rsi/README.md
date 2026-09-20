# Lesson 08 - A meta skill generates the RSI harness, under human approval

Lesson 05's writer, extended to emit the packs of lessons 06 and 07: the
actor (with `memory.json` born empty, `memory.schema.json`, `config.md`,
`eval.md`) and the verifier. One thing changes in kind. What the human
approves here is not a one-off pack but a *mechanism that will change
itself later* - the verifier will write cards the actor obeys on its next
run - so the proposal shows the verifier contract first, verbatim, under a
heading that says what it is: the acceptance rule you are approving. The
lint refuses a verifier `SKILL.md` without that line, word for word, and
the writer proves it by linting a planted `bad_verifier.md` before it
trusts its own output. The framework paper's autonomy-attribution challenge
is the point of this page: the human approves an improver, not a result,
and the README shows exactly the diff the human saw.

## Getting started

Prerequisites: lesson 07 (the template is that lesson's two packs with the
intent's facts as placeholders) and lesson 03 (the approval cycle). This
lesson adds `.claude/skills/rsi-writer/` with `template/actor/` (seven
files), `template/verifier/` (three files) and `bad_verifier.md`.

## How to execute it

1. Open your agent in this directory and type the prompt:

   ```text
   Use the rsi-writer skill: generate the RSI packs (actor and verifier) for ../tasks/01_adult_income and propose them.
   ```

   The agent fills the ten files, lints the bad verifier (refused: no
   contract line), lints the real proposal (passes), records it, and shows
   you: the contract line under **The contract (the acceptance rule you are
   approving)**, one paragraph on what you are approving, then every file
   of both packs. It asks **approve / edit / reject** and stops.

2. Answer `approve` (as recorded): both packs land in both mirrors. An
   `edit` that removes the contract line is refused and you are asked
   again; `reject` lands nothing.

3. Headless, as recorded, two turns:

   ```bash
   claude -p "Use the rsi-writer skill: generate the RSI packs (actor and verifier) for ../tasks/01_adult_income and propose them." \
     --allowedTools "Bash,Read,Write,Edit,Skill" --setting-sources project --strict-mcp-config
   claude -p --continue "approve" \
     --allowedTools "Bash,Read,Write,Edit,Skill" --setting-sources project --strict-mcp-config
   ```

4. Tests: `python run_tests.py rsi`. Offline: the filled template is
   lesson 07's two packs (`eval.md`, the schema, `config.md`, `tools.md`,
   the verifier `SKILL.md` byte-identical); the contract line is in the
   template and absent from `bad_verifier.md`; the procedure shows the
   contract under its heading before it asks. `RSI_LIVE=1`: turn one shows
   the contract verbatim and lands nothing; after `approve` all ten files
   equal the fill in both mirrors and the trace holds the word.

5. To reset: `rm -rf runs .claude/skills/adult-income .agents/skills/adult-income .claude/skills/adult-income-verifier .agents/skills/adult-income-verifier`.

## What it looks like

`.claude/skills/rsi-writer/SKILL.md` - the step that shows the human what
they are approving:

```markdown
4. `propose W T --target adult-income,adult-income-verifier --files runs/rsi-writer/adult_income/proposals/p001 --summary "<one line>"`. Show the user: first the verifier contract line, verbatim, under a heading **The contract (the acceptance rule you are approving)**; then what they are approving in one paragraph - a mechanism that will change itself later (the verifier writes cards the actor obeys on the next run; the human approves the rule, not the cards); then every file of both packs. Ask **approve / edit / reject**. Stop and wait.
```

and the rule that the lint enforces, quoted in the writer's own text:

```markdown
1. Build `lint_pack`, `propose` and `apply` under `runs/rsi-writer/helpers/` if they are not there yet. `lint_pack` now also refuses a verifier `SKILL.md` that lacks the contract line, word for word: `Contract: the verifier sees only {recipe, val_score, error, profile}; it never sees the actor's transcript, the test split or the intent.`
```

`.claude/skills/rsi-writer/bad_verifier.md` - lesson 06's verifier with the
contract line and the "you never read" sentence removed; everything else
intact, so the only reason to refuse it is the one that matters.

`test_step.py` - the fill is lesson 07:

```python
    lesson_07 = RSI / "step_07_proof" / ".claude" / "skills"
    for name in ("eval.md", "memory.schema.json", "tools.md", "config.md", "schema.json"):
        assert (lesson_07 / "adult-income" / name).read_text(encoding="utf-8") == f[f"actor/{name}"], name
    assert (lesson_07 / "adult-income-verifier" / "SKILL.md").read_text(encoding="utf-8") == f["verifier/SKILL.md"]
```

The recorded run (Claude Code 2.1.278, headless, two turns; the proposal
trimmed to the contract and its heading):

```text
[Skill rsi-writer]
agent> Following the boot order: tools.md, the templates, bad_verifier.md, then the intent.
[Read tools.md]  [Glob .claude/skills/**/*]  [Read bad_verifier.md]  [Read ../tasks/01_adult_income/intent.md]
agent> Now the ten template files.
[Read template/actor/{SKILL.md, tools.md, schema.json, memory.json, memory.schema.json, config.md, eval.md}]  [Read template/verifier/{SKILL.md, tools.md, memory.schema.json}]
[Grep {{placeholders}} in the template]  -> schema.json: {{task}}, {{metric}}, {{budget_fits}}; tools.md: {{budget_fits}}; SKILL.md: {{task_dir}}
$ ls -la && ls -R runs 2>/dev/null | head -50; ls .claude/skills .agents/skills; ls ../tasks/01_adult_income; cat .claude/settings.json; python --version
.agents/skills:  rsi-writer
.claude/skills:  rsi-writer
agent> No runs/ yet, so I build the three helpers. Let me check the README and the lesson's test for the exact shapes they expect.
[Read README.md]  [Read test_step.py]
agent> I have everything I need. No runs/ exists yet, so I'll build the three helpers (plus a small shared module and a deterministic fill step) under runs/rsi-writer/helpers/.
[Write runs/rsi-writer/helpers/common.py (72 lines)]  [Write .../lint_pack.py (171 lines)]  [Write .../fill.py (41 lines)]  [Write .../propose.py (94 lines)]  [Write .../apply.py (81 lines)]
agent> Step 2: fill the ten files into p001/, then check the fill against lesson 07's packs (the template's source) byte for byte.
$ python runs/rsi-writer/helpers/fill.py .claude/skills/rsi-writer ../tasks/01_adult_income runs/rsi-writer/adult_income/proposals/p001 && ...
Traceback ... Path(path).read_text(encoding="utf-8", newline="")
agent> Path.read_text(newline=...) is 3.13-only; use open() instead.
[Edit runs/rsi-writer/helpers/common.py]
$ python runs/rsi-writer/helpers/fill.py .claude/skills/rsi-writer ../tasks/01_adult_income runs/rsi-writer/adult_income/proposals/p001 && grep -rc '{{' runs/rsi-writer/adult_income/proposals/p001 | grep -v ':0$'; echo "--- diff vs lesson 07 (empty = identical) ---"; diff -r ../step_07_proof/.claude/skills/adult-income runs/rsi-writer/adult_income/proposals/p001/adult-income; diff -r ../step_07_proof/.claude/skills/adult-income-verifier runs/rsi-writer/adult_income/proposals/p001/adult-income-verifier; echo "exit $?"
{"values": {"task": "adult_income", "task_dir": "01_adult_income", "metric": "roc_auc", "budget_fits": "24"}, "targets": {"actor": "adult-income", "verifier": "adult-income-verifier"}, "files": [... 10 files ...]}
--- diff vs lesson 07 (empty = identical) ---
exit 0
$ (copy p001 to selfcheck/ with bad_verifier.md as the verifier's SKILL.md)
$ python runs/rsi-writer/helpers/lint_pack.py runs/rsi-writer/adult_income/selfcheck ../tasks/01_adult_income/intent.md
{"ok": false, "packs": ["adult-income", "adult-income-verifier"], "problems": ["adult-income-verifier/SKILL.md: a verifier SKILL.md lacks its contract line, word for word: `Contract: the verifier sees only {recipe, val_score, error, profile}; it never sees the actor's transcript, the test split or the intent.`"], "error": "refused: 1 problem(s); ..."}
$ python runs/rsi-writer/helpers/lint_pack.py runs/rsi-writer/adult_income/proposals/p001 ../tasks/01_adult_income/intent.md
{"ok": true, "packs": ["adult-income", "adult-income-verifier"], "problems": []}
agent> The lint refuses the planted bad verifier for exactly one reason - the missing contract line - and passes the real proposal. Step 4: record the proposal.
$ python runs/rsi-writer/helpers/propose.py .claude/skills/rsi-writer ../tasks/01_adult_income --target adult-income,adult-income-verifier --files runs/rsi-writer/adult_income/proposals/p001 --summary "Birth of the RSI harness for adult_income: actor pack adult-income (memory.json born empty) and verifier pack adult-income-verifier, filled from the template with task=adult_income, metric=roc_auc, budget_fits=24"
{"id": "p001", "visit": 1, "target": ["adult-income", "adult-income-verifier"], "born": ["adult-income", "adult-income-verifier"], "n_files": 10, ...}
$ cat runs/rsi-writer/adult_income/traces.jsonl && ls .claude/skills .agents/skills && ls runs/rsi-writer/adult_income/proposals
{"event": "propose", "id": "p001"}
rsi-writer
rsi-writer
p001  p001.json
agent> Proposal p001 is recorded (runs/rsi-writer/adult_income/proposals/p001.json, trace event propose). Nothing has landed: both mirrors still hold only rsi-writer.

## The contract (the acceptance rule you are approving)
Contract: the verifier sees only {recipe, val_score, error, profile}; it never sees the actor's transcript, the test split or the intent.

## What you are approving
Not a one-off pack but a mechanism that will change itself later. The actor pack adult-income searches 24 fits per arm and obeys whatever cards sit in its memory.json (born empty here). The verifier pack adult-income-verifier reads only the actor's fit rows {recipe, val_score, error} plus the five-number table profile, tallies pairs one field apart, and writes prefer / counter / forbid cards into the actor's memory.json - cards the actor will obey on its next run without asking you. So the human approves the rule above (what the verifier may see and therefore on what evidence the actor's memory may change), not the individual cards. The lint enforces the rule mechanically: it refused the planted bad_verifier.md (missing contract line) and passed p001; an edit that removes the line will be refused too.
Lint results: bad verifier -> refused (lacks its contract line); p001 -> ok: true, problems: []. Fill: task=adult_income, task_dir=01_adult_income, metric=roc_auc, budget_fits=24; no placeholder left; the compared files are byte-identical to lesson 07's.

## Every file of both packs (p001)
### adult-income/SKILL.md
... (the whole file)
### adult-income/tools.md ... schema.json ... memory.json ([]) ... memory.schema.json ... config.md ... eval.md
### adult-income-verifier/SKILL.md (with the contract line) ... tools.md ... memory.schema.json
... (239 more lines)

approve / edit / reject?
[37 turns, 368 s]

--- turn 2: claude -p --continue "approve"
agent> Recording your word, then landing p001.
[Write runs/rsi-writer/adult_income/proposals/p001.approved (1 lines)]
$ python runs/rsi-writer/helpers/apply.py .claude/skills/rsi-writer ../tasks/01_adult_income p001 --approved "approve"
{"id": "p001", "version": "adult-income:gen_001, adult-income-verifier:gen_001", "approved": "approve", "edited": false, "files": ["adult-income/config.md", "adult-income/eval.md", "adult-income/memory.json", "adult-income/memory.schema.json", "adult-income/schema.json", "adult-income/SKILL.md", "adult-income/tools.md", "adult-income-verifier/memory.schema.json", "adult-income-verifier/SKILL.md", "adult-income-verifier/tools.md"], "mirrors": [".../.claude/skills", ".../.agents/skills"]}
$ diff -r .claude/skills .agents/skills && echo "mirrors identical" && diff -r runs/rsi-writer/adult_income/proposals/p001/adult-income .claude/skills/adult-income && diff -r runs/rsi-writer/adult_income/proposals/p001/adult-income-verifier .claude/skills/adult-income-verifier && echo "landed == proposal" && cat runs/rsi-writer/adult_income/traces.jsonl
mirrors identical
landed == proposal
{"event": "propose", "id": "p001"}
{"event": "apply", "id": "p001", "approved": "approve", "version": "adult-income:gen_001, adult-income-verifier:gen_001", "files": [...]}
agent> Proposal: p001 (visit 1) - the birth of the RSI harness for adult_income.
Lint: the planted bad_verifier.md was refused for exactly one reason (a verifier SKILL.md lacks its contract line, word for word: ...); the real proposal passed (problems: []), and passed again inside propose.
Decision: approve - written verbatim to runs/rsi-writer/adult_income/proposals/p001.approved and into the trace's apply event. Trace events: propose, apply.
Landed (version adult-income:gen_001, adult-income-verifier:gen_001; both mirrors verified identical and byte-equal to the proposal):
- adult-income/ - SKILL.md, tools.md, schema.json, memory.json ([]), memory.schema.json, config.md, eval.md
- adult-income-verifier/ - SKILL.md (with the contract line), tools.md, memory.schema.json
The writer itself is unchanged; the two new packs are now visible as skills. Done.
[4 turns, 42 s]
```

What to notice: the writer diffed its own fill against lesson 07's packs
before linting (empty diff), then proved the lint on the planted bad
verifier - refused for exactly one reason, the missing contract line - and
showed the human that line first, under the heading the skill prescribes,
with one paragraph on what approving it means. The agent learned this time
to write `.approved` in a separate step before `apply`, so the hook did not
fire. Ten files landed, both mirrors, byte-equal to the proposal.

Files:

```text
step_08_meta_generates_rsi/
├── README.md
├── test_step.py
├── .claude/
│   ├── settings.json
│   └── skills/rsi-writer/
│       ├── SKILL.md                    fill, lint the bad verifier (refused), lint, propose with the contract first, wait, apply
│       ├── tools.md                    lint_pack (with the contract check), propose, apply
│       ├── bad_verifier.md             a verifier SKILL.md without the contract line: refused
│       └── template/
│           ├── actor/                  SKILL.md, tools.md, schema.json, memory.json ([]), memory.schema.json, config.md, eval.md
│           └── verifier/               SKILL.md, tools.md, memory.schema.json
├── .agents/skills/rsi-writer/          the same
├── .claude/skills/adult-income/, adult-income-verifier/   (after `approve`) the landed packs, both mirrors
└── runs/rsi-writer/                    helpers/, adult_income/{proposals/p001/, p001.json, p001.approved, traces.jsonl}
```

## Governance considerations

- **Who approves what.** The human approves the verifier contract - the
  acceptance rule under which the actor's memory will later change without
  asking - and the packs that implement it. The trace records the words.
- **The hook.** No `apply` command before `p001.approved`.
- **What the helper refuses.** A verifier without its contract line (before
  the human sees it, and again on an `edit` that removes it); everything
  lesson 05's lint refused; a second proposal in the visit.
- **What is and is not self-modified.** The writer writes two packs that
  will later modify one of them (`memory.json`); the writer itself never
  changes and never sees a run.
- **Rung.** L1 for the generation; what it generates runs at L4. The
  attribution is explicit: the human chose the rule, the system will make
  the revisions.

## How to measure it

| Claim | Test |
|---|---|
| the filled template is lesson 07's actor and verifier, `memory.json` born empty | `test_template_is_lesson_07s_two_packs` |
| the contract line is in the template, absent from the bad verifier, quoted in the writer and required by the lint contract | `test_the_contract_line_is_mandatory` |
| the writer shows the contract under its heading and says what is being approved, before it asks; lint before propose before apply; `patches:` names both packs | `test_the_human_approves_the_contract_first` |
| the pack contract | `test_front_matter` .. `test_no_python_shipped` |
| the recorded run: the contract shown verbatim, nothing landed; after `approve` ten files equal to the fill in both mirrors, the trace `propose` then `apply` with the word (`RSI_LIVE=1`) | `test_live_claude_code` |

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 09 - the RSI meta harness](../step_09_rsi_meta_harness/README.md):
a pack that patches the pack, problem by problem, under the human and then
under a private gate. Previous: [lesson 07 - the proof](../step_07_proof/README.md).
