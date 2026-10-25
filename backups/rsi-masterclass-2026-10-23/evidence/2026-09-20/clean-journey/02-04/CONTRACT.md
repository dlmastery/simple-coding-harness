# Frozen experiment contract

- version: 1
- task: bike
- data_sha256: e03de4ee4ef4dc376ac6e04bf829673c6269e8eba5c60fa121640fa2f829504f
- tool_sha256: 1febbe8eacac7873d9a09031cc133200e55224e2fea0205c88090eea4bd5b5a0
- max_attempts: 2
- max_fit_seconds: 120
- metric: MAE
- split: 2011 / 2012-H1 / 2012-H2
- label: cnt

The agent can read the public source. This workspace is not a secret evaluation service.
The fit budget excludes agent inference costs; record those separately when available.
Keep rejected and interrupted attempts. Final evaluation closes this workspace to search.
