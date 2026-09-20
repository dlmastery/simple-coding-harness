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

<!-- transcript -->

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
