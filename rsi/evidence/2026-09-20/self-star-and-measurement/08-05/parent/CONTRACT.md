# Frozen experiment contract

- version: 1
- task: wine
- data_sha256: 4a402cf041b025d4566d954c3b9ba8635a3a8a01e039005d97d6a710278cf05e
- tool_sha256: d69d3fbd8a4ace3e0332f4dfbc9a2648f87f858867229db63bc854f7810120a0
- max_attempts: 2
- max_fit_seconds: 120
- metric: balanced accuracy
- split: feature-group hash wine-v1: 60/20/20
- label: quality >= 7

The agent can read the public source. This workspace is not a secret evaluation service.
The fit budget excludes agent inference costs; record those separately when available.
Keep rejected and interrupted attempts. Final evaluation closes this workspace to search.
