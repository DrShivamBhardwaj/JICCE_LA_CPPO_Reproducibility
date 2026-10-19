"""Independently verify archived MCU Ed25519 outputs using public material only."""
import argparse,hashlib,json
from pathlib import Path
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

DOMAIN=b'JICCE-sink-v1\x00'  # C sizeof includes the terminating NUL.

def check(folder):
    report=json.loads((folder/'verification.json').read_text())
    if report['status']!='passed':raise ValueError('Functional run did not pass')
    public=Ed25519PublicKey.from_public_bytes(bytes.fromhex(report['sink_public']))
    signed={};mutations=0
    for line in (folder/'uart_3.jsonl').read_text().splitlines():
        event=json.loads(line)
        if event.get('event')!='local_tx':continue
        wire=bytes.fromhex(event['wire'])
        if wire[1]!=3:continue
        if len(wire)!=114 or int.from_bytes(wire[18:20],'big')!=78:raise ValueError('Signed receipt framing mismatch')
        body=wire[20:98];identity=body[:14];signature=body[14:]
        if int.from_bytes(identity[:2],'big')!=0 or int.from_bytes(identity[6:14],'big')!=report['sessions'][0]:raise ValueError('Signed source/session mismatch')
        pid=int.from_bytes(identity[2:6],'big')
        if pid in signed:raise ValueError('Duplicate signed packet')
        public.verify(signature,DOMAIN+identity)
        changed=bytes([signature[0]^1])+signature[1:]
        try:public.verify(changed,DOMAIN+identity)
        except InvalidSignature:mutations+=1
        else:raise ValueError('Altered signature accepted')
        signed[pid]=body
    source_frames={};accepted=[]
    for line in (folder/'uart_0.jsonl').read_text().splitlines():
        event=json.loads(line)
        if event.get('event')=='rx':
            wire=bytes.fromhex(event['wire'])
            if len(wire)==114 and wire[1]==3:
                body=wire[20:98];source_frames[int.from_bytes(body[2:6],'big')]=body
        if event.get('event')=='local_receipt':
            pid=event['pid'];body=source_frames.get(pid)
            if body is None or body!=signed.get(pid):raise ValueError('Source receipt has no matching sink-signed received frame')
            public.verify(body[14:],DOMAIN+body[:14]);accepted.append(pid)
    if len(signed)!=100 or len(accepted)!=100 or len(set(accepted))!=100 or set(accepted)!=set(signed):raise ValueError('Incomplete signed endpoint coverage')
    return dict(topology=folder.name,sink_signatures_verified=len(signed),source_receipts_matched_to_received_signatures=len(accepted),signature_mutations_rejected=mutations,public_key=report['sink_public'],verification_sha256=hashlib.sha256((folder/'verification.json').read_bytes()).hexdigest())

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--profile',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=dict(status='passed_public_signature_and_source_frame_recheck',rows=[check(a.profile/(t+'_100')) for t in ['chain','choice']],private_hop_tags_reverified=False,production_security_validated=False,physical_validation=False,scope='Independent public-key/signature and recorded source-receipt linkage check. Private hop secrets are not exported; no physical provenance, protected-storage, provisioning or secure-boot claim.')
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
