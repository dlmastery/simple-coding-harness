# Illustration brief

Status: production started on 20 September 2026. The user explicitly approved the available image generator in place of the original Imagen 2.5 preference. Seventeen selected illustrations and all thirty-seven generated versions are retained in the [generation gallery](generated/README.md). The actual tool exposes no model identifier. See the [provider decision](GENERATOR-DECISION.md); no further provider approval is needed.

The course also has original Mermaid technical schematics for all 101 labs, authored in `scripts/lesson-diagrams.mjs`. These supplement the generated illustrations. The measured data plots remain a third, separate class of visual evidence. The initial ten-topic brief is now generated and selected after full-size review. Further method-specific illustrations and the full rendered-page review remain in progress; ten assets do not complete every theme or lab.

## Shared visual language

Quality correction, 20 September: the user prefers the first illustration and reports declining quality. The selected [main overview](generated/main-overview-v2.png) is now the explicit style reference. Its concrete bike station, purposeful object detail, connected story, and carefully drawn scenes set the standard. New images must be compared with this actual reference. Revise the ScienceBuddy composition before extending the batch. Repeated generic folder and chip layouts are insufficient even when their labels are correct. The current priority is authored diagrams, READMEs, skills, and GitHub checkpoints; the full execution and reproduction pass follows later.

White canvas. Deep navy text. Muted blue for fixed procedures, warm amber for the component being changed, teal for checked evidence, and restrained brick red for a rejected path. Color must be reinforced with a label or shape. Use fine, consistent strokes and simple objects. Keep ample space between groups. Avoid gradients, glow, mascot robots, decorative code, fake dashboards, and ornamental scientific symbols.

Use a left-to-right reading path for a small mechanism. Use clearly separated panels for a complex comparison. Place the main causal relationship at the center. Secondary details may reward a closer look, but essential text must remain legible at 800 pixels wide. Do not put paragraphs inside the image. Explain the idea in the adjacent Markdown.

The illustrations are conceptual schematics. Do not invent empirical curves, scores, hardware performance, benchmark badges, or paper logos. Do not suggest a private evaluator when the local teaching files are readable by the agent. Use original compositions; do not copy a paper figure.

## Generation prompts

Each prompt inherits the shared visual language above. Save the exact submitted prompt, returned provider/model metadata if supplied, image file, and review result together. A provider name must come from actual metadata, not our requested prompt.

### 01 · From one experiment to an improving research process

Create a professional educational illustration on a pure white background, landscape 3:2. Show three connected panels. Panel one: a small hourly bike-rental table enters a model and produces predictions checked against observations. Panel two: a readable research procedure chooses one new experiment using a checked error report. Panel three: an improvement procedure is revised, visibly saved as a new version, and then used in a later research round. Keep the task model distinct from the coding agent. Use blue for unchanged procedures, amber for the changed procedure, and teal for evidence. Main labels only: “One experiment”, “Improve the research skill”, “Use a revised improver”. Include a small fixed evaluation track beneath the panels. No rising performance curve or claim that each revision wins. The immediate intuition is that different layers can be the object of improvement.

### 02 · The answer hidden in an input

Create a precise white-background teaching illustration, landscape 3:2. Show a bike station and one simple hourly data row. Two count tiles, “casual” and “registered”, visibly add to the “total rentals” outcome. Put those count tiles behind an outcome boundary. Calendar and observed-weather tiles enter the permitted prediction route. Draw a blocked shortcut from the component counts into the model. The image should explain target leakage without equations beyond the addition relation. Do not imply observed weather was known one day ahead. Use a small caption label “Retrospective teaching task”.

### 03 · A loop carries state and spends a budget

Create a white-background educational mechanism illustration. Show four stages around a clear open loop: “Propose”, “Run”, “Check”, “Record”. Place a persistent experiment notebook in the center containing a candidate identity, incumbent, and remaining-attempt markers without measured scores. A distinct exit leaves the loop at “Stop rule”. A failure goes into the notebook and consumes an attempt. A small resume panel reads the same notebook after interruption. Do not show infinite repetition or an always-rising result. Make state and stopping more prominent than the circular arrows.

