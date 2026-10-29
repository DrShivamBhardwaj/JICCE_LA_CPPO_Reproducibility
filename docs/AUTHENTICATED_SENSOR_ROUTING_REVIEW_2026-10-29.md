# Authenticated Sensor Routing — reproducibility and editorial review (29 October 2026)

Study: *Forwarding Evidence and Receipt Deadlines in Authenticated Sensor Routing*.

## Verified provenance
- Historical repository snapshot: `ba1411f26c3ecd68b3a220dc990f4ddb6c36a830`.
- Protocol source at `experiments/remediation_v1/` (including `run.py`, `analyze.py`, `audit.py`, `design.py`, `protocol.json` and trace tools).
- Recorded outcomes at `outputs/remediation_v1/`; this is a tracked repository location, not an assertion of independent regeneration.
- Contiki-NG version: `4ccd1a3b9e767f168d12ec3df187fe6b7dc736b5`.
- Cooja commit: `fabff3ee41eeeb6f3de7bd11f7c9cdf0a7d7dfc4`.

## Scope that must survive any manuscript revision
1. The primary inference units are **12 geometry blocks**, not 1,440 independent radio runs. Geometry is confounded with checkpoint, onset and channel probability assignments. Intervention assignment was not randomised.
2. Penalising expired ACK-eligible watches improved post-onset delivery by 19.00 pp (native) and 21.17 pp (scheduled), with reported Holm-adjusted p = 0.00586; these are **within-design** contrasts only.
3. Proof generation used **no direct proof credit** in the matched factorial arms. Its delivery confidence intervals span zero. Proof transmissions and transmit duration increased.
4. Scheduled processing adds specified delays but does not model a serial CPU queue, overload, worst-case interrupt response or embedded scheduling. It is not hardware timing certification.
5. The Q22 parameters consume 176,644 bytes and its tanh table 32,772 bytes. These values exceed the cited 32 KiB RAM if resident together; deployment requires verified memory placement and real board measurements.
6. The tested public signed-receipt endpoint misses 68/200 deadlines for both O3 and O3+LTO. Eventual authentication is not timely authentication.
7. The attacker has a valid relay key but does not forge telemetry or collude. These threat classes were not evaluated.
8. Historical paired risk features changed without changing 11,927 corresponding selected actions; offline risk perturbation is not network-level causal evidence.
9. Physical RF/current, battery lifetime, production key storage, reset/replay, and cross-topology scalability remain unvalidated.

## Reproducibility gate before describing this as an independently replicated result
- Restore sparse-checkout entries for `experiments/remediation_v1/` and `outputs/remediation_v1/` in a separate working copy.
- Check recorded commit and package manifests; verify every referenced input/output hash.
- Run documented verification and analysis commands in a pinned Python environment. Compare generated artifacts and numerical contrasts to recorded files.
- Run unit, fault-injection and negative-case tests; log pass/fail rather than inferring from existing records.
- Preserve raw packet captures where available and explicitly identify missing raw records.
- Separate author-reviewed manuscript files from the immutable historical snapshot; do not overwrite the recorded protocol or results.

## Editorial improvements applied to the working manuscript
Threat-model limits, geometry-level inference, scheduled processing, and embedded RAM feasibility were clarified. No results, p values, sample counts or reference identifiers were changed by the editorial revision.

**Status:** historical source and reported data are identifiable in Git; independent reruns, full artifact verification, physical hardware validation and author approval are not certified by this note.
