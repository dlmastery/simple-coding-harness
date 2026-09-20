# RSI course requirements and restart notes

Updated: 19 September 2026. This file records the user's directions and the current decisions. It is a handoff record, not a finished course.

## Read this first

Repository: [dlmastery/simple-coding-harness](https://github.com/dlmastery/simple-coding-harness). Course area: `rsi/`. Planning and process records: `how-did-i-generate-it/rsi/`.

The user requested a plan before implementation. Understanding and scope have been refined through further instructions. **The final implementation plan has not yet been approved.** Continue necessary research and planning. Do not treat the request to checkpoint documents as approval to replace the course.

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

Use UCI Bike Sharing for the main regression path. Use UCI Wine Quality for a classification and transfer path. Dataset choices are a concrete proposal in the plan, not implemented exercises. Both sources and licenses were checked. Pin the actual source files and verify their contents during implementation.

Show the full data science process: problem definition, data acquisition and provenance, data inspection, EDA, missingness, duplicates, leakage, split design, baselines, features, model selection, error analysis, generalization, and reproducibility. Introduce these in small steps. Agent-generated reports and plots make each decision visible.

Freeze target, metrics, split rules, and final evaluation during ordinary search. Fit transformations on training data only. For time-based data, respect information available at the prediction time. Retain failures and rejected experiments. Measure costs beyond model-fit count.

Ordinary model and feature search is the inner task. Later experiments improve the agent's research skills and the procedure that proposes or evaluates improvements. Inherited changes must actually run in later rounds. Compare old and new improvers under matched resources. Report regression or uncertainty honestly.

## Laptop defaults and larger jobs

Every required lab has a laptop-sized route. Train small CPU models. Do not require foundation-model training, large downloads, or a cluster. Hosted coding-agent inference can require internet access and paid usage; state that clearly.

The user also wants a path to larger, harder jobs on available GPUs or clusters. Separate task and evaluation contracts from compute adapters. Preserve readable briefs, skills, evidence, and stop rules across backends. The agent writes launch files and configuration.

Plan for CPU, GPU, batch-scheduler, and cloud execution where available. Include checkpoints, resumption, cancellation, failed-job records, data versions, concurrency limits, and resource accounting. Test each supported backend before calling it supported. An increased budget is not evidence of a better method.

For ScienceBuddy and other training methods, the laptop activity may use a small numerical demonstration or an audit of released results. Clearly distinguish these from actual LLM weight training. Larger-compute extension guides can support genuine training and model–harness co-evolution.

## Research

All current discovery queries target **20 August–19 September 2026**, with priority given to 6–19 September. Refresh the one-month window before implementation and delivery. Verify source publication and revision dates. Search snippets and recent crawl dates are not evidence of a new release.

Search primary sources from frontier labs, arXiv, author repositories and projects, and original X/Twitter threads. Include Meta/FAIR researchers who announce work through social posts. Record failed access and unverified claims instead of inventing missing content. Reputation is not a substitute for checking methods.

Explicit user requirements include arXiv 2609.11873, AIDE², Dream-RSI, ScientistTwo, ScienceBuddy, and RSIAgent. ModularRSI and related mechanisms are included. Give the named systems substantial advanced treatment, with prerequisites and practical exercises. Separate papers, lab self-reports, forecasts, social announcements, and independently reproduced evidence.

The broader inventory currently has 23 papers and five reports within the month. It records reading depth. Some entries have only abstract and metadata checks; complete their method review before writing authoritative lessons. Do not claim that every paper has been read in full or reproduced.

Older foundations such as AIDE² are explicit exceptions. Keep them visibly dated. The course's small historical datasets are teaching fixtures, not recent research claims.

## Writing and illustrations

Use ASD-STE100 as the writing reference. Write short, direct sentences with familiar words, active verbs, consistent terms, and descriptive headings. Keep the tone natural and respectful. Avoid hype, filler, ornate headings, repeated summaries, badges, and generated author or tool footers. Full standards compliance needs its own review; do not claim it without one.

The user requests **Imagen 2.5** illustrations with white backgrounds, professional composition, rich but readable detail, and immediate explanatory value. Keep visual symbols and colors consistent. Embed images beside the relevant explanation. Include captions and alt text.

Current tool discovery exposes image generation but no Imagen 2.5 model selector. Access to the requested generator remains unresolved. Do not silently substitute a model or claim it was used. No course illustrations have been generated yet.

Check every diagram's arrows, boundaries, labels, and meaning. Use actual run data for measured plots. A generated illustration cannot serve as experimental evidence.

## GitHub checkpoints and process record

The user explicitly authorized periodic GitHub check-ins. Store all plans, requirements, design decisions, research notes, and the work log in `how-did-i-generate-it/rsi/`. Keep explanations of decisions and completed steps; do not publish the private source transcript or credentials.

Use the working branch `codex/rsi-masterclass-rebuild` for planning checkpoints and subsequent approved work. Do not merge the course replacement before plan approval. After each meaningful milestone, update these records, inspect the diff, run appropriate checks, commit, push, and verify the remote hash. A local commit alone is not a GitHub backup.

## Restart checklist

1. Read this file and the latest user messages. Determine whether implementation has since been approved.
2. Check Git status, branch, remote, and recent commits. Preserve work already present.
3. Read the master plan and work log. Continue from the recorded next step.
4. Use the research inventory's reading status. Do not repeat completed searches without a freshness or coverage reason.
5. Keep the user's execution, writing, illustration, scale, and teaching requirements intact.
6. Record new decisions and evidence. Checkpoint meaningful progress in GitHub.

Current blueprint: 99 small labs in 12 main themes, including 36 advanced labs in 12 subdirectories. Counts are provisional. Clarity and learning dependencies take priority over reaching a particular number.
