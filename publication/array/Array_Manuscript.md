A Reproducible Benchmark of Receipt Assisted Passive Feedback and Authenticated Routing in Wireless Sensor Networks

Shivam Bhardwaj¹*, Dr. Abhishek Kumar Pandey² and Dr. Abhinandan Tripathi³

¹ Assistant Professor, Department of Computer Applications (MCA), United Institute of Management, Prayagraj, Uttar Pradesh, India
² Department of Computer Science and Engineering, Bennett University, Greater Noida, India
³ Department of Computer Science and Engineering, Buddha Institute of Technology, Gorakhpur, India

*Corresponding author: shibambhardwaj@gmail.com; ORCID: 0009-0005-4554-7397
Abhishek Kumar Pandey: abhishek.pandey2@bennett.edu.in; ORCID: 0000-0003-3799-9754
Abhinandan Tripathi: abhinandan282@bit.ac.in

Abstract

Missing forwarding evidence can reflect packet loss, contention or an unobserved transmission, making feedback design a joint problem of inference and airtime. We benchmark ACK-gated censored passive feedback against active proofs in 750 IEEE 802.15.4 runs on 30 new fixtures, with naive-passive, frozen-prior and capacity-matched policy controls. Under blackholes, delivery increases from 71.28% to 75.94%, a paired gain of 4.67 percentage points (95% interval 2.36–6.97; Holm-adjusted p=0.0161). Energy per delivered byte falls while total modeled radio energy rises slightly. The controls do not establish a unique censoring or attention advantage. A separate 180-run experiment tests frozen policies over authenticated messages and node-local records. Attention delivers 81.61% in benign conditions and 61.11% under selective dropping, without an established advantage over greedy or multilayer-perceptron routing. In 600 Cooja transfer runs, a relay that starts dropping after warm-up exposes a failure: delivery with scheduled processing delays is 32.94% with censored feedback and 79.11% with active proofs. A further 240-run factorial study separates proof traffic from evidence handling; adding proofs reduces delivery by 6.11 percentage points with always-on listening. A fixed-point MCU actor reduces signed-receipt deadline misses; a separate source-authenticated receipt profile meets its tested deadlines while retaining deferred public signatures. An exploratory 60–300 s extension exposes routing-energy exhaustion and increasing service debt. The contribution is a traceable comparison of feedback mechanisms and transport boundaries; the evidence does not establish sustained operation, physical-board performance, measured energy consumption or absolute deadline compliance.

Keywords: Wireless sensor networks; Routing feedback; Authentication; Policy transfer; Reproducibility; Virtual validation

1. Introduction

Multihop sensor networks depend on link estimates, progress toward the sink and control traffic. RPL, expected transmission count and the Collection Tree Protocol use these ingredients in different ways [1, 2, 3]. Adding forwarding evidence changes the balance: an acknowledgment can improve confidence in a relay while consuming airtime that would otherwise carry data. Assessing a feedback mechanism therefore requires measuring both the information it provides and the traffic it creates.

Watchdog monitoring and explicit acknowledgments have long been used to detect forwarding misbehavior [4, 5]. Their observations need careful interpretation. Overhearing confirms a transmission attempt, while reception by the intended next hop remains uncertain. Silence is also ambiguous: the first hop may have failed, the channel may be busy, or the observer may have missed a frame. Penalizing every silence can redirect traffic even when no node is malicious. We study how routing should handle this missing evidence; we do not train an intrusion classifier.

Recent studies combine trust with edge-assisted routing [6], optimizer-based next-hop selection [7], learned trust estimates [8], failure-aware deep Q-learning [9] and opportunistic forwarding [10]. Trust-gated reinforcement learning [11] and secure deep reinforcement learning [12] address related interactions between routing and security. Table 1 compares their stated mechanisms with the question examined here. Differences in channels, workloads and attack models prevent a defensible numerical ranking against those published results.

Table 1. Literature and experimental focus

Earlier architecture comparisons found no joint advantage over a multilayer perceptron of similar capacity. The earlier 600-run telemetry study likewise found no advantage after correction for multiple testing and exposed the traffic cost of active proofs. Both stages and their raw outputs are retained. They motivated the present comparison of receipt-assisted passive feedback with active proofs, subject to prespecified margins against a frozen-prior control on new fixtures.

1.1 Benchmark contribution

We benchmark ACK-gated censored passive feedback against active proofs while retaining controls for missing-evidence penalties, evidence updating and policy capacity. Own first-hop ACK success gates credit; each observer–relay–packet record retains its strongest matched observation; missing evidence leaves the effective failure count unchanged. Packet-reception callbacks connect the ledger to simulated radio events. In Fig. 1, Eq. (1) supplies the candidate shortlist, while Eq. (2) scores the retained candidates. Figure 2 maps the record updates in Eqs. (3)–(4). The benchmark builds on established watchdog, censoring and learning methods.

The prespecified decision combines a blackhole delivery comparison against active proofs with delivery, critical-service and energy-efficiency margins against frozen-prior attention. Naive-passive and capacity-matched controls assess whether the outcome can be attributed specifically to censoring or policy architecture. An improvement over active proofs alone cannot establish either attribution.

A second implementation stage examines whether the frozen policies can use authenticated messages and node-local transit records. It comprises 180 new radio runs and separate serial-interface and firmware-emulation checks. Sections 2–4 report the feedback benchmark; Section 5 describes the authenticated transport and evaluates it separately. Its changed observation model prevents carrying the earlier performance claim into this branch.

2. System model and methods

2.1 Radio traffic and threat model

The simulated network has 100 stationary sensors in a 150 × 150 m field and a sink at (75, 75) m. The ns-3.44 low-rate wireless personal area network model provides unslotted access, MAC acknowledgments and packet reception [13]. The log-distance model uses exponent 3 and a reference loss of 40 dB, increased to 54 dB in the weak-link setting. A separate 50 m range limit applies. These settings describe the simulated radio environment.

Runs last 4 s. After a 0.4 s warm-up, the source offers 60 packets at 20 ms intervals, shortened to 2 ms for the congested burst. The three traffic classes have probabilities 0.35, 0.45 and 0.20, with deadlines of 90, 350 and 1,500 ms. Each 64-byte application frame contains 12 identifier bytes and 52 payload bytes; MAC and physical-layer overhead is additional. Nodes broadcast application telemetry every 0.5 s with a 3 ms node offset. We call these messages beacons, although they are distinct from IEEE superframe beacons. Table 2 lists the shared settings.

Table 2. Frozen network settings

For each blackhole fixture, 25% of sensor identities are selected independently as faulty relays. They accept packets but skip the forwarding decision, while retaining the modeled beacon and receipt behavior. The threat model excludes forged control values, collusion and a compromised sink. Attack labels are used only by the simulator and evaluator; the router sees forwarding observations, not those labels.

2.2 State construction and frozen routing policy

