# Training behind the compatibility analogy

Read on 21 September 2026: [primary paper v1](https://arxiv.org/html/2609.09134v1), sections 3.1–3.4 and appendices A–B. Selected-method reading; no reproduction.

The study compares full expert-trajectory imitation with correction of a failed turn in the weaker model's own rollout. It examines seven enterprise tasks using Qwen3-Coder-30B-A3B-Instruct and Gemma-4-26B-A4B-IT, with Gemini-3.1-Pro-Preview as expert. The diagnosis concerns planning compatibility, beyond field names.

Appendix B describes successful-trajectory imitation data and roughly 500 correction-training rows, including corrected failures and self-passing examples. Its component counts are approximate. LoRA uses ranks 16 or 64, two epochs, learning rate 0.0001, bf16, and effective batch eight. Context length is 49,152, extended to 98,304 under its truncation rule.

Section 3.1 names H100/H200 GPUs. Appendix B explicitly assigns two H200 GPUs to serving merged checkpoints; this does not specify two-GPU training for every run. A faithful comparison needs documented training allocation, rollout generation, correction selection, fixed evaluation splits, multiple seeds, and total costs. The laptop exercise supplies none of those training measurements. It tests one parser against four reports.
