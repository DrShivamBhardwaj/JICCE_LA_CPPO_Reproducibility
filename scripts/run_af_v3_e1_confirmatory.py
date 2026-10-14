from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import torch
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wsn_sim.baselines import select_baseline_action
from wsn_sim.env import PacketRoutingEnv
from wsn_sim.evaluation import summarize_env_records
from wsn_sim.rl import MaskedActorCritic, ConstrainedPPO
from wsn_sim.training import CPPOTrainer

SEEDS = [
    13001, 13003, 13007, 13009, 13033, 13037, 13043, 13049, 13063, 13093,
    13099, 13103, 13109, 13121, 13127, 13147, 13151, 13159, 13163, 13171,
    13177, 13183, 13187, 13217, 13219, 13229, 13241, 13249, 13259, 13267,
]
ATTN = "af_v3_attention_cppp"
MLP = "af_v3_mlp_cppp"
BASELINES = ["static_energy_risk_etx", "periodic_roa_energy_risk_etx"]
PRIMARY_METRICS = ["class_0_mean_delay_ms", "class_0_delay_violation_rate"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def holm(pvals: list[float]) -> list[float]:
    p = np.asarray(pvals, dtype=float)
    order = np.argsort(p)
    out = np.empty(len(p), dtype=float)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (len(p) - rank) * p[idx])
        out[idx] = min(running, 1.0)
    return out.tolist()


def validate_primary_config(cfg: dict) -> None:
    assert cfg["clustering"]["enabled"] is False
    assert cfg["rl"]["cluster_aware_routing"] is False
    assert cfg["rl"]["cluster_hierarchy_mask"] is False
    assert cfg["rl"]["shield_enabled"] is False
    assert cfg["trigger"]["debt_enabled"] is False
    assert cfg["clustering"]["qos_conditioning"]["enabled"] is False
    assert cfg["clustering"]["qos_conditioning"]["gate_enabled"] is False
    assert float(cfg["trigger"]["weights"].get("qos_violation", 0.0)) == 0.0


def configure_policy(trainer: CPPOTrainer, arm: str) -> CPPOTrainer:
    if arm == ATTN:
        return trainer
    if arm != MLP:
        raise ValueError(arm)
    b = trainer.env.builder
    hidden = int(trainer.cfg.get("rl", {}).get("hidden", 96))
    model = MaskedActorCritic(b.obs_dim, b.k, hidden=hidden, n_costs=trainer.env.n_costs).to(trainer.device)
    trainer.model = model
    rcfg = trainer.cfg.get("rl", {})
    trainer.ppo = ConstrainedPPO(
        model,
        lr=float(rcfg.get("learning_rate", 3e-4)),
        clip=float(rcfg.get("ppo_clip", 0.2)),
        entropy_coef=float(rcfg.get("entropy_coef", 0.01)),
    )
    return trainer


def model_param_count(model: torch.nn.Module) -> int:
    return int(sum(p.numel() for p in model.parameters()))


def measure_actor_latency(model: torch.nn.Module, obs_dim: int, k: int) -> dict:
    model.eval()
    obs = torch.zeros((1, obs_dim), dtype=torch.float32)
    mask = torch.ones((1, k), dtype=torch.bool)
    with torch.no_grad():
        for _ in range(20):
            model.act(obs, mask, deterministic=True)
        times = []
        for _ in range(200):
            t0 = time.perf_counter_ns()
            model.act(obs, mask, deterministic=True)
            times.append((time.perf_counter_ns() - t0) / 1e6)
    a = np.asarray(times, dtype=float)
    return {
        "inference_latency_mean_ms": float(a.mean()),
        "inference_latency_median_ms": float(np.median(a)),
        "inference_latency_p95_ms": float(np.percentile(a, 95)),
    }


