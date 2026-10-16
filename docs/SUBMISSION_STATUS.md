# Current submission status

The active target is Array. Read [the consolidated current status](ARRAY_TARGET_AND_VIRTUAL_STATUS.md) and [submission checks](ARRAY_SUBMISSION_CHECKLIST.md).

The original 750-run feedback study and the separate 180-run authenticated transfer remain unchanged. Four Renode CC2538 boards execute compiled radio-interface firmware; routing and cryptography remain on the host. Physical board, embedded inference/crypto and calibrated power validation are not complete. No attention superiority or live intrusion detector claim is supported.

The stricter runner requires ten offered packets, ten unique sink deliveries, ten runtime-accepted source receipts, complete source/relay final records, five probes and a public capture audit before it writes passed. The new audit supports --run PATH and fails on missing evidence. Historical captures are retained unchanged, including an incomplete greedy relay-final log discovered by the stricter audit.

Earlier stages are preserved in [the historical record](HISTORICAL_SUBMISSION_STATUS.md); their old test totals and pending statements do not describe the current implementation.
