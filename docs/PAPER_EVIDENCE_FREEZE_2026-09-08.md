# Evidence-Consistent Paper Freeze — 2026-09-08

Status: **FROZEN AFTER AF-v4 DEVELOPMENT GATE FAILURE**.

This document terminates iterative architecture search under the current AF-v3/AF-v4 research program and fixes the manuscript direction to the evidence actually obtained. It does not change any historical protocol or result.

## 1. Research decision

No AF-v5 tuning cycle is authorized under this paper branch. The untouched AF-v4 `230xx` confirmatory seed vault must not be used because no AF-v4 candidate satisfied the pre-outcome development gate.

The manuscript will therefore be written as an evidence-consistent constrained-routing study, not as a superiority paper and not as an ROA/clustering paper.

## 2. Authoritative confirmatory evidence

The authoritative efficacy test remains AF-v3 E1, run `34178527532`, using 30 fresh matched `130xx` seeds.

For local attention minus the matched fixed-slot MLP comparator:

- Class-0 mean delivered delay: `+1.015758 ms`, 95% CI `[-0.503912, +2.535429]`, Holm-adjusted `p=0.182115`; the direction is unfavorable and the endpoint did not confirm superiority.
- Class-0 total delay-violation rate: `-0.031254`, 95% CI `[-0.051601, -0.010906]`, Holm-adjusted `p=0.007703`; favorable and corrected-significant.
- Overall delivery-rate difference: `+0.031528`; the frozen delivery non-inferiority guardrail passed.
- Energy-per-delivered-packet geometric ratio: `0.971801`, one-sided 95% upper ratio `1.000405`; the frozen energy non-inferiority guardrail passed.

Because both co-primary endpoints did not satisfy the frozen favorable-and-significant rule, AF-v3 E1 remains `FAIL_OR_INCONCLUSIVE_AF_V3_E1`.

## 3. Mechanism evidence

Post-confirmatory forensic analysis is exploratory and must be labelled as such.

The total Class-0 violation improvement decomposed into approximately `-0.027483` loss-rate difference and `-0.003771` delivered-late difference. Thus about 88% of the observed violation improvement was attributable to reduced packet loss rather than reduced delivered-packet latency.

Among delivered Class-0 packets, attention increased mean hop count by approximately `+0.06478` and increased the three-hop share by approximately `+0.04577`. Within matched hop-count strata, pooled attention delay was not higher than MLP delay. The evidence is therefore consistent with a reliability-latency trade-off: attention selected safer paths that delivered more difficult packets, but the resulting route-length composition prevented improvement in aggregate mean delivered delay.

This is a mechanism interpretation, not a causal mediation claim.

## 4. AF-v4 development result

AF-v4 tested two pre-specified residual-slack-aware repairs on 20 fresh development seeds. Run `34192491741` completed successfully at source commit `8f3d3813140009efb4f9660acda11f7d09ae85aa`. Artifact `af-v4-development`, ID `10042998980`, digest `sha256:b53def60d883a8d8e0c04bef0509405345407c11f794e3c8bb3e5305dfa56ca4`.

Neither candidate met the frozen eligibility gate:

- `slack_feature_attention - slack_mlp_anchor`: Class-0 mean delay `+3.225549 ms` (95% CI `[+1.201671, +5.249426]`); violation difference `-0.002782`. Delivery and energy non-inferiority passed, but latency requirements failed.
- `slack_monotone_attention - slack_mlp_anchor`: Class-0 mean delay `+1.628427 ms` (95% CI `[-1.030817, +4.287672]`); violation difference `-0.014978`. Delivery and energy non-inferiority passed, but latency requirements failed.

`selected_candidate = null`; `ready_for_af_v4_freeze = false`; AF-v4 confirmation is blocked. The reserved `230xx` confirmatory vault remains untouched.

AF-v4 results are development/selection evidence only and must not be presented as confirmatory efficacy evidence.

## 5. Final manuscript framing

Recommended title:

**Permutation-Equivariant Local Attention for Constrained IoT-WSN Routing: Confirmatory Evidence of a Reliability-Latency Trade-off**

Acceptable shorter title:

**QoS- and Risk-Aware Local-Attention Constrained Routing for IoT Wireless Sensor Networks**

The first title is preferred because it states the actual empirical outcome instead of implying unqualified superiority.

## 6. Claims permitted in the manuscript

1. The proposed controller uses a node-ID-free, permutation-equivariant local candidate representation with shared candidate encoding and context-to-candidate attention.
2. The routing policy jointly conditions on class-specific QoS virtual-debt state and label-free posterior security risk/risk-UCB under a Lagrangian constrained-PPO formulation.
3. In the frozen AF-v3 confirmatory comparison, attention significantly reduced Class-0 total violation rate and satisfied delivery/energy non-inferiority guardrails, but did not reduce mean Class-0 delivered delay.
4. Exploratory mechanism analysis is consistent with attention trading modestly longer routes for improved reliability/security behavior.
5. A pre-specified AF-v4 residual-slack refinement failed its development gate, providing negative design evidence against that repair under the tested budget and simulator conditions.

## 7. Claims prohibited

Do not claim:

- attention/LA-CPPO is superior overall to MLP;
- mean latency improvement;
- state of the art, first, or guaranteed QoS;
- scalability or zero-shot transfer, because E5 was never authorized after the failed primary gate;
- attack-diversity robustness, because E3 was never authorized;
- computational-overhead superiority, because E6 was never authorized;
- ROA/clustering efficacy or novelty;
- an external IDS dataset, Deep Maxout classifier, or the legacy 98.34% figure;
- AF-v4 development outcomes as confirmatory evidence.

## 8. Paper structure

1. Introduction: reliability-latency tension in constrained IoT-WSN routing and the need for evidence under matched stochastic evaluation.
2. Related work: attention/GNN/PPO/trust/constrained routing; novelty restricted to the exact representation and evaluation formulation.
3. System model and constrained routing formulation.
4. LA-CPPO architecture: local candidate state, permutation-equivariant actor, invariant critic, QoS debts, posterior risk, vector constraints.
5. Confirmatory experimental protocol: 30 fresh matched seeds, two co-primary endpoints, Holm correction, delivery and energy non-inferiority guardrails, anti-p-hacking rules.
6. Confirmatory results: report both success and failure without rescue language.
7. Exploratory mechanism analysis: loss-vs-late decomposition and route-length composition.
8. Targeted AF-v4 negative refinement evidence: clearly labelled development-only.
9. Limitations: simulator-only, 100-node primary setting, one frozen mixed-attack configuration, no authorized scalability/attack-diversity/overhead study after the failed gate.
10. Conclusion: local attention improved reliability-related outcomes under the tested setting but did not establish mean-delay superiority; future work requires a genuinely new hypothesis rather than post-hoc tuning.

## 9. Submission rule

The paper may be submitted only with evidence-consistent wording. Any future architecture redesign must be treated as a separate research program with a new theory-driven hypothesis, new development protocol, and a newly reserved confirmatory seed vault. It must not use the untouched AF-v4 `230xx` vault to rescue the present paper.

