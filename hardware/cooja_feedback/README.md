# Cooja policy and feedback comparison

This experiment ports the frozen Q22 attention actor and the weighted feedback ledger into four native Contiki-NG motes. It is a separate policy-transfer evaluation, not a reproduction of the original 100-sensor experiment, a physical-board test or a claim of attention superiority.

## Controlled comparison

The planned family contains 30 independent radio/MAC seeds, five arms, two attack settings and two timing settings: 600 runs, each offering 60 packets at 300 ms intervals. Every arm uses the same frozen checkpoint, geometry, source schedule, nominal beacon energy/queue fields and authentication format. The arms are censored passive feedback, active proofs, naive passive feedback, frozen prior and censored passive feedback with proof generation enabled. The last arm matches the extra proof mechanism while retaining the censored evidence rule. It is not a claim that all packet-level random events remain coupled after traffic changes.

Positions are source (0,0), relays (45,15) and (45,-15), and sink (90,0) metres. UDGM transmission and interference ranges are 50 and 100 m. Receiver success probability is 1.0, so losses arise from modeled contention, missing ACKs, retries and application behavior. There is one source and at most two feasible relay choices. The blackhole condition drops application data at relay 1 from packet ID 20 onward, after the normal radio/MAC reception; no attack flag or true attack state enters the 93 policy features. This is a single noncolluding dropper, not a comprehensive adversarial model.

Native Cooja does not charge instruction cycles for the host-compiled actor or cryptography. The second timing setting adds the frozen protocol's illustrative per-packet delays: outbound data 14 ms; other outbound frames 1 ms; received public receipts 81 ms; sink data processing 31 ms; other received frames 1 ms. These are scheduling assumptions rather than a calibrated whole-node or serial-CPU service model. In particular, the two-candidate actor, queue service and simultaneous workload are not certified by the one-candidate MCU measurement. Energest reports modeled state durations; no current, joule, battery-life or compute-energy measurement is inferred.

## Actual events and feedback semantics

The patched native radio process calls a read-only observation hook after a real simulated frame reception and before MAC destination filtering. The hook parses the received IEEE 802.15.4 frame; it does not query a global packet history or infer that a transmission was heard solely from distance. Cooja interference/reception determines which frames reach it. The observer logs captured forwarding data and supplies half-strength passive evidence only to a matching local watch. Public test link keys permit retrospective envelope checks and observer validation in this fixture. This key access is not an operational key-distribution design or confidentiality claim.

Real CSMA send callbacks provide MAC outcome and transmission counts. Censored and naive passive records require a successful first-hop MAC outcome before positive credit; a failed first hop closes without a forwarding-failure increment. The 150 ms timer starts after that ACK. Censored expiry adds no failure and permits a later observed receipt to upgrade evidence while the matching feedback slot remains retained. Naive expiry adds a failure and closes late upgrades. The active arm accepts explicit proof events, uses registration-relative expiry and records missing proofs as failures. Its proof is sent after the relay's successful downstream MAC outcome and has an authenticated application envelope; it is not a public end-to-end sink signature. The frozen arm leaves effective counts unchanged. Direct-sink hops are excluded from the forwarding-risk ledger, matching their zero-risk candidate treatment.

Maximum retained strength is 0.5 for passive data and 1 for receipt/proof evidence. Each new credit applies the retained Python estimator's clipped expected-delivery weight, including its 0.05 floor. The fixed 1.645 multiplier remains a heuristic risk-score parameter, unrelated to bootstrap confidence intervals. The local pending routing table has sixteen entries and a two-second lifetime. Feedback slots are reused with routing slots; a closed censored watch can retain late-upgrade eligibility until that slot is reused, so the pending timeout is not a guaranteed feedback-retention horizon. This bounded implementation does not establish arbitrary-load stability.

The policy observation uses weighted alpha/beta risk instead of the earlier MCU pilot's integer success proxy. Features are reconstructed independently in Python from logged authenticated cache values, MAC link estimates, counts and local service debt. All trained weights remain frozen. A matching action on tested observations does not prove universal FP32/Q22 equivalence or that this transferred feature distribution matches training.

## Authentication boundaries

