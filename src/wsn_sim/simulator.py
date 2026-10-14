from __future__ import annotations
import numpy as np
import pandas as pd
from .network import WSNNetwork, Packet
from .security import SecurityRiskEstimator
from .clustering import select_cluster_heads
from .trigger import ReclusterTrigger
from .routing import hierarchical_path


class Simulator:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.net = WSNNetwork(cfg)
        self.sec = SecurityRiskEstimator(self.net.n)
        self.trigger = ReclusterTrigger(cfg["trigger"])
        self.chs: list[int] = []
        self.assignment = np.full(self.net.n, -1, dtype=int)
        self.qos_ewma = 0.0
        self.rows = []
        self.recluster_count = 0
        self._recluster(initial=True)

    def _recluster(self, initial: bool = False):
        old = [] if initial else list(self.chs)
        self.chs, self.assignment, info = select_cluster_heads(self.net, self.sec.risk, old, self.cfg["clustering"])
        self.recluster_count += 1
        return info

    def _generate_packets(self, round_id: int) -> list[Packet]:
        tc = self.cfg["traffic"]
        probs = np.asarray(tc["class_probs"], dtype=float)
        probs = probs / probs.sum()
        packets = []
        for i in np.flatnonzero(self.net.alive):
            if self.net.rng.uniform() < float(tc["generation_prob"]):
                c = int(self.net.rng.choice(len(probs), p=probs))
                packets.append(Packet(int(i), c, float(tc["deadlines_ms"][c]) / 1000.0, round_id))
        return packets

    def _malicious_drop(self, node: int, is_transit: bool) -> bool:
        if not is_transit or not self.net.malicious[node]:
            return False
        kind = self.net.attack_kind[node]
        if kind == "blackhole":
            return True
        if kind == "selective":
            return self.net.rng.uniform() < float(self.cfg["attack"]["selective_drop_prob"])
        return False

    def run(self) -> pd.DataFrame:
        sim = self.cfg["simulation"]
        nc = self.cfg["network"]
        round_s = float(nc["round_duration_s"])
        packet_bits = int(nc["packet_bits"])
        max_hops = int(sim["max_hops"])
        for r in range(int(sim["rounds"])):
            self.net.update_dynamic_state()
            generated = delivered = dropped = 0
            total_delay = 0.0
            energy_before = float(self.net.energy.sum())
            qos_bad = 0
            control_msgs = 0
            for i in range(self.net.n):
                excess = max(self.net.queue[i] - 0.4, 0.0) / 0.6
                self.sec.observe_rate(i, excess)
            packets = self._generate_packets(r)
            generated = len(packets)
            for pkt in packets:
                path = hierarchical_path(self.net, pkt.source, self.chs, self.assignment, self.sec.risk, sim["router"])
                if len(path) < 2 or len(path) > max_hops + 1:
                    dropped += 1
                    qos_bad += 1
                    continue
                delay = 0.0
                ok = True
                for hop in range(len(path) - 1):
                    u = path[hop]
                    v = path[hop + 1]
                    assert u is not None
                    if not self.net.alive[u]:
                        ok = False
                        break
                    d = self.net.distance(u, None if v is None else v)
                    if d > self.net.radio_range:
                        ok = False
                        break
                    p = self.net.radio.pdr(d, self.net.interference[u])
                    txe = self.net.radio.tx_energy(d)
                    self.net.energy[u] = max(0.0, self.net.energy[u] - txe)
                    if v is not None and self.net.alive[v]:
                        self.net.energy[v] = max(0.0, self.net.energy[v] - self.net.radio.rx_energy())
                    malicious = self._malicious_drop(u, is_transit=(hop > 0 or pkt.source != u))
                    phys_success = self.net.rng.uniform() < p
                    success = phys_success and not malicious
                    delay += self.net.radio.hop_delay_s(self.net.queue[u])
                    self.sec.observe_forward(u, success, p)
                    if not success:
                        ok = False
                        break
                if ok and path[-1] is None:
                    delivered += 1
                    total_delay += delay
                    if delay > pkt.deadline_s:
                        qos_bad += 1
                else:
                    dropped += 1
                    qos_bad += 1
            qv = qos_bad / max(generated, 1)
            self.qos_ewma = 0.8 * self.qos_ewma + 0.2 * qv
            trigger_score, trigger_parts = self.trigger.score(self.net, self.chs, self.assignment, self.sec.risk, self.qos_ewma)
            recluster = self.trigger.update(r, trigger_score)
            roa_fit = np.nan
            if recluster:
                info = self._recluster()
                roa_fit = info["fitness"]
                control_msgs = int(self.net.alive.sum()) + len(self.chs)
            energy_used = max(0.0, energy_before - float(self.net.energy.sum()))
            throughput = delivered * packet_bits / round_s
            pdr = delivered / max(generated, 1)
            mean_delay_ms = (total_delay / max(delivered, 1)) * 1000.0
            self.rows.append({
                "seed": self.cfg["seed"], "round": r, "router": sim["router"], "n_nodes": self.net.n,
                "malicious_ratio": float(self.cfg["attack"]["malicious_ratio"]), "generated_packets": generated,
                "delivered_packets": delivered, "dropped_packets": dropped, "pdr": pdr,
                "throughput_bps": throughput, "mean_delay_ms": mean_delay_ms, "qos_violation_rate": qv,
                "energy_consumed_j": energy_used, "alive_nodes": int(self.net.alive.sum()),
                "mean_security_risk": float(np.mean(self.sec.risk[self.net.alive])) if self.net.alive.any() else 1.0,
                "cluster_heads": len(self.chs), "recluster_triggered": int(recluster), "recluster_score": trigger_score,
                "control_messages": control_msgs, "roa_fitness": roa_fit,
                **{f"trigger_{k}": v for k, v in trigger_parts.items()},
            })
        return pd.DataFrame(self.rows)

