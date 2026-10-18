# Current validation register

This file replaces the earlier duplicated status paragraphs. Historical states remain in Git history. The manuscript is a reproducible simulation benchmark with separately scoped emulation diagnostics; its completed tests do not certify deployment.

## Completed evidence

- Original 750-run feedback benchmark, separate 180-run authenticated transfer, and separately frozen 240-run factorial analysis remain preserved.
- Bounded ledger, battery cutoff, sleep/wake, clock-envelope, isolated Cortex-M3 actor/crypto and native bridge checks are executed within their stated boundaries.
- Four-node live MCU routing/authentication: public-fixture chain and multiple-choice runs each deliver ten packets and return ten source-verified receipts; fifty decisions match the host reference.
- Private provisioning and rolling source replay: hundred-packet chain and choice runs each deliver all hundred packets and receipts, with five hundred matching decisions in total. All six negative controls per run pass, including stale sessions and reprovisioning rejection. The persistent host allocator passes sequential, concurrent and exhaustion tests.
- Latest manuscript: Section 5.8 and Table 10 integrate the live results. Exact document counts and rendered-page checks are in publication/array/document_checks.json. The corresponding author's supplied metadata, no-funding and no-interest statements are retained.

## Observed failures and scope boundaries

Current receipt validation (18 October 2026): Q22 inference and cached signing keys reduce original signed-receipt deadline misses from 134/200 to 68/200. The experimental source-only HMAC receipt meets 200/200 tested deadlines (chain 61–63 ms; choice 49–50 ms); deferred Ed25519 proofs still miss 68/200 original deadlines. These are distinct endpoints, not a repaired original signed deadline. Both new profiles deliver all 200 packets and verify all 200 deferred proofs. ACK plus Ed25519 remains the forwarding-credit gate. Extra private receipt traffic has no measured energy benefit. Tested stack guards remain intact under the 32 KiB linker budget; this is not a worst-case bound. Physical RF/energy, protected MCU key storage and persistent MCU sessions remain unvalidated. The attached-hardware inventory found no matching board/instrument. Coauthor consent and authenticated portal checks require genuine author actions; no approval or submission is inferred.

Four-node sequential streams do not establish network-size scaling, queue-overload stability, worst-case stack, calibrated timing, protected MCU key storage or reboot-persistent MCU sessions. Host allocation and trusted UART provisioning address the emulator fixture only. Beacon energy/queue inputs are nominal, and scheduling is test-triggered. These are explicit scope exclusions, not completed deployment checks.

## Work requiring unavailable hardware or author actions

Physical board startup/clock/peripheral validation, RF/interference measurements and calibrated energy acquisition require actual compatible boards and instruments. No such measurements are fabricated. Acquisition requirements and a trace-integrity/energy-integration script are prepared in hardware/cc2538_live/PHYSICAL_ACQUISITION.md.

Individual coauthor approvals, contribution roles, exclusivity/related-work declarations, authenticated Array portal checks and final submission approval remain author actions. The official guide again returned HTTP 403 during the latest access check. No author consent, signature, message, portal submission or payment is inferred or performed.
