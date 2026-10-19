# Remaining gates: evidence needed to execute

Follow-up starts at commit `86dde525a081dc76b98f1417329e4f26cb4768bb`.

The software work can proceed on GitHub; five completion gates require distinct evidence. No script or simulator can supply author consent or measured physical current. No coauthor request or submission has been sent.

| Gate | Prepared material | Exact next input/action |
|---|---|---|
| Original signed deadline | New frozen LTO compiler pilot, `experiments/mcu_deadline_v2`; original O3 data retained. Packet-level accounting is `outputs/mcu_deadline_v1/critical_path_accounting.json`. | Fixed pilot completed and audited: 68/200 misses remain, with 200/200 delivered and signed. An independently specified, endpoint-preserving accelerated crypto backend would require a further study. Do not extend 90 ms or count a private MAC as the signed endpoint. |
| Physical RF/current | `hardware/PHYSICAL_VALIDATION_PROTOCOL.md`, `hardware/cc2538_live/PHYSICAL_ACQUISITION.md`, `scripts/analyse_physical_power_trace.py`. | Bring the linked desktop online and provide access to four compatible physical radio boards, debugging/programming interfaces, a packet sniffer and calibrated current acquisition equipment. Record actual board/radio/instrument models and serials first; review a compatible board port before programming. Freeze the acquisition design before measurements. Retain calibration, supply boundary, firmware hash, synchronized raw current and packet traces. A simulator image is not yet a physical-board firmware port. |
| Production security | `docs/SECURITY_EVIDENCE_MATRIX.md` and retained emulator negative controls. | Identify actual board, boot root of trust and key-storage mechanism. Implement and test board-specific key readout restrictions, authenticated provisioning, unauthorized firmware rejection, and reset/power-cut/rollback-resistant sessions. Retain logs and independently reviewed configuration; do not publish secrets. Unavailable hardware protections require an explicit reduced claim or a different platform, not a passed checkbox. |
| Coauthor approvals | Exact-paper-version requests in `publication/array/Coauthor_review_request_*_DRAFT.txt`; pinned PDF and Word hashes in `author_review_version.json`. | User must explicitly authorize sending the prepared requests, or obtain the confirmations directly. Each actual author must approve the pinned version and confirm contributions, disclosures and overlap/exclusivity. Silence and this handoff do not establish consent. Private replies stay private. A substantive manuscript revision needs renewed review. |
| Authenticated Array checks | `docs/ARRAY_SUBMISSION_CHECKLIST.md`; manuscript, highlights, figures and cover-letter draft. | Provide an accessible authenticated official portal session. Check article type, file roles/anonymity, declarations, costs and final assembled review PDF against current journal rules. Official guide retrieval currently returns 403. Do not accept agreements or submit without explicit authorization and actual author declarations. |

The linked desktop was offline (last seen eight hours ago) during this follow-up. This blocks inventory inspection and acquisition; it does not establish that no hardware exists. The official guide again returned 403. General Elsevier help is not proof of Array-specific authenticated checks.

## Reproduce the new diagnostic

```
python scripts/diagnose_signed_critical_path.py --profile outputs/mcu_deadline_v1 --output outputs/mcu_deadline_v1/critical_path_accounting.json
python -m unittest discover -s tests -p test_signed_path_accounting.py -v
```

Every successful source receipt must immediately follow a verify-stage event, and every sink delivery a sign-stage event. Duplicate or unsupported attribution fails. The O3 packet-matched sign-plus-source-verify minima are 109 ms (chain) and 110 ms (choice); both medians are 112 ms. All 34 critical packets in each topology exceed 90 ms in these two serial stages alone. This is a retrospective observation within the retained emulator, not a universal timing lower bound or a prediction about another crypto backend. Intermediate verification, routing, radio and other work add further latency.

## Executed LTO follow-up

Frozen source commit `b52842496dc625ad30ff95bdefad4c107366080e`; successful workflow `39179074994` (2026-10-19 00:03:54–00:07:25 UTC). Chain signed delays: 299–308 ms; choice: 213–220 ms. Both have 34/100 deadline misses. All 200 sink signatures independently verify, all 200 accepted source receipts match received signed frames, and all 200 one-bit signature mutations are rejected. The actor matches the frozen host choices at all 500 decisions; maximum logit error is 1.9073486328125e-6.

Endpoint sign-plus-source-verify observed minima are 104 ms (chain), 105 ms (choice), with 106 ms medians in both. All 68 critical packets exceed their deadline in those two stages alone. Faster observed receipt ranges do not demonstrate a statistically established compiler speedup: these are sequential diagnostics, not independently replicated timing experiments. No packet, class, failure or historical profile was removed.

Raw logs, ELF, generated firmware, environment, build and packet audits are under `outputs/mcu_deadline_v2`. The downloaded artifact SHA-256 is `ee4d87c1d6d1e806c0725c4c2758ca34ef5fa22dd28d3057cf90b5889de2b961`. Physical RF/current, production security, actual author approvals and authenticated portal checks remain open.
