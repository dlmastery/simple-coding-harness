# Modular edits and source-specific lineage

Inspected on 21 September 2026. These are selected-method audits, not full-paper reviews or reproductions. No discovery search was run for the older foundations.

## ModularRSI

Source: [v1, 14 September 2026](https://arxiv.org/html/2609.14857v1), sections 3.1–3.6. Same-task contrasts inform restricted module edits. Validation includes program checks, diff review, and execution. Independently evolved modules need integration because their assumptions can conflict. The evolved harness is frozen for downstream evaluation.

Our context and units fixtures illustrate those boundaries. They omit multi-task evidence aggregation, autonomous modification, the function library, and benchmark evaluation. A locally passing patch is not evidence of generalizable harness evolution.

## DGM mechanism map

Source: [DGM v3](https://arxiv.org/html/2505.22954v3#S1.F1), Figure 1 and section 3; first submitted 29 May 2025, revised 12 March 2026. Figure 1 was visually inspected in the browser.

| Question | Source mechanism |
|---|---|
| What changes? | Coding-agent repository; pretrained models stay frozen |
| Who edits? | A selected evolving parent edits its own implementation |
| How is a parent chosen? | Archive sampling uses performance and prior branching; the exploration process stays fixed |
| What is evaluated? | Coding-task performance, with executability and editing capability checks |
| What can persist? | Archived descendants can become later modifying parents |

The diagram separates self-modification from downstream evaluation. It does not justify calling all improvement machinery editable. Nor does a fixed archive controller imply that the modifying coding agent stays fixed. This audit does not independently verify the reported gains.

## HyperAgents mechanism map

Source: [HyperAgents v1](https://arxiv.org/html/2603.19461v1#S3.F1), Figure 1, section 3, and the main-experiment parent-selection qualification. Figure 1 was visually inspected. The [submission history](https://arxiv.org/abs/2603.19461) dates v1 to 19 March 2026; Meta's linked manuscript says 17 March and its publication page says 24 March. An August date in the HTML front matter is not evidence of a new submission or substantive revision.

| Question | Source mechanism |
|---|---|
| What changes? | Task-agent and meta-agent procedures in one editable program |
| Who edits? | The selected parent's meta-agent produces a descendant |
| How is a parent chosen? | Handcrafted archive selection in the main experiments; a separate appendix explores changing it |
| What is evaluated? | Empirical task results under the declared domain protocol |
| What can persist? | Revised meta-agent code can generate later descendants |

The figure distinguishes fixed instruction generation from editable meta-agent behavior. Structural editability alone does not prove effective improvement.

## Access and scope

The official Meta page and its linked PDF were readable. A web PDF screenshot attempt first returned an internal error; subsequent calls exposed references without image pixels to this client. Browser inspection of the canonical arXiv HTML figures resolved the visual check. No source diagram was redrawn as a measured local result. Original figures remain with their authors.

Local lineage conclusions come from retained instruction hashes and before-action records, not these source diagrams. The two-generation classroom run rejected both improver proposals; it supplies a useful negative case for this audit.