### 04 · Workflow graph and ontology answer different questions

Create a balanced side-by-side white-background comparison. Left panel is an execution graph: data check, split validation, model fit, result check, with one explicit failure branch. Right panel is a concept map: dataset, training partition, candidate, run, metric, with labelled relations such as “trained on” and “measured by”. Title labels: “What runs next?” and “What does it mean?” Use different arrow styles with a clear legend. The same objects appear across panels but the relationships differ. Do not draw the ontology as a second schedule.

### 05 · The builder and the system it builds

Create a professional white-background diagram with three main objects. A readable task brief enters a builder workspace. A distinct generated harness package exits, containing skill instructions, tools, state, checks, and limits. That package runs a small model experiment after the builder is no longer involved. Main labels: “Brief”, “Meta-harness”, “Generated harness”, “Executed result”. Keep the builder blue and highlight the generated package amber. Do not add a self-improvement arrow back to the builder: generation alone does not establish RSI.

### 06 · Similar self-* words describe different mechanisms

Create a white-background comparison plate with six restrained panels. Show correction of the current output; reflection as a proposed explanation tested against a counterexample; a saved lesson used in a later task; local rules changing work assignments; a collective pattern arising from interactions; and a component modifying its own instructions. Use a short label for each. Arrange these as parallel examples, never as a staircase or maturity ladder. Include one small shared note, “Benefit needs evaluation”. Keep the detail readable and avoid implying that every mechanism is recursive self-improvement.

### 07 · The next round must inherit the change

Create a white-background version timeline with two rounds. Round one has solver S0, improver I0, and a fixed evaluator E. Evidence motivates a proposed I1. Between rounds, show a visible version handoff carrying I1. Round two visibly reads I1 and executes its new required result check before proposing a solver revision. Keep E unchanged on a separate lower track. Main emphasis: the handoff and changed action, not merely a saved file. Add a rejected branch to show that a revised improver can fail. Do not claim effectiveness or acceleration from the structure alone.

### 08 · Replay cannot reveal an unvisited branch

Create a detailed but readable white-background discovery-tree illustration. Solid nodes are completed experiments with linked report icons, using no invented numerical results. Dashed empty nodes are unvisited possibilities labelled “Unknown”. A replay policy traces only solid recorded nodes. A separate live-execution arrow can explore a dashed node later. Main labels: “Recorded work”, “Replay”, “New execution”. Do not let replay cross into an unvisited node and return a score. This is a classroom explanation inspired by Dream-RSI, not the paper’s result figure.

### 09 · Harness and model can change on different cycles

Create a professional white-background diagram with two clearly separated update tracks. One track changes the harness while the language model stays fixed. A second track updates model parameters from declared training evidence under a chosen harness. Join each pair at an evaluation checkpoint labelled with a model version and harness version. Human requests and corrections feed a task-and-rubric stage; distinguish this from model-generated feedback. The image must make parameter training visibly different from editing instructions. Label the local numerical exercise as an illustration, not a full ScienceBuddy or GRPO training run. Do not include reported accuracy numbers.

### 10 · Keep the experiment identity when compute moves

Create a white-background illustration connecting a laptop, one accelerator worker, and a cluster of workers. A single experiment contract travels with a candidate, data version, evaluator version, and result record. Around the compute side show queue, checkpoint, cancel, resume, and failed-attempt records. The research skill remains separate from backend launch machinery. Do not imply linear speedup or universal support. Use a small label “Test each backend”. The main intuition is that infrastructure can change while evidence remains traceable.

## Review each returned asset

Inspect at full size, at 800 pixels wide, and in a narrow Markdown column. Check text, arrows, boundaries, model/agent distinctions, fixed and mutable parts, and whether the caption's claim follows from the image. Reject any image that silently depicts a stronger mechanism than the lesson executes. Save failed versions and revision prompts rather than overwriting them.

Only embed an accepted asset in a lesson. Add descriptive alternative text and a caption. Check the image on GitHub in light and dark modes; the canvas itself must remain white. The technical schematic remains useful as a precise companion and accessible explanation.
