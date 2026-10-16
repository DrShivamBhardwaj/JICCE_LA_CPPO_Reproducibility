"""Audit public signatures, wire provenance, local cache and frozen decisions."""
import gzip,hashlib,json,sys,struct,math
from pathlib import Path
import numpy as np
import torch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wsn_sim.auth_policy import observation,load_policy
from wsn_sim.distributed_auth import HEADER,BEACON,RECEIPT,TAG,SINK

def main():
    torch.set_num_threads(1);out=ROOT/'outputs/auth_policy';rows=json.loads((out/'summary.json').read_text())
    assert len(rows)==180
    protocol=json.loads((ROOT/'configs/auth_policy_protocol.json').read_text())
    assert {(r['seed'],r['setting'],r['arm']) for r in rows}=={(s,t,a) for s in protocol['seeds'] for t in protocol['settings'] for a in protocol['arms']}
    counts=dict(runs=0,decisions=0,multichoice=0,received_frames=0,signatures=0,energy_identities=0)
    max_probability_error=0.
    for r in rows:
        path=out/f"{r['seed']}_{r['setting']}_{r['arm']}.jsonl.gz"
        assert hashlib.sha256(path.read_bytes()).hexdigest()==r['trace_sha256']
        stream=[json.loads(x) for x in gzip.decompress(path.read_bytes()).decode().splitlines()]
        first=stream[0];public=Ed25519PublicKey.from_public_bytes(bytes.fromhex(first['sink_public']))
        model=None
        if r['arm']!='greedy':
            cp=ROOT/f"outputs/jicce_validation/checkpoints/{'capacity_mlp' if r['arm']=='mlp' else 'attention'}_{41001+r['seed']-83001}.pt"
            assert hashlib.sha256(cp.read_bytes()).hexdigest()==first['checkpoint_sha256']==protocol['checkpoints'][str(cp.relative_to(ROOT))]
            model=load_policy(cp,r['arm'])
        tx=set();caches=[{} for _ in range(6)];lqis=[{} for _ in range(6)];beacon_seq=[{} for _ in range(6)];offered={};delivered={};decision_count=0;multi=0
        source_receipts=set()
        for t in stream:
            kind=t['event']
            if kind in ['tx','rx']:
                wire=bytes.fromhex(t['wire']);ver,k,sender,receiver,boot,seq,length=HEADER.unpack(wire[:HEADER.size])
                assert ver==1 and len(wire)<=114 and len(wire)==HEADER.size+length+TAG
                if kind=='tx':assert sender==t['node'] and receiver==t['peer'];tx.add((sender,receiver,wire))
                else:
                    assert (t['peer'],t['node'],wire) in tx;counts['received_frames']+=1
                    if k==1:
                        x,y,e,q,stamp=BEACON.unpack(wire[HEADER.size:-TAG]);stamp/=1e6
                        if -1e-6<=t['time']-stamp<=.75 and seq>beacon_seq[receiver].get(sender,-1):
                            beacon_seq[receiver][sender]=seq
                            caches[receiver][str(sender)]=[x,y,e,q,stamp];lqis[receiver][str(sender)]=t['lqi']/255.
                if k==3:
                    body=wire[HEADER.size:-TAG];public.verify(body[RECEIPT.size:],SINK+body[:RECEIPT.size]);counts['signatures']+=1
                    if kind=='rx' and receiver==0:source_receipts.add(RECEIPT.unpack(body[:RECEIPT.size])[1])
            elif kind=='offered':offered[t['pid']]=t['time']
            elif kind=='sink_delivered':
                assert t['pid'] not in delivered;delivered[t['pid']]=t['time']
            elif kind=='decision':
                state=t['state'];i=state['node'];decision_count+=1
                # Every neighbor feature must originate in an actual received
                # byte beacon; no global-position sidecar is used by this node.
                for peer,value in state['cache'].items():
                    np.testing.assert_allclose(value,caches[i][peer],rtol=0,atol=1e-7)
                for peer,value in state['lqi'].items():assert abs(value-lqis[i][peer])<1e-7
                obs,mask,ids=observation(state);np.testing.assert_allclose(obs,t['observation'],atol=1e-7)
                assert mask.tolist()==t['mask'] and ids==t['candidate_ids'] and t['chosen'] in [p for p,m in zip(ids,mask) if m]
                multi+=int(mask.sum()>1)
                if model is not None:
                    with torch.no_grad():logits,_,_=model(torch.tensor(obs)[None],torch.tensor(mask)[None]);probs=torch.softmax(logits,-1).squeeze(0).numpy()
                    max_probability_error=max(max_probability_error,float(np.max(np.abs(probs-np.asarray(t['probabilities'])))))
                    # Different CPU math backends may differ by a few float32
                    # ULPs. Keep action identity exact; tolerate only numeric
                    # replay noise, without editing saved observations/outcomes.
                    np.testing.assert_allclose(probs,t['probabilities'],rtol=1e-6,atol=1e-6)
                    assert ids[int(np.argmax(probs))]==t['chosen']
                else:
                    expected=min((math.dist(state['cache'][str(p)][:2],state['sink_xy']),state['cache'][str(p)][3],p) for p,m in zip(ids,mask) if m)[2]
                    assert t['chosen']==expected
        assert len(offered)==60 and len(delivered)==r['delivered']
        assert r['delivery']==len(delivered)/60
        assert abs(r['total_radio_j']-sum(e[0] for e in r['radio_energy']))<1e-10
        assert abs(r['energy_per_delivered_byte']-r['total_radio_j']/(16*len(delivered)))<1e-12
        assert len(source_receipts)==round(r['verified_receipts']*60)
        critical=[p for p in offered if p%3==0]
        assert sum(p not in delivered or delivered[p]-offered[p]>.09 for p in critical)/20==r['critical_violation']
        assert decision_count==r['decisions'] and multi==r['multichoice']
        for energy,tx_s,rx_s,off_s,frames,nbytes,pending in r['radio_energy']:
            assert abs(tx_s+rx_s+off_s-7.5)<1e-7
            assert abs(energy-3*(.0174*tx_s+.0188*rx_s+.000020*off_s))<1e-9;counts['energy_identities']+=1
        counts['runs']+=1;counts['decisions']+=decision_count;counts['multichoice']+=multi
    report=dict(status='passed',**counts,physical_validation=False,max_probability_replay_error=max_probability_error,probability_atol=1e-6,probability_rtol=1e-6,action_identity='exact argmax required',
        limits='Recomputed frozen probabilities, declared features and endpoints; checked byte cache provenance and public signatures. Runtime nodes check secret hop tags. No independent RF model validation or MCU timing.')
    (out/'audit.json').write_text(json.dumps(report,indent=2));print(report)

if __name__=='__main__':main()
