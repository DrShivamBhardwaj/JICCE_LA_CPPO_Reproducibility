# Isolated Cortex M3 validation harness

This directory contains a bare-metal C actor and cryptographic test image. It executes on QEMU MPS2 AN385 with a Cortex-M3 CPU and software floating point. It is distinct from the CC2538 UART/radio bridge. It contains no radio drivers, authenticated packet transport loop, RTOS or physical-board initialization.

## Reproduce

Install Zig 0.17.0, QEMU 11.1.2 and the Python project dependencies. The audit uses LLVM 22 readelf/size tools. From the repository root:

1. Run python scripts/fetch_mcu_crypto.py. It verifies the official Monocypher 4.0.3 release archive hash and records pinned B-Con source provenance and licences.
2. Run python scripts/export_cortex_actor.py. It exports all 44,161 actor parameters from attention_41001.pt, eight retained radio observations and eight labelled candidate-permutation controls.
3. Run python scripts/build_cortex_validation.py. The linker limits flash to 512 KiB and SRAM to 32 KiB; its image starts at address zero for MPS2, not the CC2538 flash address.
4. Run qemu-system-arm -M mps2-an385 -cpu cortex-m3 -nographic -monitor none -semihosting-config enable=on,target=native -kernel build/cortex_m3.elf and save the output as outputs/validation_20261018/cortex_mcu.txt.
5. Run python scripts/audit_cortex_validation.py.

The build compiles Zig's target compiler runtime explicitly for soft-float support. The generated include shims supply only the freestanding memory declarations needed by SHA256; no host libc is linked.

## Evidence

Sixteen decisions match PyTorch, including all eight selected candidate indices. All 128 logits differ by at most 1.7881393432617188e-7 on these vectors. HMAC-SHA256 matches RFC 4231 case 1. Ed25519 signing and verification match Python cryptography, while a corrupted signature is rejected. An empty candidate mask is rejected.

The ELF report records ARM architecture and text/read-only size 341,600 bytes. The ELF container size 407,536 bytes is a different quantity. The observed stack watermark is 3,080 bytes on these test paths; this is not a proof of a global worst-case stack bound. The harness has no static writable state.

The activation uses a finite exp-series approximation; agreement on this vector set is not an exhaustive numerical guarantee. No latency or energy claim is inferred from emulator wall time. Complete radio/RTOS/queue memory is excluded. Deployment requires target integration, larger validation sets and physical-board tests.

All embedded seeds, private keys and messages are public test fixtures. Never deploy them as operational keys. Vendor sources retain their original licences and hashes.
