# One additional seed, two new fits

Before either follow-up fit, freeze forest/all and linear/all with seed 29. Keep all other supplied recipe settings, preprocessing, training dates, selection dates, clipping, and MAE unchanged. Fit each once in a fresh workspace allocated two attempts. Check both saved prediction files.

Primary observation: the sign and size of forest MAE minus linear MAE at seed 29. If it is negative, say the forest advantage repeats at this second seed. If zero or positive, say the original advantage did not repeat. Retain both outcomes and do not try a third seed within this allocation.

The linear recipe has no random component affected by this seed, so its result should match the earlier linear result; verify it rather than assuming it. The follow-up addresses one seed sensitivity concern, not new-data generalization. No confidence interval or statistical significance is estimated from these two paired observations. No final model evaluation occurs.
