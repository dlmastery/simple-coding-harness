# Efficient harnesses and their builders

Preflight: 20 September 2026. The local lab sources are [10.30 and 10.31 in lessons-frontier.mjs](../scripts/lessons-frontier.mjs). Read the primary methods before saving both exact prompts. The images explain classroom activities rather than reproduce the papers.

## Primary checks

- [SoL-Pi, sections 2.1–2.2](https://arxiv.org/html/2609.20519v1): capability tolerances and efficiency criteria precede search. Development feedback and evaluation after freezing are separate. The classroom exercise removes redundant reporting under a fixed quality requirement and includes search overhead. It does not implement the paper’s four mechanisms or establish recursive cost compounding.
- [HarnessDev, sections 3.1–3.4 and 4.3](https://arxiv.org/html/2609.01437v1): distinguish creator, generated harness, executor, and evaluator. Development feedback is not held-out evidence. The figure names the harness as the changed artifact and retains the freeze boundary; no benchmark score is copied.
- [Harness-of-Harness, section 3](https://arxiv.org/html/2609.01481v1): model, base harness, role definitions, and runtime policy remain fixed within a run. Software, development documentation, and execution evidence evolve. The planner, developer, and tester are separate invocations. Do not infer harness self-modification from the title.

## Classroom constraints

10.30 compares two harness variants, with at most two fits each. Keep the necessary checker in the main candidate, count proposal and checking costs, and use a separate fit-stub counterexample with a removed checker. Unknown cost stays unknown. A quality-gate pass only permits the efficiency comparison; it does not decide the winner.

10.31 makes one harness edit and two checks or fits. Builder B0 stays unchanged. Compare parent and child under matched conditions. The two-fresh-brief builder comparison is a proposed follow-up, not another completed experiment or an automatic extension to the lab budget.

Both prompts use the main overview as the actual style reference, with exact labels and object identities fixed before generation. Maximum three outputs per figure; no cosmetic alternatives. Reviews and publication results will follow below.

## Full-size review

Selected quality-cost-v1 on its first attempt. The main candidate retains its necessary checker. Both variants receive matching cases, quality precedes the efficiency decision, and the missing-checker counterexample is rejected. Blank ledger cells are not measured results. The failure tray represents archived attempts, not discarded evidence; its costs remain included. Decorative book and mug text did not justify a cosmetic regeneration.

Retained builder-and-artifact-v1 as an unselected draft. It misdirected fresh-brief arrows away from builders, allowed an evaluation connector to bypass freezing, and lacked an explicit parent input to matched checks. One combined edit produced selected builder-and-artifact-v2: briefs feed both builders, freezing precedes held-out evaluation, and H0 and H1 both feed the comparison. Inspected the entire revised figure. Source roles remain distinct and no winner is asserted. The first draft and both exact prompts remain in the archive.

Two selected figures used three outputs. All selected copies match their archived original bytes. These are explanatory images; neither the source systems nor the local activities were executed in this pass.

Publication checks: 101 lessons, 35 gallery figures, 63 manifest outputs with all 35 published hashes matching, and 3,502 local links with zero publication problems. Generated lab coverage is 31 of 101. Git whitespace validation passed. Full execution and viewport review remain separate.
