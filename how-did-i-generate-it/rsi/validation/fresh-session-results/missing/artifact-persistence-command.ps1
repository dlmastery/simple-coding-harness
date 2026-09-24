try { [Console]::OutputEncoding=[System.Text.Encoding]::UTF8 } catch {}
$invokedDefinition = $MyInvocation.MyCommand.Definition
$output = 'C:\Users\abhir\Documents\Codex\2026-09-19\lo\work\rsi-fresh-missing-2026-09-23'
if (Test-Path -LiteralPath $output) { throw 'Refusing: output directory already exists.' }
New-Item -ItemType Directory -Path $output -ErrorAction Stop | Out-Null
Set-Content -LiteralPath (Join-Path $output 'FINDINGS.md') -Value '# Fresh-session missing-input inspection

Status: inspection complete; scientific execution blocked by missing inputs. Zero model fits, zero metric computations, and zero data reads. This was a maintenance test.

## Evidence and actual source reads

Only these source files were read:
- `C:\Users\abhir\Documents\Codex\2026-09-19\lo\work\simple-coding-harness\how-did-i-generate-it\rsi\validation\fresh-session-plan\missing-task\HANDOFF.md` (630 bytes; text read once).
- `C:\Users\abhir\Documents\Codex\2026-09-19\lo\work\simple-coding-harness\how-did-i-generate-it\rsi\validation\fresh-session-plan\missing-task\BASELINE-SKILL.md` (539 bytes; text read once and bytes hashed twice).

Recursive directory metadata listing showed exactly these two files and no subdirectories. TASK.md presence was checked twice and returned false. No file outside this packet was read. Output-path existence checks inspected metadata only.

Expected and actual skill SHA-256 both equal:
`210bed6c0528855a878771f8c8c9acd635a7af1da38ab6f8d15a9ab1946e1d2b`.
The initial hash command''s output was lost to PowerShell table formatting; the subsequent JSON command exposed the hash and a true comparison.

## Missing scientific inputs and controlled choices

| Missing input | Choices that cannot be established |
| --- | --- |
| TASK.md | Exact scientific task, target and units, selection metric and formula, split definitions and boundaries, allowed candidate configuration, acceptance requirements, and expected evaluation row identities. |
| Pinned data card and dataset reference | Dataset identity/version/checksum, provenance, schema, target and timestamp interpretation, data location, permitted columns, exclusions, and leakage restrictions. No dataset is present in the packet. |
| Course tool instructions | Approved tool entry points, invocation and configuration format, inspection procedure, how a permitted fit would be run, output contracts, and how source targets and expected row identities would be obtained for independent metric recomputation. |

These are the categories left unspecified by the supplied skill, not a reconstruction of any missing document''s contents. Even the exact filenames/locations of the pinned data card and course tool instructions are unspecified. The task-specific missing documents may allocate details differently; no such allocation was assumed.

Known skill constraints: a reproducible bike baseline; seed 17; one constant/calendar candidate; preserve metric, split, target and data; refuse leaked inputs; independently recompute selection metric; retain failures and progress. The inspection handoff overrides the skill''s fit step: this test requires zero fits. A seed and candidate family alone do not establish a runnable scientific protocol. No default target, metric, split, data source, candidate parameters or tool command was invented.

## Host context and isolation limits

Visible host context included:
- The delegated NEW_TASK message with the exact allowed input directory and output directory; fresh-session maintenance-test purpose; inspection-only/zero-fit restriction; prohibition on reading other packets, repository task/evidence/tool files, previous results or parent records; no publishing, spawning/delegation or contacting others; required missing-input, file-read, hash, command and progress reporting.
- Explicit instruction that learner prediction and quiz responses were not supplied and must be skipped, and that the shared filesystem is a procedural boundary rather than security isolation.
- Environment context: cwd `C:\Users\abhir\Documents\Codex\2026-09-19\lo`, PowerShell 7.6, date 2026-09-23, America/Los_Angeles timezone, and listed workspace roots.
- Generic system/developer operating instructions, tool descriptions, skill names/descriptions/paths, installed-capability descriptions, recommended plugin names, collaboration-role instructions, and unrestricted filesystem/network availability. Those catalogs were visible contextual metadata; their referenced skill files and resources were not opened.
- No parent conversation, prior run records, learner answers, dataset, task specification, metric result or candidate result was visible.

This is procedural isolation on a shared filesystem, not a security-isolated sandbox or a claim of zero host context. No parent or external tools were used to recover absent choices.

## Learner activities

Prediction: skipped — maintenance test; no learner response supplied.
Quiz: skipped — maintenance test; no learner response supplied.
No learner responses or scores were fabricated.

## Stop condition

Inspection stopped after establishing the packet''s insufficiency. Scientific work cannot resume from this packet without the missing task specification, pinned data card/data reference, and course tool instructions. No attempt was made to obtain them elsewhere.
' -Encoding utf8 -NoNewline
Set-Content -LiteralPath (Join-Path $output 'PROGRESS.md') -Value '# PROGRESS

