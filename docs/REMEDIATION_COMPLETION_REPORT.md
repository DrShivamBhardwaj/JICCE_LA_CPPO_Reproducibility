# Evidence-based remediation completion report

Starting commit: `f9bf3c9382c73cee2f21fffa94e07f1a0affe415`. New mechanisms and experiments reside in versioned remediation directories; original experiments and failures remain retained.

The separate Cooja study completes 1,440 cases over twelve geometry blocks. Archive integrity and all per-case audits pass. Its questions were motivated by historical outcomes, and its new analysis was frozen before new runs. No historical statistical family is pooled or overwritten.

## Concern-to-evidence matrix

| Concern | Status | Verified outcome | Limit / next action |
|---|---|---|---|
| A: causal attribution | RESOLVED | Four matched arms share ACK, expiry, positive-credit and late-positive semantics; negative update and proof traffic cross independently. Separate active reference retained. Evidence: `experiments/remediation_v1; outputs/remediation_v1/analysis.json`. | Conditional effects within this fixture family; not attribution of the complete historical ns-3 gain. |
| B: identity / ordering | RESOLVED | Both physical attackers, two relay-ID permutations, 12 perturbed geometries, three retained checkpoints and benign controls executed. Evidence: `experiments/remediation_v1/protocol.json; outputs/remediation_v1/integrity_recheck.json`. | Geometry/checkpoint/onset/channel are balanced block factors, not a fully crossed population study. |
| C: censored-frozen equality | RESOLVED | 11927 matched decisions: 7023 risk differences, no ordering or action disagreement. 1010/4800 offline interventions change action. Evidence: `outputs/remediation_v1/archive_diagnostics; outputs/remediation_v1/feedback_trajectories.csv.gz`. | Offline sensitivity does not establish closed-loop radio gain or invariance to every risk input. |
| D: failure characterization | RESOLVED | Frozen onset/channel/geometry/checkpoint design and sustained-recovery/censoring metrics completed. Evidence: `outputs/remediation_v1/secondary_summary.json; outputs/remediation_v1/exposure_summary.json; outputs/remediation_v1/secondary_run_diagnostics.json`. | No universal threshold; narrow fixture family and conditional latency summaries. |
| Transfer scope / onset threshold | SCIENTIFIC LIMITATION | The shared four-node graph, 38 m progress normalization, clipped source progress, two onsets and three retained policies support conditional transfer findings. Evidence: `outputs/remediation_v1/design_geometry_audit.json; experiments/remediation_v1/protocol.json`. | No universal threshold or broad network-scale claim. Wider independently varied graphs and fully crossed warm-up/onset/checkpoint fixtures need a new frozen study if that claim is pursued. |
| E: loss versus lateness | RESOLVED | Benign delayed censored critical packets: 7 lost, 563 late, 30 timely of 600. Sink and source latency endpoints remain separate. Evidence: `outputs/remediation_v1/archive_diagnostics; outputs/mcu_deadline_v1/stage_profile.json`. | Injected Cooja delays are not a serial CPU model or measured timing. |
| E: original signed deadline | SCIENTIFIC LIMITATION | Compiler-only O3 still misses 68/200; 200 packets and signed receipts delivered. Evidence: `outputs/mcu_deadline_v1`. | A further endpoint-preserving crypto/execution redesign and separately frozen evaluation are required; no pass claimed. |
| F: security assumptions | RESOLVED | Implementation-wise key/evidence/ACK/session/provisioning matrix; unsupported identity/ACK/processing/credit mutation checks. Evidence: `docs/SECURITY_EVIDENCE_MATRIX.md; tests/test_remediation*`. | Public fixture validation supplies no secrecy against fixture-key holders or runtime Byzantine truth guarantee. |
| G: statistical analysis | RESOLVED | 12-block paired inference; six primary Holm contrasts; separate secondary families; pointwise bootstrap intervals and explicit symmetric sign-flip assumption. Evidence: `experiments/remediation_v1/protocol.json; outputs/remediation_v1/analysis.json`. | No nonsignificance-as-equivalence claim or invented deployment margin; no packet pseudoreplication. |
| H: physical RF and energy | BLOCKED BY EXTERNAL ACCESS OR HUMAN CONFIRMATION | No compatible physical boards/instruments accessible; linked Mac offline at this check. Evidence: `publication/array/external_validation_access_check.json`. | Provide compatible boards plus calibrated RF/current equipment; freeze protocol, acquire raw calibrated traces. |
| H: production security | IMPLEMENTED BUT UNVALIDATED | Emulated key/session negative controls exist; protected storage, authenticated provisioning, firmware authenticity and reset-safe device sessions lack board evidence. Evidence: `hardware/cc2538_live; docs/SECURITY_EVIDENCE_MATRIX.md`. | Board-specific port, secure provisioning/boot/storage tests and reset/power-loss captures required. |
| H: author approval | BLOCKED BY EXTERNAL ACCESS OR HUMAN CONFIRMATION | Exact-version requests and approval register prepared; not sent; all final approval fields remain null. Evidence: `publication/array/Coauthor_review_request_*; Approval_evidence_register_TEMPLATE.json`. | Actual authors must review the pinned paper and supply consent, roles, overlap and declarations. |
| H: authenticated submission | BLOCKED BY EXTERNAL ACCESS OR HUMAN CONFIRMATION | Official guide returned 403 and browser homepage unavailable; authenticated requirements and assembled portal PDF unchecked. Evidence: `publication/array/external_validation_access_check.json`. | Accessible official guide and authorized authenticated portal session; actual declarations require author confirmation. |
| I: manuscript and exhibits | RESOLVED | Completed evidence integrated; old 11 tables, 12 images and 10 native equations preserved. Two data-derived figures and six-contrast Table 12 added. Evidence: `publication/array; remediation_manuscript_audit.json`. | Array-specific final portal compliance and author approval remain separate gates. |
| J: reproducibility / publication | RESOLVED | Frozen source, raw outputs, analyses, environments, regression records, durable releases and hashes provided. Evidence: `docs/REMEDIATION_REPRODUCTION.md; FILE_MANIFEST.json`. | A published research package is not a submitted or accepted paper. |

