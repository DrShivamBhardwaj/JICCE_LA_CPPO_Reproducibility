"""Post-freeze censored ledger variant; not used by the manuscript benchmark.

Reliability is clipped once per record, then multiplied by evidence increments.
Records and diagnostics have explicit capacities. Packet identifiers must increase
within a bounded 64-identity replay window for each observer/peer pair.
"""
import math
from collections import deque
from .censored_feedback import FeedbackLedger

class BoundedFeedbackLedger(FeedbackLedger):
    def __init__(self, n_nodes, capacity=128, retention_s=2.0, history_capacity=256, mode='censored'):
        if not isinstance(n_nodes, int) or n_nodes < 1:
            raise ValueError("positive node count required")
        if not isinstance(capacity, int) or capacity < 1 or not isinstance(history_capacity, int) or history_capacity < 1:
            raise ValueError("positive capacities required")
        if not math.isfinite(retention_s) or retention_s < .15:
            raise ValueError("retention must cover the 150 ms evidence timeout")
        if mode not in ('censored','naive'):raise ValueError('unsupported bounded mode')
        super().__init__(n_nodes, mode)
        self.n_nodes = n_nodes
        self.capacity = capacity
        self.retention_s = retention_s
        self.updates = deque(maxlen=history_capacity)
        self.highest_pid = {}
        self.identity_bits = {}
        self.old_identity_rejections = 0
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
        high = self.highest_pid.get(pair, -1)
        bits = self.identity_bits.get(pair, 0)
        if pid > high:
            gap = pid - high
            bits = 1 if high < 0 or gap >= 64 else ((bits << gap) | 1) & ((1 << 64) - 1)
            high = pid
        else:
            distance = high - pid
            if distance >= 64:
                self.old_identity_rejections += 1
                return False
            if bits & (1 << distance):
                raise ValueError("packet identity already registered within session")
            bits |= 1 << distance
        # Reserve rejected identities too; delayed evidence cannot attach to reuse.
        self.highest_pid[pair] = high
        self.identity_bits[pair] = bits
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
