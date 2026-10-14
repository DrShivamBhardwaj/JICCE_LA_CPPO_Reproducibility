# AF-v3 E1 primary confirmatory protocol — AF-2026-09-08-v3

Status: **FROZEN BEFORE ANY AF-v3 OUTCOME GENERATION**.

Primary configuration: `configs/af_v3_final.yaml`.

Architecture freeze: `docs/ARCHITECTURE_FREEZE_AF_V3_2026.md`.

## 1. Scientific question

Does the frozen permutation-equivariant `LocalAttentionActorCritic` improve critical-traffic routing QoS relative to the fixed-slot `MaskedActorCritic` when every non-policy factor is held constant?

This is the only AF-v3 primary causal comparison.

## 2. Arms

### `af_v3_attention_cppp`

- exact AF-v3 configuration;
- `LocalAttentionActorCritic`;
- Lagrangian CPPO;
- no clustering/ROA;
- no cluster-aware features or hierarchy mask;
- no hard shield;
- QoS debt remains only in fast policy context;
- posterior mean risk and risk-UCB remain controller-visible;
- no attack labels.

### `af_v3_mlp_cppp`

Identical to `af_v3_attention_cppp` in configuration, observation serialization, candidate set, mask, reward, cost critics, Lagrange budgets, training budget, random seeds, and evaluator. The **only intended difference** is replacing `LocalAttentionActorCritic` with the fixed-slot `MaskedActorCritic` using the same hidden width and number of action slots.

## 3. Fresh confirmatory seed vault

The following 30 seeds are reserved exclusively for AF-v3 E1:

`13001, 13003, 13007, 13009, 13033, 13037, 13043, 13049, 13063, 13093, 13099, 13103, 13109, 13121, 13127, 13147, 13151, 13159, 13163, 13171, 13177, 13183, 13187, 13217, 13219, 13229, 13241, 13249, 13259, 13267`

These seeds may not be used for smoke tests, structural qualification, debugging, tuning, pilot analysis, or AF-v3 E2-E6.

The unused AF-v2 seed vault (`120xx`) is retired and remains unused; AF-v3 does not repurpose it.

## 4. Training/evaluation budget

For each of the 30 matched seeds and each learning arm:

- 8 policy updates;
- 50 training packet episodes/update;
- 3 PPO epochs/update;
- 240 deterministic evaluation packet episodes;
- training environment seed = `seed + 10000`;
- Torch training seed = `seed + 20000`;
- NumPy training seed = `seed + 30000`;
- evaluation environment seed = `seed`;
- Torch evaluation seed = `seed + 40000`;
- NumPy evaluation seed = `seed + 50000`.

The model trained for one seed is evaluated only on that seed's matched evaluation environment; no cross-seed model selection is allowed.

## 5. Co-primary endpoints

Paired difference is `af_v3_attention_cppp - af_v3_mlp_cppp`; negative is favorable.

1. `class_0_mean_delay_ms`;
2. `class_0_delay_violation_rate`.

For each endpoint:

- all 30 matched seed pairs are used;
- paired mean difference;
- two-sided 95% CI;
- paired t-test;
- paired Cohen's `dz`;
- Wilcoxon signed-rank sensitivity analysis.

The two paired t-test p-values are Holm-adjusted as one co-primary family at family-wise alpha 0.05.

## 6. Guardrails

### Delivery non-inferiority

For paired `attention - MLP` delivery-rate differences, the one-sided 95% lower confidence bound must be strictly greater than `-0.01` absolute.

### Energy non-inferiority

For `energy_per_delivered_packet_j`, calculate the paired log ratio `log(attention/MLP)`. The one-sided 95% upper confidence bound on the geometric mean ratio must be `<= 1.05`.

## 7. Strict primary decision

`PASS_AF_V3_E1` requires all of:

1. both co-primary mean differences are negative;
2. both Holm-adjusted p-values are `<0.05`;
3. delivery non-inferiority passes;
4. energy non-inferiority passes;
5. all 30 matched seeds are present, except a documented whole-seed integrity failure that invalidates both arms for that seed;
6. no frozen configuration/protocol deviation occurred.

Any other result is `FAIL_OR_INCONCLUSIVE_AF_V3_E1`.

No secondary endpoint can rescue a failed strict decision.

## 8. Secondary/descriptive outcomes

Report, without replacing the primary decision:

- overall delivery rate;
- class-specific delivery rates;
- overall and class-specific mean delay;
- class-specific loss rates;
- final/mean/peak QoS debts;
- security-drop and link-drop rates;
- energy consumed and energy per delivered packet;
- mean episode reward;
- hop count and retry distributions where available;
- final Lagrange multipliers;
- policy parameter count and deterministic inference latency measured under E6 rules.

Secondary p-values are clearly labeled exploratory unless a separate frozen family is specified before E1 starts.

## 9. Secondary baselines

On the same 30 evaluation seeds, evaluate for context only:

- `static_energy_risk_etx`;
- `periodic_roa_energy_risk_etx` using the previously frozen 12-packet periodic topology refresh and the same ROA parameter block.

These baselines are descriptive and do not enter `PASS_AF_V3_E1`. The periodic ROA baseline is not part of the proposed AF-v3 architecture.

## 10. Structural eligibility

E1 may start only after AF-v3 E0 structural qualification verifies at minimum:

- `clustering.enabled=false` prevents initial and adaptive ROA invocation;
- no ROA RNG consumption occurs in the AF-v3 primary controller;
- `cluster_aware_routing=false` and `cluster_hierarchy_mask=false`;
- `shield_enabled=false` makes final action mask equal the physical/loop-free base mask;
- attention actor equivariance and critic invariance under candidate permutation;
- no controller-facing attack-label leakage;
- same-seed deterministic replay and different-seed network divergence;
- exact config checksum/semantic match to the architecture freeze.

Structural qualification produces no efficacy claim.

## 11. Stage gate after E1

- If `PASS_AF_V3_E1=true`, reviewer-facing E2-E6 may execute under their frozen protocols/matrix.
- If E1 is fail/inconclusive, E2-E6 are marked `BLOCKED_BY_AF_V3_E1` and are not launched for subgroup mining or claim rescue.

## 12. Anti-p-hacking and provenance

- no post-start reward-weight, architecture, margin, endpoint, seed, training-budget, attack-model, or preprocessing changes;
- retain raw episode metrics, seed summaries, training logs, exact config, protocol snapshot, package versions, commit SHA, and artifact digest;
- record any technical rerun as a reproducibility rerun, not as a fresh independent confirmatory sample;
- negative results remain in the paper/repository record;
- a new primary architecture requires a new versioned freeze and a disjoint untouched seed vault.

