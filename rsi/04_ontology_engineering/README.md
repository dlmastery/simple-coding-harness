# Agree on what the experiment means

[Course](../README.md)

**You are here:** Theme 04 of 00–11 · Dependable workflows · 5 labs. [Your place in the guided map](../COURSE-MAP.md#theme-04).

Two files can both say “score” while describing different measurements. A shared vocabulary connects the data, models, decisions, and evidence.

Begin with concrete entities and relations in Markdown. Add only the rules needed to catch a real inconsistency.

![A workflow graph routes valid data toward fitting and invalid data toward repair. Separate domain relations say the scaler is fit on training data, search selects on selection data, and the model is measured by MAE.](../assets/illustrations/graph-ontology-v1.png)

*Read the left arrows as dependencies between actions. Read the right arrows as sentences about domain meaning. These are selected facts and one rule, not a complete ontology. Correct execution order cannot rescue a leaked feature or the wrong metric. A declared fact also needs evidence that the implementation follows it.*

[Open the illustration at full size](../assets/illustrations/graph-ontology-v1.png).

<details>
<summary>Find theme 04 in the whole-course mindmap</summary>

![A bike-demand research project connects six learning blocks and all twelve themes: one experiment, dependable workflows, a system and builder, changes and evidence, research studio, and capstones.](../assets/illustrations/course-mindmap-v2.png)

*Follow theme numbers 00–11. The branches group concepts; they are not execution dependencies or a universal maturity ladder. The research names are selected examples. Use the theme number on each lesson to locate it here. This map describes the planned route, not completed experiments.*

[Open the illustration at full size](../assets/illustrations/course-mindmap-v2.png).

</details>

| Lab | What you will build |
|---|---|
| [04.01 · Name the objects in an experiment](step_01_entities/README.md) | A small vocabulary for data, columns, targets, partitions, models, metrics, and evidence. |
| [04.02 · Connect data, models, and evidence](step_02_relations/README.md) | A readable relation table describing one ML experiment. |
| [04.03 · State rules that must always hold](step_03_invariants/README.md) | Three domain invariants, each with a passing and failing example. |
| [04.04 · Catch a plausible but invalid experiment](step_04_catch_contradictions/README.md) | A semantic failure report and a corrected relation table. |
| [04.05 · Change a definition without losing its consequences](step_05_evolve_vocabulary/README.md) | A versioned vocabulary change and an impact report for a new forecasting task. |

Start with the first lab and follow its next link. Each lab keeps its notes in a separate workspace and links any earlier experiment it reuses. The agent writes code; you predict, inspect, and explain. [Skill entry point](../skills/rsi-tutor/SKILL.md).

**Ready to continue when:** Use named objects, relations, and meaning rules to reject a plausible experiment with a wrong metric, unit, or leaked input.

You can now inspect both the route of an experiment and the meaning of its records. These become parts of a coordinated research system.
