## Current simulation and emulation benchmark

The paper is a simulation/emulation benchmark with 34 reviewed pages, a 222-word abstract, 16 figures, 13 tables, 25 references and 10 native equations. It combines controlled feedback comparisons, frozen-policy transfer diagnostics, compiled-MCU emulation and explicit negative deadline outcomes. No new experiments or altered acceptance criteria accompany this scope clarification.

Physical RF/current acquisition and production-board security are outside the selected research scope and have not been validated. They are not completed hardware gates. The original signed endpoint still misses 68/200 deadlines in each O3/LTO diagnostic; deadlines and endpoint remain unchanged. These failures are retained results, not a passed real-time compliance claim. Native Cooja radio states and assumed current ratios are not physical energy measurements.

This package is ready for author review within its declared virtual scope. Array-specific authenticated portal checks, required final declarations and the portal-generated review PDF remain unchecked; no submission or message has been sent. The official guide previously returned 403. This is not a submission or acceptance certificate.

See [the manuscript package](publication/array/README.md).

> Historical transport stage: [Array manuscript and validation status](docs/ARRAY_TARGET_AND_VIRTUAL_STATUS.md). 180 authenticated policy-transfer runs audited; 83 tests pass. Four Renode CC2538 MCUs execute compiled bridge firmware. Strict attention/MLP/greedy controls each deliver 10/10 packets with ten accepted source receipts. Physical RF/current and embedded inference/crypto remain unvalidated.

## Historical package stage before Cooja integration

The active draft integrates live MCU routing/authentication in Section 5.8 and Table 10: 25 pages, 242-word abstract, ten native equations, eleven figures, ten tables and twenty-four references. Two hundred-packet private-provisioning diagnostics deliver 200/200 packets and verified receipts with 500 matching decisions, while 134 receipt deadlines are missed. Host-persisted boot allocation is not MCU NVM. No physical RF/energy or deployment-readiness claim is made. See docs/COMPLETION_MATRIX_20261018.md and hardware/cc2538_live/PRIVATE_PROVISIONING.md. Earlier experimental stages below retain their original scopes.


> New: [distributed authenticated transport](docs/DISTRIBUTED_AUTH_STATUS.md) and hardware test harness; 30 separate chain fixtures, 68 tests passed. Real Chromium rendering now verified. The new transport uses greedy routing; physical validation and attention-policy evaluation on this transport remain pending.

> Current manuscript: [focused redesign](publication/redesigned/JICCE_Redesigned_Manuscript.docx) and [PDF](publication/redesigned/JICCE_Redesigned_Manuscript.pdf), with six vector figures, five tables, ten native equations and an [interactive architecture](publication/redesigned/interactive_architecture.html) (download and open locally). The [new implementation audit](docs/IMPLEMENTATION_REVIEW_2026_10_16.md) reconstructs all 750 endpoints and exposes source-only QoS state, shared route history, unbounded watch retention and listening-dominated energy. Frozen outcomes are unchanged.

> Latest: [locked censored-feedback holdout](docs/CENSORED_FEEDBACK_RESULTS.md), 750 runs on 30 new fixtures. The prespecified incremental simulation gate passed: blackhole delivery +4.67 percentage points versus active proofs (Holm p=0.0161). Matched naive/frozen controls do not establish a unique censoring or architecture advantage. [Current review draft](publication/censored_feedback/JICCE_Censored_Feedback_Review_Draft.docx) · [PDF](publication/censored_feedback/JICCE_Censored_Feedback_Review_Draft.pdf). Historical negative stages are retained.

> Latest evidence: [local telemetry and radio overhead results](docs/NS3_TELEMETRY_RESULTS.md). The 600-run study found no corrected architecture advantage and adverse feedback-control results. Use [the revised manuscript](publication/ns3_evidence/JICCE_LA_CPPO_Telemetry_Review_Draft.docx). Earlier documents are historical evidence stages.

> New: [ns-3 packet-level validation addendum](docs/NS3_VALIDATION_ADDENDUM.md). 120 exploratory runs with topology-constrained radio feedback; manuscript integration and deployment validation remain open.

# JICCE LA-CPPO reproducibility package

This repository accompanies a substantially redesigned IoT-WSN routing study
prepared after JICCE-26-0057 was rejected with an invitation to submit new work.
It is public so editors and reviewers can inspect the implementation and outputs.
No submission or email has been sent by this package-building workflow.

## Earlier integrated review draft (historical)

Use [the updated manuscript](publication/updated_evidence/JICCE_LA_CPPO_Integrated_Review_Draft.docx) and [PDF](publication/updated_evidence/JICCE_LA_CPPO_Integrated_Review_Draft.pdf). The [updated reviewer evidence record](publication/updated_evidence/JICCE_Updated_Reviewer_Evidence_Record.pdf) maps completed actions and remaining limits. Older publication files remain historical drafts.

The new matched-capacity UDP diagnostic contains 3,600 attempts across 30 fixture-level pairs: attention delivery 85.39%, MLP 32.22%, difference +53.17 percentage points (95% CI +35.31 to +71.02). This is targeted localhost software evidence. It does not establish physical wireless effectiveness or supersede the failed nominal co-primary superiority result. Twenty-six fixtures have identical fault targets in their two strata.

See [concern resolution](docs/REVIEWER_CONCERN_RESOLUTION.md), [raw diagnostic data](outputs/udp_matched_comparison/), and [required network validation](docs/NETWORK_VALIDATION_REQUIREMENTS.md). The earlier 47-test suite passed; 65 native equations and 7 figures are retained. The manuscript is not certified submission-ready.

