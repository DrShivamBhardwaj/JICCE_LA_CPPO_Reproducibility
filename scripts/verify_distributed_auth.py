"""Public-key and frame-provenance audit of post-holdout transport traces."""
import sys,json,gzip,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wsn_sim.distributed_auth import HEADER,RECEIPT,SINK,TAG,MAX_WIRE
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
out=ROOT/'outputs/distributed_auth';rows=json.loads((out/'summary.json').read_text());counts=dict(runs=0,received_frames=0,signed_receipt_transmissions=0,energy_identities=0);hashes=[]
for r in rows:
    counts['runs']+=1;public=Ed25519PublicKey.from_public_bytes(bytes.fromhex(r['sink_public_key']));path=out/f"wire_{r['seed']}.jsonl.gz";seen=set();transmitted=0;received=0;frames=0
    with gzip.open(path,'rt') as f:
        for line in f:
            e=json.loads(line)
            if e['event'] not in ['tx_request','rx']:continue
            wire=bytes.fromhex(e['wire']);assert len(wire)<=MAX_WIRE;ver,kind,sender,receiver,session,seq,length=HEADER.unpack(wire[:HEADER.size]);assert ver==1 and len(wire)==HEADER.size+length+TAG
            if e['event']=='tx_request':
                assert sender==e['node'] and receiver==e['peer'];seen.add((sender,receiver,wire));transmitted+=len(wire);frames+=1
                if kind==3:public.verify(wire[HEADER.size+RECEIPT.size:-TAG],SINK+wire[HEADER.size:HEADER.size+RECEIPT.size]);counts['signed_receipt_transmissions']+=1
            else:
                assert (e['peer'],e['node'],wire) in seen;assert sender==e['peer'] and receiver==e['node'];received+=1
    assert transmitted==r['application_tx_bytes'] and received==r['received_frames'] and frames==r['tx_requests'];counts['received_frames']+=received
    for energy,tx,rx,off,frames,bytecount,pending in r['radio_energy']:
        assert abs(tx+rx+off-2.)<1e-8;assert abs(energy-3*(.0174*tx+.0188*rx+.000020*off))<1e-10;counts['energy_identities']+=1
    hashes.append(dict(path=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
assert counts['runs']==30
report=dict(status='passed',**counts,trace_hashes=hashes,limits='Public sink signatures, frame matching and modeled energy checked. Pairwise hop tags were checked by runtime nodes; secret keys are not exported. No hardware validation or frozen-policy performance inference.');(out/'verification.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='trace_hashes'})
