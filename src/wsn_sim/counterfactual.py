from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import torch

from .env import PacketRoutingEnv


@dataclass
class CounterfactualBranchResult:
    policy: str
    metrics: dict
    topology: dict


def _model_device(model: torch.nn.Module) -> torch.device:
    try:
        return next(model.parameters()).device
    except StopIteration:
        return torch.device("cpu")


def _rollout_fixed_schedule(
    env: PacketRoutingEnv,
    model: torch.nn.Module,
    sources: np.ndarray,
    classes: np.ndarray,
) -> dict:
    """Evaluate a branch on a fixed packet/class schedule with slow dynamics frozen."""
    if len(sources) != len(classes):
        raise ValueError("sources and classes must have the same length")
    device = _model_device(model)
    records: list[dict] = []
    start_energy = float(np.sum(env.net.energy))
    start_max_debt = float(env.qos.max_normalized_debt)
    start_delay_debt = env.qos.normalized_delay_debt.copy()
    start_loss_debt = env.qos.normalized_loss_debt.copy()

    for source, traffic_class in zip(sources, classes):
        source = int(source)
        traffic_class = int(traffic_class)
        if source < 0 or source >= env.net.n or not env.net.alive[source]:
            alive = np.flatnonzero(env.net.alive)
            if not len(alive):
                break
            source = int(alive[0])
        obs = env.reset_packet(source=source, traffic_class=traffic_class)
        ep_reward = 0.0
        while True:
            ot = torch.as_tensor(obs.flat_obs, dtype=torch.float32, device=device).unsqueeze(0)
            mt = torch.as_tensor(obs.mask, dtype=torch.bool, device=device).unsqueeze(0)
            with torch.no_grad():
                action, _, _, _ = model.act(ot, mt, deterministic=True)
            res = env.step(int(action.item()))
            ep_reward += float(res.reward)
            if res.done:
                row = dict(res.info)
                row["episode_reward"] = float(ep_reward)
                records.append(row)
                break
            obs = res.observation
            assert obs is not None

    delivered = np.asarray([bool(r.get("delivered", False)) for r in records], dtype=bool)
    delays = np.asarray([float(r.get("delay_s", np.nan)) for r in records], dtype=float)
    classes_arr = np.asarray([int(r.get("traffic_class", -1)) for r in records], dtype=int)
    class0 = classes_arr == 0
    class0_delivered = class0 & delivered
    class0_deadline = float(env.qos.deadlines_s[0]) if env.qos.n_classes else np.inf
    class0_viol = np.asarray([
        bool(c == 0 and ((not d) or (not np.isfinite(delay)) or delay > class0_deadline))
        for c, d, delay in zip(classes_arr, delivered, delays)
    ], dtype=bool)
    end_energy = float(np.sum(env.net.energy))

    metrics = {
        "episodes": int(len(records)),
        "delivery_rate": float(delivered.mean()) if len(delivered) else np.nan,
        "mean_delivered_delay_ms": 1000.0 * float(np.nanmean(delays[delivered])) if delivered.any() else np.nan,
        "class_0_packet_count": int(class0.sum()),
        "class_0_delivery_rate": float(delivered[class0].mean()) if class0.any() else np.nan,
        "class_0_mean_delay_ms": 1000.0 * float(np.nanmean(delays[class0_delivered])) if class0_delivered.any() else np.nan,
        "class_0_delay_violation_rate": float(class0_viol[class0].mean()) if class0.any() else np.nan,
        "energy_consumed_j": float(start_energy - end_energy),
        "start_max_qos_debt": start_max_debt,
        "end_max_qos_debt": float(env.qos.max_normalized_debt),
        "delta_max_qos_debt": float(env.qos.max_normalized_debt - start_max_debt),
        "shield_fallback_ewma_end": float(env.shield_fallback_ewma),
    }
    for c in range(env.qos.n_classes):
        metrics[f"class_{c}_delta_delay_debt"] = float(env.qos.normalized_delay_debt[c] - start_delay_debt[c])
        metrics[f"class_{c}_delta_loss_debt"] = float(env.qos.normalized_loss_debt[c] - start_loss_debt[c])
    return metrics


def _topology_actionability(
    trigger_env: PacketRoutingEnv,
    conditioned_env: PacketRoutingEnv,
    source: int,
    traffic_class: int,
) -> dict:
    """Check whether changing only CH topology can alter the routing observation/action set."""
    visited = {int(source)}
    a = trigger_env.builder.build(trigger_env.net, trigger_env.sec, trigger_env.qos, int(source), int(traffic_class), 0.0, visited)
    b = conditioned_env.builder.build(conditioned_env.net, conditioned_env.sec, conditioned_env.qos, int(source), int(traffic_class), 0.0, visited)
    flat_delta = float(np.max(np.abs(a.flat_obs - b.flat_obs))) if len(a.flat_obs) else 0.0
    mask_changed = bool(np.any(a.mask != b.mask))
    base_mask_changed = bool(np.any(a.base_mask != b.base_mask))
    node_ids_changed = bool(np.any(a.node_ids != b.node_ids))
    return {
        "routing_observation_linf_delta": flat_delta,
        "routing_mask_changed": mask_changed,
        "routing_base_mask_changed": base_mask_changed,
        "routing_candidate_ids_changed": node_ids_changed,
        "topology_actionable_to_router": bool(flat_delta > 1e-10 or mask_changed or base_mask_changed or node_ids_changed),
    }


