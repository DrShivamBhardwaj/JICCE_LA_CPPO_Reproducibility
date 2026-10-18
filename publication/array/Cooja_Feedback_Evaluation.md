# Cooja policy and feedback evaluation

The separately frozen comparison contains 600 runs: thirty independent seeds, five feedback arms, two attack settings and two timing settings. It offers 36,000 packets. These results do not replace or pool with the original 750-run, 180-run or 240-run evidence families.

## Group results

| Setting | Feedback arm | Delivery base (%) | Delivery delayed (%) | Critical failure delayed (%) | TX delayed (s) |
|---|---|---:|---:|---:|---:|
| Benign | Active proofs | 98.78 | 99.17 | 94.17 | 8.282 |
| Benign | Naive passive | 98.67 | 98.39 | 95.17 | 7.933 |
| Benign | Frozen prior | 98.33 | 98.50 | 95.00 | 7.932 |
| Benign | Censored + proofs | 98.50 | 98.72 | 94.50 | 8.277 |
| Benign | Censored passive | 98.33 | 98.50 | 95.00 | 7.932 |
| Blackhole | Active proofs | 71.39 | 79.11 | 96.00 | 7.931 |
| Blackhole | Naive passive | 47.00 | 54.89 | 96.67 | 7.341 |
| Blackhole | Frozen prior | 32.83 | 32.94 | 98.17 | 7.048 |
| Blackhole | Censored + proofs | 33.17 | 32.83 | 97.50 | 7.169 |
| Blackhole | Censored passive | 32.83 | 32.94 | 98.17 | 7.048 |

Means over thirty seeds. Base adds no instruction-cost delay. Critical failure uses the sink application delivery event after configured sink processing and includes missing packets. TX is summed modeled transmit-state duration across four motes; it is not joules.

## Primary paired contrasts

| Attack | Timing | Arm minus censored | Difference (pp) | 95% paired interval (pp) | Holm p |
|---|---|---|---:|---|---:|
| Benign | Base | active | +0.44 | -0.28 to +1.22 | 1 |
| Benign | Base | naive | +0.33 | +0.00 to +0.78 | 1 |
| Benign | Base | frozen | +0.00 | +0.00 to +0.00 | 1 |
| Benign | Base | censored_proof | +0.17 | -0.56 to +0.89 | 1 |
| Benign | Delayed | active | +0.67 | -0.06 to +1.44 | 1 |
| Benign | Delayed | naive | -0.11 | -0.44 to +0.17 | 1 |
| Benign | Delayed | frozen | +0.00 | +0.00 to +0.00 | 1 |
| Benign | Delayed | censored_proof | +0.22 | -0.61 to +1.11 | 1 |
| Blackhole | Base | active | +38.56 | +27.39 to +49.39 | 0.000159998 |
| Blackhole | Base | naive | +14.17 | +5.89 to +23.39 | 0.100879 |
| Blackhole | Base | frozen | +0.00 | +0.00 to +0.00 | 1 |
| Blackhole | Base | censored_proof | +0.33 | -0.11 to +0.78 | 1 |
| Blackhole | Delayed | active | +46.17 | +36.89 to +54.50 | 0.000159998 |
| Blackhole | Delayed | naive | +21.94 | +13.33 to +30.83 | 0.000419996 |
| Blackhole | Delayed | frozen | +0.00 | +0.00 to +0.00 | 1 |
| Blackhole | Delayed | censored_proof | -0.11 | -0.50 to +0.39 | 1 |

## Exploratory matched proof contrasts

These direct active-minus-censored-plus-proof comparisons were added after the primary protocol freeze, as documented in exploratory_analysis_amendment.json. Each endpoint uses a separate four-contrast Holm family; they are not confirmatory primary tests.

| Attack | Timing | Delivery difference (pp) | 95% paired interval (pp) | Exploratory Holm p |
|---|---|---:|---|---:|
| Benign | Base | +0.28 | -0.28 to +0.83 | 0.448086 |
| Benign | Delayed | +0.44 | -0.11 to +1.00 | 0.383496 |
| Blackhole | Base | +38.22 | +27.28 to +49.06 | 3.99996e-05 |
| Blackhole | Delayed | +46.28 | +37.06 to +54.61 | 3.99996e-05 |

Intervals are pointwise, based on 20,000 paired seed bootstrap draws. Two-sided paired sign-flip tests use 100,000 Monte Carlo draws and plus-one correction. Holm adjustment covers sixteen declared contrasts within the delivery family. The two secondary endpoints each have a separate sixteen-contrast family in paired_contrasts.csv. Sign-flip inference assumes exchangeability of paired differences under the null; intervals and tests are conditional on this fixed topology, checkpoint, traffic and radio model. Packets are not treated as independent experimental replicates.

## Execution and independent audit

All 61,845 decisions and 143,928 recorded ledger events were independently checked. The maximum reconstructed feature discrepancy is 1.1920929e-07; the maximum unmasked logit discrepancy is 2.20537186e-06. The frozen checkpoint SHA-256 is 25d6418482ac7318e9f73656aefe95c68fefeb3e1266c084f5993bf59c72ecf8.

The audit verifies hop HMACs, source tags, sink signatures, local ledger counts, candidate construction, policy decisions, source/sink IDs, transmitted/received envelopes and radio state-time conservation. Native images are retained with per-run hashes. Queue overflow or missing final records would fail acceptance; packet loss remains an outcome. The original checker’s freshness tolerance failure and its correction are recorded without altering simulation sources, packets, decisions or statistics.

## Scientific boundaries

Only one source, two feasible relays and a sink are tested. All conditions use the same public test keys, nominal energy/queue/LQI fields, unicast beacon roster and fixed trained attention weights. Active proofs and censored-plus-proof share a proof-generation rule, not necessarily byte-identical realized traffic after routing diverges. The attack is one relay beginning to drop application data after packet ID 20; spoofing, collusion, jamming and compromised-key claims are outside this experiment.

The delay setting is an illustrative scheduling sensitivity: 14 ms before outbound data, 1 ms before other outbound frames, 81 ms before received public-receipt handling, 31 ms before sink data handling and 1 ms before other received frames. It is not instruction-level MCU emulation or a serial CPU queue model. Energest state durations do not establish measured current, physical energy or battery lifetime. The retained port can exclude beacons about 1 ms early because of float32-to-integer timestamp conversion; corrected auditing reproduces that representation.

Censored feedback cannot lower previously accumulated positive trust merely because later forwarding evidence is absent. Authentication establishes message validity under the test key model, not truthful forwarding behavior by a compromised relay. Physical hardware security and RF/energy validation remain open.

Implementation and reproduction details are in hardware/cooja_feedback/README.md. Twenty preflight runs, setup failures and a scheduler interruption are retained separately and excluded from the primary 600-run family. No author approval or submission is inferred from these experiments.
