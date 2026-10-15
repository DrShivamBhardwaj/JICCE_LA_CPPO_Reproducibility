import json
import socket
import threading
import pytest
from wsn_sim.security import SecurityRiskEstimator
from wsn_sim.packet_feedback import UDPFeedbackAdapter


def exercise(reply):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as receiver:
        receiver.bind(('127.0.0.1', 0))
        receiver.settimeout(1)
        endpoint = receiver.getsockname()
        def serve():
            data, peer = receiver.recvfrom(65535)
            packet = json.loads(data)
            for ack in reply(packet):
                receiver.sendto(json.dumps(ack).encode(), peer)
        worker = threading.Thread(target=serve)
        worker.start()
        risk = SecurityRiskEstimator(2)
        record = UDPFeedbackAdapter(risk, .1).forward(1, endpoint, b'fixture', 1.0)
        worker.join(timeout=2)
        assert not worker.is_alive()
        return risk, record


def test_real_matching_udp_ack_updates_only_selected_node():
    risk, record = exercise(lambda p: [dict(p, forwarded=True)])
    assert record.acknowledged
    assert record.risk_after < record.risk_before
    assert risk.a.tolist() == [1, 2]
    assert risk.b.tolist() == [1, 1]


def test_stale_ack_does_not_count_as_forwarding_success():
    risk, record = exercise(lambda p: [dict(p, sequence=p['sequence']-1, forwarded=True)])
    assert not record.acknowledged
    assert record.risk_after > record.risk_before
    assert risk.b.tolist() == [1, 2]


def test_missing_ack_updates_failure_without_attack_labels():
    risk, record = exercise(lambda p: [])
    assert not record.acknowledged
    assert risk.b[1] == 2


def test_malformed_ack_then_valid_ack():
    _, record = exercise(lambda p: [[], dict(p, forwarded=True)])
    assert record.acknowledged


def test_invalid_input_does_not_update_posterior():
    risk = SecurityRiskEstimator(1)
    adapter = UDPFeedbackAdapter(risk)
    with pytest.raises(ValueError):
        adapter.forward(2, ('127.0.0.1', 9), b'', 1)
    assert risk.a[0] == risk.b[0] == 1
