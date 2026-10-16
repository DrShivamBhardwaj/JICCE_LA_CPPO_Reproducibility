"""Host-driven 802.15.4 radio integration; requires matching board firmware.
This is not evidence of embedded crypto timing or physical validation by itself.
"""
import argparse,json,time,sys,os,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wsn_sim.distributed_auth import Channel,Node
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey,Ed25519PublicKey

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,required=True);ap.add_argument('--port',required=True);ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--duration',type=float,default=60);ap.add_argument('--packets',type=int,default=0);ap.add_argument('--policy',choices=['greedy','attention','mlp'],default='greedy');ap.add_argument('--checkpoint',type=Path);args=ap.parse_args()
    import serial
    cfg=json.loads(args.config.read_text());keys={int(k):bytes.fromhex(v) for k,v in cfg['keys'].items()};ch=Channel(cfg['node'],cfg['session'],keys,{int(k):v for k,v in cfg['peer_sessions'].items()});signer=Ed25519PrivateKey.from_private_bytes(bytes.fromhex(cfg['sink_private'])) if 'sink_private' in cfg else None
    node_args=(cfg['node'],cfg['xy'],cfg['sink'],cfg['sink_xy'],ch,Ed25519PublicKey.from_public_bytes(bytes.fromhex(cfg['sink_public'])),signer)
    if args.policy=='greedy':node=Node(*node_args)
    else:
        if args.checkpoint is None:ap.error('--checkpoint is required for a learned policy')
        import torch
        torch.set_num_threads(1)
        from wsn_sim.auth_policy import PolicyNode,load_policy
        node=PolicyNode(*node_args,arm=args.policy,model=load_policy(args.checkpoint,args.policy))
    # An exclusive persistent marker prevents replay-window reset with a reused
    # session. It is intentionally not removed on exit or after a crash.
    marker=args.config.with_suffix('.used');fd=os.open(marker,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
    start=time.monotonic();pending={};accepted_source_receipts=set();token=0;pid=0;next_beacon=0.;next_data=2.
    with serial.Serial(args.port,115200,timeout=.01) as port,args.capture.open('x') as capture:
        def log(event,**fields):capture.write(json.dumps(dict(event=event,host_monotonic_s=time.monotonic(),node=node.id,**fields))+'\n');capture.flush()
        def send(peer,wire):
            nonlocal token
            if len(pending)>=256:log("host_tx_capacity");return
            token+=1;pending[token]=(peer,wire,time.monotonic()+2.);port.write((json.dumps(dict(command='tx',token=token,peer=peer,wire=wire.hex()))+'\n').encode());log('tx',peer=peer,token=token,wire=wire.hex())
        log('session',session=cfg['session'],clock='common host monotonic; USB latency included',physical_radio_claim='requires operator run and capture validation')
        while time.monotonic()-start<args.duration:
            now=time.monotonic();elapsed=now-start
            if elapsed>=next_beacon:
                # Hardware telemetry is intentionally not fabricated. Firmware
                # must report energy_fraction and queue before cache exchange.
                port.write(b'{"command":"telemetry"}\n');next_beacon+=.5
            if pid<args.packets and elapsed>=next_data:
                for peer,wire in node.originate(pid,pid%3,b'0123456789abcdef',now):send(peer,wire)
                pid+=1;next_data+=.2
            line=port.readline()
            if line:
                # readline can block. Authenticate freshness against reception
                # time, not the timestamp sampled before waiting for bytes.
                now=time.monotonic()
                r=json.loads(line);kind=r.get('event');log('board',record=r)
                if kind=='rx':
                    actions=node.receive_with_lqi(bytes.fromhex(r['wire']),int(r['peer']),now,int(r.get('lqi',0))) if hasattr(node,'receive_with_lqi') else node.receive(bytes.fromhex(r['wire']),int(r['peer']),now)
                    for key,record in node.pending.items():
                        if key[0]==node.id and record.receipt:accepted_source_receipts.add(key)
                    for peer,wire in actions:send(peer,wire)
                elif kind=='ack':
                    old=pending.pop(int(r['token']),None)
                    if old:node.ack(old[0],old[1],bool(r['ok']),now)
                elif kind=='telemetry':
                    if hasattr(node,'own'):node.own=(float(r['energy_fraction']),float(r['queue']))
                    for peer in cfg['neighbors']:
                        dst,wire=node.beacon(peer,float(r['energy_fraction']),int(r['queue']),now);send(dst,wire)
            node.expire(now)
            for handle,(_,_,expiry) in list(pending.items()):
                if now>=expiry:del pending[handle];log("missing_mac_confirm",token=handle)
        log('final',sink_delivered=node.delivered_total,settlements=node.settlements,debts=node.debts,rejects=node.rejects,max_pending=node.max_pending,accepted_source_receipts=len(accepted_source_receipts),offered_packets=pid)
if __name__=='__main__':main()
