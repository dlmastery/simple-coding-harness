# Words for inspecting a coding agent

[Course](../README.md) · [Every lesson](COURSE-MAP.md) · [Teaching roadmap](TEACHING-ROADMAP.md)

Use a definition when its mechanism appears in your current lesson. Ask what object changed and which observation supports the claim.

| Term | Plain meaning | Example or important distinction |
|---|---|---|
| Model | The component that produces a response from an input | Its statement that a file was read is not an executed file operation |
| Message | One structured piece of a model conversation | A user request or returned tool observation |
| Context | Information supplied to a particular request | It can omit earlier material when the budget is limited |
| Token | A unit used by the model's text representation | Token counts depend on the model and tokenizer |
| Tool call | A proposed operation with arguments | The host still has to validate and execute it |
| Tool result | An observation returned after tool handling | It can report an error; a result is not necessarily success |
| Agent loop | Repeated model decisions and observations with exit conditions | Read a file, inspect the result, then answer |
| Harness | Instructions, tools, state, controls and execution around a model | The surrounding system determines how proposals become actions |
| Skill | A reusable procedure supplied as instructions | A file explaining how to review a module; loading it does not enforce it |
| System prompt | Instructions placed in the system role for a request | It cannot alone create operating-system isolation |
| Late injection | Add current facts near the time they are needed | A fresh file observation enters a later request |
| Prompt cache | Provider-side reuse of supported repeated input computation | It is not a guarantee of identical answers or current file contents |
| File freshness | Whether an observation still describes the current file | Re-read after a relevant edit rather than relying on stale text |
| Session | Saved conversational or execution state | It does not automatically preserve all workspace files |
| Rewind | Restore a supported earlier state | Name whether messages, files or both are restored |
| Permission / approval | A decision about whether an operation may proceed | Allowing a command is separate from limiting its access |
| Sandbox | An enforced boundary around execution | Capabilities and limitations depend on the actual implementation |
| Plan | Intended actions before execution | A checked box is not sufficient evidence that the action happened |
| Compaction | Reduce retained context to fit a budget | Summaries can lose facts; inspect what must survive |
| Subagent | A worker given a scoped task and context | It may still share files or runtime resources with the parent |
| SDK | Software development kit | It can provide mechanisms, but you still need to inspect ownership and behavior |
| Adapter | Code translating between interfaces | Similar response shapes do not prove identical semantics |
| Endpoint | An address exposing an API | A compatible URL does not guarantee every tool or streaming feature |
| Streaming | Receive output incrementally | The last visible text is not necessarily a terminal status |
| Headless | Run without an interactive interface | Results and stopping conditions still need a usable record |
| Parallelism | Operations overlap in execution | Shared writes can create conflicts even if requests are independent |
| MCP | Model Context Protocol | A protocol for exposing capabilities; it does not decide all authorization policy |
| Hook | Code triggered at a defined lifecycle event | A hook must actually run to affect the action |
| Background job | Work that continues outside the current interaction | Track its identity, outcome and resource use |
| Evaluation | Compare observed behavior with declared criteria | Passing chosen cases does not establish all future behavior |
| Instruction file | Project guidance loaded by the harness | Inspect which files were found and how conflicts were handled |
| Checkpoint | Saved state for a supported restore or resume | Know which objects were captured and which were not |
| Durability | State survives an interruption within stated guarantees | Saving an intent does not prove the intended external effect happened |
| Idempotence | Repeating an operation has the same relevant effect as doing it once | Appending a line twice generally does not have that property |
| Reconciliation | Compare saved intent with observed effects before deciding what follows | Inspect a file after an interrupted write before blindly retrying |
| Human in the loop | A person makes specified decisions during work | Name which decision and what information they receive |
| Orchestration | Coordinate dependencies, workers and transitions | A pipeline chooses what is ready to run next |
| Handoff | Transfer responsibility with the required state | A new role name alone does not supply missing context |
| Stop condition | A rule that ends or suspends work | Completion, budget exhaustion and cancellation differ |
| Extension | A supported addition to the harness | Loading an extension expands behavior and needs its own checks |
| Trace | Recorded events from a run | A retrospective story is not the same evidence as recorded events |
| Replay | Read or process a saved sequence | Displaying a tool result again does not re-execute its operation |
| Terminal event | A signal that declares how a turn ended | Without it, a dropped stream can leave status incomplete |
| Fake / test double | Controlled replacement for an external dependency | Useful for contract checks, not evidence that the real service works |
| Capstone | An integrated task demonstrating several course capabilities | Preserve failures and limits, not only a final successful screenshot |

Try this distinction: a model proposes a command, the policy permits it, the executor starts it, and the connection drops. Which of those facts establishes completion? None alone. Inspect the actual effect and the relevant completion record. Revisit the [recovery theme](05_recovery/README.md) and [service theme](07_server/README.md).
