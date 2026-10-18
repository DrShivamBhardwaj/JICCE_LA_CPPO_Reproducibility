"""Post-freeze censored ledger variant; not used by the manuscript benchmark.

Reliability is clipped once per record, then multiplied by evidence increments.
Records and diagnostics have explicit capacities. Packet identifiers must increase
strictly for each observer/peer pair within this ledger session.
"""
import math
from collections import deque
from .censored_feedback import FeedbackLedger

class BoundedFeedbackLedger(FeedbackLedger):
    def __init__(self, n_nodes, capacity=128, retention_s=2.0, history_capacity=256):
        if not isinstance(n_nodes, int) or n_nodes < 1:
            raise ValueError("positive node count required")
        if not isinstance(capacity, int) or capacity < 1 or not isinstance(history_capacity, int) or history_capacity < 1:
            raise ValueError("positive capacities required")
        if not math.isfinite(retention_s) or retention_s < .15:
            raise ValueError("retention must cover the 150 ms evidence timeout")
        super().__init__(n_nodes, "censored")
        self.n_nodes = n_nodes
        self.capacity = capacity
        self.retention_s = retention_s
        self.updates = deque(maxlen=history_capacity)
        self.highest_pid = {}
        self.last_time = -math.inf
        self.retired = 0
        self.capacity_rejections = 0

    def _advance(self, time):
        if not math.isfinite(time) or time < self.last_time:
            raise ValueError("event times must be finite and nondecreasing")
        self.last_time = time
        for key, watch in list(self.watches.items()):
            if time >= watch.registered + self.retention_s:
                del self.watches[key]
                self.retired += 1

    def register(self, observer, peer, pid, time, expected):
        if not all(isinstance(i, int) and 0 <= i < self.n_nodes for i in (observer, peer)):
            raise ValueError("node bounds")
        if not isinstance(pid, int) or not 0 <= pid < 2**32:
            raise ValueError("packet identifier bounds")
        if not math.isfinite(expected) or not 0 <= expected <= 1:
            raise ValueError("link success must lie in [0,1]")
        self._advance(time)
        pair = observer, peer
        if pid <= self.highest_pid.get(pair, -1):
            raise ValueError("packet identifiers must increase within session")
        # Reserve even rejected identities so delayed evidence cannot attach to reuse.
        self.highest_pid[pair] = pid
        if len(self.watches) >= self.capacity:
            self.capacity_rejections += 1
            return False
        super().register(observer, peer, pid, time, expected)
        return True

    def _credit(self, key, watch, time):
        if watch.acked is not True or watch.seen <= watch.credited:
            return
        delta = min(1., max(.05, watch.expected)) * (watch.seen - watch.credited)
        self.risk[key[0]].a[key[1]] += delta
        watch.credited = watch.seen
        self.positives += 1
        self.updates.append(dict(time=time, key=list(key), success=True, weight=delta))

    def acknowledge(self, observer, peer, pid, success, time):
        self._advance(time)
        watch = self.watches.get((observer, peer, pid))
        # The first final MAC result is terminal; duplicates cannot reverse it.
        if watch is not None and watch.acked is None:
            super().acknowledge(observer, peer, pid, success, time)

    def evidence(self, observer, peer, pid, kind, time):
        if kind not in ("passive", "receipt"):
            raise ValueError("unknown evidence kind")
        self._advance(time)
        super().evidence(observer, peer, pid, kind, time)

    def expire(self, time):
        self._advance(time)
        return super().expire(time)
