# Fixed point inference and experimental fast receipts

The original FP32, private-key hundred-packet diagnostics remain unchanged under outputs/cc2538_v2. The new profiles address measured computation cost and preserve separate authentication endpoints. All times below use the emulator's 1 MHz SysTick, not measured physical execution.

| Profile over two hundred-packet streams | Signed receipt delay | Signed deadline misses | Private fast receipt delay | Private fast misses |
|---|---|---:|---|---:|
| Retained FP32 | 925–1142 ms | 134/200 | Not present | Not applicable |
| Q22 plus cached signing key | 238–339 ms | 68/200 | Not present | Not applicable |
| Q22 fast private receipt plus deferred Ed25519 proof | 240–343 ms | 68/200 | 49–63 ms | 0/200 |

Each profile executes one chain and one multiple-choice stream, with one hundred packets per geometry. These are functional diagnostics, not independent statistical replicates, a general reliability bound or a guarantee under interference.

## Kernel and numerical scope

The frozen actor's 44,161 parameters are represented with 22 fractional bits; matrix accumulators use 64 bits. An 8193-point interpolated tanh table adds 32,772 bytes. Export checks establish arithmetic bounds for the declared input cube [-32,32]. NaN, infinity, out-of-range inputs and an empty mask are rejected. This narrower input domain is explicit; the implementation is not a universally interchangeable FP32 kernel for arbitrary queue features.

The native check matches all five hundred retained decisions with maximum logit error 2.03e-6. The two new MCU profiles independently reconstruct features and compare every decision with the FP32 model at the recorded observation. Original weights are not retrained; tested approximation agreement is not a proof that every possible argmax is unchanged. In the declared emulator, one-candidate inference drops from about 270 ms to 12–13 ms. Operation timing includes coarse millisecond resolution and diagnostic UART output.

## Authentication endpoints

Ordinary data and the original kind-3 Ed25519 receipt are preserved. The fast profile adds kind 4: 20-byte hop header + 14-byte packet identity + 16-byte source–sink HMAC + 16-byte hop HMAC, totaling 66 application bytes. Its domain is JICCE-fast-sink-v1 followed by a zero byte.

The sink sends the private receipt after authenticating source data and then generates the Ed25519 proof. Relays authenticate the hop envelope and pending reverse route but cannot authenticate the end-to-end source–sink tag; they forward it opaquely and do not assign positive credit from it. The source alone verifies the private tag and may settle source service debt before the public proof arrives. Positive forwarding credit at every node still requires a MAC ACK and a verified Ed25519 receipt. The trace audit reconstructs this credit condition from prior events and state snapshots.

Consequently, zero private-receipt deadline misses do NOT mean that the original public-signature deadline passed. The signed endpoint still misses 68/200 deadlines. A source holding the symmetric key can create a private tag, so this fast receipt is not transferable public evidence. The deferred signature supplies the original public verification later. The extra private receipts add three application frames per chain packet or two per choice packet; no energy benefit is asserted.

## Software security and memory checks

The profiles retain random per-run keys, distinct persisted host boot sessions and locked one-time trusted-UART provisioning. A provisioned signing seed must match the public key; mismatch is rejected before startup. The signing secret is derived once, and temporary seed/HMAC material and UART command buffers use volatile erasure. This is software hygiene, not protected hardware storage or a side-channel certificate.

Both hundred-packet fast-profile runs reject replay, stale sessions, repeated provisioning, mismatched signing material, corrupt hop/source tags, forged public signatures and forged private receipts. Tested-path stack watermarks reach 6624 bytes; static RAM is 3968 bytes and guards remain intact under the 32 KiB linker budget. This does not establish a worst-case stack or overload bound. Protected MCU storage, persistent device sessions, authenticated physical provisioning, real board startup and physical RF/current remain unvalidated.

## Reproduce

Use the existing Python environment, Zig 0.17.0 and Renode 1.17.0. Follow this order when regenerating sources:

```sh
python scripts/prepare_cc2538_profile.py
python scripts/export_cc2538_q22.py
python scripts/prepare_cc2538_q22.py
python scripts/build_cc2538_q22.py
python scripts/prepare_cc2538_fast_receipt.py
python scripts/add_fast_stack_checks.py
python scripts/build_cc2538_fast.py
python scripts/run_cc2538_q22.py --renode /absolute/path/to/renode --topology chain --packets 100
python scripts/run_cc2538_fast.py --renode /absolute/path/to/renode --topology chain --packets 100
```

Repeat with `--topology choice`. Default outputs use fresh names; private audit files stay outside Git with restrictive permissions. Retained captures are independently re-audited with scripts/audit_cc2538_q22.py or scripts/audit_cc2538_fast.py and an explicit --run/--topology/--expected-packets. scripts/summarise_receipt_profiles.py reconciles all three retained profiles and checks ordinary wire authentication, credit gating and private-material boundaries. The six-packet fast pilot retains its original ELF in its run folder; later stack-instrumented captures use the final shared ELF.
