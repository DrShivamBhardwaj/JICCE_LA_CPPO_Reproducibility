# Compiled MCU and virtual radio validation

Renode 1.17.0 executes our compiled ARM Cortex-M3 firmware on four CC2538 emulated boards. A range medium connects a four-node chain. Actual host processes run the frozen routing policy and cryptography; firmware parses UART commands, bounds frames, drives the radio FIFO and correlates MAC ACKs. This is a working virtual MCU experiment, not a physical hardware validation.

## Reproduce

Install Python dependencies in a dedicated environment:

```bash
python -m pip install -r requirements-emulation.txt
python -m pip install --no-deps ns3==3.44.post0
```

Install the official Renode 1.17.0 Linux portable release outside this repository and outside directories named `/tmp/renode-*` (Renode cleans its temporary directory namespace):
https://github.com/renode/renode/releases/tag/v1.17.0

```bash
python scripts/run_renode_boards.py --renode /absolute/path/to/renode --policy attention
python scripts/run_renode_boards.py --renode /absolute/path/to/renode --policy mlp
python scripts/run_renode_boards.py --renode /absolute/path/to/renode --policy greedy
python scripts/audit_renode_boards.py
```

The runner compiles `bridge.c` using Zig 0.17.0, creates four UART pseudo-terminals, waits for firmware readiness, runs five probes and starts four host adapters. New captures use unique directories; existing results are never overwritten. The audit verifies the three archived final fixtures, rather than selecting the latest directory. Archived `chain.resc` files contain ephemeral port paths; use the runner to regenerate those paths.

## Retained results

The final `attention_20261016`, `mlp_20261016` and `greedy_20261016` folders under `outputs/renode_boards/` each delivered 10/10 offered packets, with ten verified source receipts. Every run passed five probes: explicitly uncalibrated telemetry, exact 114-byte radio delivery with ACK, rejection of 115 bytes, rejection of malformed hex and failure of out-of-range transmission. The public audit checks UART byte provenance, frame identities, ELF/source hashes and sink signatures. Private keys are ephemeral and not published.

Two development captures remain separate: `attention_startup_diagnostic_20261016` exposed a startup UART warning before readiness synchronization; `attention_ready_diagnostic_20261016` predates addition of the public sink key to the report. Both delivered 10/10, but the final fixtures use synchronized startup and complete public metadata. Their firmware images are retained as historical builds.

## Evidence boundary

- The MCU executes compiled C firmware. Routing, attention/MLP inference, source/hop HMACs and Ed25519 remain on the host.
- IEEE 802.15.4 frame and ACK handling run through Renode's radio model. Range reachability is deterministic, not a calibrated physical channel or the ns-3 PHY used in the statistical study.
- Energy telemetry is explicitly `emulated_no_power_model`, with placeholder remaining fraction 1.0. It is not used as a measured battery result. Pending queue telemetry counts MCU ACK records.
- The four-node chain has one feasible next hop at each relay. These are integration controls, not policy comparisons or reliability estimates. Nonzero deadline debts prohibit a deadline-compliance claim.
- No physical UART timing, RF interference, current measurement, flash-ready physical-board initialization or embedded inference/crypto timing has been validated.

For physical follow-up use `../BOARD_AND_ANDROID_GUIDE.md`. An Android phone can potentially serve as a USB host/gateway with an external radio and a dedicated app; it does not replace an IEEE 802.15.4 radio.

Official platform references:
https://renode.readthedocs.io/en/latest/networking/wireless.html
https://renode.readthedocs.io/en/latest/host-integration/uart.html
https://github.com/renode/renode/blob/master/scripts/multi-node/cc2538/rpl-udp.resc
