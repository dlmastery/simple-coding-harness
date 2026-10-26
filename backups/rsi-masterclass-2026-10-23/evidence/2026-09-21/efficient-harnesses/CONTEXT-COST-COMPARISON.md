# A per-call limit is not a cumulative budget

Read [VideoHarness-RSI version 2, section 4.5](https://arxiv.org/html/2608.24302v2#S4.SS5) and its adjacent cost notes on 21 September 2026. Version 2 is dated 3 September; the original submission was in August.

The source separates a per-invocation visual-frame cap from cumulative answer-time context. Its reported input-token accounting does not cover every search, indexing, output, or monetary cost. Several bounded calls can consume more in total than one bounded call.

Our local ledger makes an analogous accounting distinction: summary subprocesses are a subset of all subprocesses, fit time is inside command time, and derived-report bytes exclude other artifacts. It does not measure model context. Reducing one line in a ledger cannot establish that every other cost fell.