## Scientific status

The historical AF-v3 joint superiority test failed. Those results are preserved.
A separately frozen 30-seed study uses an approximately capacity-matched MLP,
risk-removal and incomplete-feedback arms, and frozen-policy sensitivity checks.
Neither nominal capacity-comparison co-primary endpoint is significant after
the planned six-test Holm correction. Risk removal substantially worsens
reliability. The method is an online simulated risk-aware router, not a validated
live-traffic IDS, a hardware-tested deployment or a guaranteed-QoS protocol.

The manuscript and reviewer evidence record are review drafts. Outstanding
submission checks and deployment limits are listed in docs/SUBMISSION_STATUS.md.

## Contents

- `src/wsn_sim/`: simulation, policy, online risk and training implementation.
- `configs/`: network, radio, traffic, attack and training inputs.
- `docs/JICCE_VALIDATION_PROTOCOL.md`: pre-outcome specification for new evidence.
- `data/historical_af_v3/`: original confirmatory episode and seed outputs.
- `data/historical_af_v4/`: unsuccessful development outputs and selection record.
- `outputs/jicce_validation/`: new trajectories (CSV or gzip-compressed CSV), summaries, analyses, training logs,
  execution metadata and 120 learned state-dictionary checkpoints.
- `publication/`: revised manuscript, evidence record and figures.
- `publication/source/`: author-provided input used by the manuscript builder.
- `FILE_MANIFEST.json`: SHA-256 hashes of the distributed files.

The data are simulated packet trajectories; this redesigned study does not use
WSN-DS or an offline supervised intrusion-detection dataset. No original
ROA-DLID classification accuracy is carried forward.

## Reproduce

Use Python 3.12 and the versions in `requirements-lock.txt` for the recorded
environment. Platform changes may change training and floating-point results.

```bash
python -m pip install -r requirements-lock.txt
PYTHONPATH=src python -m pytest -q
python scripts/verify_results.py
python scripts/run_jicce_validation.py
python scripts/build_jicce_publication.py publication/source/Author_Integrated_Input.docx
```

The full simulation regenerates all 30 seeds and four arms. Existing output files
are overwritten by that command; make a separate copy to preserve the release.
Optional deterministic shards use `JICCE_SEED_START`, `JICCE_SEED_END` (exclusive)
and `JICCE_OUTPUT`; the seed set and scientific settings must not change.
Recorded execution used six five-seed shards. An earlier serial execution was
interrupted for scheduling only; its 212 saved summary rows matched the completed
shards exactly. All final outputs contain the entire frozen sample.

Historical AF-v3 provenance: source commit
`0f60eb5514961eb7430142239789887e386023b4`, workflow `34178527532`, artifact
`10038372790`, digest `sha256:d118c10e48c2bf634d0fb8b6ab8a5c3fe446ff6493c30babb446eb3d0b3a826d`.
Historical training requires that original source and environment; the current
code is not advertised as a bitwise historical rerun.

Checkpoints should be loaded as state dictionaries with
`torch.load(path, weights_only=True)`. Model dimensions and arm definitions are
specified in the source and output metadata.

## Interpretation limits

Stream separation prevents radio draws from shifting subsequent traffic draws;
it is not exact policy-independent event-trace replay. The 200-node test changes
density in the same area. Feedback omission is simulated. Feedback cost,
authentication, per-hop energy traces and embedded-device measurements are not
provided. A statistical benefit does not establish absolute QoS feasibility.

## Compiled virtual boards (16 October 2026)

Four Renode CC2538 Cortex-M3 boards now execute compiled radio-interface firmware. Greedy, MLP and attention host-policy controls each delivered 10/10 packets and passed five firmware/radio probes. The capture audit verifies MCU UART provenance and public sink signatures. [Reproduce the virtual MCU experiment](hardware/renode_cc2538/README.md). This is emulation: host inference/crypto, deterministic radio reachability, no calibrated power or physical hardware claim. [Board and Android options](hardware/BOARD_AND_ANDROID_GUIDE.md).

## Current receipt endpoint validation

Current receipt validation (18 October 2026): Q22 inference and cached signing keys reduce original signed-receipt deadline misses from 134/200 to 68/200. The experimental source-only HMAC receipt meets 200/200 tested deadlines (chain 61–63 ms; choice 49–50 ms); deferred Ed25519 proofs still miss 68/200 original deadlines. These are distinct endpoints, not a repaired original signed deadline. Both new profiles deliver all 200 packets and verify all 200 deferred proofs. ACK plus Ed25519 remains the forwarding-credit gate. Extra private receipt traffic has no measured energy benefit. Tested stack guards remain intact under the 32 KiB linker budget; this is not a worst-case bound. Physical RF/energy, protected MCU key storage and persistent MCU sessions remain unvalidated. The attached-hardware inventory found no matching board/instrument. Coauthor consent and authenticated portal checks require genuine author actions; no approval or submission is inferred.

See `docs/RECEIPT_DEADLINE_RESOLUTION.md` and `hardware/cc2538_q22/README.md` for reproduction and scope.

## Additional native Cooja diagnostics

Nine four-node CSMA/UDGM transport runs deliver 900/900 packets and signed receipts, with public test keys and three rejection controls. This separate simplified fixture omits trained policy and passive feedback; native execution does not model MCU compute cycles. Energest state durations are reported without physical energy claims. See hardware/cooja_receipt_transport/README.md and publication/array/Cooja_Transport_Validation_Addendum.md.