A received beacon creates or refreshes an observer-specific cache entry containing energy fraction, pending-request pressure, timestamp and link-quality indication. Entries expire after 0.75 s. The current node, visited nodes, exhausted nodes and nodes beyond 50 m are excluded from relay selection. The following fixed score retains at most eight candidates:

		(1)

• For observer u and candidate v, g is sinkward progress divided by 50 m and q is the current estimated MAC success probability; both are dimensionless.

• Candidate energy fraction e is remaining modeled energy divided by 0.5 J; Q is pending-request pressure normalized by 32; R is the dimensionless risk score from Eq. (5). The preselection score S is dimensionless.

The observation contains 13 context values and eight candidate rows of ten values each. Context records local energy and queue state, normalized sink distance, remaining deadline, traffic class and six node-local service-debt coordinates, updated only at sources in this benchmark. A candidate row records whether the node is the sink, its energy fraction, estimated MAC success, received link quality, queue pressure, sinkward progress, evidence risk and uncertainty, expected retries and normalized link delay. During radio transfer, received link-quality indication replaces the RSSI proxy used in training. The weights remain fixed despite this feature shift.

Equation (1) uses hand-set preselection coefficients, not learned parameters. The retained source records the values but contains no systematic tuning history. The later ±20% coefficient experiment in Section 5.5 is a local sensitivity check and does not retrospectively optimize this score. Equation (2) divides the query–key product by the square root of 96, as implemented in PyTorch.

Shared encoders map context x and candidate h to separate 96-dimensional representations. Their query–key interaction and a shared candidate bias give the action logit:

		(2)

• For context vector x at observer u and candidate feature vector h for link (u,v), ℓ is a dimensionless action logit. Both feature vectors contain normalized, dimensionless coordinates in the frozen benchmark.

• qθ and kθ are learned query and key transforms; bθ is the learned scalar candidate bias. The symbol qθ denotes a neural transform, whereas q in Eqs. (1) and (4) denotes link success. Parameters θ are fixed during evaluation.

A masked argmax chooses the relay. Candidate encoders share their weights, and the critic pools valid candidates by a masked mean, following the set-function motivation in [14]. The attention model has 63,368 parameters; the capacity-matched perceptron has 63,554 parameters and 203 hidden units. Candidates are ranked by the preselection score, with configured node identity breaking ties. Shared scoring therefore does not make the entire routing pipeline invariant to arbitrary node relabeling.

Both model families were trained on seeds 41001–41030 for 400 episodes per seed. Training used eight updates of 50 episodes, each followed by three full-batch PPO epochs. The learning rate was 0.0003, clipping parameter 0.2, discount 0.99, generalized-advantage factor 0.95 and entropy coefficient 0.01 [15, 16]. Six cost channels represented class-specific delay violations and losses. Lagrange multipliers used an update rate of 0.03 and were clipped to [0, 50]. This finite-budget procedure does not inherit the guarantee of constrained policy optimization [17]. Checkpoints and thresholds were held fixed throughout the new radio experiments.

2.3 Receipt assisted censored evidence

Observer u maintains a separate record for each selected sensor relay v and packet p. Evidence strength s and credited strength c are indexed by that record; effective counts α and β are shared across records for the same observer–relay pair. Each record stores the link-success estimate at registration, ACK status and expiry. A matched overheard forwarding frame contributes strength 0.5 and a reverse receipt generated by sink delivery contributes strength 1.0. Equation (3) retains the maximum, suppressing duplicate credit.

		(3)

• s is the strongest matched evidence for record (u,v,p), initialized to 0 and bounded by 1; it is dimensionless.

• I_overheard and I_receipt are dimensionless binary indicators of a matched forwarding-frame event and reverse-receipt event for the same record. Their weights are 0.5 and 1 in Eq. (3).

Credit is assigned only when the observer’s own first hop is acknowledged and s exceeds c. Evidence received before the ACK is stored. When that ACK arrives, the same eligibility check applies to the stored evidence. In Eq. (4), q denotes the value cached when record (u,v,p) was registered, rather than a later link estimate. The update is executed only for a strictly positive uncredited increment:

		(4)

• α is the dimensionless effective success count for observer–relay pair (u,v), initialized to 1; c is the dimensionless credited strength for record (u,v,p), initialized to 0.

• q is the dimensionless cached registration-time link-success estimate. The clip operator limits each positive increment to [0.05, 1]; c is then set to the current s.

In the censored arm, β stays at its initial value of 1 for each observer–relay pair. A failed first hop closes the record without positive credit. For an acknowledged first hop, expiry is set 150 ms after the ACK; absent forwarding evidence causes closure without a failure increment. A later matched observation can still increase s and earn previously unassigned credit. For q<0.1, the 0.05 floor can make two half-credit updates exceed one full q-weighted update. The smallest q in the audited decisions was 0.6923, so this case did not occur in those decisions.

The static floor in Eq. (4) acts on effective counts and is not a Bayesian update. Max-strength deduplication bounds the evidence state but does not remove the clipping artifact. Equation (5) uses 1.645 as a fixed multiplier on a beta-form standard deviation; neither this coefficient nor the score clipping provides calibrated 95% coverage or an exact Beta quantile. The fixture-level confidence intervals reported in the results are calculated independently of this routing heuristic. Changing these scoring rules would define a different feedback mechanism.

With the rate-anomaly term disabled, the retained policy maps the pair-specific effective counts to a risk coordinate ρ and an augmented routing score R:

		(5)

• ρ and R are dimensionless scores for observer–relay pair (u,v). The factor 0.75 scales both the failure-related coordinate and its uncertainty term; clipping bounds R to [0, 1].

• σ = sqrt[αβ / ((α+β)²(α+β+1))] is dimensionless, with α and β taken from the same observer–relay pair. The beta-form expression supplies a score component, not an evaluated posterior interval.

Table 3 sets out the feedback controls. Naive passive uses the same observations and duplicate suppression but penalizes an acknowledged forwarding attempt when evidence is still missing at expiry. Active proofs use separate packets and the earlier timeout convention; their credit rule does not require the passive arm's first-hop ACK gate. Frozen prior keeps the initial risk coordinates without updating them. The capacity-matched MLP uses the censored ledger. Thus, the active-versus-censored comparison changes feedback semantics as well as traffic; it does not isolate airtime alone.

Table 3. Feedback controls

2.4 Source service state and simulator boundaries

For a fixed source and traffic class c, the online service debt is updated once when that source settles a packet. The recurrence follows the virtual-queue form associated with constraint tracking [18]:

		(6)

• Zc is the dimensionless debt for class c at the fixed source; bc is the dimensionless allowed violation fraction per settled class-c packet. The source index and update-event index are suppressed in Eq. (6).

• I_violation is 1 if no receipt is available by service expiry or receipt age exceeds the class deadline, and 0 otherwise. A separate loss-debt channel uses the analogous receipt/expiry outcome. These online indicators differ from the sink-arrival endpoint in Eq. (8).

