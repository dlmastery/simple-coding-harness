# CI inspected on 22 September

Inspected commit: 2c07c602e844cc6564f5c6b69d618a59f5579a3d. This is the published saved-reuse checkpoint, before the research-refresh edits.

[RSI course run](https://github.com/dlmastery/simple-coding-harness/actions/runs/35709437793): completed, success.

- CPU checks (macos-latest, Python 3.12): success
- CPU checks (windows-latest, Python 3.12): success
- CPU checks (ubuntu-latest, Python 3.12): success

The workflow installs the documented requirements, checks runtime behavior and links, checks snippet discovery, rebuilds lesson pages, refreshes guidance/activity inventories, and rejects stale generated pages. This establishes those automated checks, not learner comprehension, every codelab session, paper reproduction, or remote compute support.

[Separate repository tests](https://github.com/dlmastery/simple-coding-harness/actions/runs/35709437801): completed; conclusion: failure. The [filtered log excerpt](CI-2026-09-22-REPOSITORY-FAILURE.txt) includes TrueForge pagination failures (`SyncPager.data`) and GenUI operation-object expectations. These concern other course series. The excerpt is not a complete classification of every repository failure. No workflow was restarted or suppressed.

Local research-refresh checks: lesson generation, guidance inventory and activity inventory completed; the publication checker found 101 lessons, 5,589 local links and zero problems. Runtime code was not changed by this refresh.
