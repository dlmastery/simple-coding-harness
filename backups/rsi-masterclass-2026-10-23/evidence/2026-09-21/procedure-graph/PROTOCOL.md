# Procedure-graph verification protocol

Author walkthrough for lab 10.28, 21 September 2026. No learner participates and no paper reproduction or model training is intended.

Use a new sibling workspace. Save the protocol, source snapshot, parent graph, domain facts, and fixtures before execution. The runner must read the Markdown graph rather than select a route from a version name.

Budget: one transition edit and four fixture checks. The first two compare parent and child, so six graph traversals are allowed in total: two parent traces, two child selection traces, one frozen later fixture, and one frozen semantic fixture. Every fit operation is an explicit stub. Domain audits are subprocess checks, not model fits.

The parent mistakenly routes a failed input-type check to the fit stub. The candidate changes only that edge to diagnosis. Selection cases are a nonnumeric hour and a valid calendar row. Capture parent success/failure traces before recording the edit. Accept only if the invalid case avoids the fit stub and the valid case still reaches reporting.

Save the chosen graph hash before constructing the later fixture (a different calendar row) and the numeric target-component fixture. The latter must pass the type check but fail the unchanged supplied domain audit. These are author-constructed cases in one context, not a blinded or statistical generalization test.

Persist each node's inputs, action, completion condition, and neighboring edges before performing its action. Retain all paths, stub calls, audit exit statuses, timing, source identities, and rejected outcomes. Verify the frozen graph hash after both later checks. Stop on any mismatch. No extra proposals or budget extension.

The supplied domain tool uses declared facts; it does not infer all real-world semantics from column names. Its fixed scope and trust boundary remain unchanged.
