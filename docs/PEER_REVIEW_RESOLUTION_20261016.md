# Peer review resolution record

Base manuscript and frozen evidence: `ea747d8a86aa8f848002d3101adf58e30270f0b2`. The 750-run and 180-run studies remain unchanged. Post-review diagnostics are exploratory and do not enter the original Holm family.

| Concern | Action and evidence | Status |
|---|---|---|
| Neural architecture has no established advantage | Reframed title and contribution as a reproducible benchmark; retained null comparisons; greedy recommended as economical starting point, not proven superior. | Claims corrected |
| Eq. 2 multiplication instead of division | Executable tensor identity confirms division by sqrt(96); Word contains native fraction; PDF visually checked. No implementation bug found. | Verified reviewer allegation not reproduced |
| Eqs. 5, 7, 8, 9, 10 flattened | Native fractions and summation operators checked by XML audit; rendered displays inspected. Existing mathematical expressions retained. | Presentation verified |
| Eq. 1 coefficient origins | Explicitly hand-set constants; no tuning history invented. Added 33 new blackhole sensitivity runs, 3 fixtures, each coefficient ±20%. | Local sensitivity completed; broader robustness unproven |
| Clipping floor | Executable q=0.04 counterexample: two half-credits add 0.10, one full-credit adds 0.05. The frozen method is now explicitly a heuristic, not Bayesian inference. | Defect disclosed; alternative update remains a different mechanism |
| 1.645 score interpreted as coverage | Removed any basis for a calibrated 95% coverage interpretation; score multiplier identified as heuristic. | Interpretation corrected |
| PRISMA misnomer | Renamed figure and prose to experimental protocol pipeline. | Corrected |
| Fig. 4 inconsistent axes | Both panels use −2 to +9 percentage points. | Corrected |
| Fig. 6 missing title units | mJ, mJ/byte and frames included in subplot titles and axes. | Corrected |
| Fig. 7 target boundary | Explicit HOST PC inference/HMAC/Ed25519 and EMULATED MCU C UART/radio FIFO bridge. No fabricated board photographs. | Corrected |
| Unrealistic imagery | Exact observations/intervals, trace-derived diagnostics and implementation schematics only; no image generation, invented hardware or smoothed observations. | Verified data provenance |
| Host versus target claims | Abstract, Section 5.4, model-memory paragraph and diagram explicitly retain inference/crypto on host. | Corrected |
| MCU memory assessment | Full model 63,368 parameters; inference actor 44,161; FP32 weight storage 253,472 and 176,644 bytes. SRAM feasibility cannot be inferred from weight storage alone. | Arithmetic checked; target linker/peak-memory validation open |
| Greedy zero overhead | Clarified that greedy avoids neural weights/inference but still needs neighbor state, crypto and packet processing. Difference interval includes zero. | Corrected |
| Cause of transfer differences | Feature distribution shift presented as hypothesis; no causal feature attribution claimed. | Interpretation corrected; causal experiment open |
| Four-second horizon | Added 18 actual 60/300 s runs: 3 fixtures × 3 arms × 2 horizons. Recorded delivery, debt, retained watches and handle exhaustion. | Stress test completed; sustained-operation claim rejected |
| Long-run battery realism | Routing energy gate closes, but PHY/beacon accounting continues. The manuscript reports this model boundary instead of calling post-depletion energy physical battery use. | Limitation exposed, not repaired in frozen model |
| Queue overflow / stability | No handle exhaustion observed; one-second pending samples cannot establish absence of transient MAC queue drops. Debts increase. | No bounded-queue or stability guarantee |
| Duty cycling | Added explicit 0.008451 J marginal listening-window example and accounting requirements; no prediction of energy ranking. | Analytical concern addressed; duty-cycled MAC experiment not performed |
| Clock drift / timeout | Added contention, late receipt and separate-clock discussion. Shared-clock tests do not validate drift. | Scope corrected; drift experiment open |
| Mechanical prose | Removed RQ enumeration and PRISMA pre-emption; shortened headings; preserved scientific caveats. | Editorial revision completed |

## Executed checks

- `scripts/check_review_math.py`: numeric attention scaling, model/actor parameter counts, static-floor counterexample and native equation operators.
- `scripts/audit_array_figure_values.py`: 33 intervals, 750 source rows, 180 transfer rows and 240 original plotted observations reconciled.
- `scripts/analyse_review_extensions.py`: 18 stress and 33 sensitivity summaries reconciled against compressed final records. New figures show real per-run samples; ranges in sensitivity figure are observed ranges, not confidence intervals.
- `scripts/audit_array_manuscript.py`: frozen tables/equations, author details, inline exhibits, references and embedded image hashes.
- Targeted regression suite: `tests/test_censored_feedback.py`, `tests/test_auth_policy.py`, `tests/test_renode_audit.py`: **19 passed**. After rebuilding all historical ns-3 bridges and installing the missing pandas dependency, the complete suite passed: **83 passed in 5.12 s**.

## Reproduction

Install CPU PyTorch, ns3==3.44.post0, numpy, scipy, PyYAML, cryptography and python-docx. ns-3 is used through a compiled C bridge; its Python/cppyy bindings are not required.

```
python scripts/build_ns3_passive.py
python scripts/run_review_long_horizon.py --duration 60 --start 84001 --end 84003
python scripts/run_review_long_horizon.py --duration 300 --start 84001 --end 84003
python scripts/run_review_sensitivity.py --start 85001 --end 85003
```

Repeat the sensitivity runner with `--weight 0` through `--weight 4`, each with `--factor .8` and `--factor 1.2`. Then run the math check, extension analysis, figure builder, manuscript builder and audits. Use the retained protocol and summaries for the exact run scope. Reduced diagnostic traces retain run/final/evidence records; they are not advertised as complete event traces.

## Submission status

This revision corrects presentation and claim scope and adds negative stress evidence. It does not establish physical-board operation, embedded inference/crypto, duty-cycled MAC energy, clock-drift tolerance, long-run record reclamation or queue stability. These must not be described as resolved deployment validation. Coauthor approvals and final portal declarations remain author responsibilities.
