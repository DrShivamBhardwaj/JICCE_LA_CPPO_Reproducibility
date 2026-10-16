# Implementation review on 16 October 2026

The frozen 4027f07 implementation and its 750-run outcomes remain unchanged. The review adds an independent endpoint audit and corrects the manuscript's deployment and energy interpretation. All 51 existing tests and the physical callback control passed again.

## Critical vulnerabilities and limitations

| Finding | Evidence | Treatment in redesign |
|---|---|---|
| Route state is partly centralized | One shared visited set per packet; Python reverse-path map | Architecture explicitly separates simulator state from radio-carried identifiers; no embedded distributed claim |
| QoS debt is source only in transfer | Updates occur at source receipt or 1.5 s expiry | Transit relays are not described as maintaining fully observed service debt |
| Energy per byte hides a denominator effect | Blackhole sensor radio energy increases by 0.000531 J, while energy per byte falls | Plot both absolute radio energy and energy per delivered byte; no total-energy saving claim |
| Listening dominates | Mean receive/listen component is 99.36% of modeled sensor radio energy | Four-second always-listening experiment cannot establish duty-cycle or lifetime gains |
| Beacon values use a metadata sidecar | Actual reception gates cache entry, but energy/queue values are not serialized | Disclosed in architecture, methods and limitations |
| Feedback semantics differ | Active proofs bypass the passive first-hop ACK requirement and use different expiry semantics | Compare complete mechanisms, not airtime alone; retain naive/frozen controls |
| Watch memory is unbounded over long runs | Records retained; full scan every 1 ms | State O(W) memory and O(W) expiration work per poll; long-horizon reclamation is future work |
| Fractional clipping is path dependent near the floor | Each half-credit passes through clip(q delta, 0.05, 1) | Disclose edge case; observed decision q minimum 0.6923 keeps audited runs away from that floor |
| Audit has finite scope | Endpoint reconstruction is independent of stored final values; original action audit reuses feature code | No external capture, full callback replay, formal proof or independent implementation claim |

The additional audit reconstructs all 750 delivery and critical-violation values from sink reception events and source generation times, and checks energy identities, beacon counts and decision counts. It reads all 30 gzip streams to EOF. It found zero rejected MAC handles and 53 failed-ACK callbacks after an overheard event; those events illustrate why passive evidence does not override first-hop ACK gating. These are event counts across all controls, not distinct packets or attack labels.

## High novelty opportunities

A future experiment could isolate adaptive evidence acquisition from the risk score by matching data airtime, receipt load, ACK eligibility and idle schedules across arms. An authenticated, bounded-memory implementation would then test selective probes only when the expected reduction in routing loss exceeds measured radio and processing cost. This is a proposed research direction; no such controller is included in the frozen results. Long-horizon mobility, duty cycling, deceptive beacons, receipt forgery and held-out deployment geometries require a separately frozen validation program.

## Reporting decision

The redesigned main manuscript concentrates on feedback-mechanism attribution. Previous nominal and telemetry architecture failures remain in the public record and are summarized in the paper. A successful incremental gate does not establish a new intrusion detector, unique censoring benefit, architecture superiority or original absolute QoS compliance. Current JICCE instructions were retrieved: the redesign uses Arabic table numbers, a 140–160-word abstract, A4/2.5 cm margins and 9.5-point double-spaced review text. Author phone/fax details and submission forms remain author-side completion items; they are not fabricated.
