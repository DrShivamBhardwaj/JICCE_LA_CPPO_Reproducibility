"""Software UDP feedback adapter; not a radio or authenticated watchdog model."""
from __future__ import annotations
import json
import secrets
import socket
import time
from dataclasses import dataclass
from .security import SecurityRiskEstimator


@dataclass(frozen=True)
class FeedbackRecord:
    sequence: int
    node: int
    acknowledged: bool
    elapsed_s: float
    risk_before: float
    risk_after: float


class UDPFeedbackAdapter:
    """Update risk only after a matching endpoint/nonce/sequence ACK.

    Timeouts are forwarding failures, not proof of malicious behavior. Expected
    PDR is an externally supplied calibration assumption. Nonces prevent stale
    packet confusion but do not authenticate peers. Use one instance per sender.
    """
    def __init__(self, estimator: SecurityRiskEstimator, timeout_s: float = 0.05):
        if timeout_s <= 0:
            raise ValueError('timeout_s must be positive')
        self.estimator = estimator
        self.timeout_s = timeout_s
        self.sequence = 0

    def forward(self, node: int, endpoint: tuple[str, int], payload: bytes,
                expected_pdr: float) -> FeedbackRecord:
        if not 0 <= node < len(self.estimator.a):
            raise ValueError('invalid node')
        if not 0 <= expected_pdr <= 1:
            raise ValueError('invalid expected PDR')
        resolved = (socket.gethostbyname(endpoint[0]), endpoint[1])
        self.sequence += 1
        sequence, nonce = self.sequence, secrets.token_hex(16)
        message = json.dumps({'sequence': sequence, 'nonce': nonce,
                              'payload_hex': payload.hex()}).encode()
        before = float(self.estimator.risk[node])
        start = time.monotonic()
        acknowledged = False
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender:
            sender.sendto(message, resolved)
            deadline = start + self.timeout_s
            while time.monotonic() < deadline:
                sender.settimeout(max(deadline - time.monotonic(), 1e-6))
                try:
                    data, peer = sender.recvfrom(65535)
                except socket.timeout:
                    break
                if peer != resolved:
                    continue
                try:
                    ack = json.loads(data)
                except (ValueError, UnicodeDecodeError):
                    continue
                if isinstance(ack, dict) and ack.get('sequence') == sequence and ack.get('nonce') == nonce and ack.get('forwarded') is True:
                    acknowledged = True
                    break
        elapsed = time.monotonic() - start
        self.estimator.observe_forward(node, acknowledged, expected_pdr)
        return FeedbackRecord(sequence, node, acknowledged, elapsed, before,
                              float(self.estimator.risk[node]))
