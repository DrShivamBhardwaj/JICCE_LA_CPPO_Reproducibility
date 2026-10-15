# Local telemetry and radio overhead validation

The completed 600-run study does not establish attention superiority over the capacity-matched MLP. Forwarding-proof removal improves delivery in several conditions. This supersedes any interpretation of the earlier clean-radio diagnostic as evidence of a general practical advantage.

## Completed changes

The new C++ bridge and Python controller use ns-3.44 LR-WPAN PHY/MAC frames. Neighbour energy and pending-request occupancy arrive through actual broadcast radio beacons, with measured LQI and a finite cache lifetime. Unheard neighbours are unavailable. Link delivery and service delay estimates update from MAC confirmations. Each observer has a separate risk posterior. Source service debts update from actual radio receipts along the reverse route or receipt timeout. No attack label or final sink-delivery truth is supplied as a policy feature.

PHY state residence times charge data, forwarding proofs, beacons, reverse delivery receipts, MAC acknowledgments, retries and listening. The current/voltage assumptions are explicit in the protocol and verified by the state-time energy identity. This is modeled radio energy, not hardware-calibrated energy. CPU and sensing costs are excluded.

The frozen-weight transfer changes the former normalized RSSI slot to normalized received LQI. It uses a Beta(9,1) prior for untried link delivery. These are declared transfer assumptions; no data-driven calibration or retraining was performed after outcomes. Static neighbour geometry is configured, while energy/queue reports have actual radio acquisition delays.

## Design

Thirty new fixture seeds 76001–76030 are paired with the existing checkpoints trained on 41001–41030. Four arms face five settings: benign, blackhole, congested benign, congested blackhole and weak-link benign. Each run generates 60 packets, giving 36,000 source packets. There are 100 sensors plus one sink. The pilot seed 75901 is excluded. All radios run for four seconds. Source/traffic/fault schedules are policy independent; policy-dependent MAC histories are not identical exogenous event replays.

The complete configuration is in `configs/ns3_telemetry_protocol.json`. Forty-five paired tests form one Holm family: five settings × three comparators × three endpoints. Inference uses n=30 fixtures; packets are not independent replicates.

## Critical findings

| Condition | Attention delivery | Capacity MLP delivery | Difference pp | Holm p |
|---|---:|---:|---:|---:|
| Benign | 80.11% | 79.33% | +0.78 | 1 |
| Blackhole | 68.22% | 66.72% | +1.50 | 1 |
| Congested benign | 24.61% | 24.17% | +0.44 | 1 |
| Congested blackhole | 23.61% | 22.89% | +0.72 | 1 |
| Weak-link benign | 77.89% | 77.94% | −0.06 | 1 |

None of the 15 architecture contrasts across delivery, critical violation and energy per delivered payload byte survived correction. This is not proof of equivalence; intervals and raw effects remain in `paired_analysis.json`.

Disabling forwarding proofs increases delivery by 5.06 pp in benign conditions (Holm p=.00444), 7.50 pp under blackholes (p=.00222), and 6.89 pp with weak links (p=.03060). Under blackholes, the full mechanism raises critical violations by 8.95 pp (p=.00947) and energy per delivered byte by .001158 J/B (p=.02322). The control removes both proof traffic and proof-driven risk updates, so this does not isolate a pure airtime effect. It nevertheless contradicts a net-benefit claim for the tested full mechanism.

The 90 attack-free attention runs contain 2,022 forwarding timeouts at benign relays. A timeout is ambiguous evidence of forwarding failure, not an attack diagnosis. Absolute service budgets are not met. Favourable earlier localhost or clean-radio results cannot override these outcomes.

## Verification and remaining scope

The verifier rebuilds recorded observations and actions, replays local risk updates, verifies checkpoint hashes and valid data/proof paths, and checks energy against state residence times. Cache snapshots match transmitted beacon values; raw beacon receptions and full QoS/link histories are not independently replayed. These are internal consistency checks, not external capture or independent implementation validation.

Technical trace integrity failures were repaired using the identical seeds, checkpoint pairing, protocol and settings. Regenerated final metrics match all original 600 summaries exactly. No unsuccessful scientific outcome was removed. Complete gzip traces, including all four arms and all five conditions, are retained per fixture.

Feedback and beacon producers are trusted. Authentication, spoofing and malicious telemetry are not evaluated. There is no live IDS or physical testbed, and the Python controller is not a distributed embedded implementation. The evidence resolves missing experimental controls within this bounded simulator design; it does not resolve the lack of demonstrated practical superiority or field deployment validation. The revised manuscript is an evidence review draft, not a certified submission-ready package.

## Reproduce

```bash
python -m pip install -r requirements.txt
python -m pip install ns3==3.44.post0 --no-deps
python scripts/build_ns3_telemetry.py
python scripts/test_ns3_telemetry.py
python scripts/run_ns3_telemetry.py
python scripts/verify_ns3_telemetry.py
python scripts/analyse_ns3_telemetry.py
python scripts/integrate_ns3_manuscript.py
```

Use Python 3.12 and a C++20-capable g++. The ns-3 wheel is accessed directly by the C++ bridge, avoiding cppyy. Shards may be run with `--start` and `--end`; generate canonical summaries from each fixture's final trace records before analysis. Raw traces are internal simulator logs and are not authenticated evidence of external traffic.
