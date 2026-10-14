from __future__ import annotations
import math
import numpy as np
import networkx as nx
from .network import WSNNetwork


def decode_heads(position: np.ndarray, alive: np.ndarray, k: int) -> list[int]:
    idx = np.flatnonzero(alive)
    if len(idx) == 0:
        return []
    k = min(k, len(idx))
    order = idx[np.argsort(position[idx])[-k:]]
    return [int(x) for x in order]


def assign_clusters(net: WSNNetwork, chs: list[int]) -> np.ndarray:
    a = np.full(net.n, -1, dtype=int)
    if not chs:
        return a
    chpos = net.positions[chs]
    for i in np.flatnonzero(net.alive):
        if i in chs:
            a[i] = i
            continue
        d = np.linalg.norm(chpos - net.positions[i], axis=1)
        j = int(np.argmin(d))
        a[i] = int(chs[j])
    return a


def _link_qos(net: WSNNetwork, i: int, j: int | None, max_retries: int) -> tuple[float, float]:
    """Deterministic retry-aware success and service-delay surrogate."""
    d = net.distance(i, j)
    if d > net.radio_range:
        return 0.0, float("inf")
    if j is None:
        interference = float(net.interference[i])
    else:
        interference = 0.5 * float(net.interference[i] + net.interference[j])
    p = net.radio.pdr(d, interference, shadowing_db=0.0)
    hop_success = 1.0 - (1.0 - p) ** (max_retries + 1)
    delay = net.radio.expected_hop_delay_s(float(net.queue[i]), p, max_retries=max_retries)
    return float(np.clip(hop_success, 0.0, 1.0)), float(delay)


def qos_gate_state(qos_context: dict | None, qos_cfg: dict) -> tuple[bool, float, float]:
    """Return whether QoS topology conditioning is permitted by the online gate.

    Legacy Stage-4C behavior is preserved when gate_enabled is absent/false.
    Stage-4F uses only the *current* max normalized QoS debt available at a
    re-clustering instant; no retrospective peak or future information enters
    the controller.
    """
    if not bool(qos_cfg.get("enabled", False)):
        return False, 0.0, float(qos_cfg.get("gate_threshold", 0.90))
    threshold = float(qos_cfg.get("gate_threshold", 0.90))
    if not bool(qos_cfg.get("gate_enabled", False)):
        return True, float(qos_context.get("max_qos_debt", 0.0)) if qos_context else 0.0, threshold
    if not qos_context:
        return False, 0.0, threshold
    signal = float(qos_context.get("max_qos_debt", 0.0))
    return bool(signal >= threshold), signal, threshold


