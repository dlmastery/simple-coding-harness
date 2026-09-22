# Follow the harness from request to reliable execution

[Course](../README.md) · [Start here](START-HERE.md) · [Teaching roadmap](TEACHING-ROADMAP.md) · [Glossary](GLOSSARY.md)

The parent course contains **54 runnable lessons in seven themes**. Original lesson IDs are preserved: stage 2 has four lessons, so the last ID is 51. Each lesson is a code snapshot, not a claim that the entire system has reached production readiness.

![One model call develops into a controlled loop and an inspectable harness.](assets/overview-v1.png)

First understand a request and observation. Then add controls. Compare adapters only after you can say what they own. Add tools, recovery and inspectability before moving the loop behind a service. See the [migration map](MIGRATION.md) if you have an old path.

## 1. From a reply to an agent

A model can describe a file without opening it. A tool gives it an observation. A loop lets that observation change its next action. Begin with one request, then make each new action visible.

**Readiness check:** Follow a tool call from proposal through execution into the next model request. Explain how a saved session differs from the files it describes.

[Theme guide and infographic](01_foundations/README.md)

| Lesson | Source and test |
|---|---|
| [Stage 1 - Minimal chat](01_foundations/step_01_minimal_chat/README.md) | [Files](01_foundations/step_01_minimal_chat/) |
| [Stage 2.1 - Chat with a simple bash tool](01_foundations/step_02_1_bash_tool/README.md) | [Files](01_foundations/step_02_1_bash_tool/) |
| [Stage 2.2 - Generic tools](01_foundations/step_02_2_generic_tools/README.md) | [Files](01_foundations/step_02_2_generic_tools/) |
| [Stage 2.3 - A read_file tool](01_foundations/step_02_3_read_file/README.md) | [Files](01_foundations/step_02_3_read_file/) |
| [Stage 2.4 - The agent loop](01_foundations/step_02_4_agent_loop/README.md) | [Files](01_foundations/step_02_4_agent_loop/) |
| [Stage 3 - Better UI](01_foundations/step_03_better_ui/README.md) | [Files](01_foundations/step_03_better_ui/) |
| [Stage 4 - Skill discovery and reading](01_foundations/step_04_skills/README.md) | [Files](01_foundations/step_04_skills/) |
| [Stage 5 - File editing tools](01_foundations/step_05_file_editing/README.md) | [Files](01_foundations/step_05_file_editing/) |
| [Stage 6 - Late injection](01_foundations/step_06_late_injection/README.md) | [Files](01_foundations/step_06_late_injection/) |
| [Stage 7 - File freshness reminders](01_foundations/step_07_file_freshness/README.md) | [Files](01_foundations/step_07_file_freshness/) |
| [Stage 8 - Sessions, slash commands and rewind](01_foundations/step_08_sessions_rewind/README.md) | [Files](01_foundations/step_08_sessions_rewind/) |

## 2. Keep actions within limits

A useful tool can also make an unwanted change. Add controls that answer separate questions: what work is planned, which actions are permitted, where they execute, and what context each worker receives.

**Readiness check:** Explain why permission, sandboxing, context management and subagents solve different problems.

[Theme guide and infographic](02_control/README.md)

| Lesson | Source and test |
|---|---|
| [Stage 9 - An installable command](02_control/step_09_installable_command/README.md) | [Files](02_control/step_09_installable_command/) |
| [Stage 10 - Todos](02_control/step_10_todos/README.md) | [Files](02_control/step_10_todos/) |
| [Stage 11 - Tool permissions](02_control/step_11_permissions/README.md) | [Files](02_control/step_11_permissions/) |
| [Stage 12 - An OS sandbox for bash](02_control/step_12_sandbox/README.md) | [Files](02_control/step_12_sandbox/) |
| [Stage 13 - Readable todos and a real input line](02_control/step_13_readable_todos_input_line/README.md) | [Files](02_control/step_13_readable_todos_input_line/) |
| [Stage 14 - Compaction and context overflow](02_control/step_14_compaction/README.md) | [Files](02_control/step_14_compaction/) |
| [Stage 15 - Exploration subagents](02_control/step_15_subagents/README.md) | [Files](02_control/step_15_subagents/) |