Data and beacons carry hop HMAC tags; source data carries a source–sink tag; returning sink receipts carry Ed25519 signatures. The original replay window and pending reverse-route checks remain in the port. Keys and sessions are public test fixtures, with boot identifiers 1000–1003 reset between independent simulations. This experiment does not validate secret storage, authenticated provisioning, device-persistent monotonic state, physical RF, side channels or compromised-key security. IEEE 802.15.4 MAC ACKs themselves are not given a new cryptographic authentication mechanism. Nominal energy, queue and LQI fields do not establish calibrated sensing, trustworthy telemetry or battery-aware operation.

## Independent verification

`scripts/check_cooja_feedback_ledger.py` compiles edge-case sequences against the C ledger and compares all four modes with the retained Python FeedbackLedger, covering early passive evidence, ACK gating, expiry, late upgrades, duplicate evidence, failed first hops and proof-only behavior.

`scripts/audit_cooja_feedback_quantized.py` replays each logged ledger operation through that Python reference, checks effective counts and feature snapshots, verifies application HMACs/source tags/public signatures, links captured frames to transmitted envelopes, checks actual observed-peer range, reconstructs all 93 features, compares the frozen FP32 policy with the Q22 decisions, reconciles unique offered/delivered/receipted IDs and verifies Energest state-time conservation. Packet losses remain outcomes; a missing offer, missing final report, queue overflow or inconsistent trace fails acceptance. TEST OK alone is insufficient. The audit records actual delays and missing receipts without relabeling partial delivery as full success.

The first setup pilot configured only one mote before boot completion and timed out. A later pilot used an offset topology inconsistent with the fixed policy's sink coordinate; it was replaced before the primary protocol was frozen. Both diagnostic captures remain outside the primary family. All 20 full-factorial preflight runs use a separate seed and are excluded from primary inference. The 600-run protocol was frozen before generating its outcomes. A scheduler interruption used to switch to four isolated native build directories is retained explicitly; it does not change experimental settings or exclude a result because of performance.

## Reproduction

Use Contiki-NG commit 4ccd1a3b9e767f168d12ec3df187fe6b7dc736b5 and the recorded Cooja commit/JAR. Create a separate Contiki worktree and apply `cooja-radio-observer.patch`; do not patch unrelated projects. Build Cooja with its supported JDK 25 and `./gradlew jar`. Regenerate the port with `python scripts/prepare_cooja_feedback.py`. The fixed-point weights and vendor crypto are reused from their retained repository paths.

```sh
python scripts/check_cooja_feedback_ledger.py
python scripts/run_cooja_feedback.py --output outputs/cooja_feedback/new_study --seed-start 93001 --seeds 30 --contiki /path/to/patched-contiki --cooja /path/to/cooja --java /path/to/jdk25/bin/java
python scripts/audit_cooja_feedback_quantized.py --run /path/to/one/run
```

The primary capture includes a protocol, configuration per run, native-image hash and retained native image. The parallel continuation script is an execution helper for the recorded Mac layout, not a portable substitute for the sequential runner. For statistical analysis, retain all declared arm/attack/timing cells and align by seed; use `analyse_cooja_feedback.py` only after every primary capture has passed audit. New acquisitions require a new empty output directory. Raw logs may be losslessly compressed after verification; the auditor supports both `.testlog` and `.testlog.gz` and records the SHA-256 of the expanded original bytes.

## Freshness representation audit correction

The firmware retains its original float32 timestamp followed by integer-millisecond conversion for the 750 ms cache-age test. Quantization and truncation can exclude a beacon about 1 ms earlier than an ideal acquisition timestamp. The first Python checker added a 1 microsecond boundary tolerance and admitted one such expired candidate; audit_revision.json preserves this failure and the corrected checker hash. The corrected auditor reproduces the declared representation. Firmware, packets, source observations and outcome measurements were not changed. This numerical boundary is a limitation, not physical clock validation.

The original scripts/audit_cooja_feedback.py is retained only to preserve the frozen checker and its documented boundary-tolerance failure. Use audit_cooja_feedback_quantized.py for primary captures. Analyse a fresh complete thirty-seed study with `python scripts/analyse_cooja_feedback.py --experiment /path/to/new_study`. Application frame counts in audit records describe submitted application requests; actual MAC attempt counts and transmit-state durations are reported separately.