def train_eval_learning(base: dict, seed: int, arm: str, updates: int, train_eps: int, eval_eps: int):
    train_cfg = copy.deepcopy(base)
    train_cfg["seed"] = int(seed + 10000)
    torch.manual_seed(int(seed + 20000))
    np.random.seed(int(seed + 30000))
    trainer = configure_policy(CPPOTrainer(train_cfg), arm)
    logs = trainer.train(updates, train_eps, ppo_epochs=3)
    state = {k: v.detach().cpu().clone() for k, v in trainer.model.state_dict().items()}

    eval_cfg = copy.deepcopy(base)
    eval_cfg["seed"] = int(seed)
    torch.manual_seed(int(seed + 40000))
    np.random.seed(int(seed + 50000))
    evaluator = configure_policy(CPPOTrainer(eval_cfg), arm)
    evaluator.model.load_state_dict(state)
    _, infos, _, _ = evaluator.collect(eval_eps, deterministic=True)
    for ep, row in enumerate(infos):
        row["episode"] = ep
        row["policy"] = arm
        row["seed"] = seed
    summary = summarize_env_records(evaluator.env, infos, arm)
    summary["seed"] = seed
    summary["training_updates"] = updates
    summary["training_episodes_per_update"] = train_eps
    summary["ppo_epochs"] = 3
    summary["model_parameter_count"] = model_param_count(evaluator.model)
    summary.update(measure_actor_latency(evaluator.model, evaluator.env.builder.obs_dim, evaluator.env.builder.k))
    return infos, summary, logs


def baseline_reset(env: PacketRoutingEnv, periodic_packets: int | None):
    every = int(env.cfg.get("rl", {}).get("dynamic_update_every_packets", 8))
    do_slow = env.packet_index > 0 and env.packet_index % max(every, 1) == 0
    if do_slow:
        env._update_slow_state()
        if periodic_packets is not None and env.packet_index % int(periodic_packets) == 0:
            env._recluster(initial=False)
        old = env.slow_dynamics_enabled
        env.slow_dynamics_enabled = False
        try:
            return env.reset_packet()
        finally:
            env.slow_dynamics_enabled = old
    return env.reset_packet()


def eval_legacy_baseline(legacy_base: dict, seed: int, name: str, episodes: int, periodic_packets: int):
    cfg = copy.deepcopy(legacy_base)
    cfg["seed"] = int(seed)
    cfg.setdefault("clustering", {})["enabled"] = True
    cfg["clustering"]["qos_conditioning"]["enabled"] = False
    cfg["clustering"]["qos_conditioning"]["gate_enabled"] = False
    cfg["trigger"]["weights"]["qos_violation"] = 0.0
    env = PacketRoutingEnv(cfg)
    env.adaptive_reclustering_enabled = False
    period = int(periodic_packets) if name == "periodic_roa_energy_risk_etx" else None
    records = []
    for ep in range(int(episodes)):
        obs = baseline_reset(env, period)
        reward = 0.0
        while True:
            action = select_baseline_action(obs, env.builder, "energy_risk_etx")
            res = env.step(action)
            reward += float(res.reward)
            if res.done:
                row = dict(res.info)
                row.update({"episode": ep, "policy": name, "seed": seed, "episode_reward": reward})
                records.append(row)
                break
            obs = res.observation
            assert obs is not None
    summary = summarize_env_records(env, records, name)
    summary["seed"] = seed
    summary["periodic_packets"] = period
    summary["role"] = "secondary_AF-v1_continuity_baseline"
    return records, summary


def paired(df: pd.DataFrame, a: str, b: str, metric: str) -> pd.DataFrame:
    x = df.loc[df.policy == a, ["seed", metric]].rename(columns={metric: "a"})
    y = df.loc[df.policy == b, ["seed", metric]].rename(columns={metric: "b"})
    return x.merge(y, on="seed", how="inner").dropna().sort_values("seed")


