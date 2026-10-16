# Section by section editorial review and revised passages

**Editorial assessment:** The manuscript is defensible as a reproducible feedback benchmark with an authenticated host-routing implementation and emulated radio bridge. The evidence does not support presentation as a superior neural routing protocol, a battery-realistic long-lived deployment or an embedded inference achievement. Publication suitability remains a reviewer/editor decision.

**Scope:** This pass changes prose, definitions and pseudocode formatting. It does not retrain a policy, change a simulator, replace a checkpoint or add statistical tests. All ten native equations, seven tables and ten figure images are preserved byte-for-byte against the preceding verified manuscript.

## Abstract

**Critical vulnerabilities and limitations.** The prior abstract spent too much space listing implementation stages before stating the benchmark contribution. It also needed one clear boundary between host execution and emulated firmware.

**Revision.** The revision leads with the feedback problem and controlled comparison. The 750-run result, 180-run transport study and exploratory stress result remain distinct. The full abstract is below 250 words.

**Specific improvement:** Sharpen contribution; distinguish the 750-run feedback benchmark, 180-run transport study and post-review stress evidence.

**Revised text:** Missing forwarding evidence can reflect packet loss, contention or an unobserved transmission, making feedback design a joint problem of inference and airtime. We benchmark ACK-gated censored passive feedback against active proofs in 750 IEEE 802.15.4 runs on 30 new fixtures, with naive-passive, frozen-prior and capacity-matched policy controls. Under blackholes, delivery increases from 71.28% to 75.94%, a paired gain of 4.67 percentage points (95% interval 2.36–6.97; Holm-adjusted p=0.0161). Energy per delivered byte falls while total modeled radio energy rises slightly. The controls do not establish a unique censoring or attention advantage. A separate 180-run experiment tests frozen policies over authenticated messages and node-local records. Attention delivers 81.61% in benign conditions and 61.11% under selective dropping, without an established advantage over greedy or multilayer-perceptron routing. Serial-interface testing identifies and corrects a receive-time freshness error. Compiled UART-to-radio firmware runs on four emulated Cortex-M3 boards; neural inference and cryptography execute on the host PC. Each host-policy control delivers ten of ten packets. An exploratory 60–300 s extension exposes routing-energy exhaustion and increasing service debt. The contribution is a traceable comparison of feedback mechanisms and transport boundaries; the evidence does not establish sustained operation, physical-board performance, measured energy consumption or absolute deadline compliance.

## 1. Introduction

**Critical vulnerabilities and limitations.** A rhetorical question and repeated statements about what the work does not invent weakened the contribution. An improvement over active proofs must not be presented as proof of attention or censoring superiority.

**Revision.** Replaced the rhetorical question with the actual contrast and decision rule. The contribution now identifies ACK eligibility, record-level maximum strength and censored missing evidence before discussing attribution.

**Specific improvement:** Replace a rhetorical research question with the concrete experimental contrast.

**Revised text:** Earlier architecture comparisons found no joint advantage over a multilayer perceptron of similar capacity. A subsequent 600-run telemetry study likewise found no advantage after correction for multiple testing and exposed the traffic cost of active proofs. Both stages and their raw outputs are retained. They motivated the present comparison of receipt-assisted passive feedback with active proofs, subject to prespecified margins against a frozen-prior control on new fixtures.

**Specific improvement:** State the implemented mechanism before its provenance and figure references.

**Revised text:** The technical contribution is a controlled comparison of feedback eligibility, evidence retention and missing-observation handling. Own first-hop ACK success gates credit; an observer–relay–packet record retains its strongest matched observation; missing evidence leaves the effective failure count unchanged. Packet-reception callbacks connect the ledger to simulated radio events. Figures 1 and 2 show the state boundaries and event logic, respectively. The benchmark builds on established watchdog, censoring and learning methods.

**Specific improvement:** Distinguish replacement performance from mechanism or architecture attribution.

**Revised text:** The prespecified decision combines a blackhole delivery comparison against active proofs with delivery, critical-service and energy-efficiency margins against frozen-prior attention. Naive-passive and capacity-matched controls assess whether the outcome can be attributed specifically to censoring or policy architecture. An improvement over active proofs alone cannot establish either attribution.

## 2. System model and methods

