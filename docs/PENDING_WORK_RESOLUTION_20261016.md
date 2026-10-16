# Resolution of five review items

## 1. Runner acceptance — implemented and executed

The runner writes pending_audit before capture verification and passed only after the independent audit succeeds. Required: ten source packet identities, ten unique sink deliveries, ten source signed receipts, ten runtime-accepted receipts, ten source/relay settlements per node, complete final logs, no protocol/transport errors and five exact probe outcomes. Any failure exits nonzero, retains failed.json and prevents a passed verification status. Nonzero deadline debt remains permitted because this is not a deadline-compliance test.

## 2. Audit new runs — implemented and executed

Use `python scripts/audit_renode_boards.py --run PATH --expected-packets 10 --output /tmp/audit.json`. Repeat --run for multiple folders. A direct call prints a report without replacing archived results unless --output is supplied. Default invocation checks the named strict suite. Runtime receipt counters are required; historical inspection must explicitly use --allow-legacy-receipt-log, reported as null counters. Actual fresh attention, MLP and greedy controls pass with ten deliveries and ten runtime-accepted receipts each.

Ten regression cases cover a complete capture and rejection of partial delivery, missing receipt, missing final log, incorrect negative probe, future-only transmission, false accepted-receipt count, altered frame, incorrect CLI run outcome and missing runtime receipt counter. The full suite passes 83 tests in 5.19 s.

The older greedy capture lacks relay-1's final record. It fails strict audit and is retained unchanged. Prior reports did not check this field; their summaries are not retroactively treated as complete raw evidence.

## 3. Documentation — consolidated

Current README, Array status, distributed-auth status, submission status, reviewer status and virtual-board instructions distinguish the PTY API model, compiled Renode MCU bridge and unvalidated physical/embedded work. Prior submission/reviewer notes are preserved under HISTORICAL_*.md. The manuscript now describes the strict gate and the discovered incomplete older capture.

## 4. Physical/embedded validation — not completed

The available firmware runs the radio/UART bridge. Policy inference and cryptography remain on the host. Neither physical RF/current measurements nor MCU inference/crypto execution is produced by the strict integration runs. The execution and evidence protocol is hardware/PHYSICAL_VALIDATION_PROTOCOL.md. No actual boards, RF sniffer or calibrated logger is connected in this environment. These items remain unavailable work, not passed tests. Simulator results cannot resolve the physical measurement requirement.

## 5. Submission checks — public requirements checked, attestations open

Public publisher-indexed Array guidance confirms the 250-word abstract ceiling, highlights, single anonymized review and AI disclosure. The full author-guide fetch returns HTTP 403. The authenticated journal portal and conditional article-type forms are not inspected. Standalone declaration drafts and editor letter are prepared; docs/ARRAY_SUBMISSION_CHECKLIST.md maps requirements to files and identifies required author confirmations. No coauthor consent, exclusivity, funding/conflict attestation, portal certification, payment or submission is fabricated.

## Scope

Original 750-run and 180-run statistical outcomes and checkpoints remain unchanged. These changes improve evidence acceptance and reporting. They do not establish attention superiority, live intrusion detection, absolute deadline compliance, calibrated energy or physical hardware validation.

## Author update received

On 16 October 2026, Shivam confirmed no funding, no competing interests, himself as first/corresponding author and Assistant Professor at UIM, and Dr. Abhishek Kumar Pandey and Dr. Abhinandan Tripathi as second and third authors. The active manuscript and declaration files reflect this order. Coauthor affiliations/emails were subsequently supplied and incorporated. Contribution roles, final coauthor approval and exclusivity remain to be supplied. Former authors’ contribution roles were removed rather than reassigned.
