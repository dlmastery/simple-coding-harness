# Course standard

Read this when starting or substantially revising a course. These requirements capture the user's reusable guidance. Apply them to the chosen subject rather than copying an unrelated course's structure.

## Teaching outcome

Combine careful research with expert teaching. Aim for a masterclass whose explanations are simple enough for a newcomer to the subject and precise enough for an advanced student. “Zero to hero” means a gradual path from the stated starting knowledge to independent practice, not exaggerated claims of expertise after following instructions.

Build lasting intuition. For each lab, identify:

- The problem students can already understand.
- The one new idea that solves or clarifies it.
- A prediction students make before the run.
- The observation that tests that prediction.
- A misconception or boundary case.
- A question that transfers the idea to a new setting.

Use a continuing task where it helps students see the effect of each change. Do not force one analogy or dataset onto mechanisms it cannot show. Introduce new task families with a clear reason and a prerequisite bridge.

## Structure and navigation

Use classic Google Codelabs principles: explicit outcomes, prerequisites, steps, observable results, and gradual progress. Organize an extensive course into themed directories with short local lessons. Do not put all labs into one long directory.

The main README explains the subject, why it matters, what the student will build, the assumed knowledge, the task and resources, the role of the coding agent, the learning path, and how to begin. Include an illustrated course map and useful routes for self-study or teaching. Keep full lesson content in its lesson.

Each theme README explains what students can already do, the new problem, the sequence, and the reason to continue. Every lab links to its theme, prerequisites, previous lesson, and next lesson. A learner opening a lab directly must know how to get the right starting state.

Provide a glossary grouped by the concepts students encounter. Use plain-language definitions, concrete task examples, expanded acronyms, common confusions, and links to the relevant lessons. Mark course-specific and source-specific meanings. Keep distinctions such as a mechanism, its measured benefit, and its evidence limits explicit.

Provide a teaching roadmap with a full route and clearly labelled shorter routes. Include prerequisite bridges, session activities, student outputs, readiness checks, and early capstone milestones. Separate estimated reading and guided discussion from setup, execution, debugging, and independent work. Check that the full calendar covers every lesson exactly once. Choose the number and size of teaching blocks for the subject; do not copy another course's calendar unchanged. Link the roadmap and glossary from the main README and instructor guide, and revise pacing from actual learner evidence.

Preserve repository integration. Update navigation and test discovery when moving lessons. Keep a migration map and useful history. Avoid unrelated changes to other course series.

## Each lab README

Use descriptive headings. The following content is required; adjacent sections may be combined when that improves readability.

| Section | Required content |
|---|---|
| What you will build | A tangible input/output example, the new idea, and one or two observable outcomes |
| Why this matters | The problem with the previous approach and the reason for this lesson |
| Before you start | Prerequisites, exact starting files, supported capabilities, setup, time and resource needs, and budget |
| How it works | A simple mechanism explanation, defined terms, a worked example, and an original illustration |
| Run the lab | Where to open the agent, which folder to use, complete copyable prompts, and ordered actions |
| Check your result | Which outputs to open, expected observations, meaningful checks, and limits of the result |
| Try one change | A prediction, a controlled intervention, and a comparison that tests understanding |
| If something goes wrong | Common symptoms, diagnosis, recovery, stop, resume, and reset instructions |
| Key takeaways | Three to five concrete principles tied to what the learner observed, including a limit |
| Check your understanding | A quiz, hints, and explained answers |
| What's next | The remaining problem, why the next mechanism helps, and a direct link |

Each run step pairs an action with its purpose, expected observation, and recovery path. Give an actual skill entry point, starting state, and check. Do not say only “run the skill.” Distinguish illustrative output from a student's measured result.

Do not let the tutor agent finish the entire lab before the student has observed anything. It guides one step at a time, offers escalating hints, and waits for the student's interpretation at useful points. Learners can reveal answers or continue; record skipped checks honestly.

## Skills as the interface

Students communicate through ordinary language and readable Markdown. They invoke skills and tools. The coding agent writes Python or other code, JSON, YAML, schemas, setup commands, and backend launch files as needed. Do not make students type machine configuration to complete the course.

Explain the distinction between the model, coding agent, skill instructions, generated tools, harness, and evaluator when relevant. Loading a skill does not guarantee a restriction is enforced. Inspectable instructions and observed execution are different evidence.

Use one canonical skill source. Generate or maintain adapters for agent-specific discovery and integration. Provide a file-reading fallback where possible. Test claimed support in the actual agent and state the versions. Do not promise that every agent supports the same hooks, isolation, or tools.

Distinguish a lesson's notes folder from an experiment's persistent state. A new lesson must not silently reset a continued experiment's attempt budget, data exposure, or final lock. State which original workspace to reuse. Before a multi-arm comparison, allocate the total lesson budget across its arms and count additional checks separately. Explicit lesson limits override a generic default while actual tool limits still apply. Creating more folders does not authorize more trials.