- [x] Refused reuse by checking that the requested output path did not exist, then using a create-only directory operation.
- [x] Read HANDOFF.md and BASELINE-SKILL.md from the authorized missing-task packet.
- [x] Enumerated packet metadata and verified the skill SHA-256.
- [x] Established that required scientific inputs are missing.
- [x] Recorded actual source reads, host context, commands/results and scientific choices left unresolved.
- [x] Marked learner prediction and quiz skipped; no responses supplied.
- [x] Stopped after inspection.
- Model fits: **0**.
- Data reads: **0**.
- Metric computations: **0**.
- Repository edits, publication, delegation and external contact: **0**.
- Scientific execution status: **blocked by missing inputs**.
- Maintenance inspection status: **complete**.

Outputs: FINDINGS.md, PROGRESS.md, command-log.json, artifact-persistence-command.ps1.
' -Encoding utf8 -NoNewline
$journal = @(ConvertFrom-Json -InputObject '[{"sequence":1,"command":"$packet = ''C:\\Users\\abhir\\Documents\\Codex\\2026-09-19\\lo\\work\\simple-coding-harness\\how-did-i-generate-it\\rsi\\validation\\fresh-session-plan\\missing-task''; $output = ''C:\\Users\\abhir\\Documents\\Codex\\2026-09-19\\lo\\work\\rsi-fresh-missing-2026-09-23''; if (Test-Path -LiteralPath $output) { throw ''Refusing: output directory already exists.'' }; Get-Content -LiteralPath (Join-Path $packet ''HANDOFF.md'') -Raw; Get-Content -LiteralPath (Join-Path $packet ''BASELINE-SKILL.md'') -Raw","result":{"exit_code":0,"chunk_id":"ac9dba","summary":"Output absent. Read both files verbatim. Handoff requires hash verification and missing-input inspection; baseline references TASK.md, pinned data card and course tool instructions."}},{"sequence":2,"command":"$packet = ''C:\\Users\\abhir\\Documents\\Codex\\2026-09-19\\lo\\work\\simple-coding-harness\\how-did-i-generate-it\\rsi\\validation\\fresh-session-plan\\missing-task''; Get-ChildItem -LiteralPath $packet -Force -Recurse | Select-Object FullName,PSIsContainer,Length; Get-FileHash -LiteralPath (Join-Path $packet ''BASELINE-SKILL.md'') -Algorithm SHA256; [pscustomobject]@{TaskPresent = Test-Path -LiteralPath (Join-Path $packet ''TASK.md''); PinnedDataCardSpecifiedByHandoff = $false; CourseToolInstructionsSpecifiedByHandoff = $false} | ConvertTo-Json","result":{"exit_code":0,"chunk_id":"12b0df","summary":"PowerShell table formatting truncated paths and did not expose hash; not used as hash evidence. TASK.md existence check returned false. Two specified-by-handoff fields were analyst-supplied classifications, not filesystem checks."}},{"sequence":3,"command":"$packet = ''C:\\Users\\abhir\\Documents\\Codex\\2026-09-19\\lo\\work\\simple-coding-harness\\how-did-i-generate-it\\rsi\\validation\\fresh-session-plan\\missing-task''; $inventory = @(Get-ChildItem -LiteralPath $packet -Force -Recurse | Select-Object FullName,PSIsContainer,Length); $skillHash = Get-FileHash -LiteralPath (Join-Path $packet ''BASELINE-SKILL.md'') -Algorithm SHA256; [pscustomobject]@{Inventory = $inventory; SkillHash = $skillHash.Hash.ToLowerInvariant(); ExpectedSkillHash = ''210bed6c0528855a878771f8c8c9acd635a7af1da38ab6f8d15a9ab1946e1d2b''; HashMatches = ($skillHash.Hash -eq ''210bed6c0528855a878771f8c8c9acd635a7af1da38ab6f8d15a9ab1946e1d2b''); TaskPresent = Test-Path -LiteralPath (Join-Path $packet ''TASK.md'')} | ConvertTo-Json -Depth 5","result":{"exit_code":0,"chunk_id":"d0113c","inventory":[{"FullName":"C:\\Users\\abhir\\Documents\\Codex\\2026-09-19\\lo\\work\\simple-coding-harness\\how-did-i-generate-it\\rsi\\validation\\fresh-session-plan\\missing-task\\BASELINE-SKILL.md","PSIsContainer":false,"Length":539},{"FullName":"C:\\Users\\abhir\\Documents\\Codex\\2026-09-19\\lo\\work\\simple-coding-harness\\how-did-i-generate-it\\rsi\\validation\\fresh-session-plan\\missing-task\\HANDOFF.md","PSIsContainer":false,"Length":630}],"SkillHash":"210bed6c0528855a878771f8c8c9acd635a7af1da38ab6f8d15a9ab1946e1d2b","HashMatches":true,"TaskPresent":false}}]')
Set-Content -LiteralPath (Join-Path $output 'artifact-persistence-command.ps1') -Value $invokedDefinition -Encoding utf8 -NoNewline
$journal += [pscustomobject]@{sequence=4; command_file='artifact-persistence-command.ps1'; result='Create-only output directory succeeded; FINDINGS.md and PROGRESS.md written; exact persistence script recorded; command log written next. No additional input files read.'}
$journal | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $output 'command-log.json') -Encoding utf8
[pscustomobject]@{OutputDirectory=$output; FilesWritten=@('FINDINGS.md','PROGRESS.md','command-log.json','artifact-persistence-command.ps1'); PersistenceCommandCharacters=$invokedDefinition.Length; ModelFits=0; InspectionComplete=$true} | ConvertTo-Json -Depth 3