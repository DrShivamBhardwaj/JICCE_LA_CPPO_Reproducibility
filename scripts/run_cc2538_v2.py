"""Host supplies traffic commands/captures; firmware selects/authenticates routes."""
from pathlib import Path
import argparse,subprocess,socket,time,json,sys,hashlib,struct,hmac,math
import numpy as np,uuid
import torch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r/'src'))
from wsn_sim.auth_policy import load_policy,observation
from wsn_sim.distributed_auth import HEADER,DOMAIN,SOURCE,SINK,Datagram
p=argparse.ArgumentParser();p.add_argument('--renode',type=Path,required=True);p.add_argument('--topology',choices=['chain','choice'],default='chain');p.add_argument('--output',type=Path);p.add_argument('--packets',type=int,default=10);a=p.parse_args();assert 1<=a.packets<=1000
exe=a.renode.resolve();out=(a.output or r/'outputs/cc2538_v2'/f'{a.topology}_{uuid.uuid4().hex[:8]}').resolve();out.mkdir(parents=True,exist_ok=False)
import secrets,os
sys.path.insert(0,str(r/'hardware/cc2538_live'))
from session_allocator import allocate
private_root=Path.home()/'Research/wsn-private-validation';private_root.mkdir(exist_ok=True);os.chmod(private_root,0o700)
sessions=allocate(private_root/'sessions.json')
keys={f'{i}:{j}':secrets.token_bytes(32) for i in range(4) for j in range(i+1,4)}
sink_seed=secrets.token_bytes(32);signer=Ed25519PrivateKey.from_private_bytes(sink_seed)
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
sink_pub=signer.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)
private=dict(keys={k:v.hex() for k,v in keys.items()},sink_seed=sink_seed.hex(),sessions=sessions)
private_path=private_root/(out.name+'.private.json');fd=os.open(private_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as f:json.dump(private,f)
def pair_key(i,j):return keys[f'{min(i,j)}:{max(i,j)}']
report=dict(elf_sha256=hashlib.sha256((r/'outputs/cc2538_v2/firmware.elf').read_bytes()).hexdigest(),status='failed',physical_validation=False,host_routing=False,host_packet_crypto=False,nominal_energy_fraction=1,operational_keys=False,private_fixture_file=str(private_path),sessions=sessions,sink_public=sink_pub.hex(),provisioning='per-run random keys; trusted emulator UART; persistent host boot allocator; not MCU NVM',private_key_commitments={k:hashlib.sha256(v).hexdigest() for k,v in keys.items()})
(out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
xy=[(0,0),(30,0),(60,0),(90,0)] if a.topology=='chain' else [(0,0),(45,0),(45,20),(90,0)];radius=40 if a.topology=='chain' else 52
edges=[(i,j) for i in range(4) for j in range(4) if i!=j and math.dist(xy[i],xy[j])<=radius]
socks=[socket.socket() for _ in range(4)]
for s in socks:s.bind(('127.0.0.1',0))
ports=[s.getsockname()[1] for s in socks]
for s in socks:s.close()
lines=['emulation CreateIEEE802_15_4Medium "wireless"',f'wireless SetRangeWirelessFunction {radius}']
for i in range(4):
 (out/f'uart_{i}.jsonl').unlink(missing_ok=True)
 lines += [f'mach create "node{i}"','using sysbus',f'machine LoadPlatformDescription @{exe.parent}/platforms/cpus/cc2538.repl',f'sysbus LoadELF @{r}/outputs/cc2538_v2/firmware.elf',f'sysbus WriteDoubleWord `sysbus GetSymbolAddress "node_id"` {i}','cpu VectorTableOffset 0x200000',f'emulation CreateServerSocketTerminal {ports[i]} "term{i}" false',f'connector Connect sysbus.uart0 term{i}',f'sysbus.uart0 CreateFileBackend @{out}/uart_{i}.jsonl true','connector Connect sysbus.radio wireless',f'wireless SetPosition sysbus.radio {xy[i][0]} {xy[i][1]} 0','mach clear']
lines+=['start'];script=out/'network.resc';script.write_text('\n'.join(lines)+'\n')
def records(i):
 f=out/f'uart_{i}.jsonl'
 if not f.exists():return []
 text=f.read_text();return [json.loads(l) for l in text.splitlines() if l.startswith('{') and l.endswith('}')]
def wait(fn,why,timeout=20):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  if child.poll() is not None:raise RuntimeError('Emulator exited')
  val=fn()
  if val:return val
  time.sleep(.005)
 raise TimeoutError(why)
with (out/'renode.log').open('w') as log:
 child=subprocess.Popen([str(exe),'--disable-gui','--plain','-P','-1','-e',f'include @{script}'],stdout=log,stderr=log)
 connections=[]
 try:
  wait(lambda:all(any(v['event']=='ready' for v in records(i)) for i in range(4)),'ready')
  connections=[socket.create_connection(('127.0.0.1',port),timeout=3) for port in ports]
  def issue(i,c):connections[i].sendall((json.dumps(c)+'\n').encode())
  for i in range(4):
   material=b''.join(pair_key(i,j) if i!=j else bytes(32) for j in range(4))+(sink_seed if i==3 else bytes(32))+sink_pub+b''.join(struct.pack('!Q',x) for x in sessions)
   issue(i,dict(command='provision_material',material=material.hex()))
  wait(lambda:all(any(v['event']=='provisioned' for v in records(i)) for i in range(4)),'provision')
  for i in range(4):issue(i,dict(command='local_start',x=xy[i][0],y=xy[i][1]))
  wait(lambda:all(any(v['event']=='local_started' for v in records(i)) for i in range(4)),'start')
  for pid in range(a.packets):
   for i,j in edges:
    before=len([v for v in records(i) if v['event']=='ack'])
    issue(i,dict(command='local_beacon',peer=j))
    wait(lambda i=i,before=before:len([v for v in records(i) if v['event']=='ack'])>before,'beacon MAC ACK')
   issue(0,dict(command='originate',pid=pid))
   wait(lambda pid=pid:any(v['event']=='local_receipt' and v['pid']==pid for v in records(0)),f'source receipt {pid}')
  # Exact replay and tag tamper travel over the emulated radio, not direct C calls.
  original=next(v for v in records(0) if v['event']=='local_tx' and bytes.fromhex(v['wire'])[1]==2)
  dst=original['peer'];before=len([v for v in records(dst) if v['event']=='reject'])
  issue(0,dict(command='tx',token=9001,peer=dst,wire=original['wire']))
  wait(lambda:len([v for v in records(dst) if v['event']=='reject'])>before,'replay rejection')
  bad=bytearray.fromhex(original['wire']);bad[-1]^=1;before+=1
  issue(0,dict(command='tx',token=9002,peer=dst,wire=bad.hex()))
  wait(lambda:len([v for v in records(dst) if v['event']=='reject'])>before,'tag rejection')
  def inject_authenticated(sender,dst,wire,seq,body):
   w=bytearray.fromhex(wire);w[14:18]=struct.pack('!I',seq);w[20:-16]=body
   key=pair_key(sender,dst);w[-16:]=hmac.digest(key,DOMAIN+w[:-16],'sha256')[:16]
   before=len([v for v in records(dst) if v['event']=='reject'])
   issue(sender,dict(command='tx',token=9100+sender,peer=dst,wire=w.hex()))
   wait(lambda:len([v for v in records(dst) if v['event']=='reject'])>before,'authenticated negative control')
  rs=[records(i) for i in range(4)]
  sender,v=next((i,v) for i in range(4) for v in reversed(rs[i]) if v['event']=='local_tx' and bytes.fromhex(v['wire'])[1]==2 and v['peer']==3)
  body=bytearray.fromhex(v['wire'])[20:-16];body[-1]^=1
  inject_authenticated(sender,3,v['wire'],100000,body)
  v=next(v for v in rs[original['peer']] if v['event']=='local_tx' and bytes.fromhex(v['wire'])[1]==3 and v['peer']==0)
  body=bytearray.fromhex(v['wire'])[20:-16];body[-1]^=1
  inject_authenticated(original['peer'],0,v['wire'],100000,body)
  w=bytearray.fromhex(original['wire']);w[6:14]=struct.pack('!Q',sessions[0]-1);w[14:18]=struct.pack('!I',100001);w[-16:]=hmac.digest(pair_key(0,dst),DOMAIN+w[:-16],'sha256')[:16]
  before=len([v for v in records(dst) if v['event']=='reject']);issue(0,dict(command='tx',token=9200,peer=dst,wire=w.hex()))
  wait(lambda:len([v for v in records(dst) if v['event']=='reject'])>before,'old boot session rejection')
  before=len([v for v in records(0) if v['event']=='reject']);issue(0,dict(command='provision_material',material=''))
  wait(lambda:len([v for v in records(0) if v['event']=='reject'])>before,'provision lock')
  for i in range(4):issue(i,dict(command='local_status'))
  wait(lambda:all(any(v['event']=='local_status' for v in records(i)) for i in range(4)),'status')
 finally:
  for s in connections:s.close()
  if child.poll() is None:child.terminate()
  child.wait(timeout=10)
from audit_cc2538_v2 import audit_run
report=audit_run(out,a.packets,a.topology)
(out/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
