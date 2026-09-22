# Read actions and facts as different kinds of statement

An action graph answers **what must happen before something else**. A domain relation answers **what a named object means or is allowed to use**. Both matter in the same experiment.

![An execution graph beside selected domain relations](../../../assets/illustrations/graph-ontology-v1.png)

[Open the illustration at full size](../../../assets/illustrations/graph-ontology-v1.png).

The workflow panel orders inspection, split validation, fitting and result checking. The domain panel names permitted data and measurement relationships. The figure shows selected facts, not every constraint or an executed run.

| Declared fact | Read it as a sentence |
|---|---|
| model uses feature hr | The model receives hour-of-day as an input. |
| scaler fit on train | The scaler learns its statistics from training rows. |
| search selects on selection | Search uses selection results to choose a candidate. |
| model measured by MAE | MAE defines the error measurement. |
| model predicts cnt | The model estimates the rental count for one hour. |

“Model” appears in both views. **Fit model** is an action. **Model measured by MAE** is a fact about an object and its measurement. Putting fitting before checking does not make the metric appropriate. Writing a correct metric fact does not prove that the checker ran.

The [five-fact input](04-02/DOMAIN.md) passes the [supplied checker](04-02/valid-CHECK.md). It permits seven relation names: uses feature, derived from, fit on, selects on, measured by, predicts and evaluated on. Its three invariants reject a directly target-derived feature, a fit-on partition other than train, and selection on final.

The [unknown relation](04-02/unknown-CHECK.md) fails. The [copy omitting target derivation](04-02/omitted-CHECK.md) passes. The tool does not infer missing facts, follow arbitrary derivation chains, establish units, choose an appropriate metric, or inspect whether real execution matches the table. A pass therefore has a precise limit.

The [original editable Mermaid draft](04-02/EXPLANATIONS.md) is retained. GitHub stacked its panels in the inspected narrow viewport; its original positional wording is superseded by this guide. Refer to the panel names when discussing that draft.
