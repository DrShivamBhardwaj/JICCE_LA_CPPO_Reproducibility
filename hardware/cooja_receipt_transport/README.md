# Separate Cooja transport validation

Nine frozen diagnostics (seeds 91001–91003) execute a four-node, 30 m-spaced chain under CSMA and the UDGM radio model. Transmission range is 40 m and interference range 80 m. Each source offers 100 unique packets at 1 s intervals after startup. Three configured per-receiver success probabilities are examined. This parameter is a simulation setting, not measured physical link quality. CSMA link-layer retries remain active, so the configured probability is not end-to-end delivery probability.

| Configured RX probability | Runs | Offered | Sink deliveries / source proofs | Receipt delay range (ms) | Missing or late: 90 / 350 / 1500 ms |
|---|---:|---:|---:|---:|---:|
| 1.0 | 3 | 300 | 300 / 300 | 67.0–242.0 | 296 / 0 / 0 |
| 0.9 | 3 | 300 | 300 / 300 | 83.0–296.0 | 297 / 0 / 0 |
| 0.7 | 3 | 300 | 300 / 300 | 86.0–353.0 | 299 / 1 / 0 |

All 900 offered packets reach the sink and return source-verified Ed25519 receipts. Each run observes rejection of a corrupt hop tag, a replayed data packet and a forged signature. The independent Python audit checks logged wire HMACs and public signatures, unique offered/delivered/receipt identities, final counters and Energest state-time conservation. Completeness means the declared packet count; TEST OK alone is insufficient.

## Boundaries

This is a new, simplified transport fixture, not a port of the benchmark's entire protocol. It uses public test keys, fixed chain forwarding and 100-byte application frames with a distinct wire format. It does not execute the trained attention policy, ACK-gated passive feedback, reverse-route pending ledger, Q22 computation model, private boot provisioning or production security. The first hop verifies link tags and every reverse relay verifies the public proof. These checks establish the fixture's tested behavior only. They do not establish cryptographic key secrecy or resistance to compromised nodes, collusion, jamming or extracted keys.

Native Cooja runs compiled host code; its simulated time does not charge Cortex-M3 actor or crypto execution cycles. The above radio/stack delays therefore cannot replace the Renode MCU deadline results. No policy advantage or new Holm-adjusted comparison is claimed. Three seeds per setting support diagnostics, not deployment reliability certification.

Energest records CPU/LPM/transmit/listen state durations. The native platform reports CPU active throughout this 116 s horizon; listen plus transmit time equals the horizon. These are modeled state counters, not current or energy measurements. No joule estimate is reported without a declared calibrated current model. Physical RF/energy, hardware-protected keys and device-persistent sessions remain unvalidated.

## Retained setup failure

The earlier pilot logged node_id=0 and offered no traffic. Its simulator script nevertheless printed TEST OK after four final status lines. That invalid run is retained in outputs/cooja_receipt_transport/pilot with INVALID_RUN.txt and is excluded from the nine-run results. Initialization now derives node_id from the Cooja-assigned link-layer address; the runner checks node identity and the independent auditor requires exactly 100 unique offered packets. The corrected pilot predates frozen wire-hex logging and is also excluded from the nine-run statistical counts.

## Reproduce

Contiki-NG and Cooja revision hashes, the simulator JAR hash, source hash and settings are in frozen_9runs/protocol.json. Build the existing Cooja with its supported JDK 25 (`./gradlew jar`). This project supplies a small free() declaration shim because the local Contiki minimal stdlib header omits the host declaration used by cooja-log.c; external Contiki sources were not patched.

```sh
python scripts/run_cooja_receipt_transport.py --contiki /path/to/contiki-ng --java /path/to/jdk25/bin/java --output outputs/cooja_receipt_transport/new_run
python scripts/audit_cooja_receipt_transport.py --experiment outputs/cooja_receipt_transport/new_run
```

Use an empty new output directory. On this Mac GNU make is provided with `--make-bin /opt/homebrew/opt/make/libexec/gnubin`. The runner rebuilds the mote type and never overwrites an experiment. Local absolute paths in retained .csc files document the original environment; the runner regenerates them for the supplied installation.
