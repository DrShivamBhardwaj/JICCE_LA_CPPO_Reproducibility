# Array target and virtual validation

## Journal assessment

Array is a plausible scope match for this computational networking study. This
is a scope assessment, not an acceptance prediction. The strongest supported
story is a reproducible comparison of forwarding feedback and a transparent
authenticated implementation transfer. The experiments do not establish a
novel attention mechanism, attention superiority, a live intrusion detector,
physical validation or compliance with the original critical-service budget.
Those boundaries remain material in editorial assessment.

Official sources checked on 16 October 2026:

- https://www.sciencedirect.com/journal/array
- https://www.sciencedirect.com/journal/array/about/insights
- https://www.sciencedirect.com/journal/array/publish/open-access-options
- https://www.sciencedirect.com/journal/array/publish/guide-for-authors

Publisher-indexed information lists open access and a standard APC of USD 2,770
excluding taxes; geographical pricing may change the actual invoice. Exact
author eligibility and payable amount have not been established. Some direct
publisher page requests returned HTTP 403; indexed publisher snippets verified
the scope, APC and 3–5 highlights of at most 85 characters. The draft uses a
single-column review layout and a concise abstract. Full portal compliance must
be checked against the live author guide at submission. No submission was made.

## Completed evidence

- Prospective transport protocol/source commit:
  `5f06b9213e73206aad11ec8f3a96079a17011a20`.
- 180 radio runs: 30 seeds × 2 settings × 3 arms; 10,800 offered packets.
- Frozen attention and capacity matched MLP checkpoints; no retraining.
- 27,240 audited decisions, 14,001 with multiple candidates.
- 88,538 received byte frames matched to prior transmissions.
- 46,204 public sink-signature occurrences verified; 1,080 modeled energy
  identities reconciled. Runtime nodes verify private hop HMACs.
- 73 automated tests passed.
- Four PTY virtual devices and four actual host-adapter processes exercised the
  serial firmware API with ns-3 as the radio backend. The corrected control
  delivered 10/10 source packets; this is one functional fixture.
- The original 750-run evidence remains unchanged.

The first virtual diagnostic delivered 5/10 packets and had false freshness
rejections because a pre-read timestamp was used after a blocking serial read.
The adapter now samples reception time after bytes arrive. Initial and corrected
captures are retained. This correction does not alter the 180-run radio study,
which does not use the serial adapter.

## Results and remaining boundaries

| Condition | Greedy delivery | MLP delivery | Attention delivery |
|---|---:|---:|---:|
| Benign | 82.72% | 83.72% | 81.61% |
| Selective dropping | 62.89% | 60.50% | 61.11% |

Paired exploratory bootstrap intervals include zero for all four attention
delivery comparisons. The new transport therefore supplies integration evidence,
not an attention superiority result. Candidate feature substitutions include
received LQI, raw MAC pending-request counts instead of normalized training
queue pressure, MAC-derived reliability, local debt and positive-only signed
receipt evidence; this is a declared distribution shift from training.

Virtual UART/API execution is not MCU instruction emulation or execution of a
compiled board image. There are no real boards, calibrated current captures,
physical antenna/channel measurements or board-specific firmware here. The
hardware adapter's learned-policy option is supplied but has not been validated
on hardware. Key provisioning remains out of band with per-peer state and
network-wide provisioning cost; compromised peers can still lie in telemetry.

## Reproduce

```sh
python scripts/build_ns3_wire.py
python -m pytest tests -q
python scripts/run_auth_policy.py
python scripts/audit_auth_policy.py
python scripts/analyse_auth_policy.py
python scripts/run_virtual_boards.py
```

The raw trace archive is distributed in numbered parts. Reassemble it with
`cat outputs/auth_policy/raw_traces.tar.gz.part* > outputs/auth_policy/raw_traces.tar.gz`.
It contains all 180 gzip streams. Extract it into
`outputs/auth_policy/` before running the audit on a fresh checkout. Host timing
makes the virtual serial control's delivery outcome sensitive to scheduling;
preserve every run. Random private keys are not published, so newly generated
cryptographic bytes differ while fixtures and frozen policy mapping are fixed.

## Compiled MCU extension, 16 October 2026

The prior UART/API boundary above describes the original ns-3/PT Y interface model. A separate Renode 1.17.0 backend now executes compiled CC2538/Cortex-M3 radio-interface firmware on four emulated boards. Greedy, MLP and attention host controls each deliver 10/10 packets and pass five probes. The independent audit validates UART byte provenance, sink signatures and identities. See [reproduction and complete limits](../hardware/renode_cc2538/README.md). Physical RF/current, physical board initialization, embedded inference and embedded cryptography remain unvalidated. The Array manuscript now has 27 rendered pages, including the revised architecture figure.

The fresh CPU audit retains exact argmax identity for all 27,240 authenticated policy decisions. Probability replay uses atol=rtol=1e-6 (maximum observed difference 1.7881393432617188e-7); this accommodates numerical backend variation without changing any recorded choice. A broad pytest recheck initially found stale/missing local ns-3 libraries after environment renewal. Rebuilding all three historical bridge libraries resolved collection; 73 tests then passed in 5.05 s. No frozen outcomes or checkpoints changed.
