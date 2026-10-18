# Remaining validation and completion record

Updated 18 October 2026. Evidence baseline: 6442d2f9caa0ac9ddf1978c3f8ed3b34fdb9b288.

## Completed package corrections

- Abstract count corrected to 198 in the submission checklist.
- Upload map reconciled with all ten current figures and the figure archive.
- Cover letter and author declaration sheet aligned with the current manuscript title.
- Author-confirmed no-funding/no-competing-interest wording retained. Coauthor approvals and contributions are not inferred.

## Execution availability

The authorized Desktop Commander device was offline at the time of this check. The local execution service was unavailable. No new simulations, hardware runs or test-suite executions were performed in this session. Direct publisher-guide retrieval returned HTTP 403. These access failures are not validation results.

## Critical vulnerabilities and required evidence

| Open item | Work required | Completion criterion |
|---|---|---|
| Low-q clipping artifact | Implement a separately versioned alternative, keeping the frozen baseline intact; test split versus combined observations, duplicates and ACK eligibility | Exact numerical regression cases pass; new fixture-level comparison reports performance and altered scoring semantics |
| Proof-traffic attribution | Freeze a design that separates eligibility/timeout semantics from proof traffic, with matched offered load and explicit receive/listen costs | Independently paired fixture results and prespecified analysis; no causal claim from the existing bundled comparison |
| Long-run battery behavior | New branch must stop or explicitly power-gate radio activity when modeled energy is exhausted | Event traces show no unpowered transmissions/listening costs; delivery/lifetime endpoints defined before running |
| Ledger growth | Specify retirement and late-evidence horizon; preserve packet/session identity isolation | Memory bound follows from a stated capacity/retention rule and stress logs; late events cannot credit a different packet |
| Duty-cycled MAC | Model rendezvous, channel checks, wake/sleep transitions and feedback listening windows for all arms | New-run energy/delivery tradeoffs under declared MAC settings; accounting example alone is insufficient |
| Clock offset and drift | Give each emulated node its own clock; freeze offsets/drifts and freshness acceptance policy | Authentic fresh frames, expired frames and replay cases evaluated across the stated clock envelope |
| Embedded inference/cryptography | Build target-specific actor and authentication functions with linker map and memory instrumentation | MCU execution traces, correct decisions/tags/signatures, peak RAM and runtime measured; host execution does not qualify |
| Physical RF and measured energy | Execute on identified boards with recorded topology, firmware, instruments and current traces | Real packet captures and calibrated energy measurements with repeated trials; emulation cannot close this item |
| External reproduction | Rebuild from a pinned commit in an independent environment | Recorded dependency versions, hashes, run commands and reconciliation results |
| Submission declarations | Obtain actual contributions, individual approvals and exclusivity/related-work confirmation | Author-provided attestations; no automated consent |
| Journal portal | Inspect actual article type, forms, file roles and generated review PDF | Portal-specific checks recorded before submission; journal guide access alone is insufficient |

## High novelty opportunities

The most discriminating extension is a frozen factorial feedback study that separates evidence semantics from acquisition cost under duty cycling. Physical-board and embedded measurements should support deployment claims only after actual execution. New branches and post-review runs must remain separate from the original confirmatory family. None of the planned criteria above has been marked as passed without execution.
