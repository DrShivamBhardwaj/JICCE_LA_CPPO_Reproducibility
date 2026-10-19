# Cooja radio-state and assumed-current sensitivity

All 600 completed historical runs were rechecked: 30 seeds, two attack settings, two timing settings and five arms. This is a new exploratory analysis of previously executed simulations, not 600 new runs. All 600 decompressed capture hashes match the retained audits; 2,400 node-final records conserve radio state time and match the archived endpoints. Every run offers 60 packets (36,000 total). The historical interrupted-attempt directory remains preserved outside the declared 600-case family.

Under the native attack setting, mean delivery is 32.833% for censored feedback and 71.389% for active proofs. Their mean summed TX durations are 7.04259 and 7.78680 seconds per four-node run, respectively; listen durations are 98.95341 and 98.20920 seconds. These are descriptive summaries of the original, confounded reference comparison. They are not matched causal attribution and are not pooled with the separate 1,440-run factorial family.

## Energy interpretation

For radio-only constant state currents, `E = V * I_listen * (T_listen + r*T_tx)`, where `r = I_tx/I_listen`. The bracketed coefficient has units of seconds. Ratios 0.5, 1, 2 and 3 are explicit assumptions, not board measurements. At ratio 1 every arm has the same radio energy in this always-on accounting window. The ordering can reverse on opposite sides of ratio 1. Lower TX airtime therefore cannot establish physical energy savings without current measurements and an explicit supply boundary. CPU, cryptography, sensing, regulator and host energy are excluded; no joules, measured current, calibrated RF, battery life or production security are certified.

`radio_delivery.*` plots descriptive 30-seed stratum means; no error bars are claimed. `assumed_current_sensitivity.*` plots the specified model sensitivity using verified state times. Each is supplied as PNG, PDF and editable SVG.

## Reproduce

```
python experiments/cooja_radio_energy_v1/analyze.py
python experiments/cooja_radio_energy_v1/plot.py
```

Requires Python and matplotlib. The retained raw inputs are `outputs/cooja_feedback/primary_600`; input capture and audit hashes are in `capture_hashes.json`. Startup inspection corrected the seed count to the archived 30-seed design and distinguished the historical interrupted-attempt directory from the completed case roster before any successful aggregate analysis. No cases or outcomes were removed.
