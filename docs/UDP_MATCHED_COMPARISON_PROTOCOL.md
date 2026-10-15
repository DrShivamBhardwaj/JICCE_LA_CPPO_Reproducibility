# Matched-capacity UDP diagnostic comparison

Frozen before outcomes on 2026-10-15. Exploratory software-in-loop comparison motivated by earlier attention-only failover results. Use fresh synthetic topology seeds 73001–73030, paired with existing attention/capacity_mlp checkpoints 41001–41030. No training or tuning. Same source-selection rule as the previous diagnostic.

For each fixture define two shared fault targets: the attention policy's initial preferred relay and the capacity-MLP policy's initial preferred relay, both evaluated at prior risk. Run both controllers independently against each shared target. Keep both target strata even if targets coincide; average strata within fixture before paired inference to avoid pseudo-replication. This symmetric design avoids evaluating each controller only against its own preferred relay.

Each run makes 30 class-0 decisions with fixed model-derived network/queue/energy/QoS state and actual localhost UDP forwarding, downstream sink witness and risk feedback. Targeted relay persistently drops; others forward. ACK timeout remains 20 ms. Candidate builder and shield are shared. Model capacities and frozen checkpoint hashes are recorded. Target labels stay out of controller observations.

Primary descriptive contrast: per-fixture delivery fraction, averaged over two target strata, attention minus MLP. Report paired mean difference, 95% Student-t CI and two-sided paired t p-value across 30 fixtures. One prespecified endpoint; no outcome-dependent endpoint selection. Provide stratum-specific and initial-target-exposure summaries without inferential claims. Keep all failures. Packet count 30 fixtures × 2 targets × 2 controllers × 30 = 3600.

This fault fixture does not reproduce wireless traffic or compare radio performance. No claim of broad attention superiority, realistic IDS integration or hardware feasibility can follow. Software ACK timings are not WSN latency. Physical validation remains outside available evidence.
