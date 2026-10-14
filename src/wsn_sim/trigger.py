from __future__ import annotations
import numpy as np
from .network import WSNNetwork


class ReclusterTrigger:
    """Dual-channel persistent slow-timescale reconfiguration trigger.

    Network stress and QoS constraint debt are evaluated as separate channels.
    Either can activate re-clustering after its own persistence requirement,
    while a shared cooldown suppresses topology churn.  This avoids diluting a
    severe QoS debt inside a weighted average of unrelated stress indicators.
    """

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.stress_count = 0
        self.debt_count = 0
        self.last_trigger = -10**9
        self.last_reason = "none"

    def score(self, net: WSNNetwork, chs: list[int], assignment: np.ndarray, risk: np.ndarray, qos_debt: float) -> tuple[float, dict]:
        w = self.cfg["weights"]
        if chs:
            er = np.clip(net.energy[chs] / net.e0, 0.0, 1.0)
            energy_imb = float(min(np.std(er) / max(np.mean(er), 1e-6), 1.0))
            queue = float(np.mean(net.queue[chs]))
            sec = float(np.mean(risk[chs]))
            link_deg = 1.0 - net.mean_member_link_pdr(chs, assignment)
        else:
            energy_imb = queue = sec = link_deg = 1.0
        parts = {
            "energy_imbalance": energy_imb,
            "queue_pressure": queue,
            "link_degradation": float(np.clip(link_deg, 0.0, 1.0)),
            "security_risk": sec,
            "qos_violation": float(np.clip(qos_debt, 0.0, 1.0)),
        }
        # Keep the legacy composite score for diagnostics, but Stage-4B's
        # network-stress channel excludes QoS debt; debt has its own trigger.
        s = sum(float(w[k]) * v for k, v in parts.items())
        return float(s), parts

    def update(self, round_id: int, score: float, qos_debt: float | None = None) -> bool:
        if round_id - self.last_trigger < int(self.cfg["cooldown_rounds"]):
            self.stress_count = 0
            self.debt_count = 0
            self.last_reason = "cooldown"
            return False

        stress_threshold = float(self.cfg.get("stress_threshold", self.cfg["threshold"]))
        stress_persistence = int(self.cfg.get("stress_persistence", self.cfg["persistence"]))
        debt_threshold = float(self.cfg.get("debt_threshold", 0.35))
        debt_persistence = int(self.cfg.get("debt_persistence", 2))
        debt_enabled = bool(self.cfg.get("debt_enabled", True))

        if score >= stress_threshold:
            self.stress_count += 1
        else:
            self.stress_count = 0

        if debt_enabled and qos_debt is not None and float(qos_debt) >= debt_threshold:
            self.debt_count += 1
        else:
            self.debt_count = 0

        stress_fire = self.stress_count >= stress_persistence
        debt_fire = self.debt_count >= debt_persistence
        if stress_fire or debt_fire:
            self.last_trigger = round_id
            self.last_reason = "qos_debt" if debt_fire and not stress_fire else ("stress+qos_debt" if debt_fire else "network_stress")
            self.stress_count = 0
            self.debt_count = 0
            return True
        self.last_reason = "none"
        return False

