from pathlib import Path
import copy
import inspect
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wsn_sim.config import load_config
from wsn_sim.env import PacketRoutingEnv
from wsn_sim.network import WSNNetwork
from wsn_sim.observation import CrossLayerObservationBuilder
from wsn_sim.rl import LocalAttentionActorCritic, ConstrainedPPO
from wsn_sim.security import SecurityRiskEstimator
from wsn_sim.training import CPPOTrainer


def _cfg():
    return load_config(ROOT / "configs" / "af_v3_final.yaml")


def _trace(env: PacketRoutingEnv, packets: int = 12):
    out = []
    for _ in range(packets):
        obs = env.reset_packet()
        packet = [(int(env.source), int(env.traffic_class))]
        for _hop in range(env.cfg["simulation"]["max_hops"] + 2):
            valid = np.flatnonzero(obs.mask)
            assert len(valid) > 0
            slot = int(valid[0])
            target = int(obs.node_ids[slot])
            res = env.step(slot)
            packet.append((target, round(float(res.reward), 12), tuple(np.round(res.costs.astype(float), 12)), bool(res.done), str(res.info.get("reason", ""))))
            if res.done:
                break
            obs = res.observation
            assert obs is not None
        out.append(tuple(packet))
    return tuple(out)


def test_af_v3_exact_primary_flags():
    cfg = _cfg()
    assert cfg["clustering"]["enabled"] is False
    assert cfg["rl"]["cluster_aware_routing"] is False
    assert cfg["rl"]["cluster_hierarchy_mask"] is False
    assert cfg["rl"]["shield_enabled"] is False
    assert cfg["trigger"]["debt_enabled"] is False
    assert cfg["clustering"]["qos_conditioning"]["enabled"] is False
    assert cfg["clustering"]["qos_conditioning"]["gate_enabled"] is False


def test_af_v3_no_roa_execution_even_through_dynamic_updates(monkeypatch):
    import wsn_sim.env as env_mod

    def bomb(*args, **kwargs):
        raise AssertionError("ROA/clustering execution is prohibited in AF-v3")

    monkeypatch.setattr(env_mod, "select_cluster_heads", bomb)
    env = PacketRoutingEnv(_cfg())
    assert env.chs == []
    assert np.all(env.assignment == -1)
    for _ in range(14):
        obs = env.reset_packet()
        valid = np.flatnonzero(obs.mask)
        assert len(valid) > 0
        env.step(int(valid[0]))
    assert env.recluster_count == 0


def test_af_v3_no_roa_rng_consumption_at_initialization():
    cfg = _cfg()
    ref = WSNNetwork(copy.deepcopy(cfg))
    env = PacketRoutingEnv(copy.deepcopy(cfg))
    assert ref.rng.bit_generator.state == env.net.rng.bit_generator.state
    assert ref.radio.rng.bit_generator.state == env.net.radio.rng.bit_generator.state


def test_af_v3_no_cluster_state_and_base_candidate_shape():
    env = PacketRoutingEnv(_cfg())
    assert env.chs == []
    assert np.all(env.assignment == -1)
    assert env.recluster_count == 0
    assert env.builder.CANDIDATE_DIM == 10
    assert env.builder.cluster_context_dim == 0


def test_af_v3_action_mask_is_only_base_physical_mask():
    env = PacketRoutingEnv(_cfg())
    seen = 0
    for _ in range(20):
        obs = env.reset_packet()
        assert np.array_equal(obs.mask, obs.base_mask)
        assert obs.shield_fallback is False
        assert obs.hierarchy_fallback is False
        seen += int(obs.base_mask.any())
    assert seen > 0


def test_af_v3_attention_equivariance_and_critic_invariance():
    env = PacketRoutingEnv(_cfg())
    b = env.builder
    torch.manual_seed(71)
    model = LocalAttentionActorCritic(b.context_dim, b.CANDIDATE_DIM, b.k, hidden=32, n_costs=env.n_costs).eval()
    x = torch.randn(4, b.obs_dim)
    mask = torch.ones((4, b.k), dtype=torch.bool)
    perm = torch.tensor([3, 0, 7, 2, 6, 1, 5, 4], dtype=torch.long)
    with torch.no_grad():
        logits, value, cvalue = model(x, mask)
        ctx = x[:, :b.context_dim]
        cand = x[:, b.context_dim:].reshape(4, b.k, b.CANDIDATE_DIM)
        x2 = torch.cat([ctx, cand[:, perm].reshape(4, -1)], dim=1)
        logits2, value2, cvalue2 = model(x2, mask[:, perm])
    assert torch.allclose(logits2, logits[:, perm], atol=1e-6, rtol=1e-6)
    assert torch.allclose(value2, value, atol=1e-6, rtol=1e-6)
    assert torch.allclose(cvalue2, cvalue, atol=1e-6, rtol=1e-6)


def test_af_v3_controller_label_isolation():
    sources = {
        "security": inspect.getsource(SecurityRiskEstimator),
        "observation": inspect.getsource(CrossLayerObservationBuilder),
        "attention_policy": inspect.getsource(LocalAttentionActorCritic),
        "cppo": inspect.getsource(ConstrainedPPO),
        "trainer": inspect.getsource(CPPOTrainer),
    }
    banned = ("net.malicious", ".attack_kind", "ground_truth_label", "blackhole", "selective_drop_prob")
    for name, src in sources.items():
        for token in banned:
            assert token not in src, f"{name} leaks evaluator-only attack truth via {token!r}"


def test_af_v3_security_posterior_sanity():
    sec = SecurityRiskEstimator(4)
    u0 = float(sec.risk_uncertainty[2])
    assert np.all(sec.risk_ucb >= sec.risk - 1e-12)
    for _ in range(120):
        sec.observe_forward(2, True, expected_pdr=0.95)
    assert float(sec.risk_uncertainty[2]) < u0
    assert float(sec.risk_ucb[2]) >= float(sec.risk[2])


def test_af_v3_cppo_has_six_costs_and_active_lagrangian():
    cfg = _cfg()
    trainer = CPPOTrainer(cfg)
    assert trainer.env.n_costs == 6
    assert len(trainer.lagrange.budgets) == 6
    assert float(cfg["rl"]["lagrange_lr"]) > 0.0
    assert trainer.model.cost_values.out_features == 6


def test_af_v3_same_seed_replay_and_different_seed_divergence():
    cfg_a = _cfg()
    cfg_b = _cfg()
    assert _trace(PacketRoutingEnv(cfg_a), 12) == _trace(PacketRoutingEnv(cfg_b), 12)
    cfg_c = _cfg()
    cfg_c["seed"] = int(cfg_c["seed"]) + 1
    env_a = PacketRoutingEnv(_cfg())
    env_c = PacketRoutingEnv(cfg_c)
    assert not np.allclose(env_a.net.positions, env_c.net.positions)


def test_af_v3_legacy_missing_enabled_defaults_to_clustering_on():
    cfg = load_config(ROOT / "configs" / "af_v1_primary.yaml")
    cfg = copy.deepcopy(cfg)
    cfg["clustering"].pop("enabled", None)
    cfg["clustering"]["roa_population"] = 4
    cfg["clustering"]["roa_iterations"] = 1
    env = PacketRoutingEnv(cfg)
    assert env.clustering_enabled is True
    assert env.recluster_count >= 1
    assert len(env.chs) > 0