def primary_analysis(df: pd.DataFrame) -> pd.DataFrame:
    rows, pvals = [], []
    for metric in PRIMARY_METRICS:
        z = paired(df, ATTN, MLP, metric)
        if len(z) != len(SEEDS):
            raise RuntimeError(f"{metric}: expected {len(SEEDS)} matched seeds, got {len(z)}")
        d = z.a.to_numpy(float) - z.b.to_numpy(float)
        n = len(d)
        mean = float(d.mean())
        sd = float(d.std(ddof=1))
        se = sd / np.sqrt(n)
        tcrit = float(stats.t.ppf(0.975, n - 1))
        tt = stats.ttest_rel(z.a, z.b)
        try:
            wp = float(stats.wilcoxon(z.a, z.b, zero_method="wilcox", alternative="two-sided").pvalue)
        except ValueError:
            wp = np.nan
        pvals.append(float(tt.pvalue))
        rows.append({
            "comparison": f"{ATTN}_minus_{MLP}", "metric": metric, "n": n,
            "mean_difference": mean, "ci95_low": mean - tcrit * se, "ci95_high": mean + tcrit * se,
            "paired_t_p_value": float(tt.pvalue), "wilcoxon_p_value": wp,
            "cohen_dz": float(mean / sd) if sd > 0 else 0.0,
            "direction_favorable": bool(mean < 0.0),
        })
    adj = holm(pvals)
    for row, p in zip(rows, adj):
        row["holm_adjusted_p"] = float(p)
        row["holm_significant_0_05"] = bool(p < 0.05)
    return pd.DataFrame(rows)


def guardrails(df: pd.DataFrame) -> dict:
    z = paired(df, ATTN, MLP, "delivery_rate")
    if len(z) != len(SEEDS):
        raise RuntimeError("delivery guardrail missing matched seeds")
    d = z.a.to_numpy(float) - z.b.to_numpy(float)
    se = float(d.std(ddof=1) / np.sqrt(len(d)))
    lower = float(d.mean() - stats.t.ppf(0.95, len(d) - 1) * se)

    e = paired(df, ATTN, MLP, "energy_per_delivered_packet_j")
    if len(e) != len(SEEDS) or (e.a <= 0).any() or (e.b <= 0).any():
        raise RuntimeError("invalid energy guardrail data")
    lr = np.log(e.a.to_numpy(float) / e.b.to_numpy(float))
    se_lr = float(lr.std(ddof=1) / np.sqrt(len(lr)))
    upper = float(np.exp(lr.mean() + stats.t.ppf(0.95, len(lr) - 1) * se_lr))
    ratio = float(np.exp(lr.mean()))
    return {
        "delivery": {"margin_absolute": -0.01, "mean_difference": float(d.mean()), "one_sided_95_lower_bound": lower, "pass": bool(lower > -0.01)},
        "energy": {"margin_ratio": 1.05, "geometric_mean_ratio": ratio, "one_sided_95_upper_ratio": upper, "pass": bool(upper <= 1.05)},
    }


