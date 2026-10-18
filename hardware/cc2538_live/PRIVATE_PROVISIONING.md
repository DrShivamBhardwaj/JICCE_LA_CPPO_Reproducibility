# Private provisioning and longer stream validation

The separate v2 image removes the deterministic public pairwise keys and fixed boot sessions from the ordinary packet path. It accepts one trusted emulator-UART provisioning operation before local start, then locks provisioning until reboot. Every run receives random 32-byte pairwise keys, a fresh sink signing seed and four distinct 64-bit sessions. Only the sink receives its signing seed. A host-side locked/fsynced allocation file reserves sessions before startup; concurrent allocation and exhaustion checks are retained. This is not MCU NVM, protected device storage or an authenticated provisioning link.

The sink uses a rolling 64-identity source replay window instead of a sixteen-packet lifetime limit. Pending records remain bounded at sixteen with two-second retirement. A hundred sequential packets therefore test repeated state reuse and source-window progression. They do not establish overload tolerance or 104-node scaling.

## Reproduce on the validation Mac

```sh
python scripts/prepare_cc2538_v2.py
python scripts/build_cc2538_v2.py
python scripts/run_cc2538_v2.py --renode /absolute/path/to/renode --topology chain --packets 100
python scripts/run_cc2538_v2.py --renode /absolute/path/to/renode --topology choice --packets 100
python scripts/check_cc2538_sessions.py
```

Each runner creates a new public output folder. Private audit material and persistent allocation state are stored outside the repository in the operator's Research/wsn-private-validation directory, with restrictive file/directory permissions. Do not copy these files into Git or a manuscript package. Public reports retain key commitments, public sink keys and session identifiers, not secret key values. Retrospective hop-tag audit requires the locally retained private fixture file referenced by the report. Another researcher can reproduce the execution with newly generated private keys; the earlier public-fixture captures remain inspectable without private files.

Use `scripts/audit_cc2538_v2.py --run NEW_RUN --topology chain --expected-packets 100` for direct capture audit. It validates complete sink delivery and source receipts, local feature reconstruction, every policy decision and ordinary wire authentication. In addition to replay and forged-tag/signature controls, authenticated old-session messages and repeated provisioning must be rejected. `scripts/summarise_cc2538_v2.py` reconciles the two retained hundred-packet diagnostics and scans checked public artifacts for the private fixture values.

The O2 build uses no fast-math relaxation or new weights. It did not fix deadline failure: chain receipts take 1134–1142 ms and choice receipts 925–931 ms in the emulation. Each hundred-packet run misses 67 receipt deadlines. These are negative execution findings under the declared clock model, not physical timings or statistical performance estimates. No deployment security, physical RF, measured energy, worst-case stack or real-time guarantee is asserted.
