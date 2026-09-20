# How this RSI course plan was developed

This log records completed actions, findings, decisions, and next steps. It is a concise process record, not a raw chat transcript. Planning date: 19 September 2026.

## Completed work

| Step | Action | Result and implication |
|---|---|---|
| 1 | Captured the user's course objective and constraints | Plan first; implementation follows review. Students use skills and natural language. |
| 2 | Cloned `dlmastery/simple-coding-harness` locally | Initial inspected revision: `eed9cbbdf19c665ae54646253f303be85030798c`. |
| 3 | Decoded the user-provided MHTML transcript locally | Used it to identify claims to check. Raw browser files remain local; a later step archives redacted text. |
| 4 | Inspected the RSI tree, README, skills, hooks, and validation discovery | Found 18 flat lesson directories, a 2,576-line README, duplicated skills, and tests tied to the old directory pattern. |
| 5 | Examined evaluation and execution claims | Identified gaps between role instructions and actual isolation, broad hook checks, and tests that check wording rather than live behavior. |
| 6 | Drafted a themed course plan | Established the progression through processes, loops, graphs, ontology, system intelligence, meta-harnesses, self-* concepts, and RSI. |
| 7 | Expanded named research sequences after user feedback | Added substantial ScientistTwo and ScienceBuddy treatment and corrected details of RSIAgent memory ownership. |
| 8 | Broadened the research search | Added procedure graphs, skill evolution, feedback design, compatibility failures, harness benchmarks, and efficiency studies. |
| 9 | Applied the user's one-month search window | Current inventory covers 20 August–19 September, with the latest two weeks prioritized. Older sources are separate. |
| 10 | Strengthened the teaching and writing requirements | Added clear run instructions, context, key takeaways, quizzes, next steps, plain technical prose, and checks for lasting understanding. |
| 11 | Revised the running task after user feedback | Replaced the provisional handbook task with regression and classification hill climbing. The ML workflow now includes the full data science process. |
| 12 | Checked primary dataset pages | Proposed small UCI Bike Sharing and Wine Quality tasks. Recorded provenance, leakage, split, and label-design issues for implementation. |
| 13 | Added a path to larger compute | Kept laptop defaults while defining compute adapters, budgets, resumption, and evaluation rules for future GPU or cluster jobs. |
| 14 | Recorded the illustration brief | Imagen 2.5 requested; white backgrounds and rich, readable technical illustration. Exact generator access remains unresolved. |
| 15 | Prepared durable planning records | Master plan, research inventory, steering/restart notes, and this work log are ready for a GitHub checkpoint. |
| 16 | Pushed and verified the first checkpoint | Commit `7f6bbd61eb029a307b38525e00beadc57d3535dc` exists on `codex/rsi-masterclass-rebuild`; the remote hash matched the local hash. |
| 17 | Added intermediate provenance | Saved search notes, claim corrections, source hashes, a redacted transcript, the redaction script, and an artifact index. Recorded missing earlier drafts and extraction-command history as gaps. |
| 18 | Created the reusable course-building skill | Full instructions, five references, and agent metadata are versioned under `skills/build-research-codelabs/`. A coverage table maps all user guidance. |
| 19 | Validated the skill and documentation | The skill validator passed after supplying its missing PyYAML dependency. The link checker found a validation file that had not yet been written; the record was added for the next check. |
| 20 | Rechecked links and installed the skill | All 85 local links across 17 Markdown files resolved. All seven installed skill files matched repository hashes; the installed package passed the validator. |
| 21 | Checked the redacted source | Output hash matched the manifest. No email addresses or original forwarded-message identifiers remained under the applied checks. |
| 22 | Pushed the complete skill and provenance checkpoint | Commit `6ae9a411d7dec732debb0293f9817350bc08dc11` was pushed; the remote hash matched local HEAD and the working tree was clean. |

## Why the plan changed

**The course needed missing conceptual steps.** The existing structure introduces machinery before students have a reason to use it. The plan adds explicit transitions and small experiments that expose the need for each mechanism.

**The research search was initially too narrow.** It relied too much on the source transcript and existing course. The wider search uses mechanism families and primary-source dates. Eight new advanced experiments cover distinct ideas that the first plan missed.

**The main task must serve an AI/ML class.** The user rejected a document-handbook example as the central project. Small supervised learning tasks preserve laptop access while making feature search, model search, error analysis, and research improvement meaningful.

**Small demonstrations should not prevent larger work.** The laptop route controls cost and teaching complexity. The compute adapter separates those choices from the research method so students can later run harder jobs without rewriting the conceptual design.

**Visual and writing quality are requirements.** Each lesson needs a clear explanation and a diagram that shows the mechanism. The plan records a concrete editorial and visual review process rather than treating polish as a final decoration pass.

## Evidence and limits

The repository inspection supports the findings in the master plan. It does not establish that every current lab was executed or that every defect has been found.

The research inventory distinguishes metadata checks from method inspection. No selected paper has been reproduced here. No course code, live lab, illustration, or cluster adapter has been built. The raw source remains local; its redacted text derivative is archived with a clear unverified-source notice.

An original X post returned HTTP 403. The linked official benchmark page was accessible. No new Meta/FAIR post-only result in the target month was verified in this pass. These limits are recorded in the inventory.

## Checkpoint procedure

Planning records belong in `how-did-i-generate-it/rsi/`. Use a dedicated working branch. For each meaningful milestone:

1. Update the plan, requirements, and work log where the decision changes them.
2. Inspect the changed files and check links, counts, and status claims.
3. Commit a coherent set of changes with a descriptive message.
4. Push the working branch to GitHub.
5. Compare the local and remote commit hashes before reporting the backup as complete.

Implementation checkpoints should include relevant runtime evidence and failures. Keep expensive or private artifacts out of Git; record their locations and checksums where appropriate. Never commit secrets or the private transcript.

## Next steps

1. The reusable skill is installed and its complete package is on GitHub. Present it with the revised plan for review.
2. After plan approval, complete the remaining source and repository audit.
3. Build representative onboarding, ML loop, ontology, and recursion lessons before expanding the pattern.
4. Validate the laptop path and the declared agent adapters. Record actual resource use.
5. Produce and inspect the requested illustrations after generator access is resolved.
6. Continue through the full course, updating this log and checkpointing progress.