**Critical vulnerabilities and limitations.** State indices were underspecified. Packet-level evidence and pair-level effective counts were conflated, q denoted both link success and a neural query, and source debt was described too similarly to the evaluated sink-delay endpoint.

**Revision.** Defined all indices, guarded Eq. (4), fixed the registration-time convention for q and distinguished receipt-age debt from sink-arrival violations. Native displays (1)–(6) remain unchanged because they already match the executable formulas.

**Specific improvement:** Link the heuristic to the actual sensitivity experiment without inventing tuning history.

**Revised text:** Equation (1) uses hand-set preselection coefficients, not learned parameters. The retained source records the values but contains no systematic tuning history. The later ±20% coefficient experiment in Section 5.5 is a local sensitivity check and does not retrospectively optimize this score. Equation (2) divides the query–key product by the square root of 96, as implemented in PyTorch.

**Specific improvement:** Define observer and relay indexing and distinguish the current link estimate.

**Revised text:** • For observer u and candidate v, g is sinkward progress divided by 50 m and q is the current estimated MAC success probability; both are dimensionless.

**Specific improvement:** Close the dimensional definitions for Eq. (1).

**Revised text:** • Candidate energy fraction e is remaining modeled energy divided by 0.5 J; Q is pending-request pressure normalized by 32; R is the dimensionless risk score from Eq. (5). The preselection score S is dimensionless.

**Specific improvement:** Define feature indexing and dimensions for Eq. (2).

**Revised text:** • For context vector x at observer u and candidate feature vector h for link (u,v), ℓ is a dimensionless action logit. Both feature vectors contain normalized, dimensionless coordinates in the frozen benchmark.

**Specific improvement:** Resolve the overload between neural query notation and link reliability.

**Revised text:** • qθ and kθ are learned query and key transforms; bθ is the learned scalar candidate bias. The symbol qθ denotes a neural transform, whereas q in Eqs. (1) and (4) denotes link success. Parameters θ are fixed during evaluation.

**Specific improvement:** Distinguish packet-specific state from pair-specific effective counts.

**Revised text:** Observer u maintains a separate record for each selected sensor relay v and packet p. Evidence strength s and credited strength c are indexed by that record; effective counts α and β are shared across records for the same observer–relay pair. Each record stores the link-success estimate at registration, ACK status and expiry. A matched overheard forwarding frame contributes strength 0.5 and a reverse receipt generated by sink delivery contributes strength 1.0. Equation (3) retains the maximum, suppressing duplicate credit.

**Specific improvement:** Specify the initialization and full evidence-record index.

**Revised text:** • s is the strongest matched evidence for record (u,v,p), initialized to 0 and bounded by 1; it is dimensionless.

**Specific improvement:** Define event indicators rather than treating overhearing as proof of reception.

**Revised text:** • I_overheard and I_receipt are dimensionless binary indicators of a matched forwarding-frame event and reverse-receipt event for the same record. Their weights are 0.5 and 1 in Eq. (3).

**Specific improvement:** Make the Eq. (4) guard and registration-time convention explicit.

**Revised text:** Credit is assigned only when the observer’s own first hop is acknowledged and s exceeds c. Evidence received before the ACK is stored. When that ACK arrives, the same eligibility check applies to the stored evidence. In Eq. (4), q denotes the value cached when record (u,v,p) was registered, rather than a later link estimate. The update is executed only for a strictly positive uncredited increment:

**Specific improvement:** Separate pair-level and packet-level indices in the update.

**Revised text:** • α is the dimensionless effective success count for observer–relay pair (u,v), initialized to 1; c is the dimensionless credited strength for record (u,v,p), initialized to 0.

**Specific improvement:** Specify clipping bounds, positive-increment guard and credit assignment order.

**Revised text:** • q is the dimensionless cached registration-time link-success estimate. The clip operator limits each positive increment to [0.05, 1]; c is then set to the current s.

**Specific improvement:** Specify ACK-relative expiry and all late-observation upgrades, consistent with FeedbackLedger.evidence.

