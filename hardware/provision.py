"""Generate private per-node configs for the documented host/radio test harness.
Provision every node again after a restart. Never publish the generated directory.
"""
import argparse,json,secrets,os
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();args.output.mkdir(mode=0o700,parents=True,exist_ok=False)
    n=4;xy=[(0.,0.),(30.,0.),(60.,0.),(90.,0.)];pairs={(a,b):secrets.token_bytes(32) for a in range(n) for b in range(a+1,n)};sessions={i:secrets.randbits(64) for i in range(n)};signer=Ed25519PrivateKey.generate();public=signer.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw).hex()
    for i in range(n):
        cfg=dict(node=i,xy=xy[i],sink=3,sink_xy=xy[3],neighbors=[j for j in range(n) if abs(i-j)==1],session=sessions[i],peer_sessions={str(j):sessions[j] for j in range(n) if j!=i},keys={str(j):pairs[min(i,j),max(i,j)].hex() for j in range(n) if j!=i},sink_public=public)
        if i==3:cfg['sink_private']=signer.private_bytes(serialization.Encoding.Raw,serialization.PrivateFormat.Raw,serialization.NoEncryption()).hex()
        path=args.output/f'node_{i}.private.json';fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as f:json.dump(cfg,f,indent=2)
    print('Created four private configs. Reprovision all nodes with new sessions after any process restart.')
if __name__=='__main__':main()
