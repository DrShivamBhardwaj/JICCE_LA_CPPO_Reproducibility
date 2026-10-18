"""Audit actor/crypto boot vectors and radio probes in the same CC2538 image.

Live routing feature construction and packet authentication remain on the host.
"""
from pathlib import Path
import argparse,subprocess,time,json,struct,hashlib,tempfile
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import serial,socket
r=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--renode',type=Path,required=True);a=p.parse_args();exe=a.renode.resolve()
out=r/'outputs/cc2538_boot_selftest';ref=json.loads((r/'hardware/cortex_m3_validation/generated/reference.json').read_text())
report=dict(status='failed',live_routing_on_mcu=False,live_packet_authentication_on_mcu=False,physical_validation=False)
(out/'execution.json').write_text(json.dumps(report,indent=2)+'\n')
with tempfile.TemporaryDirectory(prefix='wsn-combined-') as td, (out/'renode.log').open('w') as log:
 socks=[socket.socket() for _ in range(2)]
 for x in socks:x.bind(('127.0.0.1',0))
 portnums=[x.getsockname()[1] for x in socks]
 for x in socks:x.close()
 lines=['emulation CreateIEEE802_15_4Medium "wireless"','wireless SetRangeWirelessFunction 40']
 for i in range(2):
  uart=out/f'uart_{i}.txt';uart.unlink(missing_ok=True)
  lines += [f'mach create "node{i}"','using sysbus',f'machine LoadPlatformDescription @{exe.parent}/platforms/cpus/cc2538.repl',f'sysbus LoadELF @{out}/firmware.elf',f'sysbus WriteDoubleWord `sysbus GetSymbolAddress "node_id"` {i}','cpu VectorTableOffset 0x200000',f'emulation CreateServerSocketTerminal {portnums[i]} "term{i}" false',f'connector Connect sysbus.uart0 term{i}',f'sysbus.uart0 CreateFileBackend @{uart} true','connector Connect sysbus.radio wireless',f'wireless SetPosition sysbus.radio {i*30} 0 0','mach clear']
 lines+=['start'];script=out/'boot.resc';script.write_text('\n'.join(lines)+'\n')
 child=subprocess.Popen([str(exe),'--disable-gui','--plain','-P','-1','-e',f'include @{script}'],stdout=log,stderr=log)
 try:
  deadline=time.monotonic()+120
  while True:
   texts=[(out/f'uart_{i}.txt').read_text() if (out/f'uart_{i}.txt').exists() else '' for i in range(2)]
   if all('"event":"ready"' in t for t in texts):break
   if any('SELFTEST_FAILED' in t for t in texts):raise RuntimeError('Firmware rejected self-test')
   if child.poll() is not None:raise RuntimeError('Renode exited; inspect log')
   if time.monotonic()>deadline:raise TimeoutError('Boot deadline')
   time.sleep(.1)
  ports=[serial.serial_for_url(f'socket://127.0.0.1:{portnums[i]}',timeout=3) for i in range(2)]
  probes=[];transport_preamble=[]
  def issue(c):ports[0].write((json.dumps(c)+'\n').encode())
  def read(i):
   deadline=time.monotonic()+10
   while time.monotonic()<deadline:
    raw=ports[i].readline()
    if not raw:raise TimeoutError(f'No response from node {i}')
    start=raw.find(b'{')
    if start>=0:
     if start:transport_preamble.append(dict(node=i,raw_hex=raw[:start].hex()))
     record=json.loads(raw[start:])
     if record.get('event')=='ready':continue
     return record
    transport_preamble.append(dict(node=i,raw_hex=raw.hex()))
   raise TimeoutError('No JSON UART record')
  try:
   issue(dict(command='telemetry'));v=read(0);assert v['provenance']=='emulated_no_power_model';probes.append(dict(test='telemetry',record=v))
   wire=bytes(range(114)).hex();issue(dict(command='tx',token=9001,peer=1,wire=wire));ack=read(0);rx=read(1)
   assert ack==dict(event='ack',token=9001,ok=True) and rx['wire']==wire and rx['peer']==0
   probes.append(dict(test='114_byte_delivery_and_mac_ack',ack=ack,rx=rx))
   for token,bad in [(9002,'00'*115),(9003,'zz')]:
    issue(dict(command='tx',token=token,peer=1,wire=bad));ack=read(0);assert ack==dict(event='ack',token=token,ok=False);probes.append(dict(test='oversize' if token==9002 else 'invalid_hex',ack=ack))
   issue(dict(command='tx',token=9004,peer=3,wire='0102'));ack=read(0);assert ack==dict(event='ack',token=9004,ok=False);probes.append(dict(test='absent_peer_no_ack',ack=ack))
  finally:
   for port in ports:port.close()
 finally:
  if child.poll() is None:child.terminate()
  child.wait(timeout=10)
errors=[]
for i,txt in enumerate(texts):
 rows=[x.split() for x in txt.splitlines() if x.startswith('ACTOR ')]
 assert len(rows)==16
 for n,(row,case) in enumerate(zip(rows,ref['cases'])):
  assert int(row[1],16)==n and int(row[2],16)==case['action']
  vals=[struct.unpack('!f',bytes.fromhex(s))[0] for s in row[3:]];assert len(vals)==8
  errors.extend(abs(v-e) for v,e in zip(vals,case['logits']))
 assert max(errors)<1e-5
 assert 'HMAC b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7' in txt
 assert 'ED25519 00000000 ffffffff' in txt and 'DONE 00000000' in txt
 sig=bytes.fromhex(next(x.split()[1] for x in txt.splitlines() if x.startswith('SIGNATURE ')))
 Ed25519PrivateKey.from_private_bytes(bytes([42])*32).public_key().verify(sig,b'JICCE-sink-v1\0'+struct.pack('!HIQ',0,7,100))
report.update(status='passed',boot_selftest_nodes=2,actor_cases_per_node=16,matching_actions=32,compared_logits=len(errors),max_logit_error=max(errors),hmac_known_answer=True,ed25519_independently_verified=True,corrupt_signature_rejected=True,radio_probes=probes,transport_preamble=transport_preamble,elf_sha256=hashlib.sha256((out/'firmware.elf').read_bytes()).hexdigest(),compiler=subprocess.check_output(['zig','version'],text=True).strip(),emulator=subprocess.check_output([str(exe),'--version'],text=True).strip(),scope='Boot-vector and radio coexistence tests only. No live MCU routing, live packet crypto, physical RF/energy or worst-case timing validation.')
(out/'execution.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