**Revised text:** In the censored arm, β stays at its initial value of 1 for each observer–relay pair. A failed first hop closes the record without positive credit. For an acknowledged first hop, expiry is set 150 ms after the ACK; absent forwarding evidence causes closure without a failure increment. A later matched observation can still increase s and earn previously unassigned credit. For q<0.1, the 0.05 floor can make two half-credit updates exceed one full q-weighted update. The smallest q in the audited decisions was 0.6923, so this case did not occur in those decisions.

**Specific improvement:** Remove repeated caveats while preserving the distinction between evidence state, effective counts and probabilistic coverage.

**Revised text:** The static floor in Eq. (4) is a heuristic on effective counts, not a Bayesian update. Max-strength deduplication limits the record’s evidence state but does not remove this clipping artifact. In Eq. (5), 1.645 is a fixed multiplier on a beta-form standard deviation; it supplies neither calibrated 95% coverage nor an exact Beta quantile. Changing these rules would define a different feedback mechanism.

**Specific improvement:** Avoid calling an uncalibrated score a probabilistic mean or confidence bound.

**Revised text:** With the rate-anomaly term disabled, the retained policy maps the pair-specific effective counts to a risk coordinate ρ and an augmented routing score R:

**Specific improvement:** Define the scale and range of Eq. (5).

**Revised text:** • ρ and R are dimensionless scores for observer–relay pair (u,v). The factor 0.75 scales both the failure-related coordinate and its uncertainty term; clipping bounds R to [0, 1].

**Specific improvement:** State the variance indexing and limit of its probabilistic interpretation.

**Revised text:** • σ = sqrt[αβ / ((α+β)²(α+β+1))] is dimensionless, with α and β taken from the same observer–relay pair. The beta-form expression supplies a score component, not an evaluated posterior interval.

**Specific improvement:** Define Eq. (6) as an event-indexed source update, not a physical queue or per-slot recurrence.

**Revised text:** For a fixed source and traffic class c, the online service debt is updated once when that source settles a packet. The recurrence follows the virtual-queue form associated with constraint tracking [18]:

**Specific improvement:** Make suppressed indices and units explicit.

**Revised text:** • Zc is the dimensionless debt for class c at the fixed source; bc is the dimensionless allowed violation fraction per settled class-c packet. The source index and update-event index are suppressed in Eq. (6).

**Specific improvement:** Correct the distinction between source-observed receipt age and sink delivery delay.

**Revised text:** • I_violation is 1 if no receipt is available by service expiry or receipt age exceeds the class deadline, and 0 otherwise. A separate loss-debt channel uses the analogous receipt/expiry outcome. These online indicators differ from the sink-arrival endpoint in Eq. (8).

**Specific improvement:** Connect the corrected Eq. (6) definition to the implementation and the Fig. (1) boundary.

**Revised text:** Only sources update these debts, on receipt or a 1.5 s expiry; intermediate relays retain no complete debt for transit service. Receipt age includes the reverse path, so a timely sink delivery can still produce a late source-observed outcome. The simulator maintains a shared visited set and reverse-path map without serializing their dissemination. Beacon energy and queue values are likewise supplied as metadata keyed to a transmitted identifier, with access gated by a radio-receive callback. Figure 1 marks these simulator-held inputs. Section 5 evaluates a separate authenticated implementation that decodes transmitted state.

**Specific improvement:** Explicitly scope the algorithm to the censored arm and separate the Table 3 controls.

**Revised text:** Algorithm 1 gives the censored-passive event procedure; Table 3 specifies the other arms. Figure 2 shows the ACK gate and strongest-evidence lifecycle. Radio callback controls check reception of a two-hop forwarding observation, absence of reception at an out-of-range observer and absence of proof frames in the passive arm. They test callback paths rather than authentication or intrusion-classification accuracy.

**Specific improvement:** Do not imply that intermediate relays receive an updated source-debt vector.

**Revised text:** The observation contains 13 context values and eight candidate rows of ten values each. Context records local energy and queue state, normalized sink distance, remaining deadline, traffic class and six node-local service-debt coordinates, updated only at sources in this benchmark. A candidate row records whether the node is the sink, its energy fraction, estimated MAC success, received link quality, queue pressure, sinkward progress, evidence risk and uncertainty, expected retries and normalized link delay. During radio transfer, received link-quality indication replaces the RSSI proxy used in training. The weights remain fixed despite this feature shift.

## 3. Experimental design

