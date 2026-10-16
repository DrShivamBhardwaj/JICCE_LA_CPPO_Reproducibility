"""Run compiled ARM bridge firmware on four Renode CC2538 machines.

Routing/inference and crypto stay in actual host adapter processes. The MCU
executes UART parsing, frame bounds, radio FIFOs and ACK correlation. Renode's
range medium is an abstraction, not an ns3-equivalent PHY or a power instrument.
"""
import argparse,hashlib,json,os,subprocess,sys,tempfile,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--renode',type=Path,required=True)
    ap.add_argument('--policy',choices=['greedy','attention','mlp'],default='attention')
    ap.add_argument('--output',type=Path);args=ap.parse_args()
    exe=args.renode.resolve();runtime=exe.parent
    out=(args.output or ROOT/'outputs/renode_boards'/f'{args.policy}_{uuid.uuid4().hex[:8]}').resolve()
    out.mkdir(parents=True,exist_ok=False)
    elf=out/'cc2538_bridge.elf';source=ROOT/'hardware/renode_cc2538/bridge.c';link=source.with_name('link.ld')
    build=[sys.executable,'-m','ziglang','cc','-target','thumb-freestanding-eabi','-mcpu=cortex_m3','-g','-Os','-ffreestanding','-fno-builtin','-nostdlib',f'-Wl,-T,{link}','-Wl,--build-id=none','-Wl,-e,Reset_Handler',str(source),'-o',str(elf)]
    result=subprocess.run(build,capture_output=True,text=True);(out/'build.log').write_text(result.stdout+result.stderr);result.check_returncode()
    version=subprocess.run([str(exe),'--version'],capture_output=True,text=True,check=True).stdout
    checkpoint=ROOT/f"outputs/jicce_validation/checkpoints/{'capacity_mlp' if args.policy=='mlp' else 'attention'}_41001.pt" if args.policy!='greedy' else None
    children=[];handles=[];emulator=None;probes=[]
    with tempfile.TemporaryDirectory(prefix='wsn-mcu-private-') as tmpdir:
      tmp=Path(tmpdir);private=tmp/'keys'
      subprocess.run([sys.executable,str(ROOT/'hardware/provision.py'),'--output',str(private)],check=True)
      sink_public=json.loads((private/'node_3.private.json').read_text())['sink_public']
      lines=['emulation CreateIEEE802_15_4Medium "wireless"','wireless SetRangeWirelessFunction 40']
      for i in range(4):
        lines += [f'mach create "node{i}"','using sysbus',f'machine LoadPlatformDescription @{runtime}/platforms/cpus/cc2538.repl',f'sysbus LoadELF @{elf}',f'sysbus WriteDoubleWord `sysbus GetSymbolAddress "node_id"` {i}','cpu VectorTableOffset 0x200000',f'emulation CreateUartPtyTerminal "term{i}" "{tmp}/uart{i}"',f'connector Connect sysbus.uart0 term{i}',f'sysbus.uart0 CreateFileBackend @{out}/firmware_uart_{i}.jsonl true','connector Connect sysbus.radio wireless',f'wireless SetPosition sysbus.radio {30*i} 0 0','mach clear']
      lines+=['start'];script=out/'chain.resc';script.write_text('\n'.join(lines)+'\n')
      log=open(out/'renode.log','w');handles.append(log)
      try:
        emulator=subprocess.Popen([str(exe),'--disable-gui','--plain','-P','-1','-e',f'include @{script}'],stdout=log,stderr=log)
        deadline=time.monotonic()+25
        while not all((out/f'firmware_uart_{i}.jsonl').exists() and '"event":"ready"' in (out/f'firmware_uart_{i}.jsonl').read_text() for i in range(4)):
            if emulator.poll() is not None:raise RuntimeError('Renode exited during initialization')
            if time.monotonic()>deadline:raise TimeoutError('Emulated UARTs did not initialize')
            time.sleep(.05)
        import serial
        ports=[serial.Serial(str(tmp/f'uart{i}'),115200,timeout=1) for i in range(4)]
        def issue(command):ports[0].write((json.dumps(command)+'\n').encode())
        def read(i):
            raw=ports[i].readline()
            if not raw:raise TimeoutError(f'No UART response from node {i}')
            return json.loads(raw)
        try:
            issue(dict(command='telemetry'));telemetry=read(0)
            assert telemetry['provenance']=='emulated_no_power_model';probes.append(dict(test='telemetry_label',record=telemetry))
            wire=bytes(range(114)).hex();issue(dict(command='tx',token=9001,peer=1,wire=wire));ack=read(0);rx=read(1)
            assert ack==dict(event='ack',token=9001,ok=True) and rx['wire']==wire and rx['peer']==0
            probes.append(dict(test='114_byte_wire_and_real_emulated_mac_ack',ack=ack,rx=rx))
            for token,bad in [(9002,'00'*115),(9003,'zz')]:
                issue(dict(command='tx',token=token,peer=1,wire=bad));ack=read(0)
                assert ack==dict(event='ack',token=token,ok=False);probes.append(dict(test='oversize' if token==9002 else 'invalid_hex',ack=ack))
            issue(dict(command='tx',token=9004,peer=3,wire='0102'));ack=read(0)
            assert ack==dict(event='ack',token=9004,ok=False) and not ports[3].readline()
            probes.append(dict(test='out_of_range_no_delivery_no_ack',ack=ack))
        finally:
            for port in ports:port.close()
        for i in range(4):
            childlog=open(out/f'host_{i}.log','w');handles.append(childlog)
            command=[sys.executable,str(ROOT/'hardware/serial_adapter.py'),'--config',str(private/f'node_{i}.private.json'),'--port',str(tmp/f'uart{i}'),'--capture',str(out/f'node_{i}.jsonl'),'--duration','6','--packets','10' if i==0 else '0','--policy',args.policy]
            if checkpoint:command+=['--checkpoint',str(checkpoint)]
            children.append(subprocess.Popen(command,stdout=childlog,stderr=childlog))
        for child in children:
            child.wait(timeout=25)
            if child.returncode:raise RuntimeError('Host adapter exited; inspect retained host log')
        finals=[]
        for i in range(4):
            records=[json.loads(x) for x in (out/f'node_{i}.jsonl').read_text().splitlines()]
            finals.append(next(r for r in records if r['event']=='final'))
        assert finals[3]['sink_delivered']>0 and all(f['settlements']>0 for f in finals[:3]),finals
        (out/'probes.json').write_text(json.dumps(probes,indent=2))
        report=dict(status='passed',policy=args.policy,virtual_mcus=4,emulated_cpu='ARM Cortex-M3 / CC2538',compiled_firmware_executed=True,
            host_policy_and_crypto=True,physical_validation=False,physical_firmware_flash_ready=False,energy_validation=False,
            radio_model='Renode range medium: deterministic reachability; no calibrated RF or power model',
            offered=10,sink_delivered=finals[3]['sink_delivered'],final_records=finals,firmware_probes=len(probes),
            firmware_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),firmware_elf_sha256=hashlib.sha256(elf.read_bytes()).hexdigest(),
            checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest() if checkpoint else None,sink_public_key=sink_public,renode_version=version.strip(),
            zig_version=subprocess.run([sys.executable,'-m','ziglang','version'],capture_output=True,text=True,check=True).stdout.strip())
        (out/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
      except Exception as error:
        (out/'failed.json').write_text(json.dumps(dict(status='failed',error=str(error),policy=args.policy,probes=probes),indent=2));raise
      finally:
        for child in children:
            if child.poll() is None:child.terminate();child.wait(timeout=5)
        if emulator is not None and emulator.poll() is None:emulator.terminate();emulator.wait(timeout=8)
        for f in handles:f.close()

if __name__=='__main__':main()
