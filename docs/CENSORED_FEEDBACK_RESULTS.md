# Frozen censored-feedback holdout results

The design and all-required decision rule were published before evaluation at [4027f07](https://github.com/DrShivamBhardwaj/JICCE_LA_CPPO_Reproducibility/commit/4027f071322cb5682f39329f656d76df3b68ff62). Holdout fixtures 77001–77030 were not used to develop the ledger; 76001–76030 informed the redesign. Pilot 76901 is excluded. Checkpoints remain the paired 41001–41030 training checkpoints.

## Outcome

750 runs, 45,000 source packets, five settings and five controls. All four frozen incremental gate checks passed. This is a simulation mechanism result, not satisfaction of the original absolute QoS requirements.

| Blackhole comparison | Paired delivery difference, percentage points | 95% CI | Holm p |
|---|---:|---|---:|
| Censored minus active proofs | +4.667 | [2.365, 6.969] | 0.0161 |
| Censored minus frozen prior | +0.056 | [-0.498, 0.609] | 1 |
| Censored minus naive passive | -0.167 | [-1.557, 1.223] | 1 |
| Censored minus capacity MLP | +0.444 | [-1.461, 2.350] | 1 |

Censored delivery was 75.94%, active-proof delivery 71.28%. Blackhole energy per delivered payload byte decreased by 0.0006443 J/B (CI [-0.0009740, -0.0003145], Holm p=0.0239). The critical-violation contrast did not survive correction. The family includes 60 tests over all settings, comparators and three endpoints. Confidence intervals above are unadjusted paired intervals over 30 fixtures.

Against frozen prior, the one-sided delivery lower bound was -0.405 percentage points (margin -1), the critical-violation upper bound +0.925 points (margin +1), and the geometric energy-ratio upper bound 1.00505 (margin 1.02). These are non-inferiority checks, not superiority tests. No other setting's delivery contrast against active proofs survived correction. Absolute blackhole critical violations remain about 26%, above the original 1.5% budget.

The evidence supports a bounded replacement of the active proof-based mechanism. It does not isolate a benefit from censoring, updated risk coordinates, or attention. Active proofs jointly change feedback semantics and radio traffic; the comparison is not a pure airtime intervention. Passive/frozen arms emitted zero proof requests; active proofs requested 3,369 across 150 runs. Historical negative results and raw traces remain available.

## Audit and reproducibility

The internal verifier passed 750 runs, 67,522 decisions, 75,750 energy identities, 24,747 passive observations and 28,353 evidence updates; 7,020 missing observations expired as censored. It reconstructs features/actions and ledger updates, matches received forwarding-frame provenance and range, and checks radio accounting. It does not independently replay beacon-receive callbacks or complete QoS/link histories. It is not external packet capture or authentication validation.

The full unit suite passes 51 tests. The physical callback control checks actual passive overhearing, silence at an out-of-range observer and zero proof frames.

From the repository root (runtime versions in requirements-censored.txt; document generation additionally needs python-docx, lxml, matplotlib and LibreOffice):

```bash
python -m pip install ns3==3.44.post0 --no-deps
python -m pip install -r requirements-censored.txt
python scripts/build_ns3_passive.py
python -m pytest tests -q
python scripts/test_ns3_passive.py
python scripts/run_ns3_censored.py
python scripts/analyse_ns3_censored.py
python scripts/verify_ns3_censored.py
python scripts/build_censored_figure.py
python scripts/integrate_censored_manuscript.py
```

The analysis and verification scripts consume canonical outputs/ns3_censored files. Re-running the evaluation overwrites canonical traces; preserve the release files first when comparing environments.

## Model limits

Receipts are unauthenticated, and blackhole relays do not forge receipt/beacon content. Overhearing is established watchdog practice (Marti et al., MobiCom 2000, DOI 10.1145/345910.345955). Its ambiguities, collusion and unseen loss cannot be interpreted as calibrated attack labels. The asymmetric effective-count score is an evidence preference proxy, not an IDS posterior.

Beacon energy/queue values use simulator-side metadata keyed by a transmitted beacon identifier and become available only after a real radio receive event. Values are not decoded from serialized beacon fields; the charged 64-byte beacon is modeled telemetry transport, not a demonstrated embedded implementation. Geometry and packet-class configuration are simulator inputs. Radios already listen in every arm; CPU, sensing, cryptography and hardware calibration are excluded. No live IDS or physical deployment is validated.

The integrated manuscript is a review draft with retained negative stages, 67 native equations, eight figures and 28 references. Current journal portal requirements, author forms and a final editorial fit/length check remain necessary before a new submission. No manuscript or email has been submitted.