def qos_topology_penalty(
    net: WSNNetwork,
    chs: list[int],
    assignment: np.ndarray,
    risk: np.ndarray,
    qos_context: dict | None,
    qos_cfg: dict,
) -> float:
    """Debt-conditioned, class-aware topology penalty.

    The term is inactive when virtual QoS debt is zero. When debt accumulates,
    candidate cluster-head sets are scored by a retry-aware end-to-end latency
    and reliability surrogate. Stage-4F may additionally gate this term using
    the current maximum normalized debt at the re-clustering instant.
    """
    gate_active, _, _ = qos_gate_state(qos_context, qos_cfg)
    if not qos_context or not gate_active or not chs:
        return 0.0

    delay_debt = np.asarray(qos_context.get("delay_debt", []), dtype=float)
    loss_debt = np.asarray(qos_context.get("loss_debt", []), dtype=float)
    deadlines = np.asarray(qos_context.get("deadlines_s", []), dtype=float)
    pdr_targets = np.asarray(qos_context.get("pdr_targets", []), dtype=float)
    if not (len(delay_debt) and len(delay_debt) == len(loss_debt) == len(deadlines) == len(pdr_targets)):
        return 0.0

    class_debt = np.clip(
        float(qos_cfg.get("delay_debt_weight", 0.60)) * delay_debt
        + float(qos_cfg.get("loss_debt_weight", 0.40)) * loss_debt,
        0.0,
        1.0,
    )
    overall_pressure = float(np.max(class_debt))
    if overall_pressure <= 1e-12:
        return 0.0

    min_deadline = max(float(np.min(deadlines)), 1e-6)
    priority_power = float(qos_cfg.get("priority_power", 0.75))
    criticality_gain = float(qos_cfg.get("criticality_gain", 1.5))
    criticality = np.power(min_deadline / np.maximum(deadlines, min_deadline), priority_power)
    class_weights = class_debt * (1.0 + criticality_gain * criticality)
    if float(class_weights.sum()) <= 1e-12:
        return 0.0
    class_weights /= class_weights.sum()

    max_retries = int(net.cfg.get("mac", {}).get("max_retries", 3))
    bg = net.backbone_graph(chs, risk)
    sink = net.n
    backbone: dict[int, tuple[float, float]] = {}
    for ch in chs:
        if ch not in bg or not nx.has_path(bg, ch, sink):
            backbone[ch] = (0.0, float("inf"))
            continue
        path = nx.shortest_path(bg, ch, sink, weight="weight")
        p_path = 1.0
        d_path = 0.0
        feasible = True
        for u, v in zip(path[:-1], path[1:]):
            j = None if v == sink else int(v)
            p_hop, d_hop = _link_qos(net, int(u), j, max_retries)
            if not np.isfinite(d_hop):
                feasible = False
                break
            p_path *= p_hop
            d_path += d_hop
        backbone[ch] = (float(p_path) if feasible else 0.0, float(d_path) if feasible else float("inf"))

    path_pdr = []
    path_delay = []
    for i in np.flatnonzero(net.alive):
        ch = int(assignment[i])
        if ch < 0 or ch not in backbone:
            path_pdr.append(0.0)
            path_delay.append(float("inf"))
            continue
        if int(i) == ch:
            p_access, d_access = 1.0, 0.0
        else:
            p_access, d_access = _link_qos(net, int(i), ch, max_retries)
        p_back, d_back = backbone[ch]
        path_pdr.append(float(p_access * p_back))
        path_delay.append(float(d_access + d_back))

    p_arr = np.asarray(path_pdr, dtype=float)
    d_arr = np.asarray(path_delay, dtype=float)
    deadline_weight = float(qos_cfg.get("deadline_weight", 0.55))
    reliability_weight = float(qos_cfg.get("reliability_weight", 0.45))
    max_penalty = float(qos_cfg.get("max_penalty", 2.5))
    class_penalties = []
    for deadline, target in zip(deadlines, pdr_targets):
        delay_load = np.where(np.isfinite(d_arr), d_arr / max(float(deadline), 1e-6), max_penalty)
        delay_load = np.clip(delay_load, 0.0, max_penalty)
        reliability_gap = np.clip((float(target) - p_arr) / max(float(target), 1e-6), 0.0, 1.0)
        class_penalties.append(
            deadline_weight * float(np.mean(delay_load))
            + reliability_weight * float(np.mean(reliability_gap))
        )
    class_penalties = np.asarray(class_penalties, dtype=float)
    return float(overall_pressure * np.dot(class_weights, class_penalties))


def cluster_fitness(
    net: WSNNetwork,
    position: np.ndarray,
    risk: np.ndarray,
    previous_chs: list[int],
    cfg: dict,
    qos_context: dict | None = None,
) -> float:
    alive_count = int(net.alive.sum())
    k = max(int(cfg["min_ch"]), int(math.ceil(alive_count * float(cfg["ch_fraction"]))))
    chs = decode_heads(position, net.alive, k)
    if not chs:
        return 1e9
    assignment = assign_clusters(net, chs)
    w = cfg["weights"]
    energy_term = float(np.mean(1.0 - np.clip(net.energy[chs] / net.e0, 0.0, 1.0)))
    dists = []
    uncovered = 0
    loads = []
    for ch in chs:
        members = np.flatnonzero((assignment == ch) & net.alive)
        loads.append(len(members))
        for i in members:
            d = net.distance(int(i), ch)
            dists.append(d / max(net.radio_range, 1e-9))
            if d > net.radio_range:
                uncovered += 1
    dist_term = float(np.mean(dists)) if dists else 1.0
    coverage_penalty = uncovered / max(alive_count, 1)
    queue_term = float(np.mean(net.queue[chs]))
    risk_term = float(np.mean(risk[chs]))
    load_mean = max(float(np.mean(loads)), 1e-9)
    load_term = float(np.std(loads) / load_mean)
    bg = net.backbone_graph(chs, risk)
    sink = net.n
    disconnected = sum(0 if nx.has_path(bg, ch, sink) else 1 for ch in chs if ch in bg)
    disconnect_term = disconnected / max(len(chs), 1)
    if previous_chs:
        inter = len(set(chs) & set(previous_chs))
        union = len(set(chs) | set(previous_chs))
        reconf_term = 1.0 - inter / max(union, 1)
    else:
        reconf_term = 0.0
    qos_cfg = cfg.get("qos_conditioning", {})
    qos_term = qos_topology_penalty(net, chs, assignment, risk, qos_context, qos_cfg)
    fit = (
        float(w["energy"]) * energy_term
        + float(w["intracluster_distance"]) * dist_term
        + float(w["queue"]) * queue_term
        + float(w["security_risk"]) * risk_term
        + float(w["load_balance"]) * load_term
        + float(w["backbone_disconnect"]) * disconnect_term
        + float(w["reconfiguration"]) * reconf_term
        + float(qos_cfg.get("weight", 0.0)) * qos_term
        + 2.0 * coverage_penalty
    )
    return float(fit)


