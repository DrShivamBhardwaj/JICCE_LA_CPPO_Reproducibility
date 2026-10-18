# Frozen remediation study v1

Starting repository revision: f9bf3c9382c73cee2f21fffa94e07f1a0affe415.

This is a separate prospective remediation study informed by the historical negative result. It does not change the original 750, 180, 240 or 600-run experiments. The protocol is committed before any new radio outcome is acquired.

The design has 12 independent perturbed-geometry blocks. Three retained checkpoints each cover all four onset/channel combinations (onset packet 10 or 30; UDGM RX probability 0.9 or 1). Each block crosses two radio seeds, two relay-ID permutations, benign plus attacks at both physical relay positions, two scheduling conditions and five arms: 1440 runs. Geometry, checkpoint and onset/channel are not fully crossed; generalization remains conditional on this balanced fixture family.

Four arms share positive evidence, own-ACK gating, ACK-relative 150 ms expiry and acceptance of late positive evidence until watch-slot reuse. Only the missing-evidence failure increment and proof generation change. Generated proofs are excluded from matched-arm credit. The original active-proof semantics form a separate reference. The newly added proof identity check validates source/session/pending route in every arm; it does not provide production key protection.

Protocol.json defines endpoints, block averaging, paired intervals and multiplicity. Packet observations and repeated radio seeds are not independent topological replicates. Archive diagnostics are explicitly exploratory. Offline risk interventions test the compiled frozen actor on held observations; they are not closed-loop radio results. The antecedent audit checks prior wires, processing availability, own ACKs and packet identity. It complements, rather than replaces, the retained cryptographic/ledger/policy reconstruction.

Execution through .github/workflows/wsn-remediation.yml records dependency versions and uploads captures even on failure. The workflow has read-only repository permissions; it does not automatically publish a successful result or revise the manuscript. All declared cases must execute and pass integrity audits before factorial inference. Preflight is excluded; technical failures are retained and do not become zero-loss outcomes. Source changes after freeze require a named amendment/new version.

Commands, from the repository root:

    python experiments/remediation_v1/run.py --verify-only
    PYTHONPATH=src python -m pytest -q tests/test_remediation_v1.py
    python experiments/remediation_v1/diagnostics.py --output outputs/remediation_v1/archive_diagnostics
    bash experiments/remediation_v1/bootstrap.sh
    python experiments/remediation_v1/run.py --execute --workers 2
    python experiments/remediation_v1/analyze.py

The bootstrap requires a supported Java 25 installation and normal native C build tools. Python needs numpy, torch and cryptography; the workflow records exact installed versions. Native Cooja computes no Cortex-M3 cycles, and scheduling assumptions remain overlapping per-packet delays. No physical energy, production security, author consent or submission completion follows from this study.
