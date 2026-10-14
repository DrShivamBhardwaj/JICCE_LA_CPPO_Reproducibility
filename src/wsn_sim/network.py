from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import networkx as nx
from .radio import RadioModel


@dataclass
class Packet:
    source: int
    traffic_class: int
    deadline_s: float
    created_round: int


class WSNNetwork:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.rng = np.random.default_rng(int(cfg["seed"]))
        split = bool(cfg.get("validation", {}).get("split_streams", False))
        streams = [np.random.default_rng(x) for x in np.random.SeedSequence(int(cfg["seed"])).spawn(5)]
        self.traffic_rng, self.dynamics_rng, self.attack_rng, self.link_rng, self.feedback_rng = streams if split else [self.rng] * 5
        nc = cfg["network"]
        self.n = int(nc["n_nodes"])
        w, h = map(float, nc["area_m"])
        self.positions = np.column_stack((self.rng.uniform(0, w, self.n), self.rng.uniform(0, h, self.n)))
        self.sink = np.asarray(nc["sink_xy"], dtype=float)
        self.e0 = float(nc["initial_energy_j"])
        self.energy = np.full(self.n, self.e0, dtype=float)
        self.queue = self.rng.uniform(0.02, 0.12, self.n)
        self.interference = np.zeros(self.n, dtype=float)
        self.radio_range = float(nc["radio_range_m"])
        self.radio = RadioModel(cfg["radio"], int(nc["packet_bits"]), float(nc["data_rate_bps"]), self.link_rng)
        self.malicious = np.zeros(self.n, dtype=bool)
        self.attack_kind = np.array(["none"] * self.n, dtype=object)
        self._init_attacks()

    @property
    def alive(self) -> np.ndarray:
        return self.energy > 0.0

    def _init_attacks(self) -> None:
        m = int(round(self.n * float(self.cfg["attack"]["malicious_ratio"])))
        if m <= 0:
            return
        ids = self.rng.choice(self.n, size=m, replace=False)
        kinds = ["blackhole", "selective", "flooding"]
        for k, node in enumerate(ids):
            self.malicious[node] = True
            self.attack_kind[node] = kinds[k % len(kinds)]

    def distance(self, i: int, j: int | None = None) -> float:
        target = self.sink if j is None else self.positions[j]
        return float(np.linalg.norm(self.positions[i] - target))

    def feasible_neighbors(self, i: int, candidates: np.ndarray | None = None) -> list[int]:
        if not self.alive[i]:
            return []
        if candidates is None:
            candidates = np.flatnonzero(self.alive)
        d = np.linalg.norm(self.positions[candidates] - self.positions[i], axis=1)
        out = [int(x) for x, dist in zip(candidates, d) if int(x) != i and dist <= self.radio_range]
        return out

    def mean_member_link_pdr(self, chs: list[int], assignment: np.ndarray) -> float:
        vals = []
        for i in np.flatnonzero(self.alive):
            ch = int(assignment[i])
            if ch < 0 or i == ch:
                continue
            vals.append(self.radio.pdr(self.distance(i, ch), self.interference[i], shadowing_db=0.0))
        return float(np.mean(vals)) if vals else 1.0

    def update_dynamic_state(self) -> None:
        self.interference = 0.85 * self.interference + 0.15 * np.clip(self.dynamics_rng.normal(1.2, 2.0, self.n), 0.0, 8.0)
        self.queue *= 0.78
        self.queue += self.dynamics_rng.uniform(0.0, 0.08, self.n)
        flood = self.attack_kind == "flooding"
        self.queue[flood] += float(self.cfg["attack"]["flooding_queue_add"])
        self.queue = np.clip(self.queue, 0.0, 1.0)

    def backbone_graph(self, chs: list[int], risk: np.ndarray, router: str = "energy_risk_etx") -> nx.Graph:
        g = nx.Graph()
        sink_id = self.n
        g.add_node(sink_id)
        alive_chs = [int(c) for c in chs if self.alive[c]]
        g.add_nodes_from(alive_chs)
        for a_idx, i in enumerate(alive_chs):
            d_sink = self.distance(i, None)
            if d_sink <= self.radio_range:
                p = self.radio.pdr(d_sink, self.interference[i], shadowing_db=0.0)
                g.add_edge(i, sink_id, weight=self._edge_weight(i, None, p, risk, router))
            for j in alive_chs[a_idx + 1:]:
                d = self.distance(i, j)
                if d <= self.radio_range:
                    p = self.radio.pdr(d, 0.5 * (self.interference[i] + self.interference[j]), shadowing_db=0.0)
                    w = 0.5 * (self._edge_weight(i, j, p, risk, router) + self._edge_weight(j, i, p, risk, router))
                    g.add_edge(i, j, weight=w)
        return g

    def _edge_weight(self, i: int, j: int | None, pdr: float, risk: np.ndarray, router: str) -> float:
        etx = 1.0 / max(pdr, 1e-3)
        if router == "shortest_etx":
            return etx
        er = self.energy[i] / self.e0
        q = self.queue[i]
        r = risk[i]
        return etx * (1.0 + 0.75 * (1.0 - er) + 0.55 * q + 1.1 * r)

