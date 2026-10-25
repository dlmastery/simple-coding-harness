# Less duplicate reporting, unchanged predictions

All four fits passed the frozen absolute quality requirements and prediction checks. H0 and H1 produced byte-identical prediction files for each task. Bike MAE was 99.1759237869. Wine balanced accuracy was 0.7449552553; class recalls were 0.7338129496 and 0.7560975610. The paired tolerance passed.

| Measurement per task | H0 | H1 | What it means |
|---|---:|---:|---|
| Derived-report tool calls | 3 | 1 | Two duplicate processes removed |
| Bike derived-report bytes | 651 | 217 | 434 fewer bytes in these reports |
| Wine derived-report bytes | 825 | 275 | 550 fewer bytes in these reports |
| Bike arm wall seconds | 3.366569 | 3.186890 | One observation per variant |
| Wine arm wall seconds | 3.208582 | 3.148651 | One observation per variant |

Retain H1 under this protocol: required evidence and quality remain, and report calls/bytes fall. Across both tasks, the added layer goes from six summary calls to two and 1,476 derived bytes to 492. Those figures exclude primary reports, predictions, checks, and archive files. Do not describe them as a two-thirds reduction in total storage, tokens, or research cost.

The small wall-time differences include process startup and machine state. Four fits cannot establish a robust latency advantage. The deterministic reporting layer does not call an LLM, so no provider-token saving was measured. Source reading, proposal design, author inference, implementation, and publication costs are unknown and remain outside the measured driver interval.

The checker-removal fixture failed because it lacked required prediction-check evidence. Its supplied score of one is explicitly a stub value, not a measured model result. This rejected shortcut remains part of the work and cost record. A missing check is not an efficiency win.

The prior development recipes and scores were author-known. No final evaluation, independently isolated evaluator, automated discovery, or recursively cheaper improver was demonstrated. The outcome is a measured, narrow reduction in redundant report work.