class RemoraOptimizer:
    """Continuous ROA used to rank candidate cluster heads.

    Implements the original ROA's experience attempt, host-feeding, WOA-style
    and SFO-style host-switch updates in a bounded [0,1]^D search space.
    """

    def __init__(self, pop_size: int, iterations: int, c: float, rng: np.random.Generator):
        self.pop_size = int(pop_size)
        self.iterations = int(iterations)
        self.c = float(c)
        self.rng = rng

    def minimize(self, dim: int, objective) -> tuple[np.ndarray, float, list[float]]:
        pop = self.rng.uniform(0.0, 1.0, size=(self.pop_size, dim))
        prev = pop.copy()
        fitness = np.array([objective(x) for x in pop], dtype=float)
        best_i = int(np.argmin(fitness))
        best = pop[best_i].copy()
        best_f = float(fitness[best_i])
        history = [best_f]
        for t in range(self.iterations):
            V = 2.0 * (1.0 - t / max(self.iterations, 1))
            new_pop = pop.copy()
            for i in range(self.pop_size):
                r1 = self.rng.uniform()
                attempt = np.clip(pop[i] + (pop[i] - prev[i]) * r1, 0.0, 1.0)
                f_attempt = float(objective(attempt))
                if f_attempt < fitness[i]:
                    r2 = self.rng.uniform()
                    candidate = pop[i] + (2.0 * V * r2 - V) * (pop[i] - self.c * best)
                else:
                    if self.rng.uniform() < 0.5:
                        r3 = self.rng.uniform()
                        alpha = r3 * (-(1.0 + t / max(self.iterations, 1)) - 1.0) + 1.0
                        candidate = np.abs(best - pop[i]) * np.exp(alpha) * np.cos(2.0 * np.pi * alpha) + pop[i]
                    else:
                        m = int(self.rng.integers(0, self.pop_size))
                        r4 = self.rng.uniform()
                        candidate = best - (r4 * (best + pop[m]) / 2.0 - pop[m])
                candidate = np.clip(candidate, 0.0, 1.0)
                fc = float(objective(candidate))
                if fc <= fitness[i]:
                    new_pop[i] = candidate
                    fitness[i] = fc
            prev, pop = pop, new_pop
            best_i = int(np.argmin(fitness))
            if float(fitness[best_i]) < best_f:
                best_f = float(fitness[best_i])
                best = pop[best_i].copy()
            history.append(best_f)
        return best, best_f, history


def select_cluster_heads(
    net: WSNNetwork,
    risk: np.ndarray,
    previous_chs: list[int],
    cfg: dict,
    qos_context: dict | None = None,
) -> tuple[list[int], np.ndarray, dict]:
    alive_count = int(net.alive.sum())
    k = max(int(cfg["min_ch"]), int(math.ceil(alive_count * float(cfg["ch_fraction"]))))
    opt = RemoraOptimizer(cfg["roa_population"], cfg["roa_iterations"], cfg["remora_factor_c"], net.rng)
    objective = lambda x: cluster_fitness(net, x, risk, previous_chs, cfg, qos_context=qos_context)
    pos, fit, hist = opt.minimize(net.n, objective)
    chs = decode_heads(pos, net.alive, k)
    assignment = assign_clusters(net, chs)
    qos_cfg = cfg.get("qos_conditioning", {})
    qos_term = qos_topology_penalty(net, chs, assignment, risk, qos_context, qos_cfg)
    gate_active, gate_signal, gate_threshold = qos_gate_state(qos_context, qos_cfg)

    # Stage-4G1.5: expose only the selected *final* topology to the forwarding
    # observation builder. Candidate topologies evaluated inside ROA never leak
    # into the router because this assignment occurs after optimization ends.
    net.active_chs = [int(x) for x in chs]
    net.active_assignment = assignment.copy()

    return chs, assignment, {
        "fitness": fit,
        "history": hist,
        "qos_topology_penalty": qos_term,
        "qos_gate_active": bool(gate_active),
        "qos_gate_signal": float(gate_signal),
        "qos_gate_threshold": float(gate_threshold),
    }