## 3. Separate the harness from its provider

You now know the mechanisms you need. Compare alternative implementations by asking who owns the loop, tool execution, state and approvals. A shared API shape does not guarantee identical behavior.

**Readiness check:** Explain a provider change as a change of ownership and interfaces, then name what still needs testing.

[Theme guide and infographic](03_adapters/README.md)

| Lesson | Source and test |
|---|---|
| [Step 16 - The same harness on the Claude Agent SDK](03_adapters/step_16_claude_agent_sdk/README.md) | [Files](03_adapters/step_16_claude_agent_sdk/) |
| [Step 17 - The same harness on the OpenAI Agents SDK](03_adapters/step_17_openai_agents_sdk/README.md) | [Files](03_adapters/step_17_openai_agents_sdk/) |
| [Step 18 - The same harness on the Google Antigravity SDK](03_adapters/step_18_google_antigravity_sdk/README.md) | [Files](03_adapters/step_18_google_antigravity_sdk/) |
| [Step 19 - The same harness on DeepSeek Harness (dsh)](03_adapters/step_19_deepseek_harness/README.md) | [Files](03_adapters/step_19_deepseek_harness/) |
| [Step 20 - The same harness on OpenRouter](03_adapters/step_20_openrouter/README.md) | [Files](03_adapters/step_20_openrouter/) |

## 4. Connect tools and observe the work

A loop becomes more useful when it can stream progress, use external tools and coordinate work. More capabilities also create more ways to lose a result or misread a failure. Keep each observation connected to its action.

**Readiness check:** Trace a request through tools, hooks and background work into an evaluation record. Explain what an offline test leaves untested.

[Theme guide and infographic](04_tools/README.md)

| Lesson | Source and test |
|---|---|
| [Step 21 - Streaming and headless mode](04_tools/step_21_streaming_headless/README.md) | [Files](04_tools/step_21_streaming_headless/) |
| [Step 22 - Parallel tool calls](04_tools/step_22_parallel_tools/README.md) | [Files](04_tools/step_22_parallel_tools/) |
| [Step 23 - Browser use](04_tools/step_23_browser_use/README.md) | [Files](04_tools/step_23_browser_use/) |
| [Step 24 - Computer use](04_tools/step_24_computer_use/README.md) | [Files](04_tools/step_24_computer_use/) |
| [Step 25 - Persistent memory](04_tools/step_25_memory/README.md) | [Files](04_tools/step_25_memory/) |
| [Step 26 - MCP client](04_tools/step_26_mcp_client/README.md) | [Files](04_tools/step_26_mcp_client/) |
| [Step 27 - Hooks](04_tools/step_27_hooks/README.md) | [Files](04_tools/step_27_hooks/) |
| [Step 28 - Plan mode and structured output](04_tools/step_28_plan_mode/README.md) | [Files](04_tools/step_28_plan_mode/) |
| [Step 29 - Background jobs and parallel subagents](04_tools/step_29_jobs_parallel_subagents/README.md) | [Files](04_tools/step_29_jobs_parallel_subagents/) |
| [Step 30 - Evaluation harness](04_tools/step_30_eval/README.md) | [Files](04_tools/step_30_eval/) |

## 5. Resume work without guessing

A long task can outlive a terminal or exhaust its context. Instructions, checkpoints and durable records help it continue. The hard case is an action whose effect happened before its completion record was saved.

**Readiness check:** Explain how instructions, context, workspace checkpoints, durable state and human decisions contribute to a recoverable capstone.

[Theme guide and infographic](05_recovery/README.md)

