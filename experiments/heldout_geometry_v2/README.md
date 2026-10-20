# Held-out geometry validation v2 — frozen design, not executed results

Research purpose: test whether the archived 1,440-case matched-feedback result transfers beyond its tightly perturbed geometry family, and distinguish honest loss-induced negative feedback from deliberately dropped packets. This is a **new** prospective study informed by archived observations, not an independent pre-discovery replication or a replacement for existing evidence.

## Factorial design

- **30 independent geometry blocks** (no observed radio outcomes involved in selection), from deterministic RNG seed \`261020\`.
- **15 clipped + 15 unclipped source-progress geometries.** The sink remains at \`(90,0)\`, matching the hardcoded coordinate used by frozen firmware. The source shifts for unclipped geometries; both relay hops have distances below 48.5 m against Cooja's 50 m UDGM transmission range, with no source-to-sink direct edge.
- 1 relay-ID permutation per geometry (8/7 of each permutation in each stratum). The original matched study already covered both permutations per fixture; current permutation is not a within-geometry factor.
- Each block fully crosses **2 attack-onset points (10,30) × 2 RX probabilities (0.8,1.0) × 2 schedule modes × 3 physical attacker states (benign, relay A, relay B) × 4 matched arms = 96 settings**. All 30 blocks together contain **2,880 runs**, of which 1,920 are attacked and 960 are benign. The random radio seed is held paired across arms and adversarial states within each geometry/onset/RX condition.
- The three previously trained Q22 actor checkpoints rotate equally across blocks (10 blocks/checkpoint). Checkpoint and geometry are **not fully crossed**. No new training, threshold tuning, or evidence-rule retuning is permitted.
- Frozen contrasts: negative update main effect, proof-generation main effect, and negative×proof interaction. Proof frames are **excluded from feedback credit** in all four matched arms, so the proof factor evaluates extra traffic cost, not evidence benefit.

## Statistics, interpretation and limitations

For attacked settings, the primary outcome is **post-onset unique sink delivery fraction**. Average observations over both physical attacker positions, both onset points and both RX levels within each geometry, separately by timing and arm. Geometry is the independent unit; packets and paired settings are not independent samples.

Use six contrasts per endpoint (three contrasts × two schedule modes), with one Holm correction within each endpoint family. The two-sided paired sign-flip test uses 200,000 fixed-seed Monte Carlo sign assignments across 30 geometry differences, and 20,000 geometry bootstrap draws for pointwise confidence intervals. Conditional sign-symmetry is an assumption, **not** randomized arm assignment. No test result exists until the complete new archive is audited.

The benign controls at RX=0.8 and RX=1.0 reveal possible unintended failure penalties under honest channel loss. RX failure alone is **not** proof of congestion or an attacker. Recovery is only substantively interpretable for attacked runs where the last pre-onset choice selected the attacker; count initially unexposed runs separately, with right censoring. Cooja radio transmit/listen seconds remain proxy airtime, not device joules. The existing MCU 68/200 signed-receipt deadline misses remain unresolved.

The frozen actor's progress normalization remains \`/38\` and the sink coordinate \`(90,0)\`; changes to them or the original experimental scripts would alter the scientific intervention. All historical experiments are unchanged. The new results must not be retrospectively pooled with their Holm families.

## Reproduce and execute

From repo root:

\`\`\`sh
python experiments/heldout_geometry_v2/design.py --check --export outputs/heldout_geometry_v2/case_manifest.json
PYTHONPATH=src python -m pytest -q tests/test_heldout_geometry_v2.py
python experiments/heldout_geometry_v2/run.py --verify-only
\`\`\`

A native Cooja technical pilot requires the pinned Java 25 / Contiki / Cooja environment and is deliberately excluded from the scientific 2,880-case count:

\`\`\`sh
bash experiments/remediation_v1/bootstrap.sh
python experiments/heldout_geometry_v2/run.py --smoke
\`\`\`

Only after the smoke passes and the execution cost is approved:

\`\`\`sh
python experiments/heldout_geometry_v2/run.py --execute --workers 2
python experiments/heldout_geometry_v2/analyze.py
\`\`\`

**Completion rule:** every declared case must have a passing original Cooja independent audit and antecedent-event check. Failures and lost packets are retained; no partial archive may be analysed. Signed-deadline compliance, physical RF/current and device security cannot be inferred.

GitHub Actions performs outcome-free design tests and, if configured, a separate technical pilot. It **does not automatically launch the 2,880-run experiment** or silently overwrite original artifacts.
