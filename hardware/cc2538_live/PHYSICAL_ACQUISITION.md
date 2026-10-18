# Physical RF and energy acquisition: not executed

The available Mac exposes no detected USB sensor-board serial port. No power instrument or calibrated current/voltage recording is available to this session. Emulated radio traffic and nominal energy fractions cannot fill this gap.

A physical repeat of the four-node paths needs four compatible IEEE 802.15.4 CC2538 boards, board debug/programming access, and an external current/voltage instrument. Record the board revision, power boundary (whole board versus MCU/radio rail), sample timing, meter calibration/zero offset, supply voltage and raw acquisition files. A phone can collect serial logs if the interface supports it; it does not provide a calibrated sensor-board current measurement or an 802.15.4 CC2538 radio.

The present Renode image is NOT a flash-ready vendor board release. Its UART/radio register initialization and emulated 1 MHz SysTick assumptions need a real board startup/clock/peripheral port. Public fixture keys and fixed boot sessions must be replaced with private provisioning and persistent anti-replay/session management before any operational deployment.

The physical protocol should first repeat the exact offered-packet/delivery/receipt acceptance checks and authenticated negative controls, then test distance, obstruction, interference, power cycling and queue pressure under a declared schedule. Preserve failures and losses. Compare attention and matched controls with identical traffic, supply and RF conditions; use independent runs and paired confidence intervals rather than treating individual packets as independent replicates. Actual sample counts and durations must be chosen before inspecting comparative outcomes.

## Trace analysis

Export instrument samples as CSV columns `time_s,voltage_v,current_a` in SI units. Do not export a simulated trace as measured data. Supply acquisition metadata fields required by the script (including meter/calibration, firmware and packet-capture hashes).

```sh
python scripts/analyse_physical_power_trace.py --trace actual_samples.csv --metadata acquisition.json --output power_analysis.json
```

The maximum allowed sample gap is `max_sample_gap_s` in metadata, defaulting to two nominal sample intervals. Longer gaps are rejected. The script streams samples, checks finite values and monotonic time and integrates instantaneous voltage × current using the trapezoidal rule. It reports trace integrity, not physical provenance certification. Exclude unrecorded gaps only under a declared rule; do not silently interpolate acquisition outages. No measured energy values are included in this repository extension.
