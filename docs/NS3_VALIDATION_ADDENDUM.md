# Independent packet-level network validation — 15 October 2026

This addendum supplements the integrated review draft; it does not replace its failed historical and nominal gates. The experiment is exploratory simulator-transfer evidence, not a preregistered confirmatory trial, live hardware experiment or validated intrusion detector.

## What was implemented and checked

A C++/ctypes bridge runs ns-3.44 IEEE 802.15.4 LR-WPAN PHY/MAC, with actual simulated MAC frames, CSMA/CA, acknowledgments and retransmissions. Every selected hop obeys the 50 m physical range. A relay sends a separate reverse radio forwarding-proof frame only after its downstream MAC transmission succeeds. Observed proofs and 150 ms timeouts update the selected relay's Beta risk posterior. Attack labels are used only to suppress forwarding in the simulator; they are not policy inputs. The controller is centralized Python and executes frozen checkpoints at each received forwarding hop, with 1 ms event polling; this is not a distributed embedded implementation.

The bridge control test verifies direct out-of-range failure, successful two-hop delivery, and the reverse radio proof. Offline verification reconstructs all 5,840 frozen policy decisions, checks valid hop ranges, received-data provenance, proof provenance and checkpoint hashes. There were 5,840 received data hops, 2,240 received proofs, 186 proof timeouts and 2,102 multihop deliveries. This is internal trace consistency, not independent external packet capture or cryptographic proof.

## Design and results

Seeds 75001–75030 were unused in the earlier studies. Each paired fixture uses the corresponding attention and capacity-matched MLP checkpoints trained on seeds 41001–41030. Each controller faces benign and uniformly selected 25% blackhole relay conditions: 120 runs and 3,600 generated packets. The source and traffic-class schedules and fault sets are policy independent. Blackhole nodes can originate packets but suppress received data forwarding. A separate technical pilot (74001) was excluded. Build/debug failures were configuration checks, not included performance runs.

| Condition | Endpoint | Attention | Capacity MLP | Paired attention minus MLP, 95% CI | Four-test Holm p |
|---|---|---:|---:|---|---:|
| Benign | Delivery | 100% | 100% | 0 pp (all observed differences zero) | 1 |
| Benign | Critical violations | 0% | 0% | 0 pp (all observed differences zero) | 1 |
| 25% blackholes | Delivery | 91.89% | 87.44% | +4.44 pp [1.91, 6.98] | .00494 |
| 25% blackholes | Critical violations | 5.51% | 9.22% | −3.70 pp [−6.43, −0.97] | .02883 |

The unit of inference is the independent fixture, n=30, not the 3,600 packets. Two-sided paired t intervals and tests use four endpoints/settings in one Holm family. Constant-sample intervals are descriptive and do not imply zero population uncertainty. Critical violations count loss or delivery after 90 ms among critical packets. The attention violation rate still exceeds the original 1.5% budget; this experiment does not establish feasibility of that original constraint.

## Scope and unresolved work

The old observation builder is deliberately retained for frozen-weight compatibility: link PDR/RSSI, queues, energy and QoS debts remain synthetic/model-derived features. They are not measured ns-3 telemetry. Risk alone is updated from the new forwarding proof path. The result therefore supports topology-constrained packet-level feedback integration and exploratory policy transfer, not fully instrumented cross-layer deployment.

Each packet is offered every 300 ms, with 64 total application bytes (including bridge identifiers); traffic does not create a substantive congestion stress test. Log-distance propagation uses exponent 3 and 40 dB reference loss, followed by a hard 50 m range limit. This is a simplified propagation model. Actual MAC behavior is simulated, but all selected data transmissions succeeded in this particular low-load study; benign radio-loss discrimination is not established. Forwarding proof frames share the radio channel but their energy is not integrated. No hardware-calibrated energy, authenticated feedback, live IDS, risk-off ns-3 ablation, high-load congestion experiment or physical testbed has been established. A globally shared risk posterior and centralized controller remain modeling assumptions. Do not claim all Reviewer A concerns are resolved or that acceptance is assured.

## Reproduce

From repository root, use Python 3.12, g++ with C++20, the existing project dependencies and the ns-3 prebuilt wheel:

```bash
python -m pip install ns3==3.44.post0 --no-deps
python scripts/build_ns3_bridge.py
python scripts/test_ns3_bridge.py
python scripts/run_ns3_multihop.py
python scripts/verify_ns3_multihop.py
python scripts/analyse_ns3_multihop.py
```

No cppyy import is required. The shared library is built locally and is not distributed. Trace, summaries, paired analysis and verification are in `outputs/ns3_multihop/`. The manuscript DOCX/PDF predates this addendum; integrate this qualified evidence before submission.

Primary implementation references: installed ns-3.44 headers and official source `src/lr-wpan/examples/lr-wpan-data.cc`, `helper/lr-wpan-helper.cc`, `model/lr-wpan-net-device.cc`, from https://github.com/nsnam/ns-3-dev-git/tree/ns-3.44/src/lr-wpan . The helper must remain alive during simulation because its destructor disposes the channel.