Only sources update these debts, on receipt or a 1.5 s expiry; intermediate relays retain no complete debt for transit service. Receipt age includes the reverse path, so a timely sink delivery can still produce a late source-observed outcome. The simulator maintains a shared visited set and reverse-path map without serializing their dissemination. Beacon energy and queue values are likewise supplied as metadata keyed to a transmitted identifier, with access gated by a radio-receive callback. Figure 1 marks these simulator-held inputs. Section 5 evaluates a separate authenticated implementation that decodes transmitted state.



Fig. 1. Frozen benchmark architecture.

Algorithm 1 gives the censored-passive event procedure; Table 3 specifies the other arms. Figure 2 shows the ACK gate and strongest-evidence lifecycle. Radio callback controls check reception of a two-hop forwarding observation, absence of reception at an out-of-range observer and absence of proof frames in the passive arm. They test callback paths rather than authentication or intrusion-classification accuracy.

Algorithm 1: ACK-gated censored passive routing

Input: radio events, cached telemetry, fixed policy θ; censored mode, 150 ms timeout.

Output: next-hop requests, observer evidence and source-service debts.

01.  For each received event or 1 ms polling tick:

02.  If a routing request is pending:

03.  Reject visited/exhausted nodes and the 22-hop cap; form at most eight candidates.

04.  If none is feasible, stop this request; otherwise select the masked-policy argmax.

05.  For a non-sink relay, register (u,v,p) and cache q at registration; transmit DATA.

06.  Else if the event is the observer’s own first-hop MAC result:

07.  On success, mark ACK eligibility and set expiry to ACK time + 150 ms.

08.  On failure, close the record without incrementing α or β.

09.  Else if matched forwarding evidence or a reverse receipt is received:

10.  Ignore unknown records and closed records without a successful own ACK.

11.  Update the strongest evidence s by Eq. (3), retaining any earlier stronger value.

12.  After either a successful ACK or an accepted evidence event:

13.  If ACK-eligible and s > c, apply Eq. (4); then set credited strength c to s.

14.  At each polling tick, close expired records without a β increment.

15.  Retain acknowledged records so later matched evidence can upgrade s and c.

16.  At a source receipt or 1.5 s service expiry, if the packet is unsettled:

17.  Update its class debt once by Eq. (6), then mark the packet settled.



Fig. 2. ACK-gated evidence lifecycle.

3. Experimental design

3.1 Development separation and untouched fixtures

Figure 3 records the source freeze, technical pilot and retained evaluation runs. Telemetry fixtures 76001–76030 informed the redesign. The protocol, source and decision rule were committed as 4027f071322cb5682f39329f656d76df3b68ff62 before fixtures 77001–77030 were evaluated. Technical pilot 76901 is excluded from inference. Each new fixture uses unchanged attention and MLP checkpoints from seed 41001 plus its fixture offset.

The four-second horizon isolates a burst and its feedback. Positions are available at startup and telemetry begins immediately; the model does not simulate RPL or CTP parent discovery. This design therefore evaluates a transient workload rather than routing convergence or steady operation.

Thirty fixtures crossed with five settings and five feedback/policy arms yield 750 runs and 45,000 offered source packets. No run is excluded. Within a fixture, arms share topology, traffic classes, offered packets and blackhole identities. Their event schedules can diverge, so matching seeds does not guarantee identical radio draws at every event. Statistical pairing therefore applies to the complete fixture and checkpoint. Packets are not independent replicates, and the sampled geometries come from one stationary placement family with a central sink.



Fig. 3. Frozen evaluation stages.

3.2 Endpoints and radio accounting

Delivery is the fraction of offered source packets received by the sink:

		(7)

• D is dimensionless; Ndelivered counts distinct packet identifiers received by the sink during the 4 s horizon.

For critical class 0, a packet violates its requirement if it is lost or arrives after 90 ms:

		(8)

• V is a dimensionless violation fraction and C0 is the set of offered critical-class packets.

• delayp is sink reception time minus source generation time, in seconds.

PHY-state integration sums the time each sensor spends transmitting, receiving/listening and switched off, including control traffic and retries. Sink energy is recorded separately and omitted from the sensor numerator. With the assumed 3 V supply, modeled radio energy is:

		(9)

• E is modeled sensor radio energy in joules; residence times T are in seconds and coefficients are amperes.

• The supply is 3 V. Currents are explicit assumptions, not calibrated measurements; CPU, sensing and cryptography are excluded.

Dividing this expenditure over the common observation window by delivered application payload gives energy per delivered byte:

		(10)

• η is radio joules per delivered payload byte; 52 is payload bytes per packet.

• A lower η can result from a larger delivered-byte denominator even if total E does not decrease.

3.3 Statistical analysis and frozen gate

For each comparator and endpoint, we calculate one difference per fixture and summarize the 30 paired differences. The two-sided 95% Student t intervals are descriptive and unadjusted. Hypothesis tests retain the prespecified Holm family of 60 comparisons: five settings, four comparators and three endpoints [19]. Delivery and violation differences use percentage points; energy-efficiency differences use J/byte. The comparison family is unchanged after examining the results.

The replacement passes only if all four prespecified checks succeed. Against active proofs, blackhole delivery must improve with Holm p<0.05. Against frozen prior, the one-sided 95% bounds must remain above −1 delivery point, below +1 critical-violation point and below an energy-efficiency geometric ratio of 1.02. Table 5 gives the criteria and outcomes. These relative margins assess a feedback replacement; the original absolute class-0 violation budget remains 1.5%.

4. Results

4.1 Delivery and matched controls

Under blackholes, censored passive attention delivered 75.94% of offered packets, compared with 71.28% for active proofs. The paired gain was 4.67 percentage points (95% CI [2.36, 6.97]; Holm p=0.0161). Figure 4 compares delivery contrasts across settings; Fig. 5 shows the paired blackhole observations and all control contrasts. Among the delivery contrasts, only the blackhole comparison against active proofs survived the 60-test correction. The energy-per-byte contrast also survives correction (Section 4.2).



Fig. 4. Delivery effects across settings.

Table 4 reports the remaining blackhole contrasts. Delivery differed by −0.17 points against naive passive, +0.06 points against frozen prior and +0.44 points against the capacity-matched MLP. None was significant after correction. The active-proof comparison consequently does not establish a unique benefit of censoring, evidence updating or attention. The declared margins also do not establish equivalence outside the tested conditions.

Table 4. Blackhole paired effects

Values are censored passive minus comparator; intervals are unadjusted paired 95% intervals. p values are Holm adjusted over the original 60 tests. Negative critical-violation and energy-per-byte differences favor censored passive. These are differences, not absolute arm means.



Fig. 5. Blackhole observations and effects.

4.2 Energy efficiency and control traffic