When teaching coordination, distinguish a trace reconstructed after execution from state that controlled the actions. Save and read the required state before launching the next action. Test a real process boundary and a refused action when relevant. Match checker evidence to the complete candidate identity, even when two candidates produce identical predictions. Preserve the original run and its cost if review requires a separate corrective experiment.

## A meaningful task at an affordable scale

Choose an authentic task that suits the subject and audience. For advanced AI/ML teaching, use genuine ML experiments when they expose the mechanism better than a document example. Regression, classification, small generative models, or low-dimensional learning problems may fit different subjects.

Each required lab must have a laptop-sized path. Use small data, short jobs, bounded searches, and available CPU or modest hardware. Declare hosted-model usage and its costs. Do not require foundation-model training to understand a basic concept.

Preserve a path to larger experiments. Separate the scientific task and evaluation contract from the compute backend. Keep readable instructions when moving from CPU to GPU or a cluster; let the agent generate configuration. Include checkpoints, resumption, cancellation, failed-job logs, limits, and cost accounting. Distinguish tested backends from proposed ones.

Scaling must preserve the scientific question or explicitly declare a new one. More trials, larger data, a different model, or more compute can change the comparison. Give competing methods comparable resources when claiming a method improvement.

Inspect the effective behavior of composed changes before measuring them. Different source hashes or recipe names can still construct the same model or workflow when a later operation overwrites an earlier edit. Use construction or behavioral checks to identify this case. If it is discovered after an experiment is frozen, preserve the charged attempts and report the limitation; do not replace outcomes or tune against final data. Keep strong conventional controls visible even when the proposed method beats another weaker control.

Make this path concrete with a readable job brief, an adapter contract, and small backend acceptance checks. Distinguish a candidate from its submission attempts. Reconcile uncertain submission before retrying. A model without resumable training should record a failed attempt and a fresh retry; do not call it checkpoint resumption. Keep student instructions in natural language while the agent generates backend files.

## Data science and experiment design

For ML subjects, show the full process rather than beginning at an optimizer call:

1. Frame the problem, prediction or generation target, input availability, and success criterion.
2. Acquire and document data, permissions, provenance, version, schema, and units.
3. Inspect distributions, missingness, duplicates, imbalance, time or group structure, and data limitations.
4. Design splits or comparisons before search. Prevent leakage and fit preprocessing on training data only.
5. Build a simple baseline and explain what beating it would mean.
6. Make a hypothesis, change one factor where practical, run within a budget, and keep all outcomes.
7. Analyze errors, slices, uncertainty, and resource use.
8. Evaluate on protected final cases and appropriate transfer cases.
9. Package the result with its data assumptions, transforms, model, and reproduction instructions.

Introduce these gradually. Use readable reports and proper plots. Do not force statistical detail before the learner has an observation that needs it. Do not pretend a single seed or one small holdout proves a broad claim.

## Writing

Use ASD-STE100 as the writing reference. Verify the applicable edition if claiming formal conformance. Apply short sentences, active voice, clear conditions, consistent terms, and a controlled technical glossary. Avoid a formal compliance claim without the required language review.

Write natural, respectful prose. Use concrete nouns and direct verbs. Explain the example before the abstract term. Define acronyms. Keep paragraphs short and connected. Use one action per instruction. Do not make students infer a missing step.

Avoid marketing language, filler, forced enthusiasm, repetitive conclusions, artificial question-and-answer slogans, decorative headings, badges, and generated author or tool footers. Do not call a difficult concept obvious. Do not imitate a named teacher's personal voice; aim for the clarity and patient reasoning the user admires.

A takeaway explains a mechanism: “A retry helps when it receives useful new information.” A weak takeaway merely names the topic: “You learned loops.” A next-step section identifies a remaining limitation, so progression feels necessary.

Read representative lessons aloud. Check that students can explain them in their own words. Automated readability scores cannot replace an editorial review.

## Illustrations

When the user wants early visual feedback, finish and show the overview maps and major mechanisms before the full execution pass. Include an overall mindmap, clear course-location links at each theme and lab, and expanded maps for the advanced studio and capstones. Introduce course objectives, prerequisites, and a clearly labelled duration estimate near the start. An inventory alone is not a guided course map.

Use generation calls carefully. Before the first call, verify the figure against its lesson: exact labels, arrow directions, sequence, changed and fixed objects, version identity, and scientific claims. Supply a reviewed label list and tell the generator not to invent technical details. Aim for one usable draft; combine substantive corrections into one targeted edit and use no more than three outputs per figure. Do not regenerate for cosmetic alternatives. If the third output still has a material error, keep it as an unselected draft, explain the issue, and revise the specification before seeking further attempts. Preserve all outputs and the review record. This is the user's cost-and-quality preference for this course-authoring workflow.

The saved preference is **Imagen 2.5**, a white background, professional composition, and rich but readable detail. Verify access to the requested generator. If unavailable, state the precise gap and preserve the requirement. Do not silently use another model while claiming compliance.

