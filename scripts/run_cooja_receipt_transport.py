"""Separate fixed-chain native Cooja crypto/radio diagnostic; no MCU cycle claim."""
from pathlib import Path
import argparse,json,subprocess,os,hashlib,xml.etree.ElementTree as ET

def main():
 p=argparse.ArgumentParser();p.add_argument('--contiki',type=Path,required=True);p.add_argument('--java',type=Path,required=True);p.add_argument('--make-bin',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 r=Path(__file__).resolve().parents[1];out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
 if any(out.iterdir()):raise SystemExit('Refusing to overwrite existing experiment directory')
 cooja=a.contiki.resolve()/'tools/cooja';jar=cooja/'build/libs/cooja.jar';runs=[]
 protocol={'scope':'Native Cooja CSMA fixed-chain authenticated transport, not full policy/credit equivalence or physical validation','seeds':[91001,91002,91003],'udgm_rx_probabilities':[1.0,0.9,0.7],'offered_per_run':100,'source_interval_s':1,'nodes':4,'spacing_m':30,'transmitting_range_m':40,'interference_range_m':80,'frame_application_bytes':100,'public_test_keys':True,'attention_policy_executed':False,'passive_credit_implemented':False,'physical_energy_measured':False,'native_cpu_cost_modelled':False,'freeze_source_sha256':hashlib.sha256((r/'hardware/cooja_receipt_transport/receipt-transport.c').read_bytes()).hexdigest(),'contiki_commit':subprocess.check_output(['git','-C',str(a.contiki),'rev-parse','HEAD'],text=True).strip(),'cooja_commit':subprocess.check_output(['git','-C',str(cooja),'rev-parse','HEAD'],text=True).strip(),'cooja_jar_sha256':hashlib.sha256(jar.read_bytes()).hexdigest()}
 (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
 env=os.environ.copy();env['JAVA_HOME']=str(a.java.parent.parent);env['PATH']=str(a.java.parent)+(':'+str(a.make_bin) if a.make_bin else '')+':'+env['PATH']
 for rx in protocol['udgm_rx_probabilities']:
  for seed in protocol['seeds']:
   folder=out/f'rx{rx}_seed{seed}';folder.mkdir();tree=ET.parse(r/'hardware/cooja_receipt_transport/chain.csc');sim=tree.find('simulation');sim.find('randomseed').text=str(seed);sim.find('radiomedium/success_ratio_rx').text=str(rx);mt=sim.find('motetype');mt.find('source').text=str(r/'hardware/cooja_receipt_transport/receipt-transport.c');mt.find('commands').text='make receipt-transport.cooja TARGET=cooja CONTIKI='+str(a.contiki.resolve());cfg=folder/'simulation.csc';tree.write(cfg,encoding='UTF-8',xml_declaration=True)
   cmd=[str(a.java),'--enable-native-access=ALL-UNNAMED','-jar',str(jar),'--no-gui','--no-log-color','--contiki',str(a.contiki.resolve()),'--cooja',str(cooja),'--logdir',str(folder),str(cfg)]
   with (folder/'console.log').open('w') as log:ret=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
   rec={'seed':seed,'rx_probability':rx,'returncode':ret.returncode,'folder':str(folder.relative_to(r)),'command':cmd};runs.append(rec);(out/'runs.json').write_text(json.dumps(runs,indent=2)+'\n');print(folder.name,ret.returncode,flush=True)
   if ret.returncode:raise SystemExit('Cooja execution failure; inspect retained console log')
if __name__=='__main__':main()