Under blackholes, energy per delivered payload byte decreased by 0.0006443 J/byte relative to active proofs (95% CI [−0.0009740, −0.0003145]; Holm p=0.0239). Total modeled sensor radio energy rose from 22.546943 to 22.547473 J, with a mean increase of 0.000531 J computed before rounding. The lower ratio reflects delivery efficiency rather than reduced total energy. Receiving/listening accounts for an average 99.36% of modeled sensor radio energy across the 750 runs.

Duty cycling changes the cost of passive observation. As an accounting example, an extra 150 ms listening window instead of radio-off time costs 3 × (0.0188 − 0.000020) × 0.15 = 0.008451 J under the assumed currents. Overlapping windows and existing awake periods reduce the incremental cost. This calculation is not a duty-cycled MAC experiment. Such a comparison must charge channel checks, rendezvous, observation windows and proof retransmissions to all arms; the always-listening results do not predict which mechanism would use less energy.

Figure 6 separates total energy, energy per delivered byte and PHY transmission count. Censored passive generates an average 60.57 fewer PHY transmissions per blackhole run than active proofs. All passive and frozen-prior arms request zero forwarding proofs, compared with 3,369 requests across the active arm's 150 runs. Beacons and reverse receipts remain in every arm. In the assumed always-listening model, receive/listen current exceeds transmit current; reducing transmissions therefore need not reduce energy over a fixed window. More delivered bytes explain the lower energy-per-byte ratio.



Fig. 6. Modeled radio-energy attribution.

4.3 Gate outcome and service limits

All three blackhole margins against frozen prior passed. The one-sided delivery lower bound was −0.405 percentage points, the critical-violation upper bound was +0.925 points, and the geometric energy-efficiency ratio upper bound was 1.00505. With the corrected delivery comparison against active proofs, these results satisfy all four checks in Table 5. The critical-violation bound lies close to its +1-point margin, leaving little room beyond the prespecified threshold.

Table 5. Prespecified incremental gate

The reduction in critical violations against active proofs did not survive correction for multiple testing. Censored passive still violates approximately 26.2% of critical requirements under blackholes, well above the original 1.5% budget. Passing the relative replacement test therefore does not establish absolute deadline compliance or a guaranteed quality-of-service controller.

4.4 Implementation and trace audit

The action and ledger audit checked 67,522 decisions, 24,747 passive observations, 28,353 evidence updates and 75,750 node-energy identities. A separate endpoint audit reconstructed delivery and critical-violation values for all 750 runs from source decision times and sink receptions, then checked beacon counts, decision counts and PHY-state energy. All 30 gzip streams were read to completion. The original-stage suite had 51 passing tests; the pre-extension implementation had 83 passing tests, including the radio callback checks. The post-freeze suite in Sections 5.6–5.7 has 107 passing tests.

Release checks found a truncated trace for fixture 77004. It was regenerated with the same frozen implementation, and all 750 canonical summary rows matched the saved pre-recovery summary exactly. Parameters, checkpoints and analysis rules were unchanged. The recovery record and audit code accompany the raw traces. These checks reconcile the implementation's own records; they do not provide an independent radio model, external packet capture or replay of every beacon-reception and service-state transition.

5. Authenticated transport and virtual validation

5.1 Local state and authenticated evidence

The authenticated branch uses the message path in Fig. 7. Coordinates, modeled remaining radio energy, queue state and transmit time are serialized in 58-byte application telemetry frames. A node relies on its provisioned own and sink coordinates, authenticated received cache, local MAC outcomes and packet history. Pairwise HMAC-SHA256 protects each hop with a 128-bit tag [20]. Provisioned 64-bit boot sessions and a 64-entry replay window reject stale sessions and duplicates. A source authenticator binds the immutable data fields. Ed25519 signs the source, session and packet identity at the sink [21], and the receipt follows node-local reverse records. Application frames are at most 114 bytes.



Fig. 7. Authenticated state and virtual interfaces.

Pairwise keys cannot authenticate a transmission between two other nodes, so the authenticated branch in Fig. 7 assigns no credit to third-party overhearing. Unlike Eq. (3), positive forwarding evidence requires a verified sink receipt and a successful local MAC acknowledgment; missing receipts remain censored. The frozen policies therefore encounter a changed observation model rather than an exact replication of the original ledger. Each node retains at most 128 records, with a 2 s expiry. Keys and sessions are provisioned out of band. Protected key storage, online key exchange and verification of telemetry truthfulness after key compromise remain outside the implementation.

5.2 Frozen host policy transport protocol

The authenticated-transfer protocol and source were committed as 5f06b9213e73206aad11ec8f3a96079a17011a20 before its outcomes were observed. Seeds 83001–83030 define 30 independent topology fixtures. Each pairs a frozen attention checkpoint with its capacity-matched MLP and a greedy progress control. The six-node diamond has two first-hop choices and two downstream relays. Nominal positions are (0,0), (25,−15), (25,15), (50,−15), (50,15) and (75,0) m, independently jittered by ±2 m; range is 38 m. Benign and selective-dropping conditions give 180 runs. In the latter, relay 1 discards even-identifier data after MAC reception. The router cannot access this attack label.

Each run lasts 7.5 s and offers 60 packets carrying 16 payload bytes. Traffic starts at 0.5 s, uses 75 ms intervals and cycles through the three deadline classes. Authenticated telemetry is attempted to every provisioned peer every 0.5 s, staggered by 2 ms. The record includes out-of-range requests and their modeled radio costs. All arms enforce strict progress toward the sink and retain at most eight candidates. Greedy picks the shortest remaining sink distance; the learned policies retain their trained weights. Fixed ns-3 seeds and streams pair the fixtures, although different decisions can consume different random sequences.

The observation has 93 elements: 13 context values and eight ten-value candidate rows. Decoded telemetry supplies neighbor geometry and energy. MAC success starts from a Beta(9,1) prior, and an exponentially weighted ACK-delay estimate uses coefficient 0.2 with an initial value of 5 ms. Received LQI replaces the training RSSI proxy. Queue features use raw MAC pending-request counts instead of normalized training pressure. Forwarding risk uses a positive-only transform of signed-receipt success counts and current link reliability. Nodes maintain separate class-delay and loss debts. These substitutions change the observation distribution; the transfer neither recreates the training model nor calibrates intrusion probabilities.

5.3 Transfer results and audit

Table 6 and Fig. 8 summarize all 180 runs. In benign conditions, attention delivers 81.61% of packets, versus 82.72% for greedy and 83.72% for MLP. Its paired differences are −1.11 points against greedy (95% interval −3.39 to 0.83) and −2.11 points against MLP (−4.50 to 0.28). Under selective dropping, delivery is 61.11% for attention, 62.89% for greedy and 60.50% for MLP. The attention differences are −1.78 points (−6.50 to 2.67) and +0.61 points (−2.56 to 3.78), respectively. Intervals use 10,000 paired percentile-bootstrap samples across fixtures with seed 94001. They are exploratory, without multiplicity-adjusted superiority testing.

Table 6. Authenticated policy transfer.

