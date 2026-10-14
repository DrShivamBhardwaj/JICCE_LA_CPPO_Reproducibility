from __future__ import annotations
import numpy as np
from .env import PacketRoutingEnv
from .baselines import select_baseline_action


def summarize_env_records(env: PacketRoutingEnv, records: list[dict], policy: str) -> dict:
    delivered = np.asarray([bool(r.get("delivered", False)) for r in records], dtype=bool)
    delays = np.asarray([float(r.get("delay_s", np.nan)) for r in records], dtype=float)
    reasons = np.asarray([str(r.get("reason", "")) for r in records], dtype=object)
    energy_consumed = float(env.net.n * env.net.e0 - np.sum(env.net.energy))
    n_delivered = int(delivered.sum())
    rates = env.qos.empirical_rates()
    mean_debt = env.qos.mean_normalized_vector
    adaptive = max(int(env.recluster_count) - 1, 0)
    gate_opportunities = int(getattr(env, "qos_gate_recluster_opportunities", 0))
    gate_activations = int(getattr(env, "qos_conditioned_recluster_count", 0))
    summary = {
        "policy": policy,
        "episodes": len(records),
        "delivery_rate": float(delivered.mean()) if len(delivered) else np.nan,
        "mean_delivered_delay_ms": 1000.0 * float(np.nanmean(delays[delivered])) if delivered.any() else np.nan,
        "p95_delivered_delay_ms": 1000.0 * float(np.nanpercentile(delays[delivered], 95)) if delivered.any() else np.nan,
        "mean_episode_reward": float(np.mean([r.get("episode_reward", np.nan) for r in records])) if records else np.nan,
        "recluster_count": int(env.recluster_count),
        "adaptive_recluster_events": adaptive,
        "qos_gate_recluster_opportunities": gate_opportunities,
        "qos_conditioned_recluster_events": gate_activations,
        "qos_gate_activation_fraction": gate_activations / max(gate_opportunities, 1) if gate_opportunities > 0 else 0.0,
        "max_qos_debt": float(env.qos.max_normalized_debt),
        "final_max_qos_debt": float(env.qos.max_normalized_debt),
        "mean_max_qos_debt": float(env.qos.mean_max_normalized_debt),
        "peak_max_qos_debt": float(env.qos.peak_max_normalized_debt),
        "energy_consumed_j": energy_consumed,
        "energy_per_delivered_packet_j": energy_consumed / max(n_delivered, 1),
        "security_drop_rate": float(np.mean(reasons == "security_drop")) if len(reasons) else np.nan,
        "link_drop_rate": float(np.mean(reasons == "link_drop")) if len(reasons) else np.nan,
        "shield_fallback_rate": float(np.mean([bool(r.get("shield_fallback", False)) for r in records])) if records else np.nan,
        "last_qos_topology_penalty": float(env.last_cluster_info.get("qos_topology_penalty", 0.0)),
        "last_qos_gate_active": bool(env.last_cluster_info.get("qos_gate_active", False)),
        "last_qos_gate_signal": float(env.last_cluster_info.get("qos_gate_signal", 0.0)),
        "last_qos_gate_threshold": float(env.last_cluster_info.get("qos_gate_threshold", np.nan)),
    }
    for c in range(env.qos.n_classes):
        cls = np.asarray([int(r.get("traffic_class", -1)) == c for r in records], dtype=bool)
        summary[f"class_{c}_final_delay_debt"] = float(env.qos.normalized_delay_debt[c])
        summary[f"class_{c}_final_loss_debt"] = float(env.qos.normalized_loss_debt[c])
        summary[f"class_{c}_mean_delay_debt"] = float(mean_debt[2 * c])
        summary[f"class_{c}_mean_loss_debt"] = float(mean_debt[2 * c + 1])
        if cls.any():
            summary[f"class_{c}_delivery_rate"] = float(delivered[cls].mean())
            d = delays[cls & delivered]
            summary[f"class_{c}_mean_delay_ms"] = 1000.0 * float(np.nanmean(d)) if len(d) else np.nan
            summary[f"class_{c}_delay_violation_rate"] = float(rates["delay_violation_rate"][c])
            summary[f"class_{c}_loss_rate"] = float(rates["loss_rate"][c])
    return summary


def evaluate_baseline(cfg: dict, policy: str, episodes: int) -> tuple[list[dict], dict]:
    """Evaluate a baseline in the same persistent packet environment as CPPO."""
    env = PacketRoutingEnv(cfg)
    records: list[dict] = []
    for ep in range(int(episodes)):
        obs = env.reset_packet()
        reward = 0.0
        while True:
            action = select_baseline_action(obs, env.builder, policy)
            res = env.step(action)
            reward += float(res.reward)
            if res.done:
                row = dict(res.info)
                row.update({
                    "episode": ep,
                    "policy": policy,
                    "episode_reward": reward,
                    "recluster_count": env.recluster_count,
                    "max_qos_debt": env.qos.max_normalized_debt,
                })
                records.append(row)
                break
            obs = res.observation
            assert obs is not None
    return records, summarize_env_records(env, records, policy)