## New primary effects

| Timing | Contrast | Effect (pp) | Pointwise 95% interval (pp) | Holm p |
|---|---|---:|---|---:|
| 0 | negative_main | +19.000 | [+11.073, +27.198] | 0.00585938 |
| 0 | proof_main | +0.597 | [-0.642, +1.865] | 0.667969 |
| 0 | interaction | +2.569 | [-0.028, +5.167] | 0.355469 |
| 1 | negative_main | +21.170 | [+14.410, +27.834] | 0.00585938 |
| 1 | proof_main | +1.017 | [-0.826, +2.906] | 0.667969 |
| 1 | interaction | +2.563 | [-0.806, +6.271] | 0.654785 |

Timing 0 means no added compute delay; timing 1 uses illustrative overlapping scheduled delays. Intervals are pointwise and the six p-values share the prespecified Holm family. Sign flips require symmetric block effects, not assumed randomized treatment assignment. These results supply neither equivalence nor a universal operating boundary.

## Remaining full-validation gate

The original signed deadline, physical measurement, production security, actual author approval and authenticated submission are not complete. No deadline was lengthened and the fast private-MAC endpoint does not satisfy the original signature requirement. See the matrix for the exact evidence and next action. No messages were sent and no submission was made.

## Descriptive control supplement

Benign means and checkpoint/onset/channel-stratified block effects are available in publication/array/Remediation_Control_Supplement.md and outputs/remediation_v1/control_and_factor_summary.json. These exploratory post-outcome aggregations add no tests, tuning or exclusions; the primary analysis is unchanged.

## RESOLVED

