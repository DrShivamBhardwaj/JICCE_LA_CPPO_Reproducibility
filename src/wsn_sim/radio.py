from __future__ import annotations
import math
import numpy as np


class RadioModel:
    """First-order radio energy model + packet-level log-distance link abstraction.

    The energy equations follow the commonly used LEACH-family first-order model.
    Link success is intentionally a packet-level abstraction for the Python research
    simulator; selected final scenarios should later be cross-validated in ns-3.
    """

    def __init__(self, cfg: dict, packet_bits: int, data_rate_bps: float, rng: np.random.Generator):
        self.cfg = cfg
        self.packet_bits = int(packet_bits)
        self.data_rate_bps = float(data_rate_bps)
        self.rng = rng
        self.e_elec = float(cfg["e_elec_j_per_bit"])
        self.eps_fs = float(cfg["eps_fs_j_per_bit_m2"])
        self.eps_mp = float(cfg["eps_mp_j_per_bit_m4"])
        self.e_da = float(cfg.get("e_da_j_per_bit", 0.0))
        self.d0 = math.sqrt(self.eps_fs / self.eps_mp)

    def tx_energy(self, distance_m: float, bits: int | None = None) -> float:
        k = self.packet_bits if bits is None else int(bits)
        d = max(float(distance_m), 1e-9)
        amp = self.eps_fs * d**2 if d < self.d0 else self.eps_mp * d**4
        return k * (self.e_elec + amp)

    def rx_energy(self, bits: int | None = None) -> float:
        k = self.packet_bits if bits is None else int(bits)
        return k * self.e_elec

    def aggregate_energy(self, bits: int | None = None) -> float:
        k = self.packet_bits if bits is None else int(bits)
        return k * self.e_da

    def rssi_dbm(self, distance_m: float, shadowing_db: float = 0.0, interference_db: float = 0.0) -> float:
        d = max(float(distance_m), 1.0)
        pl = float(self.cfg["pl0_db"]) + 10.0 * float(self.cfg["path_loss_exponent"]) * math.log10(d)
        return float(self.cfg["tx_power_dbm"]) - pl - float(interference_db) + float(shadowing_db)

    def pdr(self, distance_m: float, interference_db: float = 0.0, shadowing_db: float | None = None) -> float:
        if shadowing_db is None:
            shadowing_db = float(self.rng.normal(0.0, float(self.cfg["shadowing_sigma_db"])))
        rssi = self.rssi_dbm(distance_m, shadowing_db, interference_db)
        snr = rssi - float(self.cfg["noise_floor_dbm"])
        midpoint = float(self.cfg["pdr_mid_snr_db"])
        slope = max(float(self.cfg["pdr_slope_db"]), 1e-6)
        x = np.clip((snr - midpoint) / slope, -30.0, 30.0)
        return float(np.clip(1.0 / (1.0 + np.exp(-x)), 1e-4, 0.9999))

    def expected_hop_delay_s(self, queue_ratio: float, pdr: float, max_retries: int = 3) -> float:
        """Approximate one-hop service delay used only for policy observation/shielding.

        The estimate truncates the geometric retransmission process at the MAC
        retry limit and adds the same queue/backoff mean used by ``hop_delay_s``.
        """
        p = float(np.clip(pdr, 1e-4, 0.9999))
        expected_attempts = 0.0
        survive = 1.0
        for _ in range(max_retries + 1):
            expected_attempts += survive
            survive *= (1.0 - p)
        tx = self.packet_bits / self.data_rate_bps
        q_delay = max(queue_ratio, 0.0) * 3.0 * tx
        mean_backoff = 0.0015
        return expected_attempts * (tx + mean_backoff) + q_delay

    def hop_delay_s(self, queue_ratio: float, retransmissions: int = 0) -> float:
        tx = self.packet_bits / self.data_rate_bps
        q_delay = max(queue_ratio, 0.0) * 3.0 * tx
        backoff = float(self.rng.exponential(0.0015))
        return tx * (1 + max(retransmissions, 0)) + q_delay + backoff

