---
name: rsi-writer
description: "A meta skill whose output is an RSI harness: from a problem's intent.md write the actor pack (SKILL.md, tools.md, schema.json, memory.json, memory.schema.json, config.md, eval.md) and the verifier pack (SKILL.md, tools.md, memory.schema.json) by filling the template, lint them - the verifier contract line is mandatory - propose them with the contract shown verbatim, and land them only with the user's words. Use in rsi/step_08_meta_generates_rsi; never fits a model."
metadata:
  type: workflow
  version: "3.0"
  rsi: "off"
  patches: ["adult-income/*", "adult-income-verifier/*"]
---
# RSI writer: a meta skill whose output is a mechanism that will change itself

You do not fit models. Run every helper through the Bash tool from this lesson's directory.
This pack's directory is `.claude/skills/rsi-writer` (`W`); the problem is
`../tasks/01_adult_income` (`T`); the packs you write are `adult-income` (the actor) and
`adult-income-verifier`, landing - only after the user's answer - under `.claude/skills/` and
`.agents/skills/`.

## Boot order
1. This file. 2. `tools.md`. 3. `template/actor/` and `template/verifier/`: the ten files with `{{placeholders}}`. 4. `bad_verifier.md`: a verifier SKILL.md without its contract line, which the lint must refuse. 5. `T/intent.md`.

## Procedure
1. Build `lint_pack`, `propose` and `apply` under `runs/rsi-writer/helpers/` if they are not there yet. `lint_pack` now also refuses a verifier `SKILL.md` that lacks the contract line, word for word: `Contract: the verifier sees only {recipe, val_score, error, profile}; it never sees the actor's transcript, the test split or the intent.`
2. Read `T/intent.md` (`{{task}}`, `{{task_dir}}`, `{{metric}}`, `{{budget_fits}}`) and write the ten files from `template/` with every placeholder replaced and nothing else changed, under `runs/rsi-writer/adult_income/proposals/p001/` (`adult-income/...` and `adult-income-verifier/...`). `memory.json` is `[]`: the pack is born empty.
3. Self-check the lint: `lint_pack` the same proposal with the verifier's `SKILL.md` replaced by `bad_verifier.md`. It must be refused, naming the missing contract. Show the refusal. Then `lint_pack` the real proposal against `T/intent.md`: it must pass.
4. `propose W T --target adult-income,adult-income-verifier --files runs/rsi-writer/adult_income/proposals/p001 --summary "<one line>"`. Show the user: first the verifier contract line, verbatim, under a heading **The contract (the acceptance rule you are approving)**; then what they are approving in one paragraph - a mechanism that will change itself later (the verifier writes cards the actor obeys on the next run; the human approves the rule, not the cards); then every file of both packs. Ask **approve / edit / reject**. Stop and wait.
5. When the answer arrives, quoting their words verbatim: approve - write them to `runs/rsi-writer/adult_income/proposals/p001.approved` and `apply W T p001 --approved "<their words>"` (both packs land, both mirrors); `edit: <a change>` - make exactly that change to a copy under `p001-edited/`, lint it (an edit that removes the contract line is refused: tell the user and ask again), then `apply ... --edited`; reject - write `p001.rejected`; nothing lands.
6. Answer in text with the proposal id, the lint results, the decision and the files that landed. Stop.

## Rules
- You never fit, never open an arm, never score anything.
- The contract line is not yours to relax: a proposal without it is refused before the human sees it, and an edit that removes it is refused after.
- Twice from the same intent gives the same bytes; running the generated packs never changes the writer.

## Off switch
None: a one-shot writer.

## Done when
`apply` answered (landed, edited, or rejected).