- **A: causal attribution**: Four matched arms share ACK, expiry, positive-credit and late-positive semantics; negative update and proof traffic cross independently. Separate active reference retained. Conditional effects within this fixture family; not attribution of the complete historical ns-3 gain.
- **B: identity / ordering**: Both physical attackers, two relay-ID permutations, 12 perturbed geometries, three retained checkpoints and benign controls executed. Geometry/checkpoint/onset/channel are balanced block factors, not a fully crossed population study.
- **C: censored-frozen equality**: 11927 matched decisions: 7023 risk differences, no ordering or action disagreement. 1010/4800 offline interventions change action. Offline sensitivity does not establish closed-loop radio gain or invariance to every risk input.
- **D: failure characterization**: Frozen onset/channel/geometry/checkpoint design and sustained-recovery/censoring metrics completed. No universal threshold; narrow fixture family and conditional latency summaries.
- **E: loss versus lateness**: Benign delayed censored critical packets: 7 lost, 563 late, 30 timely of 600. Sink and source latency endpoints remain separate. Injected Cooja delays are not a serial CPU model or measured timing.
- **F: security assumptions**: Implementation-wise key/evidence/ACK/session/provisioning matrix; unsupported identity/ACK/processing/credit mutation checks. Public fixture validation supplies no secrecy against fixture-key holders or runtime Byzantine truth guarantee.
- **G: statistical analysis**: 12-block paired inference; six primary Holm contrasts; separate secondary families; pointwise bootstrap intervals and explicit symmetric sign-flip assumption. No nonsignificance-as-equivalence claim or invented deployment margin; no packet pseudoreplication.
- **I: manuscript and exhibits**: Completed evidence integrated; old 11 tables, 12 images and 10 native equations preserved. Two data-derived figures and six-contrast Table 12 added. Array-specific final portal compliance and author approval remain separate gates.
- **J: reproducibility / publication**: Frozen source, raw outputs, analyses, environments, regression records, durable releases and hashes provided. A published research package is not a submitted or accepted paper.

## IMPLEMENTED BUT UNVALIDATED

- **H: production security**: Emulated key/session negative controls exist; protected storage, authenticated provisioning, firmware authenticity and reset-safe device sessions lack board evidence. Board-specific port, secure provisioning/boot/storage tests and reset/power-loss captures required.

## SCIENTIFIC LIMITATION

- **Transfer scope / onset threshold**: The shared four-node graph, 38 m progress normalization, clipped source progress, two onsets and three retained policies support conditional transfer findings. No universal threshold or broad network-scale claim. Wider independently varied graphs and fully crossed warm-up/onset/checkpoint fixtures need a new frozen study if that claim is pursued.
- **E: original signed deadline**: Compiler-only O3 still misses 68/200; 200 packets and signed receipts delivered. A further endpoint-preserving crypto/execution redesign and separately frozen evaluation are required; no pass claimed.

## BLOCKED BY EXTERNAL ACCESS OR HUMAN CONFIRMATION

- **H: physical RF and energy**: No compatible physical boards/instruments accessible; linked Mac offline at this check. Provide compatible boards plus calibrated RF/current equipment; freeze protocol, acquire raw calibrated traces.
- **H: author approval**: Exact-version requests and approval register prepared; not sent; all final approval fields remain null. Actual authors must review the pinned paper and supply consent, roles, overlap and declarations.
- **H: authenticated submission**: Official guide returned 403 and browser homepage unavailable; authenticated requirements and assembled portal PDF unchecked. Accessible official guide and authorized authenticated portal session; actual declarations require author confirmation.

## 2026-10-19 endpoint-preserving follow-up

A separately frozen LTO/default-loop-optimization pilot completed at source `b52842496dc625ad30ff95bdefad4c107366080e`, run `39179074994`. All 200 packets and source-verified Ed25519 receipts passed functional acceptance, with 500 matching actor decisions and seven retained negative-control categories per topology. Original deadlines still miss 68/200; chain receipt delays are 299–308 ms and choice 213–220 ms. This unsuccessful compiler optimization is retained separately from O3. Public signatures, received-source linkage and one-bit signature rejection were independently checked on both profiles. See [execution and external gate handoff](EXTERNAL_GATE_HANDOFF.md) and `outputs/mcu_deadline_v2`. No physical measurements, production security certification, author consent or authenticated submission completion is claimed. The previously pinned Word/PDF remain unchanged; this is an additional diagnostic supplement.
