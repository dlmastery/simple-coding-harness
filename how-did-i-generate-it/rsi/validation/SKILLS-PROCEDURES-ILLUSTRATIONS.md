# Knowledge, procedures, and GUI skill illustrations

Authoring review: 20 September 2026. Labs 10.27–10.29 each receive a separate figure. These are conceptual classroom adaptations, not published benchmark reproductions or records of completed student runs.

## Pre-generation method checks

The relevant primary methods were inspected before the prompts were saved. This narrow check does not replace the remaining full source audit or a new research sweep.

| Lab | Primary source and inspected sections | Constraint carried into the figure |
|---|---|---|
| 10.27 | [WikiSkill, method and validation gate](https://arxiv.org/html/2608.27454v1), three-layer architecture, training rollout access, update and validation | Raw traces, persistent knowledge, and active skills differ. Failed skill proposals do not roll back the knowledge layer. The controlled actor uses the active skill; the improver can consult retained evidence. |
| 10.28 | [Procedural graphs, sections 3.1–3.3](https://arxiv.org/html/2609.09153v1) | A frozen graph provides local guidance during a run. Refinement occurs separately and candidate changes require validation. A procedure graph is not a domain ontology. |
| 10.29 | [EvoSkill-GUI, sections 3.2–3.4 and appendix A.3](https://arxiv.org/html/2609.17653v1) | Separate skill editing from model training. Critique uses the instruction and visible interaction evidence; it excludes the skill package, executor private reasoning, and ground truth. The critic can be wrong. |

## Classroom preflight

The canonical lab sources are [lessons-frontier.mjs](../scripts/lessons-frontier.mjs). No lesson budget increased.

- 10.27: two fixture checks and no new model fit. Illustrate a rejection explicitly. Keep S0 active, archive the S1 proposal, and retain a source-linked failure note. Describe role boundaries without claiming enforced isolation.
- 10.28: one graph edit and four executable fixtures, with a fit stub. Two selection checks precede freezing, then a fresh check. A separate fourth case shows a numeric target component that violates the domain rule. Keep graph routing distinct from meaning.
- 10.29: use real saved metrics in the eventual local page, with the invalid-candidate warning in its detail view from the first attempt. Allow two UI attempts maximum. The picture contains score placeholders, not invented measurements. Check candidate selection independently from critic approval.

Each exact prompt was saved before generation. All three calls used the selected main overview as an actual style reference and the user-approved built-in image generator. The tool does not expose a model name.

## Full-size review

| Selected asset | Review and reading guidance | Outputs |
|---|---|---|
| [Knowledge stores](../visuals/generated/knowledge-stores-v1.png) | Three stores are distinct. S1 proceeds through fixtures to explicit rejection; S0 remains active. The retained notebook note can represent an earlier failure and the lower outcome adds the newly observed result. Only S0 feeds the actor. The added small actor illustration is cosmetic and did not justify regeneration. | 1 |
| [Procedure graph](../visuals/generated/procedure-graph-v1.png) | Conditional routes are legible and the candidate edit is unresolved. Selection, freezing, and fresh evaluation have the correct order. The separate semantic panel is not another procedure edge. The left graph explains routing; the right notebook isolates an illustrative defect, not a measured difference between executed versions. | 1 |
| [GUI skill repair](../visuals/generated/gui-skill-repair-v1.png) | Original detail warning exists before retry. The failed trace did not inspect it. The enlarged panel is for the reader and is explicitly excluded from that failed trace’s critic packet in the caption. No winner or numerical gain is invented. Check marks in the independent checker name operations; the result record remains unresolved. | 1 |

All were selected on their first attempt. No cosmetic variants were generated. The three archived originals and selected course copies are byte-identical; the manifest script checks this.

## Publication and limits

The illustration map embeds these figures in the three lab READMEs and the visual guide. The group introduction reuses 10.27 with a reading prompt and directs students to the other individual figures. Existing precise schematics remain accessible.

Publication commands and their results are recorded after generation. They check files and links; they do not establish execution, browser rendering on every viewport, learner understanding, model improvement, or independent context isolation. Full course verification remains deferred.

Publication results: build-lessons published 101 lessons; build-visual-guide published 33 figures and mapped 29 of 101 labs; build-illustration-manifest verified all 33 selected copies across 60 archived outputs; check_course checked 3,480 local links with zero publication problems. Git diff whitespace validation passed. No runtime tests or new ML fits were needed for this illustration-only change.
