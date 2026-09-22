# Derived scoring correction; zero additional fits

Original workspace: rsi-work-2026-09-22-headroom-v1

The pilot adapter did not enforce the existing course's nonnegative-count rule. This mismatch was found after development results were observed. Every bike prediction is clipped at zero, irrespective of its model or score. Other tasks retain their raw predictions. Original evidence is preserved separately. Fit and process times in this copy describe the original executions, not new training. The raw source snapshot describes training; correct_headroom_counts.py describes this transformation. Both raw and corrected analyses are retained. No final evaluation or positive RSI result is implied.
