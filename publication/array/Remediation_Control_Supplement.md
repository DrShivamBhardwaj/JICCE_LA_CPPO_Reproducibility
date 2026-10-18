# Matched-study control supplement

These are exploratory descriptive summaries of the completed 1,440 cases. They add no significance tests or multiplicity family. The six primary contrasts and all historical results remain unchanged.

Table S1. Benign controls.

| Timing | Arm | Delivery (%) | Critical failure (%) | TX state (s) |
|---|---|---:|---:|---:|
| Native | censored | 99.167 | 40.729 | 8.413 |
| Native | censored_proof | 98.646 | 42.083 | 8.753 |
| Native | negative | 99.306 | 40.208 | 8.420 |
| Native | negative_proof | 98.611 | 42.292 | 8.757 |
| Native | active_reference | 99.028 | 42.812 | 8.768 |
| Scheduled | censored | 98.715 | 94.688 | 8.418 |
| Scheduled | censored_proof | 98.368 | 95.312 | 8.752 |
| Scheduled | negative | 98.715 | 94.375 | 8.414 |
| Scheduled | negative_proof | 98.368 | 95.104 | 8.753 |
| Scheduled | active_reference | 98.646 | 95.625 | 8.791 |

Each row averages twelve geometry blocks, each containing two radio seeds and two relay permutations: forty-eight correlated run settings. Delivery is whole-run sink delivery, not the attacked primary post-onset endpoint. Critical failures include missing or late sink deliveries against 90 ms. TX is modeled transmit-state time, not measured energy.

The benign negative-update main-effect point estimate is +0.052 percentage points without added compute delay and +0.000 points with scheduled delays. Proof-generation point estimates are -0.608 and -0.347 points, respectively. These descriptive values establish neither equivalence nor an absence of practically relevant effects.

Checkpoint-, onset- and channel-stratified primary effect summaries are retained in `outputs/remediation_v1/control_and_factor_summary.json`. Each checkpoint has four geometry blocks; each onset or channel level has six. The factors were balanced but not fully crossed within geometry. Differences across these strata do not isolate a causal onset/channel/checkpoint effect, and their observed ranges are not statistical confidence intervals.

The original primary family, analysis SHA and radio captures are unchanged. Reproduce with `python scripts/summarize_remediation_controls.py`.
