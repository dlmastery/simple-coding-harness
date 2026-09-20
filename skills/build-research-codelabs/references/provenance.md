# Provenance and restart

## Record the whole project

Before replacing an existing course or README, preserve the original version. Record its Git commit and create an explicit, easy-to-find backup of the original README and tracked course directory under the provenance directory. Verify the copied file against its original identity. Keep backups separate from the current learning path. If work has already begun, extract the authentic pre-rewrite version from history and state when the explicit backup was created; never imply that a later extraction happened earlier. Preserve uncommitted original work separately when present. Add the backup link to the artifact index and include it in the authorized checkpoint.

The user wants the intermediate work as well as the finished course. Use `how-did-i-generate-it/<topic>/` in the authorized repository. Its README is a readable index, not a second copy of every document.

Keep these records:

| Record | Content |
|---|---|
| Steering | User requirements, accepted corrections, approvals, decisions, unresolved questions, and final outcome |
| Plan | Learning path, task choice, architecture, lesson map, research integration, implementation steps, and acceptance criteria |
| Research | Dated queries, source index, paper cards, claim checks, corrections, exclusions, and reading status |
| Work log | What was done, why it changed, what was learned, what was checked, and the next action |
| Artifact index | Each intermediate and final artifact, its purpose, source inputs, version or hash, and status |
| Lab source index | Direct links to each lab intent, procedure, canonical skills, and maintained authoring source; distinguish these from learner inputs and execution outputs |
| Validation | Exact checks, environment and versions, outputs, failures, fixes, resource measurements, and limitations |
| Restart | Current branch, checkpoint, work in progress, next step, and known blockers |

Preserve drafts, alternatives that affected a decision, review comments, representative runs, failed experiments, generated assets and their prompts, inspection notes, and implementation plans. Explain decisions concisely with evidence. A work log does not require private internal reasoning or a verbatim chat dump.

Git history can preserve successive text drafts. If a discarded draft existed before versioning, save it when still available. Do not reconstruct a missing draft and present it as original. Mark gaps honestly. Avoid silently overwriting provenance.

## Sources and sensitive material

Public provenance must not expose credentials, authentication state, unrelated personal details, private browser metadata, or material whose sharing is not authorized. For an affected source, retain the original in its permitted location and check in a redacted extract, checksum, source description, and redaction reason. Make exclusions visible in the artifact index.

Do not copy entire copyrighted papers or websites merely to make the record look complete. Preserve links, versions, hashes where available, and original analysis. For large files, use Git LFS or an authorized artifact store with a checked-in manifest and retrieval instructions. Do not represent a missing file as stored.

## Checkpoints

When the user authorizes GitHub check-ins to the named repository, commit and push at meaningful milestones. Include intermediate project artifacts, not just polished outputs. Checkpoint before a large phase change and at the end of a working session.

For each checkpoint:

1. Update steering, work log, artifact index, and restart state.
2. Inspect the diff for accidental content, missing artifacts, and unsupported status claims.
3. Run checks appropriate to the change. Save useful results.
4. Commit a coherent milestone with a descriptive message.
5. Push the authorized working branch without rewriting unrelated history.
6. Verify that the remote hash matches the local commit.

A local commit is not a GitHub backup. If a push fails, preserve local work, record the error, and report the actual state. Do not keep claiming that work is checked in remotely.

Do not infer permission to publish into a new repository, merge a branch, buy compute, or send messages to other people. Honor existing authorization without repeatedly requesting it. Planning approval and publication authority are distinct from course implementation approval.

## Resume correctly

Read the latest steering and work log before restarting. Check Git status and recent commits. Preserve existing work. Determine whether the plan was approved and whether later instructions supersede earlier proposals.

Continue from the next recorded action. Re-run a check only when changes, failures, environment drift, or missing evidence justify it. Keep completed research and validation distinguishable from planned work. Update the record as part of the work rather than relying on chat memory.
