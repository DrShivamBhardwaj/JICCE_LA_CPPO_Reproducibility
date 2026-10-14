from __future__ import annotations
import copy
from dataclasses import dataclass
import numpy as np
from .network import WSNNetwork
from .security import SecurityRiskEstimator
from .qos import QoSDebtTracker
from .clustering import select_cluster_heads
from .trigger import ReclusterTrigger
from .observation import CrossLayerObservationBuilder, CandidateObservation


@dataclass
class StepResult:
    observation: CandidateObservation | None
    reward: float
    costs: np.ndarray
    done: bool
    info: dict


class PacketRoutingEnv:
    """Persistent packet-routing environment for cross-layer policy training.

    ``clustering.enabled`` defaults to ``True`` for legacy configurations.  AF-v3
    freezes it to ``False``: in that mode no ROA/clustering call is made and no
    packet/link RNG state is consumed by topology optimization, while the normal
    queue/interference and online security dynamics continue.
    """

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.clustering_enabled = bool(cfg.get("clustering", {}).get("enabled", True))
        self.net = WSNNetwork(cfg)
        tcfg = cfg["traffic"]
        self.qos = QoSDebtTracker(tcfg["deadlines_ms"], tcfg["pdr_targets"], tcfg.get("delay_violation_budgets"))
        self.sec = SecurityRiskEstimator(self.net.n, enabled=bool(cfg.get("validation", {}).get("risk_enabled", True)))
        self.trigger = ReclusterTrigger(cfg["trigger"])
        self.builder = CrossLayerObservationBuilder(cfg)
        self.chs: list[int] = []
        self.assignment = np.full(self.net.n, -1, dtype=int)
        self.recluster_count = 0
        self.qos_conditioned_recluster_count = 0
        self.qos_gate_recluster_opportunities = 0
        self.packet_index = 0
        self.current = -1
        self.source = -1
        self.traffic_class = 0
        self.elapsed_s = 0.0
        self.hops = 0
        self.visited: set[int] = set()
        self.last_obs: CandidateObservation | None = None
        self.last_trigger_reason = "initial"
        self.last_cluster_info: dict = {}

        # Stage-4G1 counterfactual instrumentation. These controls deliberately
        # do not alter legacy behavior unless capture is explicitly enabled.
        cfcfg = cfg.get("counterfactual_capture", {})
        self.counterfactual_capture_enabled = bool(cfcfg.get("enabled", False))
        self._pending_counterfactual_snapshot: PacketRoutingEnv | None = None
        self._pending_counterfactual_state: dict | None = None
        self.counterfactual_event_count = 0
        self._previous_slow_max_qos_debt = 0.0
        self.last_recluster_packet_index = 0
        self.last_recluster_churn = 0.0
        self.shield_fallback_ewma = 0.0
        self.slow_dynamics_enabled = True
        self.adaptive_reclustering_enabled = self.clustering_enabled

        if self.clustering_enabled:
            self._recluster(initial=True)
        else:
            self.last_cluster_info = {"clustering_enabled": False}

    @property
    def n_costs(self) -> int:
        return 2 * self.qos.n_classes

    def _qos_clustering_context(self) -> dict:
        probs = np.asarray(self.cfg["traffic"]["class_probs"], dtype=float)
        probs = probs / max(float(probs.sum()), 1e-12)
        return {
            "delay_debt": self.qos.normalized_delay_debt.copy(),
            "loss_debt": self.qos.normalized_loss_debt.copy(),
            "max_qos_debt": float(self.qos.max_normalized_debt),
            "deadlines_s": self.qos.deadlines_s.copy(),
            "pdr_targets": self.qos.pdr_targets.copy(),
            "class_probs": probs,
        }

    @staticmethod
    def _churn(old: list[int], new: list[int]) -> float:
        if not old and not new:
            return 0.0
        if not old:
            return 1.0
        a, b = set(map(int, old)), set(map(int, new))
        return float(1.0 - len(a & b) / max(len(a | b), 1))

    def _recluster(self, initial: bool = False) -> None:
        if not self.clustering_enabled:
            self.chs = []
            self.assignment = np.full(self.net.n, -1, dtype=int)
            self.last_cluster_info = {"clustering_enabled": False}
            self.last_recluster_churn = 0.0
            self.last_recluster_packet_index = int(self.packet_index)
            return
        old = [] if initial else list(self.chs)
        risk = self.sec.risk_ucb
        qos_context = self._qos_clustering_context()
        qcfg = self.cfg["clustering"].get("qos_conditioning", {})
        if not initial and bool(qcfg.get("enabled", False)) and bool(qcfg.get("gate_enabled", False)):
            self.qos_gate_recluster_opportunities += 1
        self.chs, self.assignment, self.last_cluster_info = select_cluster_heads(
            self.net,
            risk,
            old,
            self.cfg["clustering"],
            qos_context=qos_context,
        )
        if not initial and bool(self.last_cluster_info.get("qos_gate_active", False)):
            self.qos_conditioned_recluster_count += 1
        self.last_recluster_churn = 0.0 if initial else self._churn(old, self.chs)
        self.last_recluster_packet_index = int(self.packet_index)
        self.recluster_count += 1

    def _slow_state_features(self, trigger_score: float) -> dict:
        """Compact state available *before* a triggered topology intervention.

        Only causal, online quantities are included. No future or retrospective
        episode summary enters this vector.
        """
        alive = self.net.alive
        alive_idx = np.flatnonzero(alive)
        if len(alive_idx):
            queue = self.net.queue[alive_idx]
            interference = self.net.interference[alive_idx]
            energy_frac = np.clip(self.net.energy[alive_idx] / max(self.net.e0, 1e-12), 0.0, 1.0)
            risk = self.sec.risk_ucb[alive_idx]
        else:
            queue = interference = energy_frac = risk = np.zeros(1, dtype=float)
        max_debt = float(self.qos.max_normalized_debt)
        state = {
            "packet_index": int(self.packet_index),
            "trigger_score": float(trigger_score),
            "max_qos_debt": max_debt,
            "qos_debt_slope": float(max_debt - self._previous_slow_max_qos_debt),
            "queue_mean": float(np.mean(queue)),
            "queue_max": float(np.max(queue)),
            "queue_p90": float(np.percentile(queue, 90)),
            "interference_mean": float(np.mean(interference)),
            "interference_max": float(np.max(interference)),
            "residual_energy_mean": float(np.mean(energy_frac)),
            "residual_energy_min": float(np.min(energy_frac)),
            "security_risk_mean": float(np.mean(risk)),
            "security_risk_max": float(np.max(risk)),
            "security_risk_p90": float(np.percentile(risk, 90)),
            "alive_fraction": float(np.mean(alive.astype(float))),
            "mean_member_link_pdr": float(self.net.mean_member_link_pdr(self.chs, self.assignment)) if self.chs else 1.0,
            "ch_count": int(len(self.chs)),
            "last_recluster_churn": float(self.last_recluster_churn),
            "packets_since_last_recluster": int(max(self.packet_index - self.last_recluster_packet_index, 0)),
            "shield_fallback_ewma": float(self.shield_fallback_ewma),
            "last_cluster_fitness": float(self.last_cluster_info.get("fitness", np.nan)),
            "last_qos_topology_penalty": float(self.last_cluster_info.get("qos_topology_penalty", 0.0)),
        }
        for c in range(self.qos.n_classes):
            state[f"class_{c}_delay_debt"] = float(self.qos.normalized_delay_debt[c])
            state[f"class_{c}_loss_debt"] = float(self.qos.normalized_loss_debt[c])
        return state

    def fork_for_counterfactual(self) -> "PacketRoutingEnv":
        """Deep-copy the live simulator without recursively copying a pending fork."""
        pending_snapshot = self._pending_counterfactual_snapshot
        pending_state = self._pending_counterfactual_state
        self._pending_counterfactual_snapshot = None
        self._pending_counterfactual_state = None
        try:
            clone = copy.deepcopy(self)
        finally:
            self._pending_counterfactual_snapshot = pending_snapshot
            self._pending_counterfactual_state = pending_state
        clone._pending_counterfactual_snapshot = None
        clone._pending_counterfactual_state = None
        clone.counterfactual_capture_enabled = False
        return clone

    def consume_counterfactual_event(self) -> dict | None:
        """Return and clear the latest pre-intervention snapshot, if one exists."""
        if self._pending_counterfactual_snapshot is None or self._pending_counterfactual_state is None:
            return None
        out = {
            "event_id": int(self._pending_counterfactual_state["event_id"]),
            "state": dict(self._pending_counterfactual_state),
            "snapshot": self._pending_counterfactual_snapshot,
        }
        self._pending_counterfactual_snapshot = None
        self._pending_counterfactual_state = None
        return out

    def apply_counterfactual_recluster(self, conditioned: bool, roa_seed: int) -> dict:
        """Apply exactly one branch-specific re-clustering action.

        This legacy research hook is unavailable when clustering is structurally
        disabled, as in AF-v3.
        """
        if not self.clustering_enabled:
            raise RuntimeError("counterfactual re-clustering is disabled when clustering.enabled=false")
        clustering_cfg = copy.deepcopy(self.cfg["clustering"])
        qcfg = clustering_cfg.setdefault("qos_conditioning", {})
        qcfg["enabled"] = bool(conditioned)
        qcfg["gate_enabled"] = False
        old = list(self.chs)
        risk = self.sec.risk_ucb
        qos_context = self._qos_clustering_context()

        original_net_rng = self.net.rng
        original_radio_rng = self.net.radio.rng
        local_rng = np.random.default_rng(int(roa_seed))
        self.net.rng = local_rng
        self.net.radio.rng = local_rng
        try:
            chs, assignment, info = select_cluster_heads(
                self.net,
                risk,
                old,
                clustering_cfg,
                qos_context=qos_context,
            )
        finally:
            self.net.rng = original_net_rng
            self.net.radio.rng = original_radio_rng

        self.chs = chs
        self.assignment = assignment
        self.last_cluster_info = info
        self.last_recluster_churn = self._churn(old, chs)
        self.last_recluster_packet_index = int(self.packet_index)
        self.recluster_count += 1
        return {
            "conditioned": bool(conditioned),
            "roa_seed": int(roa_seed),
            "churn": float(self.last_recluster_churn),
            "ch_count": int(len(chs)),
            "fitness": float(info.get("fitness", np.nan)),
            "qos_topology_penalty": float(info.get("qos_topology_penalty", 0.0)),
            "chs": [int(x) for x in chs],
            "assignment": self.assignment.copy(),
        }

    def _update_slow_state(self) -> None:
        if not self.slow_dynamics_enabled:
            return
        self.net.update_dynamic_state()
        for i in range(self.net.n):
            excess = max(self.net.queue[i] - 0.4, 0.0) / 0.6
            self.sec.observe_rate(i, excess)
        debt = self.qos.max_normalized_debt
        if not self.clustering_enabled:
            self.last_trigger_reason = "clustering_disabled"
            self._previous_slow_max_qos_debt = float(debt)
            return
        score, _ = self.trigger.score(self.net, self.chs, self.assignment, self.sec.risk_ucb, debt)
        triggered = self.trigger.update(self.packet_index, score, debt)
        if triggered and self.adaptive_reclustering_enabled:
            self.last_trigger_reason = self.trigger.last_reason
            if self.counterfactual_capture_enabled:
                self.counterfactual_event_count += 1
                event_state = self._slow_state_features(score)
                event_state["event_id"] = int(self.counterfactual_event_count)
                event_state["trigger_reason"] = str(self.trigger.last_reason)
                self._pending_counterfactual_snapshot = self.fork_for_counterfactual()
                self._pending_counterfactual_state = event_state
            self._recluster(initial=False)
        self._previous_slow_max_qos_debt = float(debt)

    def reset_packet(self, source: int | None = None, traffic_class: int | None = None) -> CandidateObservation:
        every = int(self.cfg.get("rl", {}).get("dynamic_update_every_packets", 8))
        if self.slow_dynamics_enabled and self.packet_index > 0 and self.packet_index % max(every, 1) == 0:
            self._update_slow_state()
        alive = np.flatnonzero(self.net.alive)
        if len(alive) == 0:
            raise RuntimeError("network has no alive nodes")
        self.source = int(self.net.traffic_rng.choice(alive)) if source is None else int(source)
        probs = np.asarray(self.cfg["traffic"]["class_probs"], dtype=float)
        probs /= probs.sum()
        self.traffic_class = int(self.net.traffic_rng.choice(len(probs), p=probs)) if traffic_class is None else int(traffic_class)
        self.current = self.source
        self.elapsed_s = 0.0
        self.hops = 0
        self.visited = {self.source}
        self.last_obs = self.builder.build(self.net, self.sec, self.qos, self.current, self.traffic_class, self.elapsed_s, self.visited)
        self.packet_index += 1
        return self.last_obs

    def _terminal_costs(self, delivered: bool, delay_s: float | None) -> np.ndarray:
        deadline_bad, loss = self.qos.update(self.traffic_class, delivered, delay_s)
        costs = np.zeros(self.n_costs, dtype=np.float32)
        costs[2 * self.traffic_class] = deadline_bad
        costs[2 * self.traffic_class + 1] = loss
        return costs

    def _malicious_drop(self, node: int) -> bool:
        if node == self.source or not self.net.malicious[node]:
            return False
        kind = self.net.attack_kind[node]
        if kind == "blackhole":
            return True
        if kind == "selective":
            return self.net.attack_rng.uniform() < float(self.cfg["attack"]["selective_drop_prob"])
        return False

    def step(self, action_slot: int) -> StepResult:
        if self.last_obs is None:
            raise RuntimeError("call reset_packet before step")
        self.shield_fallback_ewma = 0.95 * self.shield_fallback_ewma + 0.05 * float(self.last_obs.shield_fallback)
        slot = int(action_slot)
        valid = 0 <= slot < len(self.last_obs.mask) and bool(self.last_obs.mask[slot])
        if not valid:
            costs = self._terminal_costs(False, None)
            return StepResult(None, -3.0, costs, True, {"delivered": False, "reason": "invalid_action", "traffic_class": self.traffic_class})
        target = int(self.last_obs.node_ids[slot])
        if target == -2:
            costs = self._terminal_costs(False, None)
            return StepResult(None, -3.0, costs, True, {"delivered": False, "reason": "empty_slot", "traffic_class": self.traffic_class})

        is_sink = target < 0
        d = self.net.distance(self.current, None if is_sink else target)
        if d > self.net.radio_range:
            costs = self._terminal_costs(False, None)
            return StepResult(None, -3.0, costs, True, {"delivered": False, "reason": "out_of_range", "traffic_class": self.traffic_class})

        interference = float(self.net.interference[self.current]) if is_sink else 0.5 * float(self.net.interference[self.current] + self.net.interference[target])
        p = self.net.radio.pdr(d, interference)
        max_retries = int(self.cfg.get("mac", {}).get("max_retries", 3))
        success = False
        attempts = 0
        malicious = self._malicious_drop(self.current)
        hop_delay = 0.0
        for _ in range(max_retries + 1):
            attempts += 1
            txe = self.net.radio.tx_energy(d)
            self.net.energy[self.current] = max(0.0, self.net.energy[self.current] - txe)
            if not is_sink and self.net.alive[target]:
                self.net.energy[target] = max(0.0, self.net.energy[target] - self.net.radio.rx_energy())
            hop_delay += self.net.radio.hop_delay_s(self.net.queue[self.current], retransmissions=0)
            if self.net.link_rng.uniform() < p and not malicious:
                success = True
                break
        feedback_p = float(self.cfg.get("validation", {}).get("feedback_probability", 1.0))
        if feedback_p >= 1.0 or self.net.feedback_rng.uniform() < feedback_p:
            self.sec.observe_forward(self.current, success, p)
        self.elapsed_s += hop_delay
        self.hops += 1

        cur_dist = self.net.distance(self.current, None)
        next_dist = 0.0 if is_sink else self.net.distance(target, None)
        progress = (cur_dist - next_dist) / max(self.net.radio_range, 1e-6)
        energy_cost = attempts * self.net.radio.tx_energy(d) / max(self.net.e0, 1e-9)
        reward = 0.9 * float(np.clip(progress, -1.0, 1.0)) - 0.20 * float(self.net.queue[self.current]) - 0.35 * energy_cost
        if not is_sink:
            reward -= 0.45 * float(self.sec.risk_ucb[target])
        reward -= 0.04 * max(attempts - 1, 0)

        if not success:
            costs = self._terminal_costs(False, None)
            reward -= 2.0
            reason = "security_drop" if malicious else "link_drop"
            return StepResult(None, reward, costs, True, {"delivered": False, "reason": reason, "traffic_class": self.traffic_class, "delay_s": self.elapsed_s, "hops": self.hops, "attempts": attempts, "shield_fallback": self.last_obs.shield_fallback})

        if is_sink:
            costs = self._terminal_costs(True, self.elapsed_s)
            reward += 2.5
            if costs[2 * self.traffic_class] > 0:
                reward -= 0.8
            return StepResult(None, reward, costs, True, {"delivered": True, "reason": "sink", "traffic_class": self.traffic_class, "delay_s": self.elapsed_s, "hops": self.hops, "attempts": attempts, "shield_fallback": self.last_obs.shield_fallback})

        self.current = target
        if target in self.visited or self.hops >= int(self.cfg["simulation"]["max_hops"]):
            costs = self._terminal_costs(False, None)
            reward -= 2.0
            return StepResult(None, reward, costs, True, {"delivered": False, "reason": "loop_or_hop_limit", "traffic_class": self.traffic_class, "delay_s": self.elapsed_s, "hops": self.hops, "attempts": attempts, "shield_fallback": self.last_obs.shield_fallback})
        self.visited.add(target)
        obs = self.builder.build(self.net, self.sec, self.qos, self.current, self.traffic_class, self.elapsed_s, self.visited)
        if not obs.base_mask.any():
            costs = self._terminal_costs(False, None)
            reward -= 2.0
            self.last_obs = None
            return StepResult(None, reward, costs, True, {"delivered": False, "reason": "dead_end", "traffic_class": self.traffic_class, "delay_s": self.elapsed_s, "hops": self.hops, "attempts": attempts, "shield_fallback": obs.shield_fallback})
        self.last_obs = obs
        return StepResult(obs, reward, np.zeros(self.n_costs, dtype=np.float32), False, {"delivered": False, "reason": "continue", "traffic_class": self.traffic_class, "delay_s": self.elapsed_s, "hops": self.hops, "attempts": attempts, "shield_fallback": obs.shield_fallback})
