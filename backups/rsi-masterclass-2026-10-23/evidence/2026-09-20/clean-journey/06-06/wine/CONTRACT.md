# Frozen experiment contract

- version: 1
- task: wine
- data_sha256: 4a402cf041b025d4566d954c3b9ba8635a3a8a01e039005d97d6a710278cf05e
- tool_sha256: 1febbe8eacac7873d9a09031cc133200e55224e2fea0205c88090eea4bd5b5a0
- max_attempts: 2
- max_fit_seconds: 120
- metric: balanced accuracy
- split: feature-group hash wine-v1: 60/20/20
- label: quality >= 7

The agent can read the public source. This workspace is not a secret evaluation service.
The fit budget excludes agent inference costs; record those separately when available.
Keep rejected and interrupted attempts. Final evaluation closes this workspace to search.
