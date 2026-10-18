# Completion matrix after executed virtual extension

Updated 18 October 2026. Original manuscript evidence and the extension are separately retained.

| Item | Current completion | Evidence boundary |
|---|---|---|
| Low-q credit partition artifact | Corrected and regression-tested in opt-in bounded ledger | Frozen baseline unchanged; alternative rule remains heuristic |
| Ledger retirement/capacity | Implemented and stress-tested | This bounds ledger state, not all simulator or firmware memory |
| Packet reordering | 64-identity window tested | Older unseen identities are rejected; session management is external |
| Freshness under declared clock envelope | 675 offset/drift combinations tested | Not clock synchronization or measured oscillator calibration; stale window widens |
| Battery power-gating | Executed at ns-3 PHY boundary with zero post-cut transmissions in retained runs | Modeled current, not physical current |
| Periodic sleep/wake | Executed with busy-state deferral and PHY residence accounting | Primitive, synchronized schedule; no rendezvous/MAC deployment guarantee |
| 60 s routing extension | 27 runs reconciled with nine trace streams and 2,727 energy identities | Three fixtures per cell; sensors still exhaust energy |
| Proof-traffic attribution | 240 separately frozen factorial runs, 30 new fixtures, 30-test Holm family | Different backend/rules from original study; does not retrospectively decompose its entire gain |
| Full Python/native bridge regression | 107 tests passed | Recorded Mac/ns-3.47 environment; not a fresh ns-3.44 reproduction |
| Cortex-M3 actor/crypto execution | Compiled C and actual emulated instruction execution passed | Isolated QEMU harness, not integrated CC2538 radio firmware |
| Target numerical comparison | 16 decisions and 128 logits checked against frozen PyTorch actor | Eight retained observations plus eight permutation controls; limited input coverage |
| Target memory observation | Linker budgets and observed 3,080-byte stack watermark recorded | No full protocol buffers/RTOS; not worst-case stack proof |
| Data, logs, source and figures | Retained with hashes and reproducible scripts | New addendum accompanies the original manuscript |
| Word/PDF integration of this extension | Complete: Sections 5.6–5.7, Figure 11 and Tables 8–9 added; all 24 pages visually verified | Original statistical families preserved; see document_checks.json for delivery QA |
| Integrated on-MCU authenticated radio routing | Still open | Isolated actor/crypto and CC2538 bridge must be integrated and jointly tested |
| Physical boards, RF, current and timing | Still open | Requires real apparatus and measurements |
| Coauthor approvals/contributions/exclusivity | Still open | Requires actual author statements |
| Authenticated journal-portal checks/submission | Still open | No submission or payment made |

## Critical vulnerabilities and limitations

The study still fails absolute deadline compliance under the stress/deployment conditions. Physical and full-firmware validation cannot be replaced by separately passing isolated tests. The stale-acceptance tolerance is a security tradeoff, and nominal duty fractions differ from actual residence because busy MAC work delays sleep. These boundaries remain explicit in the addendum.

## High novelty opportunities

The executed factorial design now supplies a traffic-control contrast missing from the original benchmark. Full-target integration can build on the tested C actor and crypto code without treating emulator success as physical evidence.
