# Verification audit — matched UDP diagnostic

Rechecked on 2026-10-15 against the compressed raw archive and frozen checkpoints. All 3,600 observations, posterior updates, masked policy probability vectors and selected actions passed reconstruction. The archive contains 120 run keys, each with exactly 30 uniquely indexed attempts. All seven published artifact SHA-256 checksums match.

Independent arithmetic reproduced attention delivery 0.8538888889, MLP delivery 0.3222222222, difference 0.5316666667, t-based 95% CI [0.3531000939, 0.7102332395], and paired two-sided p = 1.2463795283e-6. A supplementary 200,000-draw paired sign-flip sensitivity calculation, seed 91015, gave Monte Carlo p approximately 0.000020. That exploratory check was added after outcomes and is not a prespecified endpoint.

Attention performed better in 21 fixtures, tied in 8, and worse in 1. Both architectures initially selected the faulty relay in 56 of their 60 target scenarios. Unequal initial exposure therefore does not explain the reported delivery contrast.

The two fault targets coincide in 26 of the 30 fixtures. There are only 34 distinct topology/target combinations, evaluated by two policies, although the experiment executed all 120 runs. The inferential unit remains 30 fixtures, with target strata averaged before inference. Calling this 120 independent experiments would be incorrect. The duplicated strata add little experimental breadth.

A fixed-initial-action counterfactual, computed analytically from the initial choice and fault target, would deliver 6.67% for either architecture. This was not a separate live feedback-disabled experiment and must not be presented as one.

The implementation has three material boundaries: source-to-relay candidate features are simulated; relay-to-sink transport is direct localhost UDP regardless of radio reachability; and the sink supplies trusted receipt acknowledgments. Raw traces record witness status and selected outcomes, rather than a separate packet capture or authenticated independent observer log. Reconstructing the trace confirms internal consistency, not external authenticity or hardware behavior.

Verdict: the numerical comparison is reproducible and the policies respond differently to feedback in this fixed-state targeted diagnostic. The experiment does not validate realistic multihop wireless routing, intrusion classification, MAC behavior, energy overhead, authenticated telemetry or deployment superiority. Earlier nominal simulation results remain unchanged. The manuscript should retain these distinctions before JICCE resubmission.
