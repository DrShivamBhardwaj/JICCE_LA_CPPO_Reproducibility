"""Public capture and signature audit for the compiled-firmware controls."""
from pathlib import Path
import hashlib,json,sys
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wsn_sim.distributed_auth import HEADER,RECEIPT,SINK,TAG,Datagram

def main():
    root=ROOT/'outputs/renode_boards';results=[]
    for policy in ['attention','mlp','greedy']:
        folder=root/f'{policy}_20261016';report=json.loads((folder/'verification.json').read_text())
        assert report['status']=='passed' and report['compiled_firmware_executed'] and not report['physical_validation']
        assert hashlib.sha256((folder/'cc2538_bridge.elf').read_bytes()).hexdigest()==report['firmware_elf_sha256']
        assert hashlib.sha256((ROOT/'hardware/renode_cc2538/bridge.c').read_bytes()).hexdigest()==report['firmware_source_sha256']
        public=Ed25519PublicKey.from_public_bytes(bytes.fromhex(report['sink_public_key']))
        traces=[[json.loads(x) for x in (folder/f'node_{i}.jsonl').read_text().splitlines()] for i in range(4)]
        tx={(i,r['peer'],r['wire']) for i,rows in enumerate(traces) for r in rows if r['event']=='tx'}
        received=0;signatures=0;source_receipts=set();sink_packets=set()
        for i,rows in enumerate(traces):
            fw=[json.loads(x) for x in (folder/f'firmware_uart_{i}.jsonl').read_text().splitlines()]
            firmware_rx={(r['peer'],r['wire']) for r in fw if r['event']=='rx'}
            assert any(r['event']=='ready' and r['node']==i for r in fw)
            for r in rows:
                if r['event']!='board' or r['record']['event']!='rx':continue
                r=r['record'];assert (r['peer'],i,r['wire']) in tx
                assert (r['peer'],r['wire']) in firmware_rx
                wire=bytes.fromhex(r['wire']);assert len(wire)+11<=127
                version,kind,sender,receiver,boot,seq,size=HEADER.unpack(wire[:HEADER.size])
                assert version==1 and sender==r['peer'] and receiver==i and len(wire)==HEADER.size+size+TAG
                received+=1
                if kind==3:
                    body=wire[HEADER.size:-TAG];public.verify(body[RECEIPT.size:],SINK+body[:RECEIPT.size]);signatures+=1
                    if i==0:source_receipts.add(RECEIPT.unpack(body[:RECEIPT.size]))
                if kind==2 and i==3:sink_packets.add(Datagram.decode(wire[HEADER.size:-TAG]).key)
        assert len(sink_packets)==report['sink_delivered'] and len(source_receipts)<=len(sink_packets)
        probes=json.loads((folder/'probes.json').read_text());assert len(probes)==5
        assert probes[-1]['test']=='out_of_range_no_delivery_no_ack' and not probes[-1]['ack']['ok']
        results.append(dict(policy=policy,received_frames=received,public_signatures=signatures,
            sink_unique_packets=len(sink_packets),source_verified_receipts=len(source_receipts),firmware_probes=5))
    result=dict(status='passed',runs=results,physical_validation=False,
        limits='Checks MCU UART byte provenance, public sink signatures and identities. Secret hop/source HMACs remain runtime checks. No measured RF, hardware energy or embedded policy/crypto claim.')
    (root/'audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

if __name__=='__main__':main()