def secondary(df: pd.DataFrame) -> pd.DataFrame:
    metrics = [
        "delivery_rate", "class_0_delivery_rate", "mean_delivered_delay_ms", "class_0_mean_delay_ms",
        "class_0_delay_violation_rate", "class_0_loss_rate", "energy_consumed_j",
        "energy_per_delivered_packet_j", "security_drop_rate", "link_drop_rate", "mean_episode_reward",
    ]
    rows = []
    for comp in [MLP] + BASELINES:
        for metric in metrics:
            if metric not in df.columns:
                continue
            z = paired(df, ATTN, comp, metric)
            if len(z) < 2:
                continue
            d = z.a.to_numpy(float) - z.b.to_numpy(float)
            sd = float(d.std(ddof=1)); se = sd / np.sqrt(len(d)); tcrit = float(stats.t.ppf(0.975, len(d)-1))
            tt = stats.ttest_rel(z.a, z.b)
            rows.append({"comparison": f"{ATTN}_minus_{comp}", "metric": metric, "n": len(d),
                         "mean_difference": float(d.mean()), "ci95_low": float(d.mean()-tcrit*se), "ci95_high": float(d.mean()+tcrit*se),
                         "paired_t_p_value_unadjusted": float(tt.pvalue), "role": "secondary_descriptive"})
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(ROOT / "configs/af_v3_final.yaml"))
    ap.add_argument("--legacy-baseline-config", default=str(ROOT / "configs/af_v1_primary.yaml"))
    ap.add_argument("--updates", type=int, default=8)
    ap.add_argument("--train-eps", type=int, default=50)
    ap.add_argument("--eval-eps", type=int, default=240)
    ap.add_argument("--periodic-packets", type=int, default=12)
    ap.add_argument("--out", default=str(ROOT / "results/af_v3_e1_confirmatory"))
    args = ap.parse_args()

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    config_path = Path(args.config)
    protocol_path = ROOT / "experiments/AF_V3_E1_CONFIRMATORY_PROTOCOL.md"
    e0_path = ROOT / "results/af_v3_e0_qualification/e0_record.json"
    with config_path.open(encoding="utf-8") as f: base = yaml.safe_load(f)
    with Path(args.legacy_baseline_config).open(encoding="utf-8") as f: legacy = yaml.safe_load(f)
    validate_primary_config(base)
    e0 = json.loads(e0_path.read_text(encoding="utf-8"))
    if e0["status"] != "PASS": raise RuntimeError("AF-v3 E0 not qualified")

    summaries, episodes, train_rows = [], [], []
    for seed in SEEDS:
        for arm in [ATTN, MLP]:
            print(f"AF-v3 E1 seed={seed} arm={arm}", flush=True)
            records, summary, logs = train_eval_learning(base, seed, arm, args.updates, args.train_eps, args.eval_eps)
            summaries.append(summary); episodes.extend(records)
            for row in logs:
                r = dict(row); r["seed"] = seed; r["policy"] = arm; train_rows.append(r)
        for b in BASELINES:
            print(f"AF-v3 E1 seed={seed} baseline={b}", flush=True)
            records, summary = eval_legacy_baseline(legacy, seed, b, args.eval_eps, args.periodic_packets)
            summaries.append(summary); episodes.extend(records)

    seed_df = pd.DataFrame(summaries)
    if len(seed_df) != len(SEEDS) * 4 or seed_df["seed"].nunique() != len(SEEDS):
        raise RuntimeError("incomplete seed-policy matrix")
    seed_df.to_csv(out / "seed_summary.csv", index=False)
    pd.DataFrame(episodes).to_csv(out / "episode_metrics.csv", index=False)
    pd.DataFrame(train_rows).to_csv(out / "training_log.csv", index=False)

    p = primary_analysis(seed_df); p.to_csv(out / "primary_analysis.csv", index=False)
    g = guardrails(seed_df); (out / "guardrails.json").write_text(json.dumps(g, indent=2), encoding="utf-8")
    s = secondary(seed_df); s.to_csv(out / "secondary_comparisons.csv", index=False)
    strict = bool(p["direction_favorable"].all() and p["holm_significant_0_05"].all() and g["delivery"]["pass"] and g["energy"]["pass"])
    decision = {
        "stage": "AF-v3-E1", "freeze_id": "AF-2026-09-08-v3",
        "primary_comparison": f"{ATTN} vs {MLP}", "n_matched_seeds": len(SEEDS),
        "co_primary_endpoints": PRIMARY_METRICS, "multiplicity": "Holm family-wise alpha=0.05",
        "delivery_noninferiority_margin": -0.01, "energy_noninferiority_ratio_margin": 1.05,
        "strict_pass": strict, "verdict": "PASS_AF_V3_E1" if strict else "FAIL_OR_INCONCLUSIVE_AF_V3_E1",
        "protocol_deviation": False,
    }
    (out / "decision.json").write_text(json.dumps(decision, indent=2), encoding="utf-8")
    snapshot = {
        "freeze_id": "AF-2026-09-08-v3", "seeds": SEEDS, "updates": args.updates,
        "train_episodes_per_update": args.train_eps, "ppo_epochs": 3, "eval_episodes": args.eval_eps,
        "training_env_seed_offset": 10000, "torch_training_seed_offset": 20000, "numpy_training_seed_offset": 30000,
        "evaluation_env_seed_offset": 0, "torch_evaluation_seed_offset": 40000, "numpy_evaluation_seed_offset": 50000,
        "primary_config": str(config_path), "primary_config_sha256": sha256(config_path),
        "protocol": str(protocol_path.relative_to(ROOT)), "protocol_sha256": sha256(protocol_path),
        "e0_record": e0, "legacy_baseline_config": str(Path(args.legacy_baseline_config)),
        "legacy_baselines_role": "secondary continuity only; excluded from strict decision",
        "technical_rerun_note": "Same frozen protocol and seed vault; rerun only because the first attempt failed after all seed computations while writing provenance paths.",
    }
    (out / "protocol_snapshot.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(json.dumps(decision, indent=2), flush=True)


if __name__ == "__main__":
    main()

