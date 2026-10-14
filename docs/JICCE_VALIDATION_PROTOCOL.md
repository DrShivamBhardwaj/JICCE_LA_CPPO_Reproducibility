# JICCE reviewer-led validation protocol — 14 October 2026

This is a new validation study, not a rescue of the historical AF-v3/AF-v4 gates.
The original failed joint test and untouched 230xx seeds remain unchanged.
Frozen new seeds: 41001–41030. No tuning or model selection on these outcomes.
Four arms: 96-width attention; nearest-total-parameter-count MLP; attention without
all risk pathways (candidate features/preselection/reward); attention with only
80% of forwarding outcomes observed. Missing-feedback sampling is independent.
The last arm is simulated imperfect feedback, not a hardware or live-IDS test.

Each arm/seed trains for eight updates of 50 episodes, three PPO epochs each.
Evaluation uses 240 episodes in each of four settings: nominal 100 nodes/25%
attack, 200 nodes in the same area, 10% attack and 40% attack. Weights remain
frozen during transfer. Transfer results are secondary sensitivity evidence;
200 nodes in the same area changes density and does not demonstrate general
scalability or density-preserving expansion.

Co-primary nominal endpoints are Class-0 mean delivered delay and total violation.
The six tests (three comparisons × two endpoints) form one Holm family.
Delivery and energy differences are descriptive guardrail context; no claim of
overall success or universal QoS is inferred from significance on one endpoint.
All confidence intervals are unadjusted paired 95% t intervals.

Traffic, dynamics, transition-attack, radio and missing-feedback generators have
separate seeded streams. This prevents radio consumption from shifting traffic
draws. It does not enforce identical per-edge exogenous schedules across policies;
radio and attack streams still advance according to actions. Source eligibility
can change after node death. Do not describe this as exact event-trace replay.

The candidate MLP width is chosen using parameter count alone, before efficacy
outcomes. Hidden width and compute are not equal. Stored checkpoints permit
independent evaluation. Report every arm/seed, including unfavorable outcomes.

Remaining external-validity limits: packet-level Python PHY/MAC abstraction;
direct simulator outcome feedback; no experimental device energy, authenticated
feedback protocol, measured telemetry overhead or field-deployment validation.
