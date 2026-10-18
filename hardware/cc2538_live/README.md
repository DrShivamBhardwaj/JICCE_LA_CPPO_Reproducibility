# CC2538 live packet integration pilot

This extension moves live feature construction, frozen attention inference, hop HMAC verification/sealing, source-tag checks, 64-sequence replay windows, MAC-gated credit and Ed25519 sink receipts into a compiled Cortex-M3 CC2538 image. The host triggers source traffic and beacon exchange and captures UART logs; it does not choose next hops or authenticate the ordinary data/receipt path. The host independently checks captured cryptography and constructs deliberately invalid authenticated negative controls.

## Reproduce

Use Zig 0.17.0, Renode 1.17.0 ARM64 portable, and the repository's Python environment with numpy, torch, cryptography. The MCU actor uses the existing attention_41001.pt export, not a newly trained policy.

```sh
python scripts/build_cc2538_live.py
python scripts/run_cc2538_live.py --renode /absolute/path/to/renode --topology chain --packets 10
python scripts/run_cc2538_live.py --renode /absolute/path/to/renode --topology choice --packets 10
```

The driver uses TCP-backed UART terminals for macOS compatibility. Actual node-to-node data still travels through the emulated CC2538 radio and FIFO/ACK logic. The chain spans three hops; the choice geometry gives the source two feasible next hops. Each run requires ten unique sink deliveries and ten source-verified signed receipts. Every ordinary transmitted wire is independently authenticated, every emitted decision is compared with the frozen Python actor, and the 93 input features/masks/candidate IDs are independently reconstructed from the logged local cache, link state, debts and timestamps. Exact replay, bad hop tag, bad source tag with a valid hop MAC, and a bad sink signature with a valid hop MAC must all be rejected. A failed criterion leaves the run marked failed.

The kernel skips candidate computation when the mask excludes that candidate; masked logits remain -1e9. This preserves actor semantics. The unoptimized predecessor evaluated all eight candidate slots and allowed relay cache expiration; its failed UART capture is retained as a development diagnostic under `development_masked_kernel_failure`. The predecessor ELF was not retained; that diagnostic is not a fully archived build artifact or a positive validation run.

The runner creates a fresh output directory by default; `--output` can name a new directory. Existing output directories are rejected. Re-audit any retained run without rerunning the emulator:

```sh
python scripts/audit_cc2538_live.py --run outputs/cc2538_live/chain --topology chain --expected-packets 10
```

## Scope and unresolved limits

- This is a bounded four-node pilot, with source node 0, sink node 3, sixteen pending/delivery records, and ten offered packets per run. It is not the full 104-node implementation or a scalability study.
- Beacon generation is triggered by the test harness. Coordinates and topology are provisioned locally. Beacon energy is explicitly nominal 1.0 and queue 0; neither is measured telemetry. The sink coordinate is fixed at (90,0) in this pilot.
- Public deterministic test keys, fixed sessions and unauthenticated fixture-control UART commands are unsuitable for deployment. Restart-safe sessions, private key provisioning and production firmware startup remain outside the pilot.
- The Renode model uses a 1 MHz SysTick and an abstract deterministic range medium. Reported receipt delays are emulated times, not measured CC2538 performance. Receipt delays must be compared with the 90/350/1500 ms class budgets; passing delivery acceptance does not establish deadline compliance.
- The image fits the configured 512 KiB flash / 32 KiB SRAM linker limits. Combined worst-case stack, queue pressure, radio/crypto concurrency, interference and long-run capacity behavior are unvalidated.
- No physical RF or energy measurements were available. See PHYSICAL_ACQUISITION.md. A linked Renode image is not a vendor-board flash-ready release.

The archived manuscript's simulation tables and statistical claims are unchanged. These small integration runs are separate validation evidence and do not establish neural superiority or a calibrated hardware benchmark.
