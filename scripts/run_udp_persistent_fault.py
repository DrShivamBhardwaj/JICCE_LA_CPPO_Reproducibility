"""Frozen-policy functional UDP integration with independent sink witness."""
import hashlib
import json
import socket
import sys
import threading
import time
from pathlib import Path
import numpy as np
import torch
import yaml
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from wsn_sim.env import PacketRoutingEnv
from wsn_sim.rl import LocalAttentionActorCritic
from wsn_sim.packet_feedback import UDPFeedbackAdapter


def main():
    torch.set_num_threads(1)
    checkpoint = ROOT / 'outputs/jicce_validation/checkpoints/attention_41001.pt'
    digest = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    state = torch.load(checkpoint, map_location='cpu', weights_only=True)
    records = []
    for seed in range(72001, 72031):
        cfg = yaml.safe_load((ROOT / 'configs/af_v3_final.yaml').read_text())
        checkpoint = ROOT / f'outputs/jicce_validation/checkpoints/attention_{41001+seed-72001}.pt'
        digest = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
        state = torch.load(checkpoint, map_location='cpu', weights_only=True)
        cfg['seed'] = seed
        cfg['attack']['malicious_ratio'] = 0.0
        env = PacketRoutingEnv(cfg)
        b = env.builder
        model = LocalAttentionActorCritic(b.context_dim, b.CANDIDATE_DIM, b.k,
            hidden=cfg['rl']['hidden'], n_costs=env.n_costs)
        model.load_state_dict(state)
        model.eval()
        eligible = [i for i in range(env.net.n) if env.net.distance(i, None) > env.net.radio_range and len(env.net.feasible_neighbors(i)) >= 2]
        source = int(np.random.default_rng(seed).choice(eligible))
        initial = b.build(env.net, env.sec, env.qos, source, 0, 0., {source})
        with torch.no_grad():
            initial_logits, _, _ = model(torch.tensor(initial.flat_obs).unsqueeze(0), torch.tensor(initial.mask).unsqueeze(0))
        faulty_node = int(initial.node_ids[int(initial_logits.argmax())])
        stop = threading.Event()
        receipts = set()
        sink = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sink.bind(('127.0.0.1', 0)); sink.settimeout(.05)
        def sink_worker():
            while not stop.is_set():
                try:
                    data, peer = sink.recvfrom(65535)
                except socket.timeout:
                    continue
                p = json.loads(data)
                receipts.add((p['sequence'], p['nonce']))
                sink.sendto(data, peer)
        workers = [threading.Thread(target=sink_worker)]
        relays = {}
        def relay_worker(sock, node):
            while not stop.is_set():
                try:
                    data, peer = sock.recvfrom(65535)
                except socket.timeout:
                    continue
                p = json.loads(data)
                if node == faulty_node:
                    continue
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as downstream:
                    downstream.settimeout(.2)
                    downstream.sendto(data, sink.getsockname())
                    try:
                        ack, endpoint = downstream.recvfrom(65535)
                    except socket.timeout:
                        continue
                    if endpoint == sink.getsockname() and ack == data:
                        sock.sendto(json.dumps(dict(p, forwarded=True)).encode(), peer)
        for node in env.net.feasible_neighbors(source):
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('127.0.0.1', 0)); sock.settimeout(.05)
            relays[node] = sock
            workers.append(threading.Thread(target=relay_worker, args=(sock, node)))
        for worker in workers:
            worker.start()
        adapter = UDPFeedbackAdapter(env.sec, timeout_s=.02)
        def decision():
            obs = b.build(env.net, env.sec, env.qos, source, 0, 0., {source})
            assert obs.mask.any()
            with torch.no_grad():
                logits, _, _ = model(torch.tensor(obs.flat_obs).unsqueeze(0),
                                     torch.tensor(obs.mask).unsqueeze(0))
                probs = torch.softmax(logits, -1).squeeze(0).numpy()
            return obs, probs
        try:
            for packet in range(30):
                start = time.monotonic()
                obs, probs = decision()
                inference_s = time.monotonic() - start
                node = int(obs.node_ids[int(np.argmax(probs))])
                expected = float(env.net.radio.pdr(env.net.distance(source, node),
                    .5 * (env.net.interference[source]+env.net.interference[node]), shadowing_db=0.))
                before_receipts = set(receipts)
                record = adapter.forward(node, relays[node].getsockname(), b'fixture', expected)
                witnessed = any(seq == record.sequence for seq, nonce in receipts - before_receipts)
                post, post_probs = decision()
                assert witnessed == record.acknowledged
                assert hashlib.sha256(checkpoint.read_bytes()).hexdigest() == digest
                records.append(dict(seed=seed, packet=packet, source=source, faulty_node=faulty_node, checkpoint_sha256=digest,
                    candidate_ids=obs.node_ids.tolist(), mask=obs.mask.tolist(),
                    observation=obs.flat_obs.tolist(), probabilities=probs.tolist(),
                    chosen_node=node, sequence=record.sequence, expected_pdr=expected,
                    acknowledged=record.acknowledged, sink_witness=witnessed,
                    risk_before=record.risk_before, risk_after=record.risk_after,
                    post_candidate_ids=post.node_ids.tolist(), post_mask=post.mask.tolist(),
                    post_observation=post.flat_obs.tolist(), post_probabilities=post_probs.tolist(),
                    inference_s=inference_s, feedback_s=record.elapsed_s))
        finally:
            stop.set()
            for worker in workers:
                worker.join(timeout=1)
                assert not worker.is_alive()
            for sock in relays.values():
                sock.close()
            sink.close()
        print(seed, 'completed', flush=True)
    assert hashlib.sha256(checkpoint.read_bytes()).hexdigest() == digest
    out = ROOT / 'outputs/udp_persistent_fault'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'trace.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
    (out / 'summary.json').write_text(json.dumps(dict(
        scope='functional localhost UDP integration; synthetic candidate features',
        checkpoint_sha256='per-run hashes recorded in trace', runs=30, packets=len(records),
        acknowledgments=sum(r['acknowledged'] for r in records),
        sink_witness_mismatches=sum(r['acknowledged'] != r['sink_witness'] for r in records),
        changed_probability_vectors=sum(r['probabilities'] != r['post_probabilities'] for r in records),
        changed_next_hop_argmax=sum(r['chosen_node'] != r['post_candidate_ids'][int(np.argmax(r['post_probabilities']))] for r in records),
        runs_with_failover=len({r['seed'] for r in records if r['chosen_node'] != r['faulty_node']}),
        conclusion='Persistent targeted fixture fault; no physical WSN performance or attention superiority claim'), indent=2))

if __name__ == '__main__':
    main()
