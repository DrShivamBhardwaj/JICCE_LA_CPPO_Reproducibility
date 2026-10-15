# Functional integration results — 2026-10-15

30 separately seeded synthetic network fixtures completed 360 real localhost UDP forwarding attempts using the unchanged attention_41001 checkpoint (SHA-256 25d6418482ac7318e9f73656aefe95c68fefeb3e1266c084f5993bf59c72ecf8). The fixed drop schedule produced 240 acknowledgments and 120 timeouts. All 240 acknowledged packets had an independent sink receipt; witness/adapter mismatches: zero.

Risk updates changed all 360 serialized post-feedback policy probability vectors. Immediate next-hop argmax changed in 0 cases. Candidate order and shield feasibility may change too: these counts represent the full observation/routing pipeline, not an isolated neural attention effect.

The independent verifier reconstructed every pre/post observation from fixture state and accumulated posteriors and recomputed all frozen-policy probabilities and selected actions. It passed. The complete repository test suite passed: 47 tests.

This demonstrates a working software chain from selected relay through UDP packet, downstream sink acknowledgment, Bayesian risk update and subsequent frozen-policy inference. No training, tuning or checkpoint selection occurred during this run. Source node, energy, queue and QoS state stayed fixed inside each fixture. Fixed packet fault injection is not an independent malicious-behavior distribution, and expected PDR remains simulator-derived. These 30 fixtures do not establish deployment generalization or routing performance superiority.

Still absent: authenticated feedback, an observer resistant to relay/sink collusion, real link telemetry, realistic concurrent MAC traffic, ACK energy accounting, and physical radio measurements. Loopback timing must not be reported as WSN latency. Reviewer A's practical integration objection therefore remains only partially addressed.

Reproduce with `python scripts/run_udp_policy_integration.py` then `python scripts/verify_udp_policy_integration.py`. Raw trace and summary are in `outputs/udp_policy_integration/`.
