from __future__ import annotations
import numpy as np


class QoSDebtTracker:
    """Per-class virtual queues for long-term QoS constraint violations.

    Each traffic class maintains one debt for deadline/timeliness violations and
    one for packet loss. The virtual queues are updated as

        Z <- max(0, Z + observed_violation - allowed_violation_rate)

    so persistent violations accumulate instead of being hidden by a global
    average. The normalized debts are safe to expose to the fast routing policy
    and to the slow re-clustering trigger.
    """

    def __init__(self, deadlines_ms, pdr_targets, delay_violation_budgets=None):
        self.deadlines_s = np.asarray(deadlines_ms, dtype=float) / 1000.0
        self.pdr_targets = np.asarray(pdr_targets, dtype=float)
        self.loss_budgets = np.clip(1.0 - self.pdr_targets, 0.0, 1.0)
        if delay_violation_budgets is None:
            delay_violation_budgets = np.minimum(0.10, np.maximum(0.02, self.loss_budgets))
        self.delay_budgets = np.asarray(delay_violation_budgets, dtype=float)
        if not (len(self.deadlines_s) == len(self.pdr_targets) == len(self.delay_budgets)):
            raise ValueError("QoS class arrays must have equal length")
        self.n_classes = len(self.deadlines_s)
        self.delay_debt = np.zeros(self.n_classes, dtype=float)
        self.loss_debt = np.zeros(self.n_classes, dtype=float)
        self.counts = np.zeros(self.n_classes, dtype=int)
        self.delay_violations = np.zeros(self.n_classes, dtype=float)
        self.losses = np.zeros(self.n_classes, dtype=float)
        self.debt_history: list[np.ndarray] = []

    def update(self, traffic_class: int, delivered: bool, delay_s: float | None) -> tuple[float, float]:
        c = int(traffic_class)
        if not 0 <= c < self.n_classes:
            raise IndexError("traffic class out of range")
        loss = 0.0 if delivered else 1.0
        deadline_bad = 1.0 if (not delivered or delay_s is None or delay_s > self.deadlines_s[c]) else 0.0
        self.delay_debt[c] = max(0.0, self.delay_debt[c] + deadline_bad - self.delay_budgets[c])
        self.loss_debt[c] = max(0.0, self.loss_debt[c] + loss - self.loss_budgets[c])
        self.counts[c] += 1
        self.delay_violations[c] += deadline_bad
        self.losses[c] += loss
        self.debt_history.append(self.normalized_vector.copy())
        return deadline_bad, loss

    @staticmethod
    def _squash(x: np.ndarray) -> np.ndarray:
        return x / (1.0 + x)

    @property
    def normalized_delay_debt(self) -> np.ndarray:
        return self._squash(self.delay_debt)

    @property
    def normalized_loss_debt(self) -> np.ndarray:
        return self._squash(self.loss_debt)

    @property
    def normalized_vector(self) -> np.ndarray:
        out = np.empty(2 * self.n_classes, dtype=float)
        out[0::2] = self.normalized_delay_debt
        out[1::2] = self.normalized_loss_debt
        return out

    @property
    def max_normalized_debt(self) -> float:
        v = self.normalized_vector
        return float(v.max()) if len(v) else 0.0

    @property
    def mean_max_normalized_debt(self) -> float:
        if not self.debt_history:
            return 0.0
        return float(np.mean([float(v.max()) for v in self.debt_history]))

    @property
    def peak_max_normalized_debt(self) -> float:
        if not self.debt_history:
            return 0.0
        return float(np.max([float(v.max()) for v in self.debt_history]))

    @property
    def mean_normalized_vector(self) -> np.ndarray:
        if not self.debt_history:
            return np.zeros(2 * self.n_classes, dtype=float)
        return np.mean(np.vstack(self.debt_history), axis=0)

    def empirical_rates(self) -> dict[str, np.ndarray]:
        den = np.maximum(self.counts, 1)
        return {
            "delay_violation_rate": self.delay_violations / den,
            "loss_rate": self.losses / den,
        }

