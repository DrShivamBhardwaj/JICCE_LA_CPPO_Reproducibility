# Post-freeze implementation validation on 18 October 2026

Baseline: 7d8ea76b042e98af306dc9d3a5eb015b52b443a8. The manuscript, frozen 750-run results and separate 180-run results are unchanged.

## Completed implementation work

An opt-in BoundedFeedbackLedger addresses the partition-dependent clipping artifact by clipping registration-time reliability once and then multiplying by the positive evidence increment. At q=0.04, combined and split observations both produce total credit 0.05. This remains a heuristic effective count, not calibrated Bayesian evidence.

The variant retains the successful-own-ACK gate and maximum-evidence rule. The first final MAC outcome is terminal. Unknown evidence types and regressing event times are rejected. Record retention is finite (default 2 s from registration); post-retention evidence cannot earn credit. Record and diagnostic-history capacities are explicit. Packet IDs must increase strictly within each observer/peer pair and session, including after retirement or capacity rejection. Reinitialize with a new externally managed session rather than reusing IDs.

The existing frozen FeedbackLedger is unchanged. The new variant is not wired into manuscript experiment runners and has not been evaluated for end-to-end routing performance.

The SecurityRiskEstimator docstring now describes heuristic effective counts consistently with the manuscript. Its numerical implementation and public property names are unchanged.

## Executed checks

- Existing feedback and authentication checks plus new ledger tests: 32 passed.
- Complete repository pytest collection, including compiled radio callbacks: 94 passed in 4.86 s.
- All four native radio bridges compiled on the authorized Mac against its available ns-3.47 libraries.
- This is a portability check against ns-3.47, not an independent reproduction of the frozen ns-3.44 numerical study.
- Deterministic ledger stress: 100,000 registration attempts, capacity 128, peak 128 retained watches, 64,000 accepted and retired records, 36,000 capacity rejections, zero final watches after retention expiry, diagnostic history bounded at 64. Bounded memory does not imply loss-free service or queue stability.
- Independent sender-clock beacon diagnostic: offsets {-20,-5,0,5,20} ms, drifts {-50,0,50} ppm, physical send times {1,60,300} s and 1 ms transport delay. Of 45 authentic fresh cases, 25 were accepted and 20 rejected by the unchanged freshness rule. This exposes a clock-envelope limitation; it does not validate or repair synchronization.

Machine-readable results, build commands, dependency versions, source hashes, pytest output and JUnit records are in outputs/validation_20261018/.

## Critical vulnerabilities and limitations

The ledger changes resolve a code-level artifact and bound its own records/history for fixed node count. Risk arrays and pair high-water state remain O(n_nodes squared). A capacity rejection is observable and irreversible for that identity. Its consequences for delivery require new paired radio experiments.

The full suite passing does not close physical RF, measured board energy, embedded neural/authentication execution, duty-cycled MAC, long-run energy power-gating or device-clock synchronization. The clock diagnostic failed to accept all fresh cases and must remain visible. No original acceptance family is enlarged with these post-freeze checks.

## High novelty opportunities

Freeze a separate factorial feedback experiment before using this alternate ledger in performance claims. Vary credit semantics and feedback traffic separately, charge wake/listen costs, and include the finite-retention and capacity-loss endpoints. A clock-handling change must explicitly state how offsets are obtained and trusted; widening a freshness window without replay analysis is insufficient.

## Reproduce on this Mac

Use the dedicated Python 3.12 environment at /Users/shivambhardwaj/Research/wsn-array-validation-env. Run scripts/build_ns3_portability.py with the installed ns-3.47 build prefix, then scripts/run_postfreeze_diagnostics.py and python -m pytest -q. The builder targets optimized native libraries; use the original wheel builders to reproduce the ns-3.44 study.

## Submission boundary

No journal submission, coauthor consent, independent contribution declaration, physical measurements or embedded execution is represented as complete by this record.
