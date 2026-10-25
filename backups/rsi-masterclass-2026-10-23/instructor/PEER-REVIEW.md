# Reproduce one result, then explain a new case

[Portfolio](../PORTFOLIO.md) · [Teaching guide](README.md)

This is a prepared peer exercise. No peer session has yet been recorded for the example portfolio. A tutor should ask one question at a time, wait for the answer, and record actual observations. Do not prefill praise, scores or feedback.

## Prepare the one-fit reproduction

Use the [exported white-wine package](../evidence/2026-09-21/capstone-harness/export/package/README.md), not the closed recursive experiment. The coding agent reads TASK.md, DATA-CARD.md, WORKFLOW.md and RECOVERY.md. It checks source and package identities against the saved capstone manifest, copies the package into a newly labelled sibling workspace, and installs its pinned dependencies in a local Python 3.12 environment. Record the actual agent, OS, Python, library versions and exact commands; unknown values stay unknown.

Ask the peer what the training-median baseline will predict and why quality must not enter the feature list. Then prepare an experiment with budget one. Before the valid fit, request target quality as an input and confirm the runner refuses before admitting an attempt. Preserve that command. Correct the feature request and run one median candidate, then use evaluate.py to check the saved selection predictions. No extra fit or final evaluation is allocated.

The author baseline's selection MAE is 0.655310621242485. A peer should first check the source hash, grouped split, recipe and prediction rows; compare the recomputed metric within 1e-10. A mismatch is evidence to diagnose, not a reason to edit the expected score or silently spend another attempt. Record errors and the remaining budget. This run tests reproducibility of the small baseline, not the revised improver's effectiveness.

If command execution is unavailable, record that this session can inspect and explain artifacts but cannot complete reproduction. If setup fails before fitting, preserve it and repair setup. If an actual fit fails, its one attempt remains charged; any retry requires a separately declared allowance. Do not rename the workspace to refund it.

## Ask for evidence, not terminology

1. Follow one row through inputs, split, prediction and error. Where is the target allowed?
2. Which operations form the process? What would make them a loop, and what stops it?
3. Draw the dependencies as a graph. Which action must not run after a failed prediction check?
4. Give a record that is syntactically valid but semantically wrong. Use a target feature or a duration unit.
5. What does the generated harness do, and what did the builder choose? Which artifacts separate them?
6. In the unit example, what changes and what stays fixed? In the eight-fit capstone, what additional object changes?
7. Which file and later decision show the revised improver was used? Was that use before or after its acceptance?
8. What is the strongest result you can defend? What evidence would you need for a broader one?

<details>
<summary>Instructor checks to use after the peer answers</summary>

Look for the following connections, not these exact words. Model inputs exclude the target, while the checker uses the observed target. A process orders operations; a loop repeats them under feedback and a stop rule. Graph edges express data or control dependencies. Meaning rules prevent leakage and invalid unit comparisons. The builder creates a task-specific execution package; that package executes the experiment. A task-skill repair can happen under a fixed updater. An improver revision needs its own identity and a later action governed by its changed instruction. In the white-wine example, I1 governs a candidate trial before the external acceptance decision. One controlled author comparison does not demonstrate autonomous discovery, fresh-task superiority or acceleration.

</details>

## Change the prediction question

Ask the peer to propose a different regression or classification problem. Record their actual proposal before discussing transfer. Reuse the readable workflow, budget accounting and evidence requirements. Redesign the target, prediction time, permitted inputs, split, metric, data permissions and relevant error analysis for the new problem. Do not run the new task in this one-fit session.

If no peer is available, the instructor may discuss a clearly labelled hypothetical example, such as predicting next-day demand from information available today. That is not peer feedback. The observed-weather bike example cannot automatically serve as a future forecast.

## Save the session honestly

Create a new PEER-REVIEW.md in the learner workspace with participant consent or an anonymous role label, date, actual environment, prediction, command/result links, explanation, failure diagnosis, transfer proposal and unresolved questions. The local four-part rubric in the teaching guide can assess the response after it exists. A prepared form is not a completed assessment.

Use the original [pending record](../evidence/2026-09-22/portfolio/PEER-STATUS.md) as a status reference, not an invitation to overwrite the archive. Keep the author walkthrough and the peer session separate.