An explicit user-approved alternative supersedes the provider preference for that project. Record the user's decision, actual tool, returned model identity when available, and remaining visual requirements. Do not reopen the same provider question or keep a stale provider blocker after approval. When the tool exposes no model identity, say so; do not infer one from appearance or a prompt. For this RSI rebuild, the user approved the available image generator on 20 September 2026.

Every image has a teaching purpose. It should show the main idea at a glance and reward closer reading. Use a clear hierarchy, consistent colors and shapes, readable labels, meaningful arrows, and enough space. Highlight the new mechanism in an evolving diagram. Dense does not mean crowded.

When individual codelab infographics are requested, an overall course map or theme overview does not satisfy that coverage. Map the appropriate generated figure directly to every requested lesson and keep an explicit list of missing figures. Count lab coverage separately from shared maps, alternative drafts, and precise companion schematics. Prioritize the specific unfinished themes the user names.

When the user prefers an earlier illustration, preserve it as an explicit visual benchmark and provide it as a style reference for subsequent generation. Compare the actual images, not only their prompt wording. Preserve concrete scenes, connected explanations, crafted drawing, and meaningful detail. Repeated generic folders, chips, cards, or text boxes can weaken the teaching even when the labels are technically correct. Revise a representative weaker image before continuing a large batch. Keep necessary qualifications in nearby prose when they overwhelm the image, without removing the scientific boundary from the lesson.

Show data flow, control flow, mutable and fixed components, feedback, and boundaries where those distinctions matter. Avoid decorative imagery that hides the mechanism. Use panels for a complex overview and focused figures for individual steps.

Review spelling, labels, arrows, missing stages, duplicated elements, scale, and scientific claims. Keep generation prompts, source assets, revisions, and review notes in provenance. Embed locally stored assets in Markdown with captions and alt text. Verify GitHub rendering and normal-size legibility. Preserve white backgrounds even when the viewer uses dark mode.

Treat generated wording as proposed technical content. A tool can add an incorrect explanation that was absent from the prompt. Check training and evaluation routes, version handoffs, state versus sample-output representations, and every advertised backend connection. Remove unrequested fine print that makes an image harder to read. Preserve the rejected image and the corrective prompt. For dense figures, keep the mechanism understandable in the adjacent caption and provide a full-size link; do not claim all labels are legible in a phone-sized thumbnail.

Trace each scientific arrow from its source to its destination. Features must enter the fitted procedure before predictions; final data must not enter development; a proposed researcher must run before its behavior can be compared. Check field names and units against the data dictionary. After every image edit, recheck the whole figure because a local correction can break another connector. If a long route remains confusing, use clearly matched labels instead of dangling or misleading arrows. In the tutor skill, use one short prediction or tracing question to connect the illustration to the next activity.

Precise technical schematics may use Mermaid or SVG as a companion. Preserve their source and render static alternatives for readers without diagram support. Keep captions sufficient to explain the diagram. Render every diagram to catch syntax failures, then inspect layout and meaning; parser success alone is not visual review. Companion schematics do not silently satisfy a specifically requested raster generator that remains unavailable.

Draw measured charts from real data with plotting tools. Mark schematic curves as schematic. Do not use image generation to manufacture empirical evidence. Check source licensing before reusing a paper figure; prefer original explanatory illustrations with citations.

For diagrams with several procedural levels, check what each procedure acts on. A task skill can fit models; an updater proposes and checks edits to skills. Do not give both the same checklist. Show the candidate before its check, preserve the changed rule at later use, and ensure rejection cannot lead to activation. Check accompanying run prompts for the same mechanism; a correct picture cannot repair a missing execution instruction.

## Assessment

Every codelab ends with a quiz, normally four to six short questions, followed by “What's next.” Adjust length to the lab. Test recognition, interpretation of the student's result, a changed condition, and an explanation in the student's own words. Use debugging or transfer questions when useful.

Explain why each answer is correct and why plausible alternatives fail. Provide hints before revealing answers. Avoid trivia about filenames, JSON keys, syntax, or authors. Keep assessment separate from runtime tests. Revisit concepts across themes and require a final teach-back.

## Acceptance

The complete course needs accurate sources, a coherent learning path, working activities, verified instructions, useful illustrations, assessment, transfer, and an honest record of what was tested. Review teaching quality, research accuracy, visual quality, and runtime behavior as separate concerns.

Honor an explicit user choice to complete and checkpoint diagrams, READMEs, and skills before the full verification pass. Continue basic link, asset, readability, and obvious-fact checks while authoring. Preserve a separate queue for deferred execution, reproduction, source-depth, and compatibility checks. Publish later corrections to the authorized branch and keep authored, visually reviewed, and execution-verified states distinct.

No guaranteed improvement, fabricated transcripts, invented citations, or untested compatibility claims. Report failed experiments as useful outcomes when students can interpret them. Keep all intermediate and final project artifacts in the authorized provenance record.
