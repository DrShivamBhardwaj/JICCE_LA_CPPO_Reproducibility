# Receipt deadline assessment

The original 134/200 signed-receipt misses were not removed by changing clocks or loosening deadlines. The implementation now isolates the computation bottleneck and records two distinct improvements.

Fixed-point inference and a cached signing key reduce the original signed endpoint to 68/200 misses; the 350 ms class passes in these runs, while the 90 ms class still fails. An additional private source-authentication frame reaches the source in 49–63 ms and has 0/200 misses, with all two hundred deferred Ed25519 proofs independently verified. This is a different endpoint, not a retroactive pass for the original public-signature criterion. It adds traffic and provides source-only MAC authentication before public evidence.

See outputs/cc2538_fast/receipt_profiles_summary.json and hardware/cc2538_q22/README.md for full numerical and security boundaries. Packet observations from two sequential streams are not independent reliability trials or physical timing measurements.

Implemented software hardening includes one-time provisioning lock, stale-session rejection, signing-key/public-key consistency, cached signing state, temporary-buffer erasure, fixed-point input/overflow bounds and tested-path stack guards. None certifies production protected storage, secure boot, physical provisioning or device-persistent anti-replay state.

The attached-device check found no USB sensor-board interface or matching board/power instrument. Physical RF/current data were not acquired. The physical acquisition procedure and power-trace analysis tool are prepared, but real measurements require actual compatible boards and a calibrated instrument.

A narrow Gmail search over the supplied coauthor addresses and this manuscript's title/identifier returned no matching approval record. It is not an exhaustive search of every possible approval channel. No message was sent and no consent was inferred. Actual author approvals, contribution/exclusivity confirmations and authenticated journal submission checks remain author actions.
