"""PTY serial firmware contract emulator backed by the ns-3 byte radio.

Runs the actual host adapter against four virtual serial ports. This does not
execute an MCU ISA, board firmware image, real UART or physical radio.
"""
import ctypes as C
import argparse,hashlib,json,os,pty,select,subprocess,sys,tempfile,time,tty,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from run_auth_policy import Event

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--policy',choices=['greedy','attention','mlp'],default='greedy')
    ap.add_argument('--output',type=Path)
    args=ap.parse_args()
    out=args.output or ROOT/'outputs/virtual_boards'/('recheck_'+args.policy+'_'+uuid.uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    checkpoint=ROOT/f"outputs/jicce_validation/checkpoints/{'capacity_mlp' if args.policy=='mlp' else 'attention'}_41001.pt" if args.policy!='greedy' else None
    # Generated secrets live in a temporary private directory and are deleted.
    with tempfile.TemporaryDirectory(prefix='jicce-private-') as tmp:
        private=Path(tmp)/'keys'
        subprocess.run([sys.executable,str(ROOT/'hardware/provision.py'),'--output',str(private)],check=True)
        lib=C.CDLL(str(ROOT/'build/libwsn_ns3_wire.so'))
        lib.wire_init.argtypes=[C.c_int,C.POINTER(C.c_double),C.c_int,C.c_double]
        lib.wire_step.argtypes=[C.c_double];lib.wire_poll.argtypes=[C.POINTER(Event)]
        lib.wire_send.argtypes=[C.c_int,C.c_int,C.POINTER(C.c_uint8),C.c_int]
        lib.wire_send.restype=C.c_int;lib.wire_energy.argtypes=[C.c_int,C.POINTER(C.c_double)]
        coords=(C.c_double*8)(0,0,30,0,60,0,90,0);lib.wire_init(4,coords,84001,40.)
        ports=[];children=[];logs=[];buffers=[b'']*4;tokens={};events=[];errors=[]
        try:
            for i in range(4):
                master,slave=pty.openpty();tty.setraw(slave);os.set_blocking(master,False);ports.append((master,slave))
                capture=out/f'node_{i}.jsonl'
                logfile=open(Path(tmp)/f'child_{i}.log','w+');logs.append(logfile)
                command=[sys.executable,str(ROOT/'hardware/serial_adapter.py'),'--config',str(private/f'node_{i}.private.json'),
                    '--port',os.ttyname(slave),'--capture',str(capture),'--duration','6','--packets','10' if i==0 else '0']
                command+=['--policy',args.policy]
                if checkpoint:command+=['--checkpoint',str(checkpoint)]
                children.append(subprocess.Popen(command,stdout=logfile,stderr=logfile))
            start=time.monotonic();sim=0.
            def emit(i,record):
                os.write(ports[i][0],(json.dumps(record)+'\n').encode());events.append(dict(node=i,record=record))
            while time.monotonic()-start<30 and any(c.poll() is None for c in children):
                ready,_,_=select.select([p[0] for p in ports],[],[],.001)
                for fd in ready:
                    i=next(i for i,p in enumerate(ports) if p[0]==fd)
                    try:buffers[i]+=os.read(fd,65536)
                    except BlockingIOError:continue
                    while b'\n' in buffers[i]:
                        line,buffers[i]=buffers[i].split(b'\n',1)
                        if not line:continue
                        command=json.loads(line);events.append(dict(node=i,command=command))
                        if command['command']=='telemetry':
                            values=(C.c_double*7)();lib.wire_energy(i,values)
                            emit(i,dict(event='telemetry',energy_fraction=max(0.,1-values[0]/.5),queue=int(values[6]),provenance='simulated'))
                        elif command['command']=='tx':
                            wire=bytes.fromhex(command['wire']);peer=int(command['peer'])
                            if len(wire)>114:raise ValueError('oversize application frame')
                            handle=lib.wire_send(i,peer,(C.c_uint8*len(wire)).from_buffer_copy(wire),len(wire))
                            if handle<0:emit(i,dict(event='ack',token=command['token'],ok=False))
                            else:tokens[i,handle]=command['token']
                target=time.monotonic()-start
                while sim+.001<=target:
                    lib.wire_step(.001);sim+=.001
                    event=Event()
                    while lib.wire_poll(C.byref(event)):
                        if event.kind==1:emit(event.node,dict(event='rx',peer=event.peer,wire=bytes(event.bytes[:event.length]).hex(),lqi=event.ok))
                        elif event.kind==2:
                            token=tokens.pop((event.node,event.handle),None)
                            if token is not None:emit(event.node,dict(event='ack',token=token,ok=bool(event.ok)))
            for i,c in enumerate(children):
                c.wait(timeout=3)
                if c.returncode:logs[i].seek(0);errors.append(dict(node=i,stderr=logs[i].read()))
            assert not errors,errors
            finals=[]
            for i in range(4):
                rows=[json.loads(x) for x in (out/f'node_{i}.jsonl').read_text().splitlines()]
                finals.append(next(x for x in rows if x['event']=='final'))
            assert finals[3]['sink_delivered']>0 and finals[0]['settlements']>0,finals
            (out/'firmware_contract.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in events))
            report=dict(status='passed',virtual_ports=4,host_adapters=4,offered=10,sink_delivered=finals[3]['sink_delivered'],
                final_records=finals,scope='PTY firmware API emulation + host crypto + simulated ns3 radio',
                physical_validation=False,mcu_isa_emulated=False,board_firmware_compiled=False,modeled_energy_only=True,
                policy=args.policy,checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest() if checkpoint else None,
                interpretation='single-path serial integration; not a policy performance comparison',
                host_adapter_sha256=hashlib.sha256((ROOT/'hardware/serial_adapter.py').read_bytes()).hexdigest())
            (out/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
        except Exception as error:
            (out/'failed.json').write_text(json.dumps(dict(status='failed',error=str(error),policy=args.policy,physical_validation=False),indent=2))
            raise
        finally:
            (out/'firmware_contract.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in events))
            for c in children:
                if c.poll() is None:c.terminate();c.wait(timeout=3)
            for a,b in ports:os.close(a);os.close(b)
            for f in logs:f.close()
            lib.wire_destroy()

if __name__=='__main__':main()
