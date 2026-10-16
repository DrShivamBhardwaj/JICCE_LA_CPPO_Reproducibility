"""Fail-closed public capture audit for archived or newly generated MCU runs."""
from pathlib import Path
import argparse, hashlib, json, sys
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wsn_sim.distributed_auth import HEADER,RECEIPT,SINK,TAG,Datagram

class AuditError(ValueError):
    pass

def require(condition, message):
    if not condition: raise AuditError(message)

def read_rows(path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]

def check_probes(probes):
    names=['telemetry_label','114_byte_wire_and_real_emulated_mac_ack','oversize','invalid_hex','out_of_range_no_delivery_no_ack']
    require([p.get('test') for p in probes]==names,'Five named probes in order are required')
    t=probes[0]['record'];require(t.get('event')=='telemetry' and t.get('provenance')=='emulated_no_power_model' and t.get('energy_fraction')==1.0,'Uncalibrated energy label/value missing')
    p=probes[1];require(p['ack']==dict(event='ack',token=9001,ok=True),'114-byte ACK failed')
    require(p['rx'].get('event')=='rx' and p['rx']['peer']==0 and p['rx']['wire']==bytes(range(114)).hex(),'114-byte payload changed')
    for p,token in zip(probes[2:],[9002,9003,9004]):
        require(p['ack']==dict(event='ack',token=token,ok=False),f'Negative probe {token} failed')

def audit_run(folder, expected_packets=None, allow_legacy_receipt_log=False):
    folder=Path(folder).resolve();report=json.loads((folder/'verification.json').read_text())
    expected=report['offered'] if expected_packets is None else expected_packets
    require(type(expected) is int and expected>0,'Expected packet count must be a positive integer')
    require(report['status'] in ['pending_audit','passed'],'Run report is not eligible for audit')
    require(report['offered']==expected,'Offered count differs from acceptance target')
    require(report['compiled_firmware_executed'] and not report['physical_validation'],'Incorrect validation boundary')
    require(hashlib.sha256((folder/'cc2538_bridge.elf').read_bytes()).hexdigest()==report['firmware_elf_sha256'],'ELF hash mismatch')
    require(hashlib.sha256((ROOT/'hardware/renode_cc2538/bridge.c').read_bytes()).hexdigest()==report['firmware_source_sha256'],'Firmware source hash mismatch')
    public=Ed25519PublicKey.from_public_bytes(bytes.fromhex(report['sink_public_key']))
    traces=[read_rows(folder/f'node_{i}.jsonl') for i in range(4)]
    # Timestamp evidence requires a matching earlier host transmission, rather
    # than membership in an unordered set that could match a future event.
    tx={};offered=set();received=0;signatures=0;source_receipts=set();sink_packets=set();source_acceptance=None
    for i,rows in enumerate(traces):
        for r in rows:
            if r['event']=='tx':
                key=(i,r['peer'],r['wire']);tx.setdefault(key,[]).append(r['host_monotonic_s'])
                raw=bytes.fromhex(r['wire']);_,kind,*_=HEADER.unpack(raw[:HEADER.size])
                if i==0 and kind==2:offered.add(Datagram.decode(raw[HEADER.size:-TAG]).key)
    session=next(r['session'] for r in traces[0] if r['event']=='session')
    expected_ids={(0,p,session) for p in range(expected)}
    require(offered==expected_ids,'Source packet identities/count differ from target')
    for i,rows in enumerate(traces):
        fw=read_rows(folder/f'firmware_uart_{i}.jsonl')
        firmware_rx={(r['peer'],r['wire']) for r in fw if r['event']=='rx'}
        require(any(r['event']=='ready' and r['node']==i for r in fw),f'MCU {i} boot evidence missing')
        finals=[r for r in rows if r['event']=='final'];require(len(finals)==1,f'Node {i} final record missing/duplicated')
        final=finals[0]
        require(not final['rejects'],f'Node {i} reported protocol rejection')
        require(not any(r['event'] in ['missing_mac_confirm','host_tx_capacity'] for r in rows),f'Node {i} transport error')
        require(final['settlements']==expected if i<3 else final['sink_delivered']==expected,f'Node {i} incomplete service')
        if i==0: source_acceptance=final.get('accepted_source_receipts')
        for row in rows:
            if row['event']!='board' or row['record']['event']!='rx':continue
            r=row['record'];times=tx.get((r['peer'],i,r['wire']),[])
            require(any(t<=row['host_monotonic_s'] for t in times),'Receive has no prior matching transmission')
            require((r['peer'],r['wire']) in firmware_rx,'Receive absent from MCU UART output')
            wire=bytes.fromhex(r['wire']);require(len(wire)<=114 and len(wire)+11<=127,'Frame exceeds application/MAC limit')
            version,kind,sender,receiver,boot,seq,size=HEADER.unpack(wire[:HEADER.size])
            require(version==1 and sender==r['peer'] and receiver==i and len(wire)==HEADER.size+size+TAG,'Frame header mismatch')
            received+=1
            if kind==3:
                body=wire[HEADER.size:-TAG];public.verify(body[RECEIPT.size:],SINK+body[:RECEIPT.size]);signatures+=1
                if i==0:source_receipts.add(RECEIPT.unpack(body[:RECEIPT.size]))
            if kind==2 and i==3:sink_packets.add(Datagram.decode(wire[HEADER.size:-TAG]).key)
    require(sink_packets==expected_ids and source_receipts==expected_ids,'Delivery or signed source receipts incomplete/mismatched')
    require(report['sink_delivered']==expected,'Report delivery differs from target')
    # Historical captures predate explicit accepted-receipt logging. Their
    # source packets, valid receipt bytes and empty rejection logs are retained.
    require(source_acceptance is not None or allow_legacy_receipt_log,'Runtime accepted-receipt count missing; legacy mode must be explicit')
    if source_acceptance is not None:require(source_acceptance==expected,'Runtime source receipt acceptance incomplete')
    check_probes(json.loads((folder/'probes.json').read_text()))
    require(report['firmware_probes']==5,'Report probe count differs')
    return dict(policy=report['policy'],folder=str(folder.relative_to(ROOT)) if folder.is_relative_to(ROOT) else str(folder),expected_packets=expected,received_frames=received,public_signatures=signatures,sink_unique_packets=len(sink_packets),source_verified_receipts=len(source_receipts),runtime_accepted_source_receipts=source_acceptance,firmware_probes=5)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,action='append',help='Audit a new/existing run; repeat for multiple runs');ap.add_argument('--expected-packets',type=int);ap.add_argument('--output',type=Path)
    ap.add_argument('--allow-legacy-receipt-log',action='store_true',help='Historical inspection only: permit absent runtime receipt counter, reported as null')
    args=ap.parse_args();root=ROOT/'outputs/renode_boards'
    folders=args.run or [root/f'{p}_strict_20261016' for p in ['attention','mlp','greedy']]
    try:
        results=[audit_run(f,args.expected_packets,args.allow_legacy_receipt_log) for f in folders]
        result=dict(status='passed',runs=results,physical_validation=False,limits='MCU UART provenance, packet identities and public signatures audited. Secret HMACs are runtime checks. No physical RF/power or embedded inference/crypto claim.')
    except Exception as error:
        result=dict(status='failed',error=f'{type(error).__name__}: {error}',physical_validation=False)
        if args.output:args.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2));return 1
    output=args.output or (root/'audit.json' if not args.run else None)
    if output:output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));return 0

if __name__=='__main__':sys.exit(main())