**Critical vulnerabilities and limitations.** The source-freeze paragraph repeated the pipeline description. Descriptive intervals could be mistaken for multiplicity-adjusted evidence.

**Revision.** Condensed the pipeline prose while retaining both complete source hashes, all fixture identifiers and the pairing caveat. The distinction between unadjusted t intervals, Holm-adjusted p-values and exploratory bootstrap intervals is retained.

**Specific improvement:** Remove redundant pipeline narration while preserving all fixture identifiers and the complete hash.

**Revised text:** Figure 3 records the source freeze, technical pilot and retained evaluation runs. Telemetry fixtures 76001–76030 informed the redesign. The protocol, source and decision rule were committed as 4027f071322cb5682f39329f656d76df3b68ff62 before fixtures 77001–77030 were evaluated. Technical pilot 76901 is excluded from inference. Each new fixture uses unchanged attention and MLP checkpoints from seed 41001 plus its fixture offset.

## 4. Results

**Critical vulnerabilities and limitations.** The phrase “only the blackhole delivery comparison survived” could be misread as denying the significant energy-per-byte result. The tiny total-energy increase could also appear inconsistent after rounding the arm means.

**Revision.** Restricted the significance statement explicitly to delivery contrasts. Reported the mean energy difference as calculated before rounding. Kept total energy, energy per delivered byte and PHY transmission count separate.

**Specific improvement:** Prevent a delivery-specific significance statement from being read as excluding the energy-per-byte result.

**Revised text:** Under blackholes, censored passive attention delivered 75.94% of offered packets, compared with 71.28% for active proofs. The paired gain was 4.67 percentage points (95% CI [2.36, 6.97]; Holm p=0.0161). Figure 4 compares delivery contrasts across settings; Fig. 5 shows the paired blackhole observations and all control contrasts. Among the delivery contrasts, only the blackhole comparison against active proofs survived the 60-test correction. The energy-per-byte contrast also survives correction (Section 4.2).

**Specific improvement:** Explain the rounded energy difference and denominator-driven efficiency gain.

**Revised text:** Under blackholes, energy per delivered payload byte decreased by 0.0006443 J/byte relative to active proofs (95% CI [−0.0009740, −0.0003145]; Holm p=0.0239). Total modeled sensor radio energy rose from 22.546943 to 22.547473 J, with a mean increase of 0.000531 J computed before rounding. The lower ratio reflects delivery efficiency rather than reduced total energy. Receiving/listening accounts for an average 99.36% of modeled sensor radio energy across the 750 runs.

## 5. Authenticated transport and virtual validation

**Critical vulnerabilities and limitations.** The negative attention–greedy difference does not prove greedy superiority. Feature-shift explanations are hypotheses, not identified causes. Full actor–critic weight storage is not an unavoidable actor-only deployment footprint.

**Revision.** Consolidated null-result interpretation and host/MCU boundaries. Retained exact sample sizes, receipt counts and signatures. Post-review stress tests report failure rather than being used to imply sustained operation.

**Specific improvement:** Separate the observed null comparison from causal hypotheses and deployment judgment.

**Revised text:** The −1.78-point attention–greedy difference under selective dropping has an interval that crosses zero. It therefore supports neither attention superiority nor a claim that greedy is better. Replacing the training RSSI proxy with LQI, using raw queue counts and restricting forwarding credit to signed receipts can change the policy’s input distribution; the experiments do not isolate their causal effects. Greedy avoids neural weights and tensor inference, making it a sensible starting point for deployment assessment, although neighbor state, authentication and packet processing still incur costs.

**Specific improvement:** Consolidate repeated non-superiority statements and retain all system-cost boundaries.

**Revised text:** The frozen host policies operate on serialized simulated-radio frames with multiple relay choices. For attention, critical-deadline failure is 31.17% in benign runs and 47.83% under selective dropping when undelivered packets count as failures. Total modeled radio energy is approximately 2.519 and 2.520 J per six-node run. Always-on listening and repeated authenticated telemetry dominate this radio-only account; embedded CPU and cryptographic energy are excluded.

**Specific improvement:** State the actor-only resource result directly without conversational reference to correcting a review.

