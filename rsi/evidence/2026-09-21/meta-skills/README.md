# Repair the decision, then repair how you repair it

This author walkthrough supports [10.16](../../../10_research_studio/05_meta_skill_evolution/step_16_task_skills/README.md) and [10.17](../../../10_research_studio/05_meta_skill_evolution/step_17_meta_skills/README.md). It executes a small decision inside an ML workflow. All candidates have equal constructed MAE, so runtime breaks the tie. The runtime numbers are fixtures, not measured training times. No models are fitted.

## First, keep the updater fixed

Candidate A takes 800 milliseconds; candidate B takes one second. The original task skill treats an unknown unit as seconds. It reads A as taking 800 seconds and chooses B. The correct comparison is 0.8 seconds against one second, so A should win.

The coding agent follows [META-SKILL-v0](skills/META-SKILL-v0.md) and adds the missing millisecond conversion. The [target check](10-16/target/RESULT.md) and [seconds regression check](10-16/second/RESULT.md) both pass. The [task child](skills/TASK-SKILL-v1.md) is retained. The updater remains unchanged. Its [renamed copy](10-16/RENAME.md) has the same hash and supplies no new mechanism.

A second, explicitly allocated prerequisite round finds the same class of mistake with minutes. A takes 0.02 minutes, or 1.2 seconds; B takes 0.8 seconds. The faulty fallback selects A. The same updater adds the minute conversion, producing [S2](skills/TASK-SKILL-v2.md). Read the [observed parent failure](prerequisites/second-parent-minutes/RESULT.md) and [second update trace](prerequisites/second-update/ROUND.md). These two real update traces provide the starting evidence for 10.17.

## Now change the updater

Both repairs fixed a named unit but left the unsafe fallback. The [meta-level proposal](10-17/META-PROPOSAL.md) applies the existing diagnosis and proposal steps to the updater's own instructions. Candidate v1 requires unknown-unit refusal in the task child and chooses an unknown-unit case for its second internal check.

The later comparison begins from identical S2 bytes. Each updater receives one task proposal for a microseconds case and two internal checks. The new instruction has two visible effects: the agent writes a refusal rule into the v1-produced task skill, and the driver selects the unknown-unit check from the active updater's policy field. Open the [v1 before-action record](10-17/v1/ROUND.md) and [actor note](10-17/v1/ACTOR-NOTE.md). A version name alone would not show either action.

## Use the same external check for both

Both children pass their own internal checks. The fixed external comparison then tests the same three cases:

| External case | Child produced under v0 | Child produced under v1 |
|---|---|---|
| Microseconds versus seconds | Correct candidate | Correct candidate |
| Unknown ticks | Selects a candidate using an invented conversion | Refuses the comparison |
| Known seconds | Correct candidate | Correct candidate |

The [comparison table](10-17/COMPARISON.csv) records two of three external passes for v0 and three for v1. The declared rule [retains candidate v1](10-17/META-RETENTION.md). Its use in a later task-skill round is visible separately from that retention decision.

This is a narrow benefit on known constructed cases. One coding agent authored both arms. The fixed driver executes the decisions but does not invent the revisions. The [claim audit](CLAIM-AUDIT.md) explains these limits and a counterexample: swapping out the known-case internal check can hide a regression. The common external seconds check covers one such risk here, not all possible regressions.

## Count the whole exercise

There were seventeen decision executions: two original parent captures, two child checks in 10.16, three decisions to prepare the missing second update trace, and ten later checks. There were zero fits. The [ledger](EXECUTIONS.csv) keeps failed parent decisions and the failed v0 external decision. The [cost record](COST.md) separates these counts from unknown agent costs.

The [schedule simulation](10-17/SCHEDULE-SIMULATION.md) compares update horizons with invented accounting units. It does not measure quality or noise. Learner predictions, teach-back, quizzes, independent-agent behavior, and larger backends remain untested. The [selected source audit](SOURCE-AUDIT.md) distinguishes this short pipeline from the full MetaSkill-Evolve method.

The [manifest](MANIFEST.csv) covers 115 original files, checked against the original workspace before publication. The manifest itself and this guide are publication additions outside that list. Keep this archive unchanged; run your own lesson in a new sibling workspace.
