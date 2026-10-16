"""Functional radio transfer of byte-serialized authenticated distributed state.
Separate post-holdout engineering control; not the 750-run policy benchmark.
"""
from pathlib import Path
import ctypes as C,json,sys,secrets,hashlib,gzip,io
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wsn_sim.distributed_auth import Channel,Node,HEADER
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
class Event(C.Structure):_fields_=[('time',C.c_double)]+[(x,C.c_int) for x in ['kind','node','peer','handle','ok','length']]+[('bytes',C.c_uint8*114)]
lib=C.CDLL(str(ROOT/'build/libwsn_ns3_wire.so'));lib.wire_init.argtypes=[C.c_int,C.POINTER(C.c_double),C.c_int,C.c_double];lib.wire_step.argtypes=[C.c_double];lib.wire_send.argtypes=[C.c_int,C.c_int,C.POINTER(C.c_uint8),C.c_int];lib.wire_send.restype=C.c_int;lib.wire_energy.argtypes=[C.c_int,C.POINTER(C.c_double)];lib.wire_poll.argtypes=[C.POINTER(Event)]
out=ROOT/'outputs/distributed_auth';out.mkdir(parents=True,exist_ok=True);summaries=[]
for seed in range(82001,82031):
    xy=[(0.,0.),(30.,0.),(60.,0.),(90.,0.)];coords=(C.c_double*8)(*[v for point in xy for v in point]);lib.wire_init(4,coords,seed,40.)
    signing=Ed25519PrivateKey.generate();pairs={(a,b):secrets.token_bytes(32) for a in range(4) for b in range(a+1,4)};sessions={i:secrets.randbits(64) for i in range(4)}
    nodes=[Node(i,xy[i],3,xy[3],Channel(i,sessions[i],{j:pairs[min(i,j),max(i,j)] for j in range(4) if j!=i},{j:sessions[j] for j in range(4) if j!=i}),signing.public_key(),signing if i==3 else None) for i in range(4)]
    pending={};trace=[];sent_bytes=0;received=0;sent=0;rejected_sends=0;fault_injected=False;replay=None
    def send(sender,peer,wire,now):
        global sent_bytes,sent,rejected_sends
        buf=(C.c_uint8*len(wire)).from_buffer_copy(wire);handle=lib.wire_send(sender,peer,buf,len(wire))
        if handle<0:rejected_sends+=1;return
        pending[(sender,handle)]=(peer,wire);sent+=1;sent_bytes+=len(wire);trace.append(dict(event='tx_request',time=now,node=sender,peer=peer,wire=wire.hex()))
    for tick in range(2000):
        now=tick*.001
        if tick in [0,500,1000,1500]:
            for i,node in enumerate(nodes):
                for peer in [j for j in range(4) if abs(i-j)==1]:
                    own=(C.c_double*7)();lib.wire_energy(i,own)
                    dst,wire=node.beacon(peer,max(0.,1-own[0]/.5),int(own[6]),now);send(i,dst,wire,now)
                    if i==0 and peer==1 and tick==0:replay=wire
        if tick==100:
            # An outsider changes the authenticated telemetry bytes and then
            # replays the original beacon. Both travel over the radio channel.
            forged=bytearray(replay);forged[HEADER.size]^=1;send(0,1,bytes(forged),now)
        if tick==150:send(0,1,replay,now)
        if 200<=tick<=1100 and (tick-200)%100==0:
            pid=(tick-200)//100
            for peer,wire in nodes[0].originate(pid,pid%3,b'0123456789abcdef',now):send(0,peer,wire,now)
        lib.wire_step(.001);now=(tick+1)*.001;e=Event()
        while lib.wire_poll(C.byref(e)):
            if e.kind==1:
                received+=1;wire=bytes(e.bytes[:e.length]);trace.append(dict(event='rx',time=e.time,node=e.node,peer=e.peer,wire=wire.hex()))
                for peer,newwire in nodes[e.node].receive(wire,e.peer,e.time):send(e.node,peer,newwire,now)
            elif e.kind==2:
                entry=pending.pop((e.node,e.handle),None)
                if entry:
                    peer,wire=entry;nodes[e.node].ack(peer,wire,bool(e.ok),e.time);trace.append(dict(event='mac_ack',time=e.time,node=e.node,peer=peer,ok=bool(e.ok),wire_sha256=hashlib.sha256(wire).hexdigest()))
        for node in nodes:node.expire(now)
    energy=[]
    for i in range(4):
        v=(C.c_double*7)();lib.wire_energy(i,v);v=list(v);assert abs(sum(v[1:4])-2.)<1e-8;assert abs(v[0]-3*(.0174*v[1]+.0188*v[2]+.000020*v[3]))<1e-10;energy.append(v)
    result=dict(sink_public_key=signing.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw).hex(),seed=seed,offered=10,sink_delivered=nodes[3].delivered_total,source_verified_receipts=nodes[0].settlements,transit_settlements=[n.settlements for n in nodes[1:3]],transit_debts=[n.debts for n in nodes[1:3]],rejects=[n.rejects for n in nodes],max_pending=max(n.max_pending for n in nodes),tx_requests=sent,application_tx_bytes=sent_bytes,received_frames=received,send_rejections=rejected_sends,max_frame_bytes=max(len(bytes.fromhex(t['wire'])) for t in trace if 'wire' in t),radio_energy=energy,mode='functional serialized transport with greedy progress; no learned-policy performance inference')
    assert 0<=result['source_verified_receipts']<=result['sink_delivered']<=10,result
    assert all(x>=result['source_verified_receipts'] for x in result['transit_settlements']),result
    # Injection frames can be lost by the real MAC; retain every fixture.
    forged_rx=sum(t['event']=='rx' and t['node']==1 and t.get('wire')==bytes(forged).hex() for t in trace)
    assert nodes[1].rejects.get('tag',0)==forged_rx,result
    result['forged_frames_received']=forged_rx
    assert result['max_frame_bytes']<=114 and not rejected_sends
    target=out/f'wire_{seed}.jsonl.gz';data=gzip.compress(('\n'.join(json.dumps(r,separators=(',',':')) for r in trace)+'\n').encode(),mtime=0);tmp=target.with_suffix('.tmp');tmp.write_bytes(data);tmp.replace(target);summaries.append(result);lib.wire_destroy()
(out/'summary.json').write_text(json.dumps(summaries,indent=2));print(json.dumps(dict(runs=len(summaries),offered=300,delivered=sum(x['sink_delivered'] for x in summaries),forged_telemetry_rejected=sum(x['rejects'][1].get('tag',0) for x in summaries),replayed_telemetry_rejected=sum(x['rejects'][1].get('replay',0) for x in summaries),hardware_validation=False,learned_policy_benchmark=False,retention='all 30 fixtures, including packet/receipt loss' ),indent=2))
