# Numerical illustration

Four enumerated actions; initial logits zero. The policy is softmax. With fixed advantages A, maximize J(theta) = mean_i A_i log p_i(theta) by one gradient-ascent step of size 0.4. Advantages use population spread plus 1e-8. The analytic gradient is (A_i - p_i sum_j A_j)/4. Each case includes a central finite-difference check with step 1e-6.

These are hand-specified rewards and an actual small numerical calculation. No text trajectories, pretrained model, token objective, ratio clipping, reference policy, sampled KL term, or optimizer loop are implemented. No LLM weights or checkpoint exist.
