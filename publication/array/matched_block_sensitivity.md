# Post-hoc geometry-block sensitivity of the frozen matched study

**Source of all numbers:** `outputs/remediation_v1/analysis.json`, endpoint `post_delivery`; values in percentage points. This is a reanalysis of stored 12-block contrasts, not an additional simulation or revised frozen test. Independent block count = 12, not 1,440. Primary confirmatory results remain the original 20,000-resample pointwise bootstrap intervals and six-contrast Holm-adjusted exhaustive sign-flip p-values.

| Timing | Contrast | All-block mean (pp) | Positive/negative/zero blocks | Individual block range (pp) | Leave-one-block-out mean range (pp) | Leave-one-out raw sign-flip p range |
|---|---|---:|---:|---:|---:|---:|
| Native | Negative updates | 19.000 | 11/0/1 | 0.000 to 39.875 | 17.102 to 20.727 | 0.000977 to 0.001953 |
| Native | Proof generation | 0.597 | 8/3/1 | -3.250 to 5.000 | 0.197 to 0.947 | 0.169922 to 0.746094 |
| Native | Interaction | 2.569 | 9/2/1 | -5.500 to 10.000 | 1.894 to 3.303 | 0.029297 to 0.177734 |
| Scheduled | Negative updates | 21.170 | 11/1/0 | -0.417 to 39.500 | 19.504 to 23.133 | 0.000977 to 0.001953 |
| Scheduled | Proof generation | 1.017 | 7/4/1 | -5.000 to 7.500 | 0.428 to 1.564 | 0.125000 to 0.642578 |
| Scheduled | Interaction | 2.563 | 9/3/0 | -8.333 to 18.500 | 1.114 to 3.553 | 0.046875 to 0.436523 |

The leave-one-out values recompute the two-sided absolute-sum sign-flip tail over **2^11 = 2,048** signs after each single-block omission; they are not multiplicity-adjusted, prespecified tests or corrected confidence intervals. In particular, the nominally small interaction leave-one-out p-values cannot be used as a claim of significant interaction. The twelve blocks are local perturbations around one four-node topology, and checkpoint/onset/channel combinations are balanced rather than fully crossed. Block sign patterns do not test the full symmetry assumption; a new independent graph-family replication would be needed for broader inference. The exact historical protocol and accepted primary results are unchanged.
