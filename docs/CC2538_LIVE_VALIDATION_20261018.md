# Live MCU packet integration — 18 October 2026

The compiled CC2538 pilot now handles ordinary data and receipt authentication and next-hop selection on the emulated MCU. It constructs the 93-feature observation from authenticated local neighbour state, computes frozen attention logits, seals/verifies pairwise HMAC, rejects replayed hop sequences, verifies the source tag at the sink, generates the Ed25519 sink receipt and verifies/forwards it along the pending reverse route. Positive credit requires both MAC acknowledgement and a verified receipt. Host control generates traffic/beacon triggers and records evidence; Python cryptography and PyTorch are used for independent audits and adversarial fixtures, not ordinary forwarding.

| Check | Three-hop chain | Multiple-choice topology |
|---|---:|---:|
| Offered packets | 10 | 10 |
| Unique sink deliveries | 10 | 10 |
| Verified receipts at source | 10 | 10 |
| MCU policy decisions matching reference | 30/30 | 20/20 |
| Decisions with multiple feasible next hops | 0 | 10 |
| Independently authenticated ordinary wires received by intended peer | 120 | 140 |
| Maximum feature error | 5.96 × 10⁻⁸ | 5.96 × 10⁻⁸ |
| Maximum actor-logit error | 2.38 × 10⁻⁷ | 2.38 × 10⁻⁷ |
| Emulated receipt delay | 1119–1128 ms | 915–922 ms |
| Receipt deadline misses | 7/10 | 7/10 |

Both topologies rejected exact replay, a corrupt hop tag, a corrupt source tag protected by a valid hop MAC, and a forged sink signature protected by a valid hop MAC. All acceptance criteria require complete delivery and receipts; a partial run cannot pass. Existing Python regression checks remain 107/107 passed. A separate one-packet workflow smoke run tests the refactored runner/auditor and is excluded from the table.

The 90 ms and 350 ms receipt targets were not met in these emulated runs. The 1500 ms class passed. This is a timing limitation, not a statistically estimated performance comparison or a physical latency measurement. Skipping masked actor candidates was necessary: the retained development failure shows cache expiry with the earlier kernel. We did not lengthen freshness or receipt windows to obtain delivery.

The pilot is limited to four provisioned nodes, source 0, sink 3, sixteen pending/delivery slots and ten packets. It uses public fixture keys and fixed sessions, nominal energy/queue values, and test-triggered beacon exchange. Private provisioning, reboot-safe sessions, real board startup, worst-case stack/queue/concurrency, full-scale generalization and RF interference remain unvalidated. The 1.645 risk multiplier remains the existing heuristic; it is not a statistical confidence bound.

`hardware/cc2538_live/README.md` contains reproduction instructions. `scripts/audit_cc2538_live.py --run ... --topology ... --expected-packets 10` audits supplied captures directly. Primary outputs are under `outputs/cc2538_live/chain` and `choice`; the shared compiled ELF and source are retained in their parent directory.

## Physical acquisition status

No sensor board serial interface or calibrated power instrument was available on the connected Mac. There are no measured RF/energy results. `hardware/cc2538_live/PHYSICAL_ACQUISITION.md` specifies the required four-board setup, evidence and firmware-port boundaries. `scripts/analyse_physical_power_trace.py` validates and integrates real voltage/current CSV traces once acquired; its four arithmetic/rejection checks use explicitly synthetic values and produce no hardware claim.

The current manuscript PDF/Word and original statistical tables are unchanged. This report is additional integration evidence, not a replacement for the manuscript's larger benchmark or a claim of completed physical validation.
