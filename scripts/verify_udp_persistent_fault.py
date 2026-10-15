"""Independently recompute trace decisions and posterior/observation causality."""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import torch
import yaml
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from wsn_sim.env import PacketRoutingEnv
from wsn_sim.rl import LocalAttentionActorCritic
from wsn_sim.security import SecurityRiskEstimator

def main():
    torch.set_num_threads(1)
    out = ROOT/'outputs/udp_persistent_fault'
    trace = out/'trace.jsonl'
    paths = [trace] if trace.exists() else sorted(out.glob('trace_part*.jsonl'))
    rows = [json.loads(x) for path in paths for x in path.read_text().splitlines()]
    summary = json.loads((out/'summary.json').read_text())
    checkpoint = ROOT/'outputs/jicce_validation/checkpoints/attention_41001.pt'
    # Per-run checkpoint hashes are verified below.
    cfg = yaml.safe_load((ROOT/'configs/af_v3_final.yaml').read_text())
    env = PacketRoutingEnv(cfg); b = env.builder
    model = LocalAttentionActorCritic(b.context_dim, b.CANDIDATE_DIM, b.k,
        hidden=cfg['rl']['hidden'], n_costs=env.n_costs)
    model.load_state_dict(torch.load(checkpoint, weights_only=True, map_location='cpu'))
    model.eval()
    assert len(rows) == 900
    assert sorted(set(r['seed'] for r in rows)) == list(range(72001,72031))
    for seed in range(72001,72031):
        run = [r for r in rows if r['seed']==seed]
        checkpoint = ROOT / f'outputs/jicce_validation/checkpoints/attention_{41001+seed-72001}.pt'
        digest = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
        assert all(r['checkpoint_sha256']==digest for r in run)
        model.load_state_dict(torch.load(checkpoint, weights_only=True, map_location='cpu'))
        assert [r['packet'] for r in run] == list(range(30))
        fixture = dict(cfg, seed=seed)
        fixture['attack'] = dict(cfg['attack'], malicious_ratio=0.)
        live = PacketRoutingEnv(fixture)
        sec = SecurityRiskEstimator(live.net.n)
        eligible = [i for i in range(live.net.n) if live.net.distance(i,None)>live.net.radio_range and len(live.net.feasible_neighbors(i))>=2]
        assert run[0]['source']==int(np.random.default_rng(seed).choice(eligible))
        assert run[0]['faulty_node']==run[0]['chosen_node']
        for r in run:
            pre = b.build(live.net, sec, live.qos, r['source'], 0, 0., {r['source']})
            np.testing.assert_allclose(pre.flat_obs, r['observation'], atol=1e-7)
            assert pre.node_ids.tolist()==r['candidate_ids']
            assert pre.mask.tolist()==r['mask']
            assert r['sequence']==r['packet']+1
            assert r['acknowledged']==r['sink_witness']==(r['chosen_node']!=r['faulty_node'])
            assert np.isclose(sec.risk[r['chosen_node']],r['risk_before'])
            sec.observe_forward(r['chosen_node'], r['acknowledged'], r['expected_pdr'])
            assert np.isclose(sec.risk[r['chosen_node']],r['risk_after'])
            post = b.build(live.net, sec, live.qos, r['source'], 0, 0., {r['source']})
            np.testing.assert_allclose(post.flat_obs,r['post_observation'],atol=1e-7)
            assert post.node_ids.tolist()==r['post_candidate_ids']
            assert post.mask.tolist()==r['post_mask']
            for prefix in ['', 'post_']:
                with torch.no_grad():
                    logits,_,_ = model(torch.tensor(r[prefix+'observation']).unsqueeze(0),
                        torch.tensor(r[prefix+'mask']).unsqueeze(0))
                    probabilities = torch.softmax(logits,-1).squeeze(0).numpy()
                np.testing.assert_allclose(probabilities,r[prefix+'probabilities'],atol=1e-7)
            assert r['chosen_node']==r['candidate_ids'][int(np.argmax(r['probabilities']))]
    assert summary['acknowledgments']==sum(r['acknowledged'] for r in rows)
    print('Verified 900 decisions, UDP outcomes, posteriors, reconstructed observations and frozen-policy probabilities.')

if __name__=='__main__':
    main()
