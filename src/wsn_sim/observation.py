from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np
from .network import WSNNetwork
from .security import SecurityRiskEstimator
from .qos import QoSDebtTracker


@dataclass
class CandidateObservation:
    flat_obs: np.ndarray
    mask: np.ndarray
    base_mask: np.ndarray
    node_ids: np.ndarray
    shield_fallback: bool
    hierarchy_fallback: bool = False


class CrossLayerObservationBuilder:
    """Build a permutation-compatible local routing observation.

    The legacy mode uses PHY/MAC/network/security candidate state plus packet
    context and per-class QoS debt. Stage-4G1.5 adds an *opt-in* cluster-aware
    mode that makes the slow clustering layer causally visible to forwarding.
    In that mode each candidate also carries cluster-role/affinity features and
    a soft hierarchical feasibility mask is applied. The mask prefers
    member->assigned-CH/same-cluster progress and CH->CH/sink forwarding, but
    falls back to the physical loop-free neighborhood if the hierarchy exposes
    no usable action. This keeps the coupling explicit without manufacturing a
    dead end solely because a metaheuristic cluster is temporarily awkward.
    """

    BASE_CANDIDATE_DIM = 10
    CLUSTER_FEATURE_DIM = 4
    CANDIDATE_DIM = BASE_CANDIDATE_DIM

    def __init__(self, cfg: dict):
        rcfg = cfg.get("rl", {})
        self.k = int(rcfg.get("top_k_neighbors", 8))
        self.shield_enabled = bool(rcfg.get("shield_enabled", True))
        self.risk_limit = float(rcfg.get("shield_risk_ucb_max", 0.85))
        self.min_progress_m = float(rcfg.get("min_progress_m", 0.25))
        self.pdr_margin = float(rcfg.get("shield_pdr_margin", 0.08))
        self.deadline_margin = float(rcfg.get("shield_deadline_margin", 1.15))
        self.max_hops = int(cfg["simulation"]["max_hops"])
        self.area_diag = float(np.linalg.norm(np.asarray(cfg["network"]["area_m"], dtype=float)))
        self.deadlines = np.asarray(cfg["traffic"]["deadlines_ms"], dtype=float) / 1000.0
        self.pdr_targets = np.asarray(cfg["traffic"]["pdr_targets"], dtype=float)
        self.n_classes = len(self.deadlines)

        self.cluster_aware = bool(rcfg.get("cluster_aware_routing", False))
        self.cluster_hierarchy_mask = bool(rcfg.get("cluster_hierarchy_mask", True))
        self.assigned_ch_bonus = float(rcfg.get("cluster_assigned_ch_bonus", 1.10))
        self.ch_bonus = float(rcfg.get("cluster_ch_bonus", 0.45))
        self.same_cluster_bonus = float(rcfg.get("cluster_same_cluster_bonus", 0.20))
        self.hierarchy_progress_bonus = float(rcfg.get("cluster_hierarchy_progress_bonus", 0.35))
        self.nonbackbone_penalty = float(rcfg.get("cluster_nonbackbone_penalty", 0.20))

        self.CANDIDATE_DIM = self.BASE_CANDIDATE_DIM + (self.CLUSTER_FEATURE_DIM if self.cluster_aware else 0)
        legacy_context = 4 + self.n_classes + 2 * self.n_classes
        self.cluster_context_dim = 4 if self.cluster_aware else 0
        self.context_dim = legacy_context + self.cluster_context_dim
        self.obs_dim = self.context_dim + self.k * self.CANDIDATE_DIM

    @staticmethod
    def _valid_assignment(assignment: np.ndarray | None, node: int) -> int:
        if assignment is None or node < 0 or node >= len(assignment):
            return -1
        return int(assignment[node])

    @staticmethod
    def _active_topology(
        net: WSNNetwork,
        chs: list[int] | None,
        assignment: np.ndarray | None,
    ) -> tuple[list[int], np.ndarray | None]:
        if chs is None:
            chs = list(getattr(net, "active_chs", []))
        if assignment is None:
            assignment = getattr(net, "active_assignment", None)
        return list(map(int, chs or [])), assignment

    def _topology_features(
        self,
        net: WSNNetwork,
        current: int,
        target: int,
        chs: list[int] | None,
        assignment: np.ndarray | None,
    ) -> tuple[np.ndarray, dict]:
        chs, assignment = self._active_topology(net, chs, assignment)
        ch_set = set(chs)
        assigned = self._valid_assignment(assignment, current)
        current_is_ch = current in ch_set
        is_sink = target < 0
        candidate_is_ch = (not is_sink) and target in ch_set
        target_assignment = self._valid_assignment(assignment, target)
        same_cluster = (not is_sink) and assigned >= 0 and target_assignment == assigned
        is_assigned_ch = (not is_sink) and assigned >= 0 and target == assigned

        if is_sink:
            hierarchy_progress = 1.0
        elif current_is_ch:
            hierarchy_progress = (net.distance(current, None) - net.distance(target, None)) / max(net.radio_range, 1e-6)
        elif assigned >= 0 and assigned < net.n:
            hierarchy_progress = (net.distance(current, assigned) - net.distance(target, assigned)) / max(net.radio_range, 1e-6)
        else:
            hierarchy_progress = 0.0
        hierarchy_progress = float(np.clip(hierarchy_progress, -1.0, 1.0))

        features = np.array([
            float(candidate_is_ch),
            float(same_cluster),
            float(is_assigned_ch),
            hierarchy_progress,
        ], dtype=np.float32)
        meta = {
            "current_is_ch": bool(current_is_ch),
            "candidate_is_ch": bool(candidate_is_ch),
            "same_cluster": bool(same_cluster),
            "is_assigned_ch": bool(is_assigned_ch),
            "hierarchy_progress": hierarchy_progress,
        }
        return features, meta

    def _cluster_context(
        self,
        net: WSNNetwork,
        current: int,
        chs: list[int] | None,
        assignment: np.ndarray | None,
    ) -> np.ndarray:
        if not self.cluster_aware:
            return np.zeros(0, dtype=np.float32)
        chs, assignment = self._active_topology(net, chs, assignment)
        ch_set = set(chs)
        assigned = self._valid_assignment(assignment, current)
        current_is_ch = float(current in ch_set)
        if assigned >= 0 and assigned < net.n and net.alive[assigned]:
            d = net.distance(current, assigned)
            assigned_reachable = float(d <= net.radio_range)
            assigned_distance = float(np.clip(d / max(net.radio_range, 1e-6), 0.0, 2.0) / 2.0)
            cluster_size = float(np.mean((np.asarray(assignment) == assigned) & net.alive)) if assignment is not None else 0.0
        else:
            assigned_reachable = 0.0
            assigned_distance = 1.0
            cluster_size = 0.0
        return np.array([current_is_ch, assigned_reachable, assigned_distance, cluster_size], dtype=np.float32)

    def _candidate_row(
        self,
        net: WSNNetwork,
        sec: SecurityRiskEstimator,
        current: int,
        target: int,
        elapsed_s: float,
        traffic_class: int,
        chs: list[int] | None = None,
        assignment: np.ndarray | None = None,
    ):
        is_sink = target < 0
        d = net.distance(current, None if is_sink else target)
        interf = float(net.interference[current]) if is_sink else 0.5 * float(net.interference[current] + net.interference[target])
        pdr = net.radio.pdr(d, interf, shadowing_db=0.0)
        rssi = net.radio.rssi_dbm(d, 0.0, interf)
        delay = net.radio.expected_hop_delay_s(net.queue[current], pdr, max_retries=int(net.cfg.get("mac", {}).get("max_retries", 3)))
        cur_dist = net.distance(current, None)
        next_dist = 0.0 if is_sink else net.distance(target, None)
        progress = cur_dist - next_dist
        energy = 1.0 if is_sink else float(np.clip(net.energy[target] / net.e0, 0.0, 1.0))
        queue = 0.0 if is_sink else float(net.queue[target])
        risk = 0.0 if is_sink else float(sec.risk[target])
        risk_ucb = 0.0 if is_sink else float(sec.risk_ucb[target])
        expected_retries = min((1.0 / max(pdr, 1e-3)) - 1.0, 4.0) / 4.0
        rssi_norm = float(np.clip((rssi + 110.0) / 60.0, 0.0, 1.0))
        progress_norm = float(np.clip(progress / max(net.radio_range, 1e-6), -1.0, 1.0))
        delay_norm = float(np.clip(delay / max(self.deadlines[traffic_class], 1e-6), 0.0, 2.0) / 2.0)
        base = np.array([1.0 if is_sink else 0.0, energy, pdr, rssi_norm, queue, progress_norm, risk, risk_ucb, expected_retries, delay_norm], dtype=np.float32)
        topology_features, topology_meta = self._topology_features(net, current, target, chs, assignment)
        row = np.concatenate([base, topology_features]) if self.cluster_aware else base
        return row.astype(np.float32), pdr, delay, progress, topology_meta

    def build(
        self,
        net: WSNNetwork,
        sec: SecurityRiskEstimator,
        qos: QoSDebtTracker,
        current: int,
        traffic_class: int,
        elapsed_s: float,
        visited: set[int] | None = None,
        chs: list[int] | None = None,
        assignment: np.ndarray | None = None,
    ) -> CandidateObservation:
        visited = visited or set()
        current_dist = net.distance(current, None)
        candidates = [j for j in net.feasible_neighbors(current) if j not in visited]
        if current_dist <= net.radio_range:
            candidates.append(-1)

        scored = []
        for j in candidates:
            row, pdr, delay, progress, topology = self._candidate_row(
                net, sec, current, j, elapsed_s, traffic_class, chs=chs, assignment=assignment
            )
            score = 1.25 * progress / max(net.radio_range, 1e-6) + 0.75 * pdr + 0.25 * row[1] - 0.55 * row[7] - 0.20 * row[4]
            if self.cluster_aware:
                score += self.assigned_ch_bonus * float(topology["is_assigned_ch"])
                score += self.ch_bonus * float(topology["candidate_is_ch"])
                score += self.same_cluster_bonus * float(topology["same_cluster"])
                score += self.hierarchy_progress_bonus * max(float(topology["hierarchy_progress"]), 0.0)
                if topology["current_is_ch"] and j >= 0 and not topology["candidate_is_ch"]:
                    score -= self.nonbackbone_penalty
            scored.append((score, j, row, pdr, delay, progress, topology))
        scored.sort(key=lambda x: x[0], reverse=True)
        selected = scored[: self.k]

        rows = np.zeros((self.k, self.CANDIDATE_DIM), dtype=np.float32)
        node_ids = np.full(self.k, -2, dtype=int)
        physical_mask = np.zeros(self.k, dtype=bool)
        topology_mask = np.zeros(self.k, dtype=bool)
        shield_feasible = np.zeros(self.k, dtype=bool)
        remaining_slack = max(self.deadlines[traffic_class] - elapsed_s, 0.0)

        for slot, (_, j, row, pdr, delay, progress, topology) in enumerate(selected):
            rows[slot] = row
            node_ids[slot] = j
            physical_mask[slot] = True
            if not self.cluster_aware:
                topology_mask[slot] = True
            elif j < 0:
                topology_mask[slot] = True
            elif topology["current_is_ch"]:
                topology_mask[slot] = bool(topology["candidate_is_ch"] and topology["hierarchy_progress"] > -0.05)
            else:
                topology_mask[slot] = bool(
                    topology["is_assigned_ch"]
                    or (topology["same_cluster"] and topology["hierarchy_progress"] > 0.0)
                    or (topology["candidate_is_ch"] and progress > 0.0)
                )

            next_dist = 0.0 if j < 0 else net.distance(j, None)
            est_hops_after = max(1, int(math.ceil(next_dist / max(0.75 * net.radio_range, 1e-6))))
            per_hop_target = self.pdr_targets[traffic_class] ** (1.0 / max(est_hops_after + 1, 1))
            pdr_ok = pdr >= max(0.55, per_hop_target - self.pdr_margin)
            delay_ok = delay * (est_hops_after + 1) * self.deadline_margin <= max(remaining_slack, delay)
            risk_ok = (j < 0) or (sec.risk_ucb[j] <= self.risk_limit)
            progress_ok = (j < 0) or progress >= self.min_progress_m
            shield_feasible[slot] = pdr_ok and delay_ok and risk_ok and progress_ok

        hierarchy_fallback = False
        if self.cluster_aware and self.cluster_hierarchy_mask:
            if (physical_mask & topology_mask).any():
                base_mask = physical_mask & topology_mask
            else:
                base_mask = physical_mask.copy()
                hierarchy_fallback = bool(physical_mask.any())
        else:
            base_mask = physical_mask.copy()

        shield_mask = base_mask & shield_feasible
        fallback = False
        if not self.shield_enabled:
            shield_mask = base_mask.copy()
        elif not shield_mask.any() and base_mask.any():
            shield_mask = base_mask.copy()
            fallback = True

        class_onehot = np.zeros(self.n_classes, dtype=np.float32)
        class_onehot[traffic_class] = 1.0
        ctx_parts = [
            np.array([
                float(np.clip(net.energy[current] / net.e0, 0.0, 1.0)),
                float(net.queue[current]),
                float(np.clip(current_dist / max(self.area_diag, 1e-6), 0.0, 1.0)),
                float(np.clip(remaining_slack / max(self.deadlines[traffic_class], 1e-6), 0.0, 1.0)),
            ], dtype=np.float32),
            class_onehot,
            qos.normalized_vector.astype(np.float32),
        ]
        if self.cluster_aware:
            ctx_parts.append(self._cluster_context(net, current, chs, assignment))
        ctx = np.concatenate(ctx_parts)
        flat = np.concatenate([ctx, rows.reshape(-1)]).astype(np.float32)
        return CandidateObservation(flat, shield_mask, base_mask, node_ids, fallback, hierarchy_fallback)

