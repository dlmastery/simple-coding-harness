# Harness reorganization validation

Validation is in progress. This file separates publication checks, offline behavior tests and live integration evidence.

The original README and discovery scripts were backed up before changes. The first offline pass is retained in `validation/before-tests.txt`; many tests could not collect because this environment initially lacked harness dependencies. The environment had no pip module. The failed installer command is retained, followed by the successful `uv pip` installation log. No model key or hosted run was used.

After the move, the test and snippet runners discover `harness/*/step_*/` and retain numeric selectors. New guides and images require a local-link check. Final results will be recorded here before handoff. GenUI and RSI remain separate series.