Means over 30 fixtures per condition and policy. Receipt rates count source-verified sink receipts. Critical failure includes undelivered critical packets. Energy covers modeled radio residence, not board or host CPU energy.



Fig. 8. Frozen policy transfer and paired effects.

The −1.78-point attention–greedy difference under selective dropping has an interval that crosses zero, establishing neither superiority nor equivalence. Replacing the training RSSI proxy with LQI, using raw queue counts and restricting forwarding credit to signed receipts can change the input distribution; their causal effects were not isolated. Greedy avoids neural weights and tensor inference, making it a sensible starting point for deployment assessment, although neighbor state, authentication and packet processing still incur costs.

The frozen host policies operate on serialized simulated-radio frames with multiple relay choices. For attention, critical-deadline failure is 31.17% in benign runs and 47.83% under selective dropping when undelivered packets count as failures. Total modeled radio energy is approximately 2.519 and 2.520 J per six-node run. Always-on listening and repeated authenticated telemetry dominate this radio-only account; embedded CPU and cryptographic energy are excluded.

The audit reconstructed 27,240 decisions, including 14,001 with more than one candidate. It matched 88,538 received byte frames to earlier transmissions, verified 46,204 public sink-signature occurrences and reconciled 1,080 radio-energy identities. Candidate cache values were checked against received beacon bytes, and frozen-policy probabilities were recomputed. Runtime nodes check the secret hop tags; the private keys are not exported for public verification. This branch leaves the original 750-run traces, checkpoints and decision rule unchanged.

5.4 Host controlled radio bridge firmware

Four pseudo-terminal devices expose the TX, RX, MAC-confirm and telemetry interface while ns-3 carries the application bytes. Four host-adapter processes use the same serial contract intended for later board integration. The first diagnostic delivered five of ten packets and revealed a timestamp error: the host sampled its clock before a blocking read, then used that earlier time to judge freshness. Sampling again when bytes arrived removed the false rejections. The corrected fixture delivers ten of ten packets and settles service at both relays. Both captures are retained. One functional fixture is insufficient to estimate reliability.

The PTY backend models the firmware interface without executing MCU instructions. Its greedy, MLP and attention rechecks each deliver ten of ten packets. A separate Renode 1.17.0 backend runs compiled C firmware on four emulated CC2538 Cortex-M3 boards (Fig. 7). Firmware parses UART JSON, bounds frame sizes, handles the IEEE 802.15.4 radio FIFO and correlates MAC acknowledgments. Routing inference and cryptography remain on the host. Each control delivers ten of ten packets and returns ten verified source receipts.

Five probes check the uncalibrated telemetry label, exact 114-byte delivery with ACK, rejection of 115-byte frames, malformed-hex rejection and failed out-of-range transmission. A separate capture audit checks MCU UART bytes, public sink signatures and packet identities. Development captures retain the startup and metadata corrections. The stricter audit also rejects an older greedy capture with a missing relay-1 final log, despite its saved summary. New runs pass only after all ten offered identities reach the sink, ten signed receipts are accepted at the source, source and relay final records are complete, all five probes succeed and the capture audit passes. All three fresh controls meet these requirements.

The full attention actor–critic stores 63,368 FP32 parameters, or 253,472 bytes (247.53 KiB). That count includes critic parameters that an actor-only implementation could omit. For comparison, the CC2538SF53 variant provides 512 KB flash and 32 KB RAM [22]. Flash-resident weights need not all occupy SRAM, but flash capacity alone says nothing about activation buffers, stack and protocol memory. An embedded build, linker map and peak-memory measurement are needed before claiming feasibility. The host-controlled firmware in this fixture handles UART parsing, frame bounds, radio FIFO access and MAC acknowledgments; it executes neither neural inference nor HMAC/Ed25519.

Renode's deterministic range medium differs from the ns-3 physical-layer model used for statistical evaluation. Energy telemetry is explicitly labeled emulated_no_power_model: the fraction is fixed, while queue telemetry counts pending MCU ACK records. It provides no battery measurement. The chain offers one feasible next hop at each relay, so it tests integration rather than policy selection or reliability. Deadline debts remain nonzero. The emulation does not validate physical clock and pin initialization, physical RF behavior, calibrated current consumption. Section 5.8 adds a separate live MCU policy/crypto pilot; this earlier host-driven fixture is unchanged.

5.5 Post review stress and sensitivity diagnostics

Table 7 and Fig. 9 report a separate exploratory extension on fixtures 84001–84003, using attention checkpoints 41001–41003. Active proofs, censored passive and frozen prior each run for 60 and 300 s, giving 18 runs. Packets arrive every 0.2 s from 0.4 s until near the end of the run: 290 and 1,490 offered packets, respectively. The topology, blackhole fraction, beacon schedule and 0.5 J routing-energy scale follow the frozen benchmark. These diagnostics were designed after review and do not enlarge the original confirmatory test family.

The extension exposes a limit rather than steady operation. At the assumed listening current, 0.5 J corresponds to roughly 8.87 s. Routing excludes an energy-depleted node, but the radio bridge continues telemetry and PHY-state integration. Delivery consequently plateaus while offered traffic and source-service debt continue to grow. Accumulated radio energy after depletion is bookkeeping for an energized simulation, not energy physically supplied by the original battery. Retained-watch counts also persist because closed records are not reclaimed.

Table 7. Long horizon stress diagnostics.

Delivery and critical-failure entries are means across three fixtures; debt is the maximum final delay debt across sources and fixtures. Zero handle-exhaustion events were recorded. Pending-map samples are taken once per second and cannot rule out transient MAC queue drops. This small extension supplies no bounded-queue or stability guarantee.



Fig. 9. Executed 300 s stress trajectories.

Figure 10 examines Eq. (1) on three further fixtures, 85001–85003, paired with checkpoints 41001–41003. Each coefficient is changed alone by −20% or +20%; the unchanged setting and ten perturbations give 33 four-second blackhole runs. All 30 perturbed fixture-level delivery contrasts are exactly zero in these runs. This limited result does not establish insensitivity in denser candidate sets or outside the tested range. These are local sensitivity observations, not a tuning procedure or a confidence interval. No checkpoint is retrained and no setting is selected from these results.



Fig. 10. Executed coefficient sensitivity contrasts.

The inference actor contains 44,161 parameters, requiring 176,644 FP32 weight bytes before runtime buffers; the full actor–critic contains 63,368 parameters. Removing training-only heads therefore changes the storage estimate, but neither count establishes target feasibility. Section 5.8 tests integrated target inference in emulation. Duty-cycled MAC performance, physical drift tolerance and measured energy still require separate validation.

5.6 Factorial traffic controls and power gating

