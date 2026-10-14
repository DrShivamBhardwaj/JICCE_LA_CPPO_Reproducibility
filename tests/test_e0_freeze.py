from pathlib import Path
import inspect
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wsn_sim.config import load_config
from wsn_sim.env import PacketRoutingEnv
from wsn_sim.clustering import cluster_fitness
from wsn_sim.observation import CrossLayerObservationBuilder
from wsn_sim.rl import LocalAttentionActorCritic, ConstrainedPPO
from wsn_sim.security import SecurityRiskEstimator


def _fast_cluster_cfg():
    cfg = load_config(ROOT / "configs" / "af_v1_primary.yaml")
    cfg["clustering"]["roa_population"] = 4
    cfg["clustering"]["roa_iterations"] = 2
    return cfg


def _source_with_neighbors_outside_sink_range(env: PacketRoutingEnv) -> int:
    for i in np.flatnonzero(env.net.alive):
        i = int(i)
        if env.net.distance(i, None) <= env.net.radio_range:
            continue
        if len(env.net.feasible_neighbors(i)) >= 1:
            return i
    raise AssertionError("no alive source with a physical neighbor outside direct sink range")


def _normalize_info(info: dict) -> tuple:
    delay = info.get("delay_s", None)
    if delay is not None and np.isfinite(float(delay)):
        delay = round(float(delay), 12)
    else:
        delay = None
    return (
        bool(info.get("delivered", False)),
        str(info.get("reason", "")),
        int(info.get("traffic_class", -1)),
        delay,
    )


def _trace(env: PacketRoutingEnv, packets: int = 12):
    out = []
    for _ in range(int(packets)):
        obs = env.reset_packet()
        packet = [("source", int(env.source), int(env.traffic_class))]
        for _hop in range(env.cfg["simulation"]["max_hops"] + 2):
            valid = np.flatnonzero(obs.mask)
            assert len(valid) > 0
            slot = int(valid[0])
            target = int(obs.node_ids[slot])
            res = env.step(slot)
            packet.append((
                "step",
                target,
                round(float(res.reward), 12),
                tuple(np.round(res.costs.astype(float), 12).tolist()),
                bool(res.done),
            ))
            if res.done:
                packet.append(("terminal",) + _normalize_info(res.info))
                break
            obs = res.observation
            assert obs is not None
        else:
            raise AssertionError("episode did not terminate within max_hops + 2")
        out.append(tuple(packet))
    return tuple(out)


def test_e0_primary_config_matches_architecture_freeze():
    cfg = load_config(ROOT / "configs" / "af_v1_primary.yaml")
    assert cfg["rl"]["cluster_aware_routing"] is True
    assert cfg["rl"]["cluster_hierarchy_mask"] is True
    assert cfg["rl"]["shield_enabled"] is True
    assert cfg["trigger"]["debt_enabled"] is True
    assert float(cfg["trigger"]["weights"]["qos_violation"]) == 0.0
    stress_weight_sum = sum(
        float(v) for k, v in cfg["trigger"]["weights"].items() if k != "qos_violation"
    )
    assert abs(stress_weight_sum - 1.0) < 1e-12
    qcfg = cfg["clustering"]["qos_conditioning"]
    assert qcfg["enabled"] is False
    assert qcfg["gate_enabled"] is False


def test_e0_controller_facing_modules_do_not_read_attack_ground_truth():
    """The simulator may own attack truth; controller-facing modules may not consume it."""
    sources = {
        "security": inspect.getsource(SecurityRiskEstimator),
        "observation": inspect.getsource(CrossLayerObservationBuilder),
        "clustering_objective": inspect.getsource(cluster_fitness),
        "attention_policy": inspect.getsource(LocalAttentionActorCritic),
        "cppo": inspect.getsource(ConstrainedPPO),
    }
    banned = ("net.malicious", ".attack_kind", "selective_drop_prob", "blackhole", "ground_truth_label")
    for name, src in sources.items():
        for token in banned:
            assert token not in src, f"controller-facing module {name} leaks attack truth via {token!r}"


