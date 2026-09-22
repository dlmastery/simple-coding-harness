# Find a lesson after the move

[Course](../README.md) · [Every lesson](COURSE-MAP.md)

The lesson IDs and implementations are preserved. The folders now live inside themes. Numeric commands such as `python run_tests.py 14 15` still run from the repository root. The full harness selector is `python run_tests.py harness`. An old bookmark to a root-level lesson may need the new path below; GitHub does not redirect file moves automatically.

The original long README is [backed up](../how-did-i-generate-it/harness/backups/README-before-reorganization.md) exactly as it was. Its old paths describe the historical layout. Use this map for current locations. The executable code remains beside each current lesson.

| Original root directory | Current lesson |
|---|---|
| `step_01_minimal_chat/` | [Stage 1 - Minimal chat](01_foundations/step_01_minimal_chat/README.md) |
| `step_02_1_bash_tool/` | [Stage 2.1 - Chat with a simple bash tool](01_foundations/step_02_1_bash_tool/README.md) |
| `step_02_2_generic_tools/` | [Stage 2.2 - Generic tools](01_foundations/step_02_2_generic_tools/README.md) |
| `step_02_3_read_file/` | [Stage 2.3 - A read_file tool](01_foundations/step_02_3_read_file/README.md) |
| `step_02_4_agent_loop/` | [Stage 2.4 - The agent loop](01_foundations/step_02_4_agent_loop/README.md) |
| `step_03_better_ui/` | [Stage 3 - Better UI](01_foundations/step_03_better_ui/README.md) |
| `step_04_skills/` | [Stage 4 - Skill discovery and reading](01_foundations/step_04_skills/README.md) |
| `step_05_file_editing/` | [Stage 5 - File editing tools](01_foundations/step_05_file_editing/README.md) |
| `step_06_late_injection/` | [Stage 6 - Late injection](01_foundations/step_06_late_injection/README.md) |
| `step_07_file_freshness/` | [Stage 7 - File freshness reminders](01_foundations/step_07_file_freshness/README.md) |
| `step_08_sessions_rewind/` | [Stage 8 - Sessions, slash commands and rewind](01_foundations/step_08_sessions_rewind/README.md) |
| `step_09_installable_command/` | [Stage 9 - An installable command](02_control/step_09_installable_command/README.md) |
| `step_10_todos/` | [Stage 10 - Todos](02_control/step_10_todos/README.md) |
| `step_11_permissions/` | [Stage 11 - Tool permissions](02_control/step_11_permissions/README.md) |
| `step_12_sandbox/` | [Stage 12 - An OS sandbox for bash](02_control/step_12_sandbox/README.md) |
| `step_13_readable_todos_input_line/` | [Stage 13 - Readable todos and a real input line](02_control/step_13_readable_todos_input_line/README.md) |
| `step_14_compaction/` | [Stage 14 - Compaction and context overflow](02_control/step_14_compaction/README.md) |
| `step_15_subagents/` | [Stage 15 - Exploration subagents](02_control/step_15_subagents/README.md) |
| `step_16_claude_agent_sdk/` | [Step 16 - The same harness on the Claude Agent SDK](03_adapters/step_16_claude_agent_sdk/README.md) |
| `step_17_openai_agents_sdk/` | [Step 17 - The same harness on the OpenAI Agents SDK](03_adapters/step_17_openai_agents_sdk/README.md) |
| `step_18_google_antigravity_sdk/` | [Step 18 - The same harness on the Google Antigravity SDK](03_adapters/step_18_google_antigravity_sdk/README.md) |
| `step_19_deepseek_harness/` | [Step 19 - The same harness on DeepSeek Harness (dsh)](03_adapters/step_19_deepseek_harness/README.md) |
| `step_20_openrouter/` | [Step 20 - The same harness on OpenRouter](03_adapters/step_20_openrouter/README.md) |
| `step_21_streaming_headless/` | [Step 21 - Streaming and headless mode](04_tools/step_21_streaming_headless/README.md) |
| `step_22_parallel_tools/` | [Step 22 - Parallel tool calls](04_tools/step_22_parallel_tools/README.md) |
| `step_23_browser_use/` | [Step 23 - Browser use](04_tools/step_23_browser_use/README.md) |
| `step_24_computer_use/` | [Step 24 - Computer use](04_tools/step_24_computer_use/README.md) |
| `step_25_memory/` | [Step 25 - Persistent memory](04_tools/step_25_memory/README.md) |
| `step_26_mcp_client/` | [Step 26 - MCP client](04_tools/step_26_mcp_client/README.md) |
| `step_27_hooks/` | [Step 27 - Hooks](04_tools/step_27_hooks/README.md) |
| `step_28_plan_mode/` | [Step 28 - Plan mode and structured output](04_tools/step_28_plan_mode/README.md) |
| `step_29_jobs_parallel_subagents/` | [Step 29 - Background jobs and parallel subagents](04_tools/step_29_jobs_parallel_subagents/README.md) |
| `step_30_eval/` | [Step 30 - Evaluation harness](04_tools/step_30_eval/README.md) |
| `step_31_instruction_files/` | [Step 31 - Project instruction files](05_recovery/step_31_instruction_files/README.md) |
| `step_32_context_budget/` | [Step 32 - Context budget](05_recovery/step_32_context_budget/README.md) |
| `step_33_checkpoints/` | [Step 33 - Workspace checkpoints and /undo](05_recovery/step_33_checkpoints/README.md) |
| `step_34_durability/` | [Step 34 - Durability and recovery](05_recovery/step_34_durability/README.md) |
| `step_35_human_in_the_loop/` | [Step 35 - Human in the loop](05_recovery/step_35_human_in_the_loop/README.md) |
| `step_36_orchestration/` | [Step 36 - Orchestration patterns](05_recovery/step_36_orchestration/README.md) |
| `step_37_production_anatomy/` | [Step 37 - Production harness anatomy](05_recovery/step_37_production_anatomy/README.md) |
| `step_38_capstone/` | [Step 38 - Capstone](05_recovery/step_38_capstone/README.md) |
| `step_39_approval_modes/` | [Step 39 - Approval modes](06_production/step_39_approval_modes/README.md) |
| `step_40_handoffs/` | [Step 40 - Handoffs](06_production/step_40_handoffs/README.md) |
| `step_41_stop_conditions/` | [Step 41 - Stop conditions](06_production/step_41_stop_conditions/README.md) |
| `step_42_streaming_tool_output/` | [Step 42 - Streaming tool output](06_production/step_42_streaming_tool_output/README.md) |
| `step_43_extensions/` | [Step 43 - Extensions](06_production/step_43_extensions/README.md) |
| `step_44_replay_trace/` | [Step 44 - Replay and trace viewer](06_production/step_44_replay_trace/README.md) |
| `step_45_typescript_core/` | [Step 45 - The core loop in TypeScript](06_production/step_45_typescript_core/README.md) |
| `step_46_trueforge_loop/` | [Step 46 - The loop on TrueForge](07_server/step_46_trueforge_loop/README.md) |
| `step_47_trueforge_tools_mcp/` | [Step 47 - Tools and permissions as MCP](07_server/step_47_trueforge_tools_mcp/README.md) |
| `step_48_trueforge_sandbox_skills/` | [Step 48 - Sandbox, skills and code mode](07_server/step_48_trueforge_sandbox_skills/README.md) |
| `step_49_trueforge_context/` | [Step 49 - Context, questions and stop conditions on TrueForge](07_server/step_49_trueforge_context/README.md) |
| `step_50_trueforge_subagents_eval/` | [Step 50 - Subagents, sessions and evaluation on TrueForge](07_server/step_50_trueforge_subagents_eval/README.md) |
| `step_51_trueforge_comparison/` | [Step 51 - TrueForge versus this codelab versus managed agents](07_server/step_51_trueforge_comparison/README.md) |
