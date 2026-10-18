"""Independent public-fixture wire, count, latency and Energest reconciliation."""
from pathlib import Path
import argparse,collections,hashlib,hmac,json,re,statistics
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature

def audit_run(folder,rx):
 folder=Path(folder);text=(folder/'COOJA.testlog').read_text();records=[]
 for line in text.splitlines():
  m=re.match(r'^(\d+) node-(\d+) (.*)$',line)
  if m:records.append((int(m[1]),int(m[2]),m[3]))
 assert 'TEST OK' in text,'Cooja did not finish'
 offers={};deliveries=[];receipts=[];finals={};proofs=set();badproofs=0;wirecount=0;rejects=collections.Counter()
 pub=Ed25519PrivateKey.from_private_bytes(bytes(range(1,33))).public_key()
 for time,node,msg in records:
  values=dict(re.findall(r'(\w+)=([^ ]+)',msg))
  if msg.startswith('WIRE '):
   w=bytes.fromhex(values['hex']);assert len(w)==100 and w[1]==node and w[2]==int(values['next'])
   key=bytes((17*i+31*min(w[1],w[2])+7*max(w[1],w[2]))%256 for i in range(32))
   assert hmac.compare_digest(hmac.new(key,w[:20]+w[36:],hashlib.sha256).digest()[:16],w[20:36])
   assert int.from_bytes(w[4:8],'big')==int(values['seq']) and w[0]==int(values['kind'])
   if w[0]==3:
    try:pub.verify(w[36:],w[4:20]);proofs.add(int(values['seq']))
    except InvalidSignature:
     assert node==4 and int(values['seq'])==100 and w[36:]==bytes(64),'Unexpected invalid signed proof'
     badproofs+=1
   wirecount+=1
  elif msg.startswith('OFFER '):
   assert node==1 and int(values['seq']) not in offers;offers[int(values['seq'])]=time
  elif msg.startswith('DELIVER '):assert node==4;deliveries.append(int(values['seq']))
  elif msg.startswith('RECEIPT '):
   assert node==1;receipts.append({'seq':int(values['seq']),'delay_ms':1000*int(values['ticks'])/int(values['hz'])})
  elif msg.startswith('REJECT '):rejects[values['type']]+=1
  elif msg.startswith('FINAL '):
   assert int(values['node'])==node and node not in finals;finals[node]={k:int(v) for k,v in values.items()}
 assert set(finals)=={1,2,3,4},'Missing per-node completion records'
 assert set(offers)==set(range(1,101)),'Not exactly 100 unique offered packets'
 assert len(set(deliveries))==len(deliveries) and set(deliveries)<=set(offers)
 seqs=[x['seq'] for x in receipts];assert len(set(seqs))==len(seqs) and set(seqs)<=set(deliveries) and set(seqs)<=proofs
 assert finals[1]['offered']==100 and finals[4]['delivered']==len(deliveries) and finals[1]['receipts']==len(receipts)
 assert sum(x['bad_hop'] for x in finals.values())==rejects['hop']
 assert sum(x['bad_signature'] for x in finals.values())==rejects['signature']
 assert sum(x['replay'] for x in finals.values())==rejects['replay']+rejects['receipt_replay']
 assert badproofs==1,'Forged-signature injection absent from transmitted wire log'
 energy=[]
 for node,v in sorted(finals.items()):
  hz=v['energy_hz'];assert hz>0 and v['tx']+v['listen']==v['cpu']+v['lpm']
  energy.append({'node':node,'cpu_s':v['cpu']/hz,'lpm_s':v['lpm']/hz,'tx_s':v['tx']/hz,'listen_s':v['listen']/hz})
 full=len(deliveries)==len(receipts)==100;controls=all(rejects[k]>=1 for k in ['hop','replay','signature'])
 if rx==1.0:assert full and controls,'Loss-free acceptance criteria not met'
 misses={str(d):sum(x['delay_ms']>d for x in receipts) for d in [90,350,1500]}
 return {'status':'audit_passed','packet_delivery_complete':full,'offered':100,'delivered':len(deliveries),'verified_receipts':len(receipts),'missing_receipts':100-len(receipts),'receipt_delay_ms':{'min':min(x['delay_ms'] for x in receipts) if receipts else None,'max':max(x['delay_ms'] for x in receipts) if receipts else None,'mean':statistics.mean(x['delay_ms'] for x in receipts) if receipts else None},'late_received_by_deadline_ms':misses,'missing_or_late_by_deadline_ms':{k:v+100-len(receipts) for k,v in misses.items()},'rejections':dict(rejects),'all_three_controls_observed':controls,'wire_hmac_records_verified':wirecount,'invalid_signature_injections_verified':badproofs,'energest_state_seconds':energy,'energy_j':None,'physical_validation':False,'mcu_cycle_timing_validated':False,'attention_policy_validated':False,'log_sha256':hashlib.sha256((folder/'COOJA.testlog').read_bytes()).hexdigest()}

def main():
 p=argparse.ArgumentParser();p.add_argument('--experiment',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[1];protocol=json.loads((a.experiment/'protocol.json').read_text());runs=json.loads((a.experiment/'runs.json').read_text());assert len(runs)==9
 expected={(s,rx) for s in protocol['seeds'] for rx in protocol['udgm_rx_probabilities']};assert {(x['seed'],x['rx_probability']) for x in runs}==expected
 reports=[]
 for run in runs:
  assert run['returncode']==0;d=audit_run(root/run['folder'],run['rx_probability']);d.update(seed=run['seed'],rx_probability=run['rx_probability']);(root/run['folder']/'audit.json').write_text(json.dumps(d,indent=2)+'\n');reports.append(d)
 result={'status':'independent_audit_passed','runs':reports,'scope':protocol['scope'],'physical_energy_measured':False,'native_cpu_cost_modelled':False,'not_a_confirmatory_comparative_study':True};(a.experiment/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
 for d in reports:print(d['seed'],d['rx_probability'],d['delivered'],d['verified_receipts'],d['receipt_delay_ms'],d['all_three_controls_observed'])
if __name__=='__main__':main()
