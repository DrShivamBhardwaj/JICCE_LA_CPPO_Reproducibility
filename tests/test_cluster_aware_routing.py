from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wsn_sim.config import load_config
from wsn_sim.env import PacketRoutingEnv


def _source_with_neighbors(env: PacketRoutingEnv) -> int:
    for i in np.flatnonzero(env.net.alive):
        if len(env.net.feasible_neighbors(int(i))) >= 2:
            return int(i)
    raise AssertionError("test topology has no node with two feasible neighbors")


def test_legacy_router_is_topology_invariant():
    cfg = load_config(ROOT / "configs" / "stage4f_frozen.yaml")
    cfg["clustering"]["roa_population"] = 4
    cfg["clustering"]["roa_iterations"] = 2
    env = PacketRoutingEnv(cfg)
    assert not env.builder.cluster_aware
    source = _source_with_neighbors(env)
    cls = 0
    visited = {source}
    a = env.builder.build(env.net, env.sec, env.qos, source, cls, 0.0, visited, chs=env.chs, assignment=env.assignment)

    neighbors = env.net.feasible_neighbors(source)
    alt_assignment = env.assignment.copy()
    alt_head = int(neighbors[0])
    alt_assignment[source] = alt_head
    b = env.builder.build(env.net, env.sec, env.qos, source, cls, 0.0, visited, chs=[alt_head], assignment=alt_assignment)

    assert np.allclose(a.flat_obs, b.flat_obs)
    assert np.array_equal(a.mask, b.mask)
    assert np.array_equal(a.base_mask, b.base_mask)
    assert np.array_equal(a.node_ids, b.node_ids)


def test_cluster_aware_router_observes_topology_change():
    cfg = load_config(ROOT / "configs" / "stage4g1_5_clusteraware.yaml")
    cfg["clustering"]["roa_population"] = 4
    cfg["clustering"]["roa_iterations"] = 2
    env = PacketRoutingEnv(cfg)
    assert env.builder.cluster_aware
    assert env.builder.CANDIDATE_DIM == env.builder.BASE_CANDIDATE_DIM + env.builder.CLUSTER_FEATURE_DIM
    assert hasattr(env.net, "active_chs")
    assert hasattr(env.net, "active_assignment")

    source = _source_with_neighbors(env)
    cls = 0
    visited = {source}
    a = env.builder.build(env.net, env.sec, env.qos, source, cls, 0.0, visited, chs=env.chs, assignment=env.assignment)

    neighbors = env.net.feasible_neighbors(source)
    alt_head = int(neighbors[0])
    alt_assignment = env.assignment.copy()
    alt_assignment[source] = alt_head
    alt_assignment[alt_head] = alt_head
    b = env.builder.build(env.net, env.sec, env.qos, source, cls, 0.0, visited, chs=[alt_head], assignment=alt_assignment)

    assert a.flat_obs.shape == b.flat_obs.shape
    assert float(np.max(np.abs(a.flat_obs - b.flat_obs))) > 1e-8 or not np.array_equal(a.base_mask, b.base_mask) or set(a.node_ids[a.node_ids != -2]) != set(b.node_ids[b.node_ids != -2])


def test_cluster_hierarchy_never_creates_empty_action_set_when_physical_neighbors_exist():
    cfg = load_config(ROOT / "configs" / "stage4g1_5_clusteraware.yaml")
    cfg["clustering"]["roa_population"] = 4
    cfg["clustering"]["roa_iterations"] = 2
    env = PacketRoutingEnv(cfg)
    source = _source_with_neighbors(env)
    obs = env.builder.build(env.net, env.sec, env.qos, source, 0, 0.0, {source}, chs=env.chs, assignment=env.assignment)
    assert obs.base_mask.any()
    assert obs.mask.any()

