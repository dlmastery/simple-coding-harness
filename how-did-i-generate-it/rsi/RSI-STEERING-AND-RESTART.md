# RSI course requirements and restart notes

Updated: 20 September 2026. This file records the user's directions and the current decisions. It is a handoff record, not a finished course.

## Read this first

Repository: [dlmastery/simple-coding-harness](https://github.com/dlmastery/simple-coding-harness). Course area: `rsi/`. Planning and process records: `how-did-i-generate-it/rsi/`.

The user requested a plan before implementation. The plan and reusable skill were saved and pushed. **The user's subsequent “continue” authorizes implementation.** The course rebuild is now in progress. Do not ask for that approval again. Publication on the existing working branch remains authorized; a merge into main has not been requested.

Read the [master plan](RSI-MASTERCLASS-PLAN.md), [research inventory](RSI-RESEARCH-SWEEP.md), and [work log](RSI-WORK-LOG.md). Inspect the current Git branch, status, and recent commits before changing files. Use the latest user instructions if they change this record.

## What the user wants

Rebuild the existing RSI course into a thorough, gentle, zero-to-hero masterclass. The audience is an advanced AI/ML class that may be new to RSI. Teach with the clarity of a patient expert: concrete examples, simple explanations, useful experiments, and lasting intuition.

Use classic Google Codelabs principles. Organize lessons into themed directories with a welcoming README for every theme. The top-level README must explain the project, prerequisites, learning path, execution model, and outcomes. It must not be a large dump of lesson text or configuration.

Keep this conceptual order:

1. An ordinary process without a learner-designed improvement loop.
2. Loop engineering.
3. Graph engineering.
4. Ontology engineering.
5. System intelligence, with a clear course-specific definition.
6. A meta-harness that generates a harness.
7. Separate experiments for the self-* terms.
8. Evidence for improvement and inherited improvement procedures.
9. Recursive self-improvement.
10. Advanced research comparisons and capstones.

Distinguish self-correction, reflection, learning, improvement, organization, emergence, self-play, modification, and recursion. Do not present them as interchangeable or as one universal ladder. A retry, a saved file, or an improved task score is not sufficient proof of a better improvement procedure.

## Student interface and execution

Students use natural language, readable Markdown, skills, and tools. They do not handwrite Python, JSON, YAML, or infrastructure configuration. The coding agent may generate all required code and configuration. Students inspect, reason about, and assess the results.

Use one canonical skill source with tested adapters for coding agents. Do not equate portable instructions with verified execution. State which agents and versions were tested. Separate real evaluator isolation from instructions that merely ask one agent to adopt another role.

Every codelab README must contain enough context to run and understand the activity after its stated prerequisites:

- What students will build and why they need the idea.
- The approach, a concrete example, and an explanatory illustration.
- Starting files, setup, agent capabilities, resources, and stop limits.
- Complete run instructions and copyable prompts, one step at a time.
- Expected observations, result files, and meaningful success checks.
- A deliberate change or counterexample, where useful.
- Troubleshooting, stop, restart, and reset steps.
- Key takeaways that explain causes and limits.
- A quiz with hints and explained answers.
- “What's next,” with the remaining problem and a direct link.

The learner must be able to explain a new case, not just complete the steps. Revisit earlier ideas through predictions, diagrams, error analysis, and teach-back exercises.

## Main project and data science

The current choice is **generic ML hill climbing for tabular regression and classification**. This supersedes the briefly proposed Markdown-handbook task. The user explicitly wanted a traditional ML task that suits an advanced AI/ML class.

Use UCI Bike Sharing for the main regression path. Use UCI Wine Quality for a classification and transfer path. Both sources and licenses were checked. Download, pin, and inspect the actual source files as part of implementation. Record completed checks separately from planned ones.

Show the full data science process: problem definition, data acquisition and provenance, data inspection, EDA, missingness, duplicates, leakage, split design, baselines, features, model selection, error analysis, generalization, and reproducibility. Introduce these in small steps. Agent-generated reports and plots make each decision visible.

Freeze target, metrics, split rules, and final evaluation during ordinary search. Fit transformations on training data only. For time-based data, respect information available at the prediction time. Retain failures and rejected experiments. Measure costs beyond model-fit count.

Ordinary model and feature search is the inner task. Later experiments improve the agent's research skills and the procedure that proposes or evaluates improvements. Inherited changes must actually run in later rounds. Compare old and new improvers under matched resources. Report regression or uncertainty honestly.

## Laptop defaults and larger jobs

Every required lab has a laptop-sized route. Train small CPU models. Do not require foundation-model training, large downloads, or a cluster. Hosted coding-agent inference can require internet access and paid usage; state that clearly.

The user also wants a path to larger, harder jobs on available GPUs or clusters. Separate task and evaluation contracts from compute adapters. Preserve readable briefs, skills, evidence, and stop rules across backends. The agent writes launch files and configuration.

Plan for CPU, GPU, batch-scheduler, and cloud execution where available. Include checkpoints, resumption, cancellation, failed-job records, data versions, concurrency limits, and resource accounting. Test each supported backend before calling it supported. An increased budget is not evidence of a better method.

For ScienceBuddy and other training methods, the laptop activity may use a small numerical demonstration or an audit of released results. Clearly distinguish these from actual LLM weight training. Larger-compute extension guides can support genuine training and model–harness co-evolution.

## Research

Current discovery queries target **20 August–20 September 2026**, with priority given to 7–20 September. Refresh the one-month window before delivery. Verify source publication and revision dates. Search snippets and recent crawl dates are not evidence of a new release.

Search primary sources from frontier labs, arXiv, author repositories and projects, and original X/Twitter threads. Include Meta/FAIR researchers who announce work through social posts. Record failed access and unverified claims instead of inventing missing content. Reputation is not a substitute for checking methods.

Explicit user requirements include arXiv 2609.11873, AIDE², Dream-RSI, ScientistTwo, ScienceBuddy, and RSIAgent. ModularRSI and related mechanisms are included. Give the named systems substantial advanced treatment, with prerequisites and practical exercises. Separate papers, lab self-reports, forecasts, social announcements, and independently reproduced evidence.

The broader inventory currently has 27 papers and five reports within the month. It records reading depth. Some entries have only abstract and metadata checks; complete their method review before writing authoritative lessons. Do not claim that every paper has been read in full or reproduced.

Older foundations such as AIDE² are explicit exceptions. Keep them visibly dated. The course's small historical datasets are teaching fixtures, not recent research claims.

## Writing and illustrations

Use ASD-STE100 as the writing reference. Write short, direct sentences with familiar words, active verbs, consistent terms, and descriptive headings. Keep the tone natural and respectful. Avoid hype, filler, ornate headings, repeated summaries, badges, and generated author or tool footers. Full standards compliance needs its own review; do not claim it without one.

The user requests **Imagen 2.5** illustrations with white backgrounds, professional composition, rich but readable detail, and immediate explanatory value. Keep visual symbols and colors consistent. Embed images beside the relevant explanation. Include captions and alt text.

Current tool discovery exposes image generation but no Imagen 2.5 model selector. Access to the requested generator remains unresolved. Do not silently substitute a model or claim it was used. All 101 labs now have original technical schematics rendered with Mermaid; both source and revision galleries are retained. These accompany, rather than fulfil, the requested Imagen raster work. Ten detailed illustration prompts are ready.

Check every diagram's arrows, boundaries, labels, and meaning. Use actual run data for measured plots. A generated illustration cannot serve as experimental evidence.

## GitHub checkpoints and process record

The user explicitly authorized periodic GitHub check-ins. Store all plans, requirements, design decisions, research notes, and the work log in `how-did-i-generate-it/rsi/`. Keep explanations of decisions and completed steps; do not publish the private source transcript or credentials.

The user then explicitly required intermediate artifacts too. Preserve drafts, research notes, source corrections, failed experiments, image prompts and revisions, reviews, and validation. Maintain the [artifact index](ARTIFACTS.md). The raw browser source remains local; a redacted text derivative and hashes are checked in. Earlier overwritten drafts are a recorded gap, not reconstructed originals.

Use the working branch `codex/rsi-masterclass-rebuild` for checkpoints. Implementation is approved; merging into main has not been requested. After each meaningful milestone, update these records, inspect the diff, run appropriate checks, commit, push, and verify the remote hash. A local commit alone is not a GitHub backup.

## Reusable course-building skill

The user explicitly requested that every instruction and the final outcome become a reusable skill for topics such as generative flow methods, diffusion models, and OPSD. The full package, including references and metadata, must be checked into GitHub.

The canonical package is [build-research-codelabs](../../skills/build-research-codelabs/SKILL.md). Its common course standard applies across topics; the RSI sequence and dataset decisions are in a separate preset. The [coverage checklist](SKILL-REQUIREMENT-COVERAGE.md) maps the user's guidance to the skill. Do not force the RSI ladder or current lab count onto another subject.

Skill creation and local installation are complete. All seven installed files matched the canonical repository package at validation, and the skill validator passed. The full package and provenance were pushed and verified in checkpoint `6ae9a411d7dec732debb0293f9817350bc08dc11`. The user's later “continue” separately authorized course implementation.

## Restart checklist

1. Read this file and the latest user messages. Implementation is approved; incorporate later steering.
2. Check Git status, branch, remote, and recent commits. Preserve work already present.
3. Read the master plan and work log. Continue from the recorded next step.
4. Use the research inventory's reading status. Do not repeat completed searches without a freshness or coverage reason.
5. Keep the user's execution, writing, illustration, scale, and teaching requirements intact.
6. Record new decisions and evidence. Checkpoint meaningful progress in GitHub.

Current implementation: 101 authored labs in 12 main themes, including 38 advanced labs in 13 subdirectories, with technical diagrams and explained quizzes. Shared tests pass, including in an exported source tree with a fresh dependency installation. Controlled ML, domain, generated-harness, and author-guided inheritance walkthroughs are retained. The compute path has a readable brief, adapter contract, and acceptance checks; no GPU or cluster was run. Full lab-by-lab clean-session execution, independent improver comparisons, remaining deep source audits, requested raster illustrations, learner validation, and further agent/backend tests remain incomplete. Continue from IMPLEMENTATION-RECORD.md; do not rebuild the written sequence.

The dedicated Linux/macOS/Windows RSI workflow passed all three jobs at `eceeeab64aa37206355f6b840b28c4d30c938c3f`. The repository-wide workflow has prior failures in other course sections; retained log excerpts distinguish these from passing RSI checks. Read `validation/CROSS-PLATFORM-CHECKS.md` before making compatibility or overall CI claims.

Latest author walkthrough: eight executed synthetic scheduling cases for 07.05 and 07.06, including overhead and lateness counterexamples. Lab 07.07 now calls its proposer–critic exchange an interaction analogy, not self-play training; SQL-Zero supplies a dated research contrast. The reusable RSI preset preserves that distinction. Requested raster illustrations, complete activity execution, stronger improver comparisons, further source audits, native agent tests, and learner validation remain open.