def test_e0_risk_ucb_is_conservative_and_uncertainty_contracts_with_evidence():
    sec = SecurityRiskEstimator(3)
    initial_uncertainty = float(sec.risk_uncertainty[1])
    assert np.all(sec.risk_ucb >= sec.risk - 1e-12)
    for _ in range(100):
        sec.observe_forward(1, True, expected_pdr=0.95)
    assert float(sec.risk_uncertainty[1]) < initial_uncertainty
    assert float(sec.risk_ucb[1]) >= float(sec.risk[1])


def test_e0_attention_is_permutation_equivariant_and_critic_is_invariant():
    cfg = _fast_cluster_cfg()
    env = PacketRoutingEnv(cfg)
    b = env.builder
    torch.manual_seed(7)
    model = LocalAttentionActorCritic(
        b.context_dim, b.CANDIDATE_DIM, b.k, hidden=32, n_costs=env.n_costs
    ).eval()
    x = torch.randn(3, b.obs_dim)
    mask = torch.ones((3, b.k), dtype=torch.bool)
    perm = torch.tensor(list(reversed(range(b.k))), dtype=torch.long)

    with torch.no_grad():
        logits, value, cvalue = model(x, mask)
        ctx = x[:, : b.context_dim]
        cand = x[:, b.context_dim :].reshape(3, b.k, b.CANDIDATE_DIM)
        x2 = torch.cat([ctx, cand[:, perm].reshape(3, -1)], dim=1)
        mask2 = mask[:, perm]
        logits2, value2, cvalue2 = model(x2, mask2)

    assert torch.allclose(logits2, logits[:, perm], atol=1e-6, rtol=1e-6)
    assert torch.allclose(value2, value, atol=1e-6, rtol=1e-6)
    assert torch.allclose(cvalue2, cvalue, atol=1e-6, rtol=1e-6)


def test_e0_hierarchy_fallback_restores_physical_actions_if_topology_mask_is_empty():
    cfg = _fast_cluster_cfg()
    env = PacketRoutingEnv(cfg)
    source = _source_with_neighbors_outside_sink_range(env)
    assignment = np.full(env.net.n, -1, dtype=int)
    obs = env.builder.build(
        env.net,
        env.sec,
        env.qos,
        source,
        0,
        0.0,
        {source},
        chs=[],
        assignment=assignment,
    )
    assert obs.hierarchy_fallback
    assert obs.base_mask.any()


def test_e0_shield_fallback_never_manufactures_a_dead_end_when_base_actions_exist():
    cfg = _fast_cluster_cfg()
    cfg["rl"]["min_progress_m"] = 1e9
    cfg["rl"]["shield_enabled"] = True
    env = PacketRoutingEnv(cfg)
    source = _source_with_neighbors_outside_sink_range(env)
    obs = env.builder.build(
        env.net,
        env.sec,
        env.qos,
        source,
        0,
        0.0,
        {source},
        chs=env.chs,
        assignment=env.assignment,
    )
    assert obs.base_mask.any()
    assert obs.shield_fallback
    assert np.array_equal(obs.mask, obs.base_mask)


def test_e0_same_seed_replays_identical_packet_and_slow_dynamics_trace():
    cfg_a = _fast_cluster_cfg()
    cfg_b = _fast_cluster_cfg()
    env_a = PacketRoutingEnv(cfg_a)
    env_b = PacketRoutingEnv(cfg_b)

    trace_a = _trace(env_a, packets=12)
    trace_b = _trace(env_b, packets=12)

    assert trace_a == trace_b
    assert env_a.chs == env_b.chs
    assert np.array_equal(env_a.assignment, env_b.assignment)
    assert env_a.recluster_count == env_b.recluster_count
    assert np.allclose(env_a.qos.normalized_vector, env_b.qos.normalized_vector)


def test_e0_different_seed_changes_initial_network_realization():
    cfg_a = _fast_cluster_cfg()
    cfg_b = _fast_cluster_cfg()
    cfg_b["seed"] = int(cfg_a["seed"]) + 1
    env_a = PacketRoutingEnv(cfg_a)
    env_b = PacketRoutingEnv(cfg_b)
    assert not np.allclose(env_a.net.positions, env_b.net.positions)

