"""Separate prospectively specified radio transfer, all fixtures retained."""
import ctypes as C
import gzip, hashlib, json, secrets, sys
from pathlib import Path
import numpy as np
import torch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wsn_sim.auth_policy import PolicyNode,load_policy,DEADLINES
from wsn_sim.distributed_auth import Channel,HEADER,Datagram,TAG

class Event(C.Structure):
    _fields_=[('time',C.c_double)]+[(x,C.c_int) for x in ['kind','node','peer','handle','ok','length']]+[('bytes',C.c_uint8*114)]

def main():
    torch.set_num_threads(1)
    protocol_path=ROOT/'configs/auth_policy_protocol.json'
    protocol=json.loads(protocol_path.read_text());out=ROOT/'outputs/auth_policy';out.mkdir(exist_ok=True)
    lib=C.CDLL(str(ROOT/'build/libwsn_ns3_wire.so'))
    lib.wire_init.argtypes=[C.c_int,C.POINTER(C.c_double),C.c_int,C.c_double]
    lib.wire_step.argtypes=[C.c_double];lib.wire_send.argtypes=[C.c_int,C.c_int,C.POINTER(C.c_uint8),C.c_int]
    lib.wire_send.restype=C.c_int;lib.wire_energy.argtypes=[C.c_int,C.POINTER(C.c_double)];lib.wire_poll.argtypes=[C.POINTER(Event)]
    summaries=[]
    for seed in protocol['seeds']:
      xy=np.array(protocol['positions'],float)+np.random.default_rng(seed).uniform(-2,2,(6,2))
      for setting in protocol['settings']:
       for arm in protocol['arms']:
        trace=[];pending={};sink_times={};offered={};send_rejections=0;faults=0
        def log(record):trace.append(record)
        cp=None;model=None
        if arm!='greedy':
            cp=ROOT/f"outputs/jicce_validation/checkpoints/{'capacity_mlp' if arm=='mlp' else 'attention'}_{41001+seed-83001}.pt"
            assert hashlib.sha256(cp.read_bytes()).hexdigest()==protocol['checkpoints'][str(cp.relative_to(ROOT))]
            model=load_policy(cp,arm)
        signing=Ed25519PrivateKey.generate();pairs={(a,b):secrets.token_bytes(32) for a in range(6) for b in range(a+1,6)};sessions={i:secrets.randbits(64) for i in range(6)}
        nodes=[PolicyNode(i,xy[i],5,xy[5],Channel(i,sessions[i],{j:pairs[min(i,j),max(i,j)] for j in range(6) if j!=i},{j:sessions[j] for j in range(6) if j!=i}),signing.public_key(),signing if i==5 else None,model=model,arm=arm,audit=log) for i in range(6)]
        coords=(C.c_double*12)(*xy.ravel());lib.wire_init(6,coords,seed,38.)
        def measure(i):
            values=(C.c_double*7)();lib.wire_energy(i,values);nodes[i].own=(max(0.,1-values[0]/.5),float(values[6]));return list(values)
        def send(sender,peer,wire,now):
            nonlocal send_rejections
            handle=lib.wire_send(sender,peer,(C.c_uint8*len(wire)).from_buffer_copy(wire),len(wire))
            log(dict(event='tx',node=sender,peer=peer,time=now,wire=wire.hex(),handle=handle))
            if handle<0:send_rejections+=1
            else:pending[sender,handle]=(peer,wire)
        log(dict(event='run',seed=seed,setting=setting,arm=arm,positions=xy.tolist(),
            checkpoint_sha256=hashlib.sha256(cp.read_bytes()).hexdigest() if cp else None,
            sink_public=signing.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw).hex()))
        for tick in range(7500):
            now=tick/1000.
            slot=tick%500
            if slot%2==0 and slot//2<30:
                i,j=divmod(slot//2,5);peer=j if j<i else j+1
                own=measure(i);dst,wire=nodes[i].beacon(peer,nodes[i].own[0],int(own[6]),now);send(i,dst,wire,now)
            if tick>=500 and (tick-500)%75==0 and (tick-500)//75<60:
                pid=(tick-500)//75;offered[pid]=now;measure(0)
                log(dict(event='offered',pid=pid,time=now,traffic=pid%3))
                for peer,wire in nodes[0].originate(pid,pid%3,b'0123456789abcdef',now):send(0,peer,wire,now)
            lib.wire_step(.001);now=(tick+1)/1000.;event=Event()
            while lib.wire_poll(C.byref(event)):
                if event.kind==1:
                    wire=bytes(event.bytes[:event.length]);log(dict(event='rx',node=event.node,peer=event.peer,time=event.time,wire=wire.hex(),lqi=event.ok))
                    kind=HEADER.unpack(wire[:HEADER.size])[1]
                    if setting=='selective_drop' and event.node==1 and kind==2 and Datagram.decode(wire[HEADER.size:-TAG]).pid%2==0:
                        faults+=1;log(dict(event='fault_drop',node=1,time=event.time));continue
                    measure(event.node);before=nodes[5].delivered_total
                    actions=nodes[event.node].receive_with_lqi(wire,event.peer,event.time,event.ok)
                    if event.node==5 and nodes[5].delivered_total>before:
                        packet=Datagram.decode(wire[HEADER.size:-TAG]);sink_times[packet.pid]=event.time
                        log(dict(event='sink_delivered',pid=packet.pid,time=event.time))
                    for peer,newwire in actions:send(event.node,peer,newwire,now)
                elif event.kind==2:
                    entry=pending.pop((event.node,event.handle),None)
                    log(dict(event='ack',node=event.node,handle=event.handle,ok=bool(event.ok),time=event.time))
                    if entry:nodes[event.node].ack(*entry,bool(event.ok),event.time)
            for node in nodes:node.expire(now)
        energy=[measure(i) for i in range(6)];total=sum(e[0] for e in energy)
        critical=[pid for pid in offered if pid%3==0]
        row=dict(seed=seed,setting=setting,arm=arm,offered=60,delivered=len(sink_times),
            delivery=len(sink_times)/60,verified_receipts=len(nodes[0].source_deliveries)/60,
            critical_violation=sum(pid not in sink_times or sink_times[pid]-offered[pid]>.09 for pid in critical)/len(critical),
            total_radio_j=total,energy_per_delivered_byte=total/(16*len(sink_times)) if sink_times else None,
            decisions=sum(n.decisions for n in nodes),multichoice=sum(n.multichoice for n in nodes),
            source_choices={str(p):sum(t['event']=='decision' and t['state']['node']==0 and t['chosen']==p for t in trace) for p in [1,2]},
            source_receipts=nodes[0].source_deliveries,radio_energy=energy,send_rejections=send_rejections,fault_drops=faults)
        assert not send_rejections
        path=out/f'{seed}_{setting}_{arm}.jsonl.gz'
        path.write_bytes(gzip.compress(('\n'.join(json.dumps(t,separators=(',',':')) for t in trace)+'\n').encode(),mtime=0))
        row['trace_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();summaries.append(row)
        (out/'summary.json').write_text(json.dumps(summaries,indent=2));lib.wire_destroy()
      print(seed,'completed',flush=True)
    (out/'provenance.json').write_text(json.dumps(dict(protocol_sha256=hashlib.sha256(protocol_path.read_bytes()).hexdigest(),runs=len(summaries),physical_validation=False,mcu_emulation=False,scope='host policy and real ns3 byte transport; no embedded CPU/firmware claim'),indent=2))

if __name__=='__main__':main()