**Revised text:** The inference actor contains 44,161 parameters, requiring 176,644 FP32 weight bytes before runtime buffers; the full actor–critic contains 63,368 parameters. Removing training-only heads therefore changes the storage estimate, but neither count establishes target feasibility. Duty-cycled MAC performance, drift tolerance, target inference and measured energy require separate validation.

## 6. Discussion

**Critical vulnerabilities and limitations.** The discussion repeated attribution caveats and risked calling all sensitivity unknown despite the added coefficient experiment.

**Revision.** Recast the attribution argument and limited the unknown-sensitivity statement to settings not varied in Section 5.5. Clock drift, duty cycling, state provenance and record reclamation remain open validation questions.

**Specific improvement:** Make the contribution and attribution limits explicit in one compact argument.

**Revised text:** The benchmark supports replacing the tested active-proof mechanism within its prespecified margins. Because eligibility and expiry rules change together with control traffic, the observed difference cannot be assigned to proof airtime alone. Comparisons with naive passive and frozen prior do not establish a unique censoring effect after correction. Retaining the earlier unsuccessful architecture comparisons prevents the feedback result from being recast as evidence for neural-policy superiority.

**Specific improvement:** Reconcile the sensitivity limitation with the new coefficient experiment.

**Revised text:** The holdout fixes passive strength at 0.5, record expiry at 150 ms, cache life at 0.75 s, the current model and all inference checkpoints. Section 5.5 varies the preselection coefficients only; sensitivity to these other choices remains unknown. Changes to serialization, ACK authentication, service tracking or ledger retirement require a separately frozen experiment because they change the evaluated mechanism.

## 7. Conclusions

**Critical vulnerabilities and limitations.** The contribution and deployment boundary were separated by a long list of implementation stages.

**Revision.** Condensed the conclusion around the controlled replacement result, null controls, separate authenticated study and explicitly host-controlled MCU bridge. The negative 60–300 s extension remains visible.

**Specific improvement:** Close on the supported contribution, null controls and host/MCU boundary without implying sustained deployment.

**Revised text:** ACK-gated censored passive feedback passed the prespecified replacement test on 30 new fixtures, improving blackhole delivery over active proofs by 4.67 percentage points. The matched controls establish neither a unique censoring effect nor an attention advantage. In the separate 180-run authenticated transport study, frozen policies operate on received wire state and local service records without an established attention benefit. Serial-interface testing corrected a receive-time error, and four emulated Cortex-M3 boards execute the compiled UART-to-radio bridge while inference and cryptography remain on the host. The 60–300 s extension exposes routing-energy exhaustion and increasing source debt. Together, these results define the benchmark’s supported feedback comparison and deployment boundary: absolute service compliance, physical-board operation, embedded policy/crypto execution and measured energy remain unvalidated.

## Equations 1–6 coherence audit

| Equation | Indices and units | Verified interpretation |
|---|---|---|
| (1) | Observer u, candidate v; score and features dimensionless | g is progress/50 m; energy is normalized by 0.5 J; queue pressure by 32. The coefficients are hand-set. R comes from Eq. (5). |
| (2) | Context at u and candidate link (u,v); 96-dimensional learned projections | Query–key product is divided by √96. qθ is a neural transform, distinct from link probability q. Numeric tensor identity was verified in the preceding math audit. |
| (3) | Record (u,v,p); s begins at 0, stays in [0,1] | Maximum of previous evidence, 0.5 for a matched forwarding event and 1 for a matched receipt. Duplicate events cannot increase s beyond the retained maximum. |
| (4) | α belongs to pair (u,v); s and c to record (u,v,p); all dimensionless | Execute only after own-hop ACK success and s>c. q is the estimate cached at registration. Increment α using clip(q(s−c),0.05,1), then c←s. The floor is heuristic and can distort split credit. |
| (5) | Pair-specific α, β, ρ, σ and R; all dimensionless | β remains 1 in the censored arm. 1.645×0.75σ is an uncalibrated score augmentation, not a Bayesian quantile or 95% bound. |
| (6) | Fixed source, class c, settlement-event update; source/event indices suppressed | Zc is a virtual service debt. Online violation uses receipt age or expiry; evaluated V uses sink-arrival delay. The recurrence is not a queue-stability theorem. |

### Portable mathematical reading