def evaluate_counterfactual_event(
    snapshot: PacketRoutingEnv,
    state: dict,
    model: torch.nn.Module,
    horizon_packets: int,
    roa_seed: int,
    schedule_seed: int,
) -> dict:
    """Evaluate trigger-only vs always-conditioned topology from one decision state.

    Both branches originate from the same post-dynamic-update, pre-recluster
    simulator snapshot. They share a fixed packet source/class schedule and an
    isolated ROA seed. Slow dynamics and additional re-clustering are disabled
    over the short horizon so the contrast is local to the current topology
    intervention rather than a sequence of later interventions.
    """
    horizon_packets = int(horizon_packets)
    if horizon_packets <= 0:
        raise ValueError("horizon_packets must be positive")
    alive = np.flatnonzero(snapshot.net.alive)
    if not len(alive):
        raise RuntimeError("counterfactual snapshot has no alive nodes")
    probs = np.asarray(snapshot.cfg["traffic"]["class_probs"], dtype=float)
    probs /= probs.sum()
    schedule_rng = np.random.default_rng(int(schedule_seed))
    sources = schedule_rng.choice(alive, size=horizon_packets, replace=True).astype(int)
    classes = schedule_rng.choice(len(probs), size=horizon_packets, replace=True, p=probs).astype(int)

    branch_envs: dict[str, PacketRoutingEnv] = {}
    branch_topologies: dict[str, dict] = {}
    for name, conditioned in (("trigger_only", False), ("conditioned", True)):
        env = snapshot.fork_for_counterfactual()
        env.counterfactual_capture_enabled = False
        env.slow_dynamics_enabled = False
        env.adaptive_reclustering_enabled = False
        branch_topologies[name] = env.apply_counterfactual_recluster(conditioned=conditioned, roa_seed=int(roa_seed))
        branch_envs[name] = env

    first_source = int(sources[0])
    first_class = int(classes[0])
    actionability = _topology_actionability(
        trigger_env=branch_envs["trigger_only"],
        conditioned_env=branch_envs["conditioned"],
        source=first_source,
        traffic_class=first_class,
    )

    branches: dict[str, CounterfactualBranchResult] = {}
    for name in ("trigger_only", "conditioned"):
        metrics = _rollout_fixed_schedule(branch_envs[name], model, sources, classes)
        branches[name] = CounterfactualBranchResult(name, metrics, branch_topologies[name])

    trigger = branches["trigger_only"]
    conditioned = branches["conditioned"]
    t_chs = set(trigger.topology["chs"])
    c_chs = set(conditioned.topology["chs"])
    ch_jaccard = len(t_chs & c_chs) / max(len(t_chs | c_chs), 1)
    assignment_change = float(np.mean(trigger.topology["assignment"] != conditioned.topology["assignment"]))

    row = dict(state)
    row.update({
        "horizon_packets": horizon_packets,
        "roa_seed": int(roa_seed),
        "schedule_seed": int(schedule_seed),
        "branch_ch_jaccard": float(ch_jaccard),
        "branch_assignment_change_fraction": assignment_change,
        **actionability,
    })
    for prefix, result in (("trigger", trigger), ("conditioned", conditioned)):
        for k, v in result.metrics.items():
            row[f"{prefix}_{k}"] = v
        row[f"{prefix}_topology_churn"] = float(result.topology["churn"])
        row[f"{prefix}_topology_fitness"] = float(result.topology["fitness"])
        row[f"{prefix}_qos_topology_penalty"] = float(result.topology["qos_topology_penalty"])

    # Conditioned minus trigger-only: negative is favorable for delay, violation,
    # energy and debt; positive is favorable for delivery.
    for metric in (
        "delivery_rate",
        "mean_delivered_delay_ms",
        "class_0_delivery_rate",
        "class_0_mean_delay_ms",
        "class_0_delay_violation_rate",
        "energy_consumed_j",
        "end_max_qos_debt",
        "delta_max_qos_debt",
    ):
        a = conditioned.metrics.get(metric, np.nan)
        b = trigger.metrics.get(metric, np.nan)
        row[f"delta_{metric}_conditioned_minus_trigger"] = float(a - b) if np.isfinite(a) and np.isfinite(b) else np.nan
    for c in range(snapshot.qos.n_classes):
        for debt_kind in ("delay_debt", "loss_debt"):
            metric = f"class_{c}_delta_{debt_kind}"
            a = conditioned.metrics.get(metric, np.nan)
            b = trigger.metrics.get(metric, np.nan)
            row[f"delta_{metric}_conditioned_minus_trigger"] = float(a - b) if np.isfinite(a) and np.isfinite(b) else np.nan
    return row

