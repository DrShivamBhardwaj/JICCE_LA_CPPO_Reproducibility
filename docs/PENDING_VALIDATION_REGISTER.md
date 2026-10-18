# Current validation register

## Completed virtual implementation work

The frozen 600-run Cooja evaluation now executes both the trained Q22 actor and weighted feedback ledger on native motes with real simulated radio receptions and MAC callbacks. All 600 captures passed independent replay, wire verification, feature and policy checks; 61,845 decisions and 143,928 ledger events were verified. The 118-test suite passes. Section 5.9, Table 11, Figure 12, abstract and conclusion integrate the findings. Existing benchmark families and prior failures remain preserved.

The post-warm-up blackhole condition exposes a substantive limitation: delayed delivery is 32.94% for censored feedback versus 79.11% for active proofs. This cannot be labeled a successful universal replacement. Proof-matched comparisons, fixed topology, public keys, nominal telemetry, scheduling assumptions, retained watches and roughly 1 ms freshness quantization are documented.

## Actual remaining requirements

1. Physical board startup, RF/interference and calibrated current/voltage measurements require actual compatible boards and instruments. No physical measurements were obtained.
2. Production security needs board-specific protected storage, authenticated provisioning, device-persistent anti-replay state and relevant physical tests. Emulator/session and software crypto checks do not certify these.
3. The original signed-receipt deadline remains unmet in the retained MCU pilot: 68/200 misses after Q22 optimization. Fast private receipts are a distinct endpoint.
4. Actual final-version coauthor approvals, contribution roles and exclusivity/overlap confirmations are not supplied by templates.
5. Authenticated Array portal requirements and its assembled submission PDF remain unchecked. The latest official guide retrieval returned 403 and the browser homepage was unavailable. No upload, agreement, submission or payment occurred.

Use scripts/audit_remaining_validation.py for the retained full-validation gate; it deliberately does not infer external approvals or physical evidence. See hardware/cooja_feedback/README.md and publication/array/Cooja_Feedback_Evaluation.md for the completed virtual study. Further algorithm redesign would be a new experimental intervention requiring a new frozen comparison, not a relabeling of these results.
