# The report improved; the builder did not run

The parent and child each fitted the same wine linear/all seed-17 recipe once. Their prediction files are byte-identical and their balanced accuracy is unchanged at 0.7449552553. Both pass prediction consistency checks. The parent fails the explicit-recall reporting requirement; the child passes with class recalls 0.733812949640 and 0.756097560976.

The change adds a report-completion function to the generated controller and invokes it after its existing prediction check. The shared course runtime and evaluator remain unchanged. The confusion matrix was already correct; the repair makes its two recalls explicit for readers. It does not improve predictive quality.

The exact historical builder skill was recovered from Git commit 3dc2e5dbcaee0686fee766e19dc169638ee056dc. Its SHA-256 matches the existing generated package's provenance. The current builder reference has a later hash; the study does not substitute that version for the historical builder. Neither version ran or changed during the comparison.

The child inherits the parent's package documents, including its historical PROVENANCE.md. That document identifies the parent generation and entry-point hash. CHILD-PROVENANCE.md provides the revised entry identity; it must accompany the child. The package still imports the course runtime. It is not standalone software or an independent reimplementation.

The two executions establish one local report repair under a known task. Source-style creator/executor isolation, withheld feedback, many-task generalization, and generator improvement were not tested. The separate two-brief generator comparison remains an unexecuted proposal. Learner prediction, quiz, and teach-back remain unattempted.
