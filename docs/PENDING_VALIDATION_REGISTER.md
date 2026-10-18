# Current validation register

This file replaces the earlier duplicated status paragraphs. Historical states remain in Git history. The manuscript is a reproducible simulation benchmark with separately scoped emulation diagnostics; its completed tests do not certify deployment.

## Completed evidence

- Original 750-run feedback benchmark, separate 180-run authenticated transfer, and separately frozen 240-run factorial analysis remain preserved.
- Bounded ledger, battery cutoff, sleep/wake, clock-envelope, isolated Cortex-M3 actor/crypto and native bridge checks are executed within their stated boundaries.
- Four-node live MCU routing/authentication: public-fixture chain and multiple-choice runs each deliver ten packets and return ten source-verified receipts; fifty decisions match the host reference.
- Private provisioning and rolling source replay: hundred-packet chain and choice runs each deliver all hundred packets and receipts, with five hundred matching decisions in total. All six negative controls per run pass, including stale sessions and reprovisioning rejection. The persistent host allocator passes sequential, concurrent and exhaustion tests.
- Latest manuscript: Section 5.8 and Table 10 integrate the live results. Exact document counts and rendered-page checks are in publication/array/document_checks.json. The corresponding author's supplied metadata, no-funding and no-interest statements are retained.

## Observed failures and scope boundaries

Deadline compliance is not achieved: the public pilots miss 14/20 receipt deadlines, and the longer private runs miss 134/200. Compiler optimization did not correct the timing. These findings are reported rather than hidden or converted to successful deadline claims.

Four-node sequential streams do not establish network-size scaling, queue-overload stability, worst-case stack, calibrated timing, protected MCU key storage or reboot-persistent MCU sessions. Host allocation and trusted UART provisioning address the emulator fixture only. Beacon energy/queue inputs are nominal, and scheduling is test-triggered. These are explicit scope exclusions, not completed deployment checks.

## Work requiring unavailable hardware or author actions

Physical board startup/clock/peripheral validation, RF/interference measurements and calibrated energy acquisition require actual compatible boards and instruments. No such measurements are fabricated. Acquisition requirements and a trace-integrity/energy-integration script are prepared in hardware/cc2538_live/PHYSICAL_ACQUISITION.md.

Individual coauthor approvals, contribution roles, exclusivity/related-work declarations, authenticated Array portal checks and final submission approval remain author actions. The official guide again returned HTTP 403 during the latest access check. No author consent, signature, message, portal submission or payment is inferred or performed.
