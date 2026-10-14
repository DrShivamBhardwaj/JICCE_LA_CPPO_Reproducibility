from pathlib import Path
import sys
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wsn_sim.config import load_config
from wsn_sim.network import WSNNetwork
from wsn_sim.clustering import select_cluster_heads, assign_clusters, qos_topology_penalty, qos_gate_state
from wsn_sim.security import SecurityRiskEstimator
from wsn_sim.rl import MaskedActorCritic, LagrangeController


def test_radio_energy_positive():
    cfg = load_config(ROOT / "configs" / "smoke.yaml")
    net = WSNNetwork(cfg)
    assert net.radio.tx_energy(10.0) > 0
    assert net.radio.rx_energy() > 0


def test_roa_cluster_selection_alive():
    cfg = load_config(ROOT / "configs" / "smoke.yaml")
    net = WSNNetwork(cfg)
    risk = SecurityRiskEstimator(net.n).risk
    chs, assignment, info = select_cluster_heads(net, risk, [], cfg["clustering"])
    assert len(chs) >= cfg["clustering"]["min_ch"]
    assert all(net.alive[c] for c in chs)
    assert np.isfinite(info["fitness"])
    assert np.all(assignment[net.alive] >= 0)


def test_masked_policy_and_lagrange():
    model = MaskedActorCritic(obs_dim=10, n_actions=4)
    obs = torch.zeros((2, 10))
    mask = torch.tensor([[1,1,0,0],[0,1,1,0]], dtype=torch.bool)
    a, logp, v, cv = model.act(obs, mask)
    assert a.shape == (2,)
    assert cv.shape == (2,2)
    lg = LagrangeController(np.array([1.0, 0.05]), lr=0.1)
    before = lg.lambdas.copy()
    after = lg.update(np.array([1.3, 0.1]))
    assert np.all(after >= before)


from wsn_sim.qos import QoSDebtTracker
from wsn_sim.env import PacketRoutingEnv
from wsn_sim.rl import LocalAttentionActorCritic


def test_qos_debt_accumulates_on_persistent_failure():
    q = QoSDebtTracker([100, 500, 2000], [0.98, 0.95, 0.90], [0.02, 0.05, 0.10])
    for _ in range(4):
        q.update(0, False, None)
    assert q.delay_debt[0] > 0
    assert q.loss_debt[0] > 0
    assert 0 < q.max_normalized_debt < 1
    assert len(q.debt_history) == 4
    assert 0 < q.mean_max_normalized_debt <= q.peak_max_normalized_debt < 1


def test_debt_conditioned_topology_penalty_activates_only_with_debt():
    cfg = load_config(ROOT / "configs" / "smoke.yaml")
    net = WSNNetwork(cfg)
    risk = np.zeros(net.n, dtype=float)
    alive = list(map(int, np.flatnonzero(net.alive)))
    chs = alive[: max(2, int(cfg["clustering"]["min_ch"]))]
    assignment = assign_clusters(net, chs)
    qcfg = {
        "enabled": True,
        "delay_debt_weight": 0.6,
        "loss_debt_weight": 0.4,
        "deadline_weight": 0.55,
        "reliability_weight": 0.45,
        "priority_power": 0.75,
        "criticality_gain": 1.5,
        "max_penalty": 2.5,
    }
    zero = {
        "delay_debt": np.zeros(3),
        "loss_debt": np.zeros(3),
        "max_qos_debt": 0.0,
        "deadlines_s": np.array([0.09, 0.35, 1.5]),
        "pdr_targets": np.array([0.985, 0.96, 0.90]),
    }
    active = dict(zero)
    active["delay_debt"] = np.array([0.8, 0.2, 0.0])
    active["loss_debt"] = np.array([0.5, 0.1, 0.0])
    active["max_qos_debt"] = 0.8
    assert qos_topology_penalty(net, chs, assignment, risk, zero, qcfg) == 0.0
    penalty = qos_topology_penalty(net, chs, assignment, risk, active, qcfg)
    assert np.isfinite(penalty)
    assert penalty > 0.0


def test_stage4f_online_qos_gate_uses_current_debt_threshold():
    cfg = load_config(ROOT / "configs" / "smoke.yaml")
    net = WSNNetwork(cfg)
    risk = np.zeros(net.n, dtype=float)
    alive = list(map(int, np.flatnonzero(net.alive)))
    chs = alive[: max(2, int(cfg["clustering"]["min_ch"]))]
    assignment = assign_clusters(net, chs)
    qcfg = {
        "enabled": True,
        "gate_enabled": True,
        "gate_threshold": 0.90,
        "delay_debt_weight": 0.6,
        "loss_debt_weight": 0.4,
        "deadline_weight": 0.55,
        "reliability_weight": 0.45,
        "priority_power": 0.75,
        "criticality_gain": 1.5,
        "max_penalty": 2.5,
    }
    context = {
        "delay_debt": np.array([0.95, 0.2, 0.0]),
        "loss_debt": np.array([0.8, 0.1, 0.0]),
        "deadlines_s": np.array([0.09, 0.35, 1.5]),
        "pdr_targets": np.array([0.985, 0.96, 0.90]),
        "max_qos_debt": 0.899,
    }
    active, signal, threshold = qos_gate_state(context, qcfg)
    assert not active
    assert signal == 0.899
    assert threshold == 0.90
    assert qos_topology_penalty(net, chs, assignment, risk, context, qcfg) == 0.0
    context["max_qos_debt"] = 0.90
    active, _, _ = qos_gate_state(context, qcfg)
    assert active
    assert qos_topology_penalty(net, chs, assignment, risk, context, qcfg) > 0.0


def test_attention_policy_permutation_equivariance():
    cfg = load_config(ROOT / "configs" / "pilot_train.yaml")
    env = PacketRoutingEnv(cfg)
    obs = env.reset_packet()
    b = env.builder
    model = LocalAttentionActorCritic(b.context_dim, b.CANDIDATE_DIM, b.k, hidden=32, n_costs=env.n_costs)
    x = torch.tensor(obs.flat_obs).unsqueeze(0)
    m = torch.tensor(obs.mask).unsqueeze(0)
    logits, _, _ = model(x, m)
    cand = x[:, b.context_dim:].reshape(1, b.k, b.CANDIDATE_DIM).clone()
    if b.k >= 2:
        cand[:, [0, 1]] = cand[:, [1, 0]]
        x2 = torch.cat([x[:, :b.context_dim], cand.reshape(1, -1)], dim=1)
        m2 = m.clone()
        m2[:, [0, 1]] = m2[:, [1, 0]]
        logits2, _, _ = model(x2, m2)
        assert torch.allclose(logits[:, 0], logits2[:, 1], atol=1e-5)
        assert torch.allclose(logits[:, 1], logits2[:, 0], atol=1e-5)


def test_packet_env_produces_valid_cost_vector():
    cfg = load_config(ROOT / "configs" / "pilot_train.yaml")
    env = PacketRoutingEnv(cfg)
    obs = env.reset_packet()
    for _ in range(cfg["simulation"]["max_hops"] + 2):
        valid = np.flatnonzero(obs.mask)
        assert len(valid) > 0
        res = env.step(int(valid[0]))
        if res.done:
            assert res.costs.shape == (env.n_costs,)
            break
        obs = res.observation
        assert obs is not None
    else:
        raise AssertionError("episode did not terminate")