A separate ns-3.47 extension tests proof traffic while holding the evidence rule fixed within each contrast. Its amended source and 30-test analysis plan were committed as 752c11e7fa3c6af427ffe4edb8fa37d3fbcd5bc7 before fixtures 89001–89030 were evaluated. An initial proof-callback error stopped a preliminary 88001 batch; those partial captures and technical pilot 76901 are excluded. Thirty fixtures, four arms and two duty settings yield 240 four-second runs, each offering 60 packets. All arms use the same bounded positive-credit rule, ACK gate, 128-record global simulation-ledger capacity, 2 s retention and frozen attention actor. Unlike Eq. (4), each record clips q once to [0.05, 1] and weights each eligible uncredited increment in s by that fixed value. Proof frames consume traffic but never enter the ledger. Censored versus naive mode changes expiry penalties and late-evidence handling. Table 8 reports arm means; Fig. 11 shows the proof-traffic contrasts.

With always-on listening, adding proofs reduces censored-mode delivery by 6.11 percentage points (unadjusted paired 95% interval −8.94 to −3.28; Holm p=0.00349), and naive-mode delivery by 5.61 points (−7.94 to −3.29; Holm p=0.000852). No evidence-mode or interaction contrast survives the separate 30-test correction. These results identify a traffic contribution in this extension, not the complete cause of the original 4.67-point gain. The nominal 20% awake schedule rejects requests while asleep and has no rendezvous protocol; delivery falls to approximately 13–14%. Busy MAC transactions defer sleep, so nominal duty is not actual PHY residence.

Table 8. Factorial arm means.



Fig. 11. Proof-traffic delivery effects.

Hard power gating stops the experimental bridge at each sensor’s 0.5 J budget. Twenty-seven further 60 s runs cross three fixtures, three feedback arms and three nominal awake fractions. All remain within the 50 J aggregate sensor budget, with zero post-cut transmissions; the audit reconciles 2,727 radio-energy identities. The bounded ledger has zero final watches in all nine runs, whereas legacy controls retain records. All sensors still exhaust their budgets within 60 s. These tests address power accounting and ledger retirement, not sustained service or a whole-system memory bound.

5.7 Clock envelope and Cortex M3 execution

Optional freshness handling uses an externally justified pairwise clock bound. A 40 ms offset bound plus 100 ppm relative drift over 300 s gives 70 ms tolerance. All 675 tested offset/drift combinations accept authentic fresh beacons, while replay and forged-tag checks remain effective. The wider window can also admit older messages near the expiry boundary. It neither synchronizes clocks nor verifies their physical drift; the original default behavior remains unchanged.

A bare-metal C harness executes the 44,161-parameter actor, HMAC-SHA256 and Monocypher 4.0.3 Ed25519 on QEMU 11.1.2’s MPS2 AN385 Cortex-M3 model [23, 24]. Eight retained radio decisions and eight candidate-permutation controls produce 128 logits; all 16 actions match PyTorch and span eight candidate indices. The largest logit difference is 1.7881393432617188e-7, below the 1e-5 tolerance. HMAC matches RFC 4231 case 1; Ed25519 signatures match independent Python verification, and a corrupted signature is rejected. Table 9 records the execution checks.

Table 9. Isolated target checks.

The image omits radio buffers, RTOS state and integrated protocol memory; its observed stack watermark is not a worst-case bound. Public test keys are used only for validation. This isolated instruction harness and the CC2538 UART/radio bridge in Section 5.4 are distinct experiments. Neither their separate success nor the activation approximation’s agreement on these vectors validates a complete embedded routing system, physical timing or measured energy. Section 5.8 subsequently evaluates a combined radio and policy/crypto image under a narrower four-node protocol.

5.8 Live MCU routing and authentication

The four-node CC2538 pilot executes observation construction, frozen attention inference, hop authentication and receipt handling inside the MCU. The host triggers traffic and beacon exchange and captures UART output. Earlier public fixtures deliver twenty packets and verified receipts, with fifty matching routing decisions. Table 10 compares the retained private-key FP32 streams with two later implementations; each profile offers one hundred packets in a three-hop chain and one hundred in a geometry with two feasible source choices. These are sequential functional diagnostics, not independent statistical replicates or a new confirmatory comparison; N is the offered count.

Operation-level profiling identifies approximately 270 ms per-hop FP32 inference and 81 ms Ed25519 verification in the declared emulator. A separate Q22 implementation uses signed 32-bit weights and activations, 64-bit accumulators and an 8193-point tanh lookup table. Export checks bound arithmetic for input coordinates in [−32, 32]; nonfinite or out-of-domain inputs are rejected. The lookup table adds 32,772 bytes beyond the 176,644 parameter bytes. All five hundred retained decisions and the later MCU decisions match the FP32 reference at their recorded observations, with logit errors below 1e-4. This is tested approximation agreement, not universal action equivalence. Inference falls to approximately 12–13 ms with one candidate. Caching the provisioned sink signing key also removes repeated key derivation from the packet path.

Table 10. MCU receipt profiles.

The experimental fast profile adds a distinct 66-byte application frame: the fourteen-byte packet identity, a sixteen-byte source–sink HMAC, the twenty-byte hop header and its sixteen-byte hop tag. The sink emits this private receipt after verifying source data, then generates the original Ed25519 proof. Relays check the hop envelope and pending route and forward the private receipt opaquely; they assign no forwarding credit from it. Only the source authenticates the end-to-end MAC and settles its service debt early. The separate public proof remains subject to Ed25519 verification and the original MAC-ACK credit gate. A private MAC is not transferable public evidence, and its deadline endpoint is not the original signed-receipt endpoint.

Fixed-point inference reduces signed-receipt misses from 134/200 to 68/200; the 90 ms class still fails. In the fast profile, all two hundred private receipts meet their source deadlines, while all two hundred deferred Ed25519 proofs are eventually verified and sixty-eight miss the original signed deadline. Extra private receipts add three radio frames per chain packet or two per choice packet; no energy saving is inferred. Tested-path stack watermarks reach 6624 bytes, with 3968 static RAM bytes and intact guards under the 32 KiB linker budget. These are observed paths, not a worst-case stack bound.

Fresh pairwise keys and a signing seed are provisioned once over the trusted emulator UART; persisted host allocation reserves distinct boot sessions. The software rejects stale sessions, repeated provisioning, mismatched signing keys and forged fast MACs, and uses explicit wipes for temporary key material and UART buffers. Source replay state rolls across longer streams. None of this establishes protected MCU storage, authenticated physical provisioning or reboot-persistent device state. The pilot still fixes four nodes, nominal energy/queue inputs and test-triggered beacons. Physical RF/energy, overload, autonomous rendezvous and deployment behavior remain unvalidated; retrospective private hop-tag audits require the locally retained fixtures.

5.9 Cooja feedback and policy transfer

