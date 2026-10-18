"""Opt-in freshness tolerance under an externally justified pairwise clock bound."""
import math
from dataclasses import dataclass

@dataclass(frozen=True)
class ClockEnvelope:
    skew_bound_s: float

    def __post_init__(self):
        if not math.isfinite(self.skew_bound_s) or self.skew_bound_s < 0:
            raise ValueError("finite nonnegative pairwise clock bound required")

    @classmethod
    def from_limits(cls, pair_offset_s, relative_drift_ppm, horizon_s):
        if not all(math.isfinite(x) and x >= 0 for x in (pair_offset_s, relative_drift_ppm, horizon_s)):
            raise ValueError("invalid clock envelope")
        return cls(pair_offset_s + relative_drift_ppm * 1e-6 * horizon_s)

    def accepts(self, stamp, now, ttl):
        if not all(math.isfinite(x) for x in (stamp, now, ttl)) or ttl < 0:
            return False
        age = now - stamp
        return -self.skew_bound_s - 1e-6 <= age <= ttl + self.skew_bound_s + 1e-6

    def expired(self, stamp, now, ttl):
        return now - stamp > ttl + self.skew_bound_s + 1e-6
