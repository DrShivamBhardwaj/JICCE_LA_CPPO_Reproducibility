"""New validation study; never overwrites the historical AF-v3 evidence."""
import copy
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import torch
import yaml
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from wsn_sim.training import CPPOTrainer
from wsn_sim.rl import MaskedActorCritic, ConstrainedPPO
from wsn_sim.evaluation import summarize_env_records

SEEDS = list(range(41001, 41031))
ARMS = ['attention', 'capacity_mlp', 'attention_no_risk', 'attention_feedback80']

def configure(cfg, arm):
    cfg = copy.deepcopy(cfg)
    cfg['validation'] = {'split_streams': True, 'risk_enabled': arm != 'attention_no_risk',
                         'feedback_probability': .8 if arm == 'attention_feedback80' else 1.}
    t = CPPOTrainer(cfg)
    if arm == 'capacity_mlp':
        b = t.env.builder
        target = sum(p.numel() for p in t.model.parameters())
        width = min(range(32, 400), key=lambda h: abs(sum(p.numel() for p in MaskedActorCritic(b.obs_dim, b.k, h, t.env.n_costs).parameters()) - target))
        t.model = MaskedActorCritic(b.obs_dim, b.k, width, t.env.n_costs)
        rc = cfg['rl']
        t.ppo = ConstrainedPPO(t.model, lr=rc['learning_rate'], clip=rc['ppo_clip'], entropy_coef=rc['entropy_coef'])
    return t

def evaluate(base, state, seed, arm, setting):
    cfg = copy.deepcopy(base)
    cfg['seed'] = seed
    if setting == 'size200':
        cfg['network']['n_nodes'] = 200
    elif setting == 'attack10':
        cfg['attack']['malicious_ratio'] = .1
    elif setting == 'attack40':
        cfg['attack']['malicious_ratio'] = .4
    torch.manual_seed(seed + 40000)
    t = configure(cfg, arm)
    t.model.load_state_dict(state)
    _, records, _, _ = t.collect(240, deterministic=True)
    summary = summarize_env_records(t.env, records, arm)
    summary.update(seed=seed, setting=setting, model_parameter_count=sum(p.numel() for p in t.model.parameters()))
    for i, x in enumerate(records):
        x.update(seed=seed, setting=setting, policy=arm, episode=i)
    return summary, records

def analyse(df):
    rows = []
    for setting in sorted(df.setting.unique()):
        sub = df[df.setting == setting]
        for other in ARMS[1:]:
            a = sub[sub.policy == 'attention'].set_index('seed')
            b = sub[sub.policy == other].set_index('seed')
            for metric in ['class_0_mean_delay_ms', 'class_0_delay_violation_rate', 'delivery_rate', 'energy_per_delivered_packet_j']:
                x = (a[metric] - b[metric]).dropna()
                ci = stats.t.interval(.95, len(x)-1, loc=x.mean(), scale=stats.sem(x))
                rows.append(dict(setting=setting, comparison='attention_minus_'+other, metric=metric,
                                 n=len(x), mean_difference=x.mean(), ci95_low=ci[0], ci95_high=ci[1],
                                 paired_t_p=stats.ttest_1samp(x, 0).pvalue))
    out = pd.DataFrame(rows)
    # One family covers all nominal-setting comparator x co-primary tests.
    family = out[(out.setting == 'nominal') & out.metric.isin(['class_0_mean_delay_ms', 'class_0_delay_violation_rate'])]
    order = family.paired_t_p.sort_values().index
    running = 0.
    for rank, idx in enumerate(order):
        running = max(running, (len(order)-rank)*out.loc[idx, 'paired_t_p'])
        out.loc[idx, 'holm_primary_p'] = min(1., running)
    return out

def main():
    torch.set_num_threads(1)
    out = ROOT / 'outputs/jicce_validation'
    out.mkdir(parents=True, exist_ok=True)
    base = yaml.safe_load((ROOT / 'configs/af_v3_final.yaml').read_text())
    rows, packets, logs = [], [], []
    for seed in SEEDS:
        for arm in ARMS:
            torch.manual_seed(seed + 20000)
            np.random.seed(seed + 30000)
            cfg = copy.deepcopy(base)
            cfg['seed'] = seed + 10000
            trainer = configure(cfg, arm)
            log = trainer.train(8, 50, ppo_epochs=3)
            for x in log:
                x.update(seed=seed, policy=arm)
            logs.extend(log)
            state = {k: v.detach().cpu().clone() for k,v in trainer.model.state_dict().items()}
            checkpoint = out / 'checkpoints' / f'{arm}_{seed}.pt'
            checkpoint.parent.mkdir(exist_ok=True)
            torch.save(state, checkpoint)
            for setting in ['nominal', 'size200', 'attack10', 'attack40']:
                summary, records = evaluate(base, state, seed, arm, setting)
                rows.append(summary)
                packets.extend(records)
            pd.DataFrame(rows).to_csv(out / 'seed_summary.csv', index=False)
            pd.DataFrame(packets).to_csv(out / 'episode_metrics.csv', index=False)
            pd.DataFrame(logs).to_csv(out / 'training_log.csv', index=False)
            print(seed, arm, 'completed', flush=True)
    analyse(pd.DataFrame(rows)).to_csv(out / 'paired_analysis.csv', index=False)
    (out / 'execution_status.json').write_text(json.dumps({'completed':True, 'seeds':SEEDS, 'arms':ARMS,
        'training_episodes_per_arm_seed':400, 'evaluation_episodes_per_setting':240,
        'status':'new validation evidence; historical AF-v3 decision unchanged'}, indent=2))

if __name__ == '__main__':
    main()
