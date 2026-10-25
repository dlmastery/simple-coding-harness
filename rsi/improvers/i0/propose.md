You improve the harness of an ML-engineering agent. The agent is a frozen language
model that writes training scripts for Kaggle competitions in a draft / debug / improve
loop. You cannot change the model. You can only edit its harness files.

The harness will be judged on competitions it has never seen, so prefer changes that
make the agent a better ML engineer in general over changes that only help the
competitions below.

# Current harness ({best})

{harness}

# Every candidate tried so far

{archive}

# Evidence from the current harness on the evolve competitions

{evidence}

# What you may change

- system.md, draft.md, improve.md, debug.md (keep their {placeholders})
- skills/<name>.md: write or delete playbooks; every skill is added to the system prompt
- memory.md, and config.json keys: steps, num_drafts, max_debug, exec_timeout, preview_rows, temperature, max_tokens, memory
- You may NOT change config.model.

# Reply

Diagnose what limits the agent, then reply with one JSON object and nothing after it:

{"hypothesis": "<one sentence: what you expect to improve and why>",
 "edits": [
   {"file": "skills/<name>.md", "action": "write", "content": "<full file>", "why": "<evidence>"},
   {"file": "config.json", "action": "set", "key": "<key>", "value": <value>, "why": "<evidence>"},
   {"file": "<file>", "action": "delete", "why": "<evidence>"}
 ]}

Use at most {budget} edits.
