# Persistent-fault diagnostic results

Executed 2026-10-15 after protocol freeze. All 30 previously trained checkpoints were used unchanged, one per fresh synthetic network fixture (72001–72030). There was no retraining, hyperparameter adjustment or selection of a favorable checkpoint.

Of 30 fixtures, 25 selected an alternative relay after feedback from the persistently failing initial relay; 5 remained on the failed relay throughout 30 attempts. Median first failover was packet 2 among the 25 switching fixtures. Across 900 real localhost UDP attempts, 718 had independently witnessed sink receipt and 182 timed out. Adapter/sink outcome mismatches: zero.

At the first switching decision in each of the 25 successful fixtures, the faulty relay remained in the top-k candidate set and remained unmasked. The frozen policy selected another available candidate. This rules out faulty-candidate removal or masking as the immediate mechanism in these first-switch decisions. Candidate order and the remaining candidate set can still change, so the experiment does not isolate attention from the full observation pipeline or compare against an MLP.

The separate verifier rebuilt all 900 pre/post observations from network fixtures and cumulative risk posteriors, recomputed frozen-policy probabilities and actions, checked all per-run checkpoint hashes, and matched outcomes to the fixed relay-fault schedule. It passed. Full repository tests: 47 passed.

This is exploratory diagnostic evidence following an earlier periodic-fault test with zero next-hop changes. The adversarial fixture targets each controller's initial preferred relay. It therefore cannot estimate random-attack effectiveness, broad network generalization, IDS accuracy, or a treatment effect against a comparator. Only risk evolves within each fixed-state source fixture. Link PDR, queues and energy are model-derived. Localhost packet/ACK exchange establishes software integration; it does not establish realistic wireless traffic performance, feedback authenticity, radio energy cost or hardware feasibility.

The five non-switching fixtures are retained in raw traces and run_summary.csv. No claim of universal failover or attention superiority is supported. JICCE resubmission still needs defensible scope, deployment-relevant feedback/telemetry evidence and journal format/citation checks.

Raw records are split across trace_part1.jsonl through trace_part3.jsonl for transport. Run `python scripts/verify_udp_persistent_fault.py` to verify them; generate a new run with `python scripts/run_udp_persistent_fault.py`. The local single trace and three archived parts contain the same records.
