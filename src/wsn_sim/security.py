from __future__ import annotations
import numpy as np


class SecurityRiskEstimator:
    """Online security-risk estimator with posterior uncertainty.

    Attack ground truth is never exposed to the controller. Successful and
    failed forwarding observations update a Beta trust posterior, weighted by
    expected link reliability, while traffic-rate anomalies contribute an EWMA
    term. ``risk_ucb`` is a conservative upper confidence proxy used by the
    routing shield and clustering fitness so sparse observations are not treated
    as certain evidence.
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

