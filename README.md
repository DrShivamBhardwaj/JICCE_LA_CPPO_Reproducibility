> Latest evidence: [local telemetry and radio overhead results](docs/NS3_TELEMETRY_RESULTS.md). The 600-run study found no corrected architecture advantage and adverse feedback-control results. Use [the revised manuscript](publication/ns3_evidence/JICCE_LA_CPPO_Telemetry_Review_Draft.docx). Earlier documents are historical evidence stages.

> New: [ns-3 packet-level validation addendum](docs/NS3_VALIDATION_ADDENDUM.md). 120 exploratory runs with topology-constrained radio feedback; manuscript integration and deployment validation remain open.

# JICCE LA-CPPO reproducibility package

This repository accompanies a substantially redesigned IoT-WSN routing study
prepared after JICCE-26-0057 was rejected with an invitation to submit new work.
It is public so editors and reviewers can inspect the implementation and outputs.
No submission or email has been sent by this package-building workflow.

## Latest integrated review draft

Use [the updated manuscript](publication/updated_evidence/JICCE_LA_CPPO_Integrated_Review_Draft.docx) and [PDF](publication/updated_evidence/JICCE_LA_CPPO_Integrated_Review_Draft.pdf). The [updated reviewer evidence record](publication/updated_evidence/JICCE_Updated_Reviewer_Evidence_Record.pdf) maps completed actions and remaining limits. Older publication files remain historical drafts.

The new matched-capacity UDP diagnostic contains 3,600 attempts across 30 fixture-level pairs: attention delivery 85.39%, MLP 32.22%, difference +53.17 percentage points (95% CI +35.31 to +71.02). This is targeted localhost software evidence. It does not establish physical wireless effectiveness or supersede the failed nominal co-primary superiority result. Twenty-six fixtures have identical fault targets in their two strata.

See [concern resolution](docs/REVIEWER_CONCERN_RESOLUTION.md), [raw diagnostic data](outputs/udp_matched_comparison/), and [required network validation](docs/NETWORK_VALIDATION_REQUIREMENTS.md). All 47 tests pass; 65 native equations and 7 figures are retained. The manuscript is not certified submission-ready.

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
