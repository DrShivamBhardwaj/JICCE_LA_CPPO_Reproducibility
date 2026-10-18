# Actor/cryptography and radio coexistence image

This extension links the frozen attention actor (44,161 FP32 parameters), SHA-256/HMAC and Ed25519 test routines into the CC2538 radio/UART bridge image. It exercises public boot vectors before enabling the bridge. A failing cryptographic boot check prevents radio initialization. The external audit compares every actor action and logit against the exported reference and independently verifies the signature.

This is a coexistence check, not an implementation of autonomous authenticated routing: live feature construction, policy dispatch and packet authentication still belong to the host adapter. The firmware's public test keys must never be used for deployment. The archived manuscript's existing hardware claims are unchanged.

## Reproduce

Dependencies: Zig 0.17.0, Python with cryptography and pyserial 3.5, and Renode 1.17.0. On macOS ARM64, the official portable DMG contains `Renode.app/Contents/MacOS/renode`; no Linux PTY transport is assumed.

From the repository root:

```sh
python scripts/build_cc2538_selftest.py
python scripts/run_cc2538_boot_selftest.py --renode /absolute/path/to/renode
```

The builder regenerates `outputs/cc2538_boot_selftest/firmware.c`, cross-compiles the soft-float runtime and links the image at CC2538 flash address 0x00200000 with a 512 KiB flash and 32 KiB SRAM linker budget. Debug symbols are retained because Renode uses the `node_id` symbol to provision each machine. The original bridge source and original validation captures remain unchanged.

The runner executes two machines, checks all 16 actor vectors on each, checks HMAC and Ed25519 outputs, and requires all five radio/UART probes: provenance, 114-byte delivery with a genuine emulated MAC ACK, 115-byte rejection, malformed hex rejection and absent-peer ACK failure. It writes `execution.json` with `passed` only after all checks succeed. A local TCP socket terminal carries UART bytes on macOS; it is not the emulated sensor radio link.

## Remaining boundary

The live packet path does not yet invoke the actor or authenticate packets on the MCU. No multi-hop autonomous routing, operational key provisioning, replay-state integration, radio/crypto concurrency stress, worst-case stack/timing, physical RF or measured energy claim follows from these tests. The original isolated MPS2 stack observation does not establish the combined image's stack requirement. Follow-up integration must call actor/crypto functions from live receive/forward/receipt handling and compare the resulting packet decisions with the host reference.

## Recorded result (18 October 2026)

The two-node run passed: 32/32 actor actions matched the reference, all 256 logits were within 1e-5 (maximum absolute error 1.7881393432617188e-7), both HMAC known-answer checks passed, and both Ed25519 signatures were independently verified with corrupt signatures rejected. All five radio/UART probes passed after boot. Linked text/rodata occupies 343,296 bytes and static BSS 2,069 bytes; stack use for this combined image has not been measured. Complete UART captures, ELF, generated C source, build command and execution report are retained under `outputs/cc2538_boot_selftest/`.