A separate Cooja evaluation [25] runs the frozen Q22 actor and weighted feedback ledger inside four native Contiki-NG motes. Thirty new simulation seeds cross five arms, benign or post-warm-up blackhole behavior, and native or scheduled processing time: 600 runs and 36,000 offered packets. The source offers sixty packets at 300 ms intervals; two feasible relays connect it to the sink. All arms share geometry, traffic, authenticated beacons, nominal energy/queue inputs and the same checkpoint. Censored-plus-proof retains the censored evidence rule while enabling the active arm’s proof-generation rule; realized traffic can still differ as routes change. This is a four-node policy-transfer experiment, not a repetition of the original network-scale benchmark.

Actual CSMA callbacks supply first-hop MAC outcomes. A radio-driver hook observes successfully received forwarding frames before destination filtering, rather than reading simulator-held forwarding histories. Passive evidence has strength 0.5 and a signed sink receipt strength 1; the Python ledger independently replays ACK gating, 150 ms expiry, maximum-strength deduplication and late upgrades. Active proofs are authenticated hop messages emitted after successful downstream MAC outcomes. Public fixture keys support trace verification, not deployment secrecy. Sixteen local pending routes expire after two seconds; closed feedback records can remain eligible for late upgrades until their slots are reused.

Native execution does not account for Cortex-M3 instruction time. The delayed setting schedules outbound data after 14 ms, other outbound messages after 1 ms, received public receipts after 81 ms, sink data processing after 31 ms and other received frames after 1 ms. These per-packet assumptions do not model serial CPU service, overload or measured compute energy. Table 11 reports means over thirty seeds; Fig. 12 shows paired delivery contrasts, with a shared horizontal scale within each attack setting. Pointwise bootstrap intervals use 20,000 seed resamples. Two-sided paired sign-flip tests use 100,000 draws, with Holm adjustment across sixteen contrasts within each endpoint family. Delivery is primary; critical sink-deadline failures and total transmit-state duration form separate secondary families. Four direct matched-proof contrasts per endpoint were added after the protocol freeze as exploratory checks, with a separate Holm family; they do not alter primary inference.

Table 11. Cooja transfer results.

Delivery counts unique sink packets; critical failure includes missing critical packets or the sink application delivery event later than 90 ms. TX is the sum of modeled transmit-state seconds over all four motes, not energy. Base uses no added instruction-cost delay; the delayed column uses the declared processing assumptions. Full per-arm intervals, proof counts and adjusted contrasts are retained with the raw traces.

With scheduled processing and a blackhole relay, active proofs change delivery relative to censored feedback by +46.17 percentage points (95% paired interval +36.89 to +54.50; Holm-adjusted p=0.00016). Enabling proofs while retaining censored evidence changes delivery by -0.11 percentage points (95% paired interval -0.50 to +0.39; Holm-adjusted p=1). These are conditional transfer results; they neither replace the original Holm family nor establish a new neural-policy advantage. Across all captures, independent reconstruction differs by at most 1.19e-07 per feature, with maximum logit discrepancy 2.21e-06.

The four-node geometry, one source, fixed nominal energy/queue/LQI telemetry, public test keys and unicast beacon roster limit generalization. The fixed-point port quantizes float timestamps to integer milliseconds; a beacon can be excluded about 1 ms earlier than its ideal acquisition timestamp. The corrected auditor reproduces that representation without changing captures or outcomes. Energest state durations do not establish current or battery consumption, and MAC ACKs are not newly cryptographically authenticated. Censoring preserves earlier positive evidence when later observations are absent; recovery from a previously cooperative relay that becomes silent therefore depends on other routing inputs or additional evidence.



Fig. 12. Paired Cooja delivery effects.

6. Discussion

6.1 Critical vulnerabilities and limitations

The original 750-run benchmark supports replacing the tested active-proof mechanism within its prespecified margins. Because eligibility and expiry rules change together with control traffic, the observed difference cannot be assigned to proof airtime alone. Comparisons with naive passive and frozen prior do not establish a unique censoring effect after correction. Retaining the earlier unsuccessful architecture comparisons prevents the feedback result from being recast as evidence for neural-policy superiority.

The frozen benchmark relies on simulator-held geometry, packet history and reverse receipt paths; beacon values are supplied through receive-gated metadata. Source-only service debts leave transit queue control untested. Its threat model also excludes forged receipts, deceptive telemetry, compromised sources, collusion and mobility. Overheard transmission confirms an attempt, while successful delivery at the next hop remains uncertain. The effective-count risk score should be read as a routing preference, not an evaluated live intrusion detector.

A four-second horizon, a central sink and a 60-packet burst are insufficient to establish steady-state scalability or network lifetime. After cache sorting, candidate scoring is linear in the bounded candidate count. Record expiry is more costly: each millisecond poll scans all W retained watches, giving O(W) work and O(W) memory. The frozen experiments provide neither a long-horizon reclamation policy nor measured embedded inference cost. Sections 5.6–5.7 add bounded-state tests and isolated instruction-level execution; physical integrated-firmware costs remain unmeasured. An always-listening radio also omits the wake-up cost that evidence collection would incur under duty cycling.

The 150 ms evidence timeout includes contention, retries and forwarding. Interference can therefore delay a valid receipt past expiry. Censoring avoids assigning failure solely from silence and allows a later receipt to upgrade the record; it does not establish an optimal timeout. The simulator also uses a shared time base. The corrected host timestamp sampling error is different from physical clock offset or drift, which remain unmeasured; Section 5.7 tests a declared virtual envelope.

The holdout fixes passive strength at 0.5, record expiry at 150 ms, cache life at 0.75 s, the current model and all inference checkpoints. Section 5.5 varies the preselection coefficients only; sensitivity to these other choices remains unknown. Changes to serialization, ACK authentication, service tracking or ledger retirement require a separately frozen experiment because they change the evaluated mechanism.

6.2 Future experiments

Section 5.6 separates proof generation from the declared evidence rule, but its periodic sleep primitive lacks rendezvous. An observation policy could choose silence, passive listening or an authenticated probe according to the expected reduction in delivery loss relative to measured radio and processing cost. A discriminating deployment experiment would integrate rendezvous, test adversarial receipts and clock uncertainty, and reserve new physical-board settings. This would evaluate evidence acquisition under execution costs not established by isolated or small-scale integrated emulation.

7. Conclusions

ACK-gated censored passive feedback improves blackhole delivery over active proofs by 4.67 percentage points in the prespecified thirty-fixture benchmark. Matched controls establish neither a unique censoring effect nor neural-policy superiority. The separate 180-run authenticated transfer study likewise shows no established attention advantage, while the 240-run factorial extension identifies a proof-traffic penalty under always-on listening. These findings apply to the declared feedback, traffic and radio models.

Behavior change exposes a different boundary. In the 600-run Cooja delayed condition, active proofs deliver 79.11%, censored feedback 32.94% and naive feedback 54.89%; censored feedback with proof generation enabled delivers 32.83%. Censoring alone cannot reduce earlier positive trust when later observations disappear. Fixed-point MCU execution and fast private receipts improve narrower execution paths, but the original 90 ms signed-receipt target remains unmet. Physical RF, measured energy, production key storage and deployment performance remain unvalidated.

