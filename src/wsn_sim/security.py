from __future__ import annotations
import numpy as np


class SecurityRiskEstimator:
    """Heuristic forwarding-risk scores from weighted effective counts.

    Attack labels are not exposed to the controller. The beta-form moments,
    clipped evidence weights and fixed multiplier are scoring conventions, not
    calibrated posteriors or statistical coverage bounds. Public property names
    are retained for compatibility with the frozen implementation.
    """

    def __init__(self, n_nodes: int, confidence_z: float = 1.645, enabled: bool = True):
        self.enabled = bool(enabled)
        self.a = np.ones(n_nodes, dtype=float)
        self.b = np.ones(n_nodes, dtype=float)
        self.rate_anomaly = np.zeros(n_nodes, dtype=float)
        self.confidence_z = float(confidence_z)

    @property
    def trust_mean(self) -> np.ndarray:
        return self.a / (self.a + self.b)

    @property
    def trust_std(self) -> np.ndarray:
        a, b = self.a, self.b
        var = (a * b) / (((a + b) ** 2) * (a + b + 1.0))
        return np.sqrt(np.maximum(var, 0.0))

    @property
    def risk(self) -> np.ndarray:
        if not self.enabled:
            return np.zeros_like(self.a)
        return np.clip(0.75 * (1.0 - self.trust_mean) + 0.25 * self.rate_anomaly, 0.0, 1.0)

    @property
    def risk_uncertainty(self) -> np.ndarray:
        if not self.enabled:
            return np.zeros_like(self.a)
        return np.clip(0.75 * self.trust_std, 0.0, 1.0)

    @property
    def risk_ucb(self) -> np.ndarray:
        return np.clip(self.risk + self.confidence_z * self.risk_uncertainty, 0.0, 1.0)

    def observe_forward(self, node: int, success: bool, expected_pdr: float) -> None:
        # A failure on a link expected to be reliable carries more evidence of
        # suspicious forwarding than a failure on an intrinsically poor link.
        w = float(np.clip(expected_pdr, 0.05, 1.0))
        if success:
            self.a[node] += w
        else:
            self.b[node] += w

    def observe_rate(self, node: int, normalized_excess_rate: float) -> None:
        x = float(np.clip(normalized_excess_rate, 0.0, 1.0))
        self.rate_anomaly[node] = 0.85 * self.rate_anomaly[node] + 0.15 * x

