# Audit the historical duplicate and budget stops

The 02.04 request trace records four requests: linear, tree, linear again, then forest; all use calendar features and seed 17. The first two are admitted. The third returns the duplicate reason with attempts staying at two. The fourth is a distinct recipe but returns exhausted budget, again with no new attempt. Only two successful fitted candidates appear in the ledger; refused requests have no fabricated score.

The preserved controller hash matches its controller contract: b3a398c89c673bbeccad73da1a5111caf927c0f41bb392f70eeae7f23092eb1e. Its source checks task/model/features/seed duplication before calling the fit operation. The controller contract fixes its own source and limit; the experiment contract separately fixes the underlying tool. Together those records bind the recipe comparison to the recorded tool version. This is a cooperative local check, not an adversarial signature.

This written stop-rule explanation was produced during reconciliation. It does not pretend to be the original missing LOOP.md. The original source, contract, command outputs and request rows provide the earlier behavior evidence. The historical controller returns exit 1 for refusal, whereas today's direct experiment CLI returns 2; the records must be interpreted under the command actually run.

Six read-only historical checks pass. INTENTIONAL-REPLICATION.md supplies the required separate-purpose explanation without another fit. A stochastic or reproducibility study needs an explicit new protocol; changing a refusal label after an accidental repeat would not create one.
