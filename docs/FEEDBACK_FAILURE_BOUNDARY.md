# Interpretation of censored feedback failure

The manuscript now centers a conditional gain and a transfer failure. This revision uses existing outcomes, not a newly executed parameter sweep.

The original 750-run protocol reports +4.67 percentage points relative to active proofs under its blackhole condition. The separate 600-run four-node Cooja study reports 32.94% delayed blackhole delivery for censored feedback, 79.11% for active proofs, 54.89% for naive feedback and 32.83% for censored feedback with proofs enabled. These implementations differ; their cross-study contrast does not isolate relay behavior change as the sole cause.

In the declared censored ledger, β stays at 1 and α never decreases. Missing evidence alone cannot reverse earlier positive evidence. Three regression cases verify prior positive evidence followed by acknowledged silence in censored, naive and active modes. This invariant does not imply fixed routing actions, since link estimates, caches and other observation coordinates can change.

The matched-proof-generation contrast changes censored delivery by −0.11 points, with paired 95% interval −0.50 to +0.39 and Holm p=1. This provides no evidence of recovery from generation alone; it is not proof of population equivalence. Active and censored eligibility and expiry semantics differ. The study does not isolate the effect of negative updates from all other semantics.

Attack onset, warm-up, topology, channel quality and checkpoint have not been swept independently. An onset threshold, safe operating region or optimal probing policy is unestablished. Adaptive authenticated probing is a prospective new mechanism, not an implemented achievement of this revision.

Reproduction: the main manuscript builder calls scripts/array_failure_boundary_revision.py after Cooja integration. scripts/audit_array_failure_boundary.py compares a prior manuscript baseline with the revised document, reconciles headline values and checks all equations, tables and embedded images. The numerical analyses and frozen protocol files are unchanged. Physical measurements, production security and actual submission approvals remain open.

The earlier unconfirmed stale-audit repair is included in this release: analysis rejects log/image hash mismatches, conflicting raw/compressed copies and nonzero runner completion. Five mutation/positive-path tests pass. Reanalysis of all 600 archived runs reproduces analysis.json byte for byte. Hashes are integrity checks, not signatures against coordinated archive replacement. Ledger-event replay is not a complete independently derived causal proof of every feedback transition from radio events.