Acknowledgments

No funding was received for this research. The authors declare no competing interests. This simulation and emulation study involved no human participants, clinical data or animal experiments.

Data and code availability: code, frozen protocol, checkpoints, historical negative outcomes, raw traces and figure sources are available at https://github.com/DrShivamBhardwaj/JICCE_LA_CPPO_Reproducibility. The pre-outcome source freeze is 4027f071322cb5682f39329f656d76df3b68ff62. The complete earlier evidence manuscript is retained in publication/censored_feedback/.

Declaration of generative AI use

ChatGPT assisted manuscript drafting, code preparation, analysis scripts and programmatic figure plotting. All numerical results reported here come from the retained executable experiments and traces. Responsibility for scientific verification, interpretation and final approval rests with the authors.

References

[1] T. Winter et al., “RPL: IPv6 Routing Protocol for Low-Power and Lossy Networks,” IETF, RFC 6550, 2012. DOI: 10.17487/RFC6550.

[2] D. S. J. De Couto, D. Aguayo, J. Bicket, and R. Morris, “A high-throughput path metric for multi-hop wireless routing,” in Proceedings of MobiCom, pp. 134–146, 2003. DOI: 10.1145/938985.939000.

[3] O. Gnawali, R. Fonseca, K. Jamieson, D. Moss, and P. Levis, “Collection tree protocol,” in Proceedings of SenSys, pp. 1–14, 2009. DOI: 10.1145/1644038.1644040.

[4] S. Marti, T. J. Giuli, K. Lai, and M. Baker, “Mitigating routing misbehavior in mobile ad hoc networks,” in Proceedings of MobiCom, pp. 255–265, 2000. DOI: 10.1145/345910.345955.

[5] K. Liu, J. Deng, P. K. Varshney, and K. Balakrishnan, “An acknowledgment-based approach for the detection of routing misbehavior in MANETs,” IEEE Transactions on Mobile Computing, vol. 6, no. 5, pp. 536–550, 2007. DOI: 10.1109/TMC.2007.1036.

[6] A. Saleh, P. Joshi, R. S. Rathore, and S. S. Sengar, “Trust-aware routing mechanism through an edge node for IoT-enabled sensor networks,” Sensors, vol. 22, no. 20, Art. no. 7820, 2022. DOI: 10.3390/s22207820.

[7] N. Kumar and S. Sharma, “PathGuard: Trustworthy routing for sustainable and secure IoT-WSN networks,” Wireless Personal Communications, vol. 136, pp. 469–487, 2024. DOI: 10.1007/s11277-024-11289-8.

[8] P. Goswami, T. Khan, V. Pathak, and A. Alabdultif, “Machine learning based dynamic trust estimation framework for securing wireless sensor networks,” Scientific Reports, vol. 15, Art. no. 35821, 2025. DOI: 10.1038/s41598-025-19768-z.

[9] S. Tao, H. Tang, J. Wang, and B. Li, “A failure risk-aware multi-hop routing protocol in LPWANs using deep Q-network,” Sensors, vol. 25, no. 14, Art. no. 4416, 2025. DOI: 10.3390/s25144416.

[10] A. A. Lata and M. Kang, “RLFS-OR: Reinforcement learning-based forwarder selection for opportunistic routing in wireless sensor networks,” Electronics, vol. 15, no. 5, Art. no. 910, 2026. DOI: 10.3390/electronics15050910.

[11] R. Zheng, D. Yamkhin, J. Wei, H. Liu, and Z. Khurelbaatar, “Trust-gated reinforcement learning-based secure routing for wireless sensor networks,” Journal of Computational and Cognitive Engineering, online first, 2026. DOI: 10.47852/bonviewJCCE62029141.

[12] R. Gupta, S. K. Gupta, S. B. Singh, R. Kumar, and R. Muthukkumar, “Adaptive deep reinforcement learning–based secure routing for wireless sensor networks,” Scientific Reports, 2026. DOI: 10.1038/s41598-026-62519-x.

[13] ns-3 Project, “IEEE 802.15.4 low-rate wireless personal area network model,” ns-3 Model Library, release 3.44. Available: https://www.nsnam.org/docs/release/3.44/models/ns-3-model-library.pdf. Accessed October 16, 2026.

[14] M. Zaheer et al., “Deep sets,” in Advances in Neural Information Processing Systems, vol. 30, pp. 3391–3401, 2017. Available: https://papers.nips.cc/paper/6931-deep-sets.

[15] J. Schulman, F. Wolski, P. Dhariwal, A. Radford, and O. Klimov, “Proximal policy optimization algorithms,” arXiv:1707.06347, 2017. DOI: 10.48550/arXiv.1707.06347.

[16] J. Schulman, P. Moritz, S. Levine, M. I. Jordan, and P. Abbeel, “High-dimensional continuous control using generalized advantage estimation,” in Proceedings of ICLR, 2016. Available: https://arxiv.org/abs/1506.02438.

[17] J. Achiam, D. Held, A. Tamar, and P. Abbeel, “Constrained policy optimization,” in Proceedings of ICML, vol. 70, pp. 22–31, 2017. Available: https://proceedings.mlr.press/v70/achiam17a.html.

[18] M. J. Neely, Stochastic Network Optimization with Application to Communication and Queueing Systems. Morgan and Claypool, 2010. DOI: 10.2200/S00271ED1V01Y201006CNT007.

[19] S. Holm, “A simple sequentially rejective multiple test procedure,” Scandinavian Journal of Statistics, vol. 6, no. 2, pp. 65–70, 1979. Available: https://www.jstor.org/stable/4615733.

[20] H. Krawczyk, M. Bellare, and R. Canetti, “HMAC: Keyed-hashing for message authentication,” IETF, RFC 2104, 1997. DOI: 10.17487/RFC2104.

[21] S. Josefsson and I. Liusvaara, “Edwards-curve digital signature algorithm (EdDSA),” IETF, RFC 8032, 2017. DOI: 10.17487/RFC8032.

[22] Texas Instruments, “CC2538 Powerful Wireless Microcontroller System-On-Chip,” datasheet SWRS096D, rev. D. Available: https://www.ti.com/lit/ds/symlink/cc2538.pdf. Accessed October 16, 2026.

[23] L. Vaillant et al., “Monocypher,” release 4.0.3, 2026. Available: https://monocypher.org/changelog. Accessed October 18, 2026.

[24] QEMU Project, “Arm MPS2 and MPS3 boards,” QEMU System Emulation Documentation. Available: https://www.qemu.org/docs/master/system/arm/mps2.html. Accessed October 18, 2026.

[25] F. Österlind, A. Dunkels, J. Eriksson, N. Finne, and T. Voigt, “Cross-level sensor network simulation with COOJA,” in Proceedings of the 31st IEEE Conference on Local Computer Networks, pp. 641–648, 2006. DOI: 10.1109/LCN.2006.322172.