For Eq. (4), let δ = s_uvp − c_uvp. The displayed update is evaluated **only if** the first-hop ACK succeeded and δ>0. Otherwise α and c do not change. This guard prevents clip(0,0.05,1) from creating credit in the absence of new evidence. It follows the implementation and is not a new update rule.

For Eq. (6), at a fixed source the event-indexed reading is Z_c(n+1)=max{0,Z_c(n)+I_c(n)−b_c}. Here n indexes settled class-c packets. I_c(n) uses receipt availability/age at the source, whereas Eq. (8) uses reception at the sink. A timely sink delivery can therefore coexist with a source-observed violation.

## Algorithm indentation and semantics

Algorithm 1 now uses 17 numbered lines with three indentation depths. Routing requests, first-hop outcomes, evidence events, polling and source settlement are separate event branches. Successful ACK/evidence events share the Eq. (4) credit guard. The heading explicitly scopes the procedure to censored passive; Table 3 retains the distinct active, naive, frozen and capacity-control semantics. Late matched evidence—not only a late receipt—can upgrade an acknowledged censored record. Non-sink registration and the once-only source settlement rule are explicit.

## Figure to text and statistical cross references

| Figure | Data or implementation anchor | Narrative check |
|---|---|---|
| 1 | ns-3 callback path, simulator cache, shared visited/reverse state | Source-held metadata and non-serialized routing state remain visible; no distributed-state claim is imported from Section 5. |
| 2 | FeedbackLedger event logic | ACK gating, retained maximum and late upgrades agree with the revised algorithm; Eq. (4) remains conditional. |
| 3 | Frozen source 4027f071322cb5682f39329f656d76df3b68ff62 | Development 76001–76030, pilot 76901, holdout 77001–77030, 750 runs and 45,000 offered packets agree. |
| 4 | Frozen delivery paired analysis | Common −2 to +9 point axes; bars are unadjusted 95% t intervals. Visual exclusion of zero is not substituted for the Holm rule. |
| 5 | 30 paired blackhole fixtures and all four controls | +4.67 points against active proofs; −0.17, +0.06 and +0.44 against the other controls remain unadjusted effect displays. |
| 6 | PHY-state energy attribution | Total energy increases slightly; energy per byte falls; receive/listen share is 99.36%. Units are mJ, mJ/byte and frames. Holm p=0.0239 for energy per byte comes from the retained test family, not plotted interval adjustment. |
| 7 | Authenticated host, PTY and Renode branches | Host executes policy/HMAC/Ed25519. Emulated MCU executes C UART/FIFO/MAC-ACK bridge. Ten-packet functional checks do not estimate deployment reliability. |
| 8 | 180 authenticated runs and retained exploratory bootstrap analysis | All four delivery-effect intervals cross zero; no attention or greedy superiority claim. 10,000 paired resamples, seed 94001. |
| 9 | 18 executed 60/300 s runs, 3 fixtures per arm/horizon | Figure shows the 300 s trajectories: delivery plateau, rising debt, retained records. It is evidence against sustained-operation claims under the tested model. |
| 10 | 33 coefficient-sensitivity runs | Ten perturbations × 3 fixtures give 30 zero delivery contrasts. The baseline adds 3 runs. Shown ranges are observed ranges, not CIs or equivalence tests. |

## Critical vulnerabilities and limitations that editing cannot resolve

- The benchmark changes feedback semantics together with traffic, so the active-proof contrast cannot isolate airtime cost.
- Three-fixture stress and sensitivity extensions are exploratory. Flat sensitivity endpoints do not prove broad parameter robustness.
- PHY accounting continues after the routing energy gate closes; post-depletion energy is not battery-realistic operation.
- Duty-cycled MAC performance, clock drift, embedded inference/cryptography, peak MCU SRAM and measured physical energy remain unvalidated.
- Open raw traces and repeated checks strengthen reproducibility but do not supply an independent radio implementation or external packet capture.

## High novelty opportunities

The strongest next study would match feedback semantics across arms and decide when to acquire forwarding evidence under measured wake-up and authentication costs. Reserve new topologies before testing, compare a low-cost greedy controller with a learned acquisition policy, and report event-log memory reclamation and deadline-debt growth under sustained traffic. This would test the value of evidence acquisition rather than re-labeling the current null architecture comparisons as a routing advance.

