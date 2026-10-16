# Post holdout distributed authentication extension

This is a separate engineering prototype. The frozen 750-run study, its inputs, checkpoints, traces and gate are unchanged. The new transport uses greedy progress routing on a four-node chain. It does not establish performance of attention with distributed/authenticated state.

| Item | Implemented and checked | Boundary |
|---|---|---|
| Neighbor state exchange | Coordinates, measured simulator radio-energy fraction and local pending-request count serialized into radio frame bytes | Configured own/sink coordinates; no localization protocol |
| Route state | Packet-carried 104-bit visited set; node-local reverse records | Honest forwarding obeys history; a compromised authenticated relay can alter mutable route fields |
| Transit service | Per-node receipt/expiry settlement and class debt | CPU latency and clock synchronization not modeled in radio study |
| Hop authentication | Pairwise HMAC-SHA256, 128-bit tag, sender/destination binding | No encryption, online key exchange, or secure key storage |
| Replay protection | Provisioned 64-bit boot sessions and 64-entry sequence window | Reboot requires out-of-band reprovisioning; host `.used` markers fail closed on reused configuration |
| Receipt authenticity | Source data HMAC and sink Ed25519 signature over source/session/packet identity | Sink/source key compromise outside scope; authenticated peers may still drop data or lie in telemetry |
| Bounded records | 128 pending records/node, 2 s expiry; finite per-peer windows | Expiration still scans pending records; capacity overflow drops new records |
| Passive overhearing | Not credited as authenticated proof in this extension | Pairwise hop keys do not let a third party verify the onward frame |
| Physical validation | Adapter, private provisioning utility, current integration and test protocol supplied | No boards, instrument traces, board firmware target or physical run available |
| Browser rendering | Real Chromium 153; 72 selections across two versions, three widths and two themes | Screenshot review supplements automated text-bound and interaction checks |

## Functional radio evidence

All 30 fixtures (82001–82030) were retained. Of 300 offered packets, 295 reached the sink. The observer rejected 30 modified telemetry frames and 30 repeated telemetry frames. There were no rejected transport send requests. These are simple chain controls, not a randomized comparative performance study. The 17 new tests cover tag corruption, replay, wrong MAC peer, stale boot sessions, forged sink receipts, source authentication, loop history, duplicate credit, failed MAC ACK, large sequence jumps, bounded memory, source packet-counter reuse, private provisioning and current-sample validation. All 68 tests, including the previous 51, pass.

The public-key verifier checked 2,552 received frames against prior transmitted bytes, 885 signed receipt transmissions and 120 radio-energy identities. Per-run keys are newly generated and private; the public sink key is retained for independent signature checks. Re-running reproduces behavior/radio fixture pairing but not byte-identical random keys and signatures. No secret is exported in the traces.

## Wire budget

| Frame | Envelope | Body | Hop tag | Total application bytes |
|---|---:|---:|---:|---:|
| Neighbor telemetry | 20 | 22 | 16 | 58 |
| Data with 16 payload bytes | 20 | 70 | 16 | 106 |
| Signed sink receipt | 20 | 78 | 16 | 114 |

The receipt body carries source ID (2), packet ID (4), source boot session (8) and Ed25519 signature (64). Data carries immutable source/session/packet/class/time/payload fields, a source authenticator, and mutable hop count and visited bitset. The hop tag covers the full envelope and body. IEEE MAC/PHY overhead is additional and appears in actual ns-3 frame counters. Authentication and processing energy are not inferred from simulated radio residence times. The added unicast telemetry and 114-byte receipts require a new overhead-aware policy evaluation; no existing energy or delivery gain is transferred to this version.

## Reproduce

```
python -m pip install ns3==3.44.post0 --no-deps
python -m pip install -r requirements-distributed-auth.txt
python scripts/build_ns3_wire.py
python -m pytest tests/test_distributed_auth.py -q
python scripts/run_distributed_auth.py
python scripts/verify_distributed_auth.py
```

For browser verification, install Playwright and a compatible Chromium, set `BROWSER_EXECUTABLE` if necessary, and run `node scripts/verify_architecture_browser.cjs`. The development environment used a separately unpacked Chromium binary after the default browser download failed; the saved report records the actual running version.

Physical work is specified in hardware/README.md. Its adapter runs authentication on the host and requires a board-specific serial-radio firmware port. Neither that host integration nor a software current fixture can be reported as validation of embedded computation or calibrated mote energy.

Authentication primitives: RFC 2104 (HMAC), RFC 8032 (Ed25519/EdDSA); implementation API checked against the official cryptography Ed25519 documentation. These references support the primitives, not a formal security proof of this reference protocol.

Telemetry includes an authenticated transmit timestamp. Receivers reject state older than 0.75 seconds, future timestamps and out-of-order cache updates. This requires a common time base; distributed clock synchronization remains outside this prototype.