| Lesson | Source and test |
|---|---|
| [Step 31 - Project instruction files](05_recovery/step_31_instruction_files/README.md) | [Files](05_recovery/step_31_instruction_files/) |
| [Step 32 - Context budget](05_recovery/step_32_context_budget/README.md) | [Files](05_recovery/step_32_context_budget/) |
| [Step 33 - Workspace checkpoints and /undo](05_recovery/step_33_checkpoints/README.md) | [Files](05_recovery/step_33_checkpoints/) |
| [Step 34 - Durability and recovery](05_recovery/step_34_durability/README.md) | [Files](05_recovery/step_34_durability/) |
| [Step 35 - Human in the loop](05_recovery/step_35_human_in_the_loop/README.md) | [Files](05_recovery/step_35_human_in_the_loop/) |
| [Step 36 - Orchestration patterns](05_recovery/step_36_orchestration/README.md) | [Files](05_recovery/step_36_orchestration/) |
| [Step 37 - Production harness anatomy](05_recovery/step_37_production_anatomy/README.md) | [Files](05_recovery/step_37_production_anatomy/) |
| [Step 38 - Capstone](05_recovery/step_38_capstone/README.md) | [Files](05_recovery/step_38_capstone/) |

## 6. Make a run inspectable

Production-oriented work needs explicit decisions, stops, handoffs and records that another person can inspect. These lessons add those surfaces to the harness; the word production is a topic, not a readiness certificate.

**Readiness check:** Explain why a run ended, which agent owned the next action, and how the trace supports the account. Compare the Python implementation with the smaller TypeScript core.

[Theme guide and infographic](06_production/README.md)

| Lesson | Source and test |
|---|---|
| [Step 39 - Approval modes](06_production/step_39_approval_modes/README.md) | [Files](06_production/step_39_approval_modes/) |
| [Step 40 - Handoffs](06_production/step_40_handoffs/README.md) | [Files](06_production/step_40_handoffs/) |
| [Step 41 - Stop conditions](06_production/step_41_stop_conditions/README.md) | [Files](06_production/step_41_stop_conditions/) |
| [Step 42 - Streaming tool output](06_production/step_42_streaming_tool_output/README.md) | [Files](06_production/step_42_streaming_tool_output/) |
| [Step 43 - Extensions](06_production/step_43_extensions/README.md) | [Files](06_production/step_43_extensions/) |
| [Step 44 - Replay and trace viewer](06_production/step_44_replay_trace/README.md) | [Files](06_production/step_44_replay_trace/) |
| [Step 45 - The core loop in TypeScript](06_production/step_45_typescript_core/README.md) | [Files](06_production/step_45_typescript_core/) |

## 7. Move the loop behind a service

A client can send a task while a service owns the agent loop. This changes where sessions, tools and approvals live. The client must distinguish a completed turn from a connection that merely ended.

**Readiness check:** Map client/server responsibilities and explain incomplete, cancelled, failed and completed turns without treating them as interchangeable.

[Theme guide and infographic](07_server/README.md)

| Lesson | Source and test |
|---|---|
| [Step 46 - The loop on TrueForge](07_server/step_46_trueforge_loop/README.md) | [Files](07_server/step_46_trueforge_loop/) |
| [Step 47 - Tools and permissions as MCP](07_server/step_47_trueforge_tools_mcp/README.md) | [Files](07_server/step_47_trueforge_tools_mcp/) |
| [Step 48 - Sandbox, skills and code mode](07_server/step_48_trueforge_sandbox_skills/README.md) | [Files](07_server/step_48_trueforge_sandbox_skills/) |
| [Step 49 - Context, questions and stop conditions on TrueForge](07_server/step_49_trueforge_context/README.md) | [Files](07_server/step_49_trueforge_context/) |
| [Step 50 - Subagents, sessions and evaluation on TrueForge](07_server/step_50_trueforge_subagents_eval/README.md) | [Files](07_server/step_50_trueforge_subagents_eval/) |
| [Step 51 - TrueForge versus this codelab versus managed agents](07_server/step_51_trueforge_comparison/README.md) | [Files](07_server/step_51_trueforge_comparison/) |
