---
name: build-research-codelabs
description: Plan, build, or rebuild a research-grounded technical masterclass as progressive, illustrated codelabs that students execute through coding-agent skills. Use for complex topics such as RSI, diffusion models, flow methods, or self-distillation, with recent research, laptop exercises, larger-compute extensions, quizzes, and versioned provenance.
---

# Build research codelabs

## Final outcome

Produce a complete, accurate, and approachable masterclass that takes the stated audience from first principles to advanced practice in the chosen topic. Students use skills and natural language to run meaningful experiments. They can explain why each method works, recognize its limits, interpret evidence, and apply the idea to a new problem. The course has themed directories, an excellent walkthrough README, clear lesson instructions, explanatory illustrations, quizzes, laptop defaults, a path to larger compute, and a complete versioned record of its development.

This outcome is the completion target. A plan, a paper list, attractive pages, or generated code alone is not a completed course. When the current request is only for a plan, deliver a concrete plan for review and preserve that scope.

## Required references

Read [the course standard](references/course-standard.md) and [the provenance rules](references/provenance.md) at intake. They preserve the user's full reusable guidance. They are requirements, not optional inspiration.

- During research, read [research and evidence](references/research-and-evidence.md).
- When choosing a new subject or exercise, read [topic adaptation](references/topic-adaptation.md).
- For RSI, read [the RSI preset](references/rsi-preset.md). Do not impose its topic-specific sequence on other subjects.

Current user instructions take precedence. Preserve all applicable requirements in a project steering record. Explain any unresolved requirement and record its status; do not silently omit it.

## Start with the user's actual request

Identify the subject, audience, repository, source material, output location, desired scope, resources, and whether implementation is approved. Infer routine choices from context. Ask only for missing information that changes the work materially; continue independent work while waiting.

If the user asks for paraphrase or approval first, restate the intended outcome and constraints before implementation. Do not ask for the same approval again after it is given. Reversible reconnaissance and concrete planning can proceed within the requested scope.

For an existing course, inspect it before proposing a replacement. Read applicable repository instructions. Map the content, navigation, skills, assets, tests, execution paths, and integration points. Verify what works instead of accepting the README's claims. Treat saved chats and transcripts as leads that need source checks.

Create a project record under `how-did-i-generate-it/<topic>/`. Keep requirements, current plan, research inventory, work log, artifacts, validation, and restart state there. Commit and push at meaningful milestones when the user has authorized that repository and publication. Record source hashes and justified redactions.

## Build the plan

1. Define the final capabilities in terms students can demonstrate. Separate topic knowledge, experiment execution, interpretation, and transfer.
2. Choose a small, authentic task that exposes the subject's mechanism. Explain why it suits the audience and fits a laptop. For an AI/ML class, prefer a genuine ML task over a convenient but unrelated document task.
3. Map prerequisite concepts and common misconceptions. Start with a simple process or baseline. Add one conceptual change when the prior method exposes a reason for it.
4. Organize the path into themed directories. Give each theme a README, a short sequence, and a clear transition. Avoid a large flat lesson directory or competing reading orders.
5. Design each lab around an observation, a mental model, a counterexample or limit, and a transfer question. Include the exact run path, expected artifacts, and assessment.
6. Sweep the last month of primary research, prioritizing the latest two weeks. Map papers to mechanisms and evidence. New publications should change the teaching where useful, not merely lengthen the bibliography.
7. Specify the agent skills, generated tools, evaluation boundaries, laptop resource limits, and path to larger jobs.
8. Include a README storyboard, visual brief, representative lesson outline, implementation order, validation plan, and acceptance criteria.

Make the plan reviewable. Do not substitute an arbitrary lab count for a justified learning path. Honor a requested plan-review stage before replacing course content.

## Build the course after approval

Create representative working lessons first: onboarding, one central mechanism, one common failure, and one difficult conceptual transition. Use them to test the teaching, runtime, and illustration standards. Then complete the full approved course. A successful pilot does not discharge the remaining work.

Keep students' interface readable. Students state intent and invoke skills; the agent creates code, configuration, schemas, dependencies, and launch files. Students need not handwrite Python, JSON, YAML, or scheduler syntax. Explain generated artifacts when they matter to the scientific question.

Use a canonical skill source and agent-specific adapters. Provide a readable file-based entry path for capable agents without native skill discovery. State capability requirements and tested versions. A role instruction is not technical isolation. A configuration file is not an executed harness.

Every lab includes what it does, why it matters, how it works, how to run it, what to expect, how to check it, how to recover, illustrations, key takeaways, a quiz with explained answers, and “What's next.” Follow the detailed standard rather than compressing lessons into a prompt and a result screenshot.

Write in direct, natural technical English guided by ASD-STE100. Use descriptive headings and stable terms. Avoid hype, filler, repeated summaries, decorative footers, and unexplained jargon. Explain a concrete example before introducing the abstraction.

Use the requested illustration generator and visual style. The saved preference is Imagen 2.5, white backgrounds, professional composition, and rich but readable detail. Verify the actual model is available. Do not claim an unavailable model was used. Review visual correctness and legibility. Plot measured results from actual data; do not generate fictional experiment charts.

## Keep the science and execution honest

Teach the full data or experimental lifecycle where relevant: question, data provenance, inspection, quality checks, split or comparison design, baseline, intervention, execution, error analysis, evaluation, and reproducibility. Separate development feedback from protected final evaluation.

Use laptop-sized defaults. Preserve task, data, evaluator, candidate, and run-record interfaces for GPU or cluster extensions. The agent generates backend setup. Include budgets, checkpoints, cancellation, retries, failed-job records, and resource accounting. Do not equate extra compute with a better method.

For every research adaptation, state what is preserved, what is simplified, and which claims cannot follow from the exercise. Distinguish live execution, replay, simulation, numerical illustration, paper-reported results, and reproduction. A prompt edit is not a model-weight update.

Assess the mechanism as well as the output. Students must predict an intervention, diagnose a failure, interpret uncertainty, and explain a new case. A quiz should reveal misconceptions rather than test memory of API fields or paper names.

## Finish and hand off

Check navigation, assets, citations, setup, run instructions, failure recovery, quizzes, explanations, resource limits, and supported agent paths. Run meaningful checks appropriate to the work. Review the prose and illustrations separately from runtime correctness.

For a course, demonstrate clean-start runs of required activities and the declared evidence boundaries. For a plan, clearly mark untested assumptions and future checks. Do not claim universal agent or hardware support.

Update the work log, requirement coverage, artifact index, and restart instructions. Commit all task-produced intermediate and final artifacts that can be published within the authorized scope. Use an authorized artifact store plus a checked-in manifest for files unsuitable for ordinary Git. Push and verify the remote commit before claiming a GitHub backup.

Report what is complete, what was checked, and any material gap. Link the course, skill, plan, and provenance as relevant. Name any skill or plugin that authorized external publication when applicable; this skill does not itself authorize sending messages to other people.

## Example requests

“Use $build-research-codelabs to plan a diffusion-model course for an advanced ML class. Use small experiments, recent primary research, and the saved teaching and illustration standards. Show the plan first.”

“Use $build-research-codelabs to rebuild this flow-methods course in the named repository. Preserve the full development record in GitHub. Students use skills; the agent writes the implementation.”

“Use $build-research-codelabs with the RSI preset. Continue from the repository's steering record and the latest approved checkpoint.”
