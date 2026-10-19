"""Recheck all retained Cooja state counters and analyze an explicit current sensitivity."""
from pathlib import Path
import collections,csv,gzip,hashlib,json,re,statistics
R=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent;O=R/'outputs/cooja_radio_energy_v1'
plan=json.loads((D/'plan.json').read_text());root=R/plan['dataset'];rows=[];hashes={}
expected={(seed,attack,timing,arm) for seed in range(93001,93031) for attack in (0,1) for timing in (0,1) for arm in ['censored','active','naive','frozen','censored_proof']}
seen=set()
for folder in sorted(root.iterdir()):
 if not folder.is_dir() or not folder.name.startswith('seed'):continue
 a=json.loads((folder/'audit.json').read_text());key=(a['seed'],a['attack'],a['timing'],a['arm'])
 if key in seen or key not in expected:raise ValueError('Duplicate or unexpected case')
 seen.add(key);raw=gzip.decompress((folder/'COOJA.testlog.gz').read_bytes());sha=hashlib.sha256(raw).hexdigest()
 if a['status']!='independent_audit_passed' or sha!=a['log_sha256']:raise ValueError('Capture/audit mismatch')
 finals={}
 for line in raw.decode().splitlines():
  match=re.match(r'^(\d+) node-(\d+) (\{.*\})$',line)
  if not match:continue
  x=json.loads(match[3])
  if x['event']=='cooja_final':
   node=x['node']
   if node in finals or int(match[2])!=node+1:raise ValueError('Duplicate or unbound final node')
   if x['hz']<=0 or any(x[k]<0 for k in ['tx','listen','cpu','lpm']):raise ValueError('Invalid state counter')
   if x['tx']+x['listen']!=x['cpu']+x['lpm']:raise ValueError('Radio state conservation failure')
   if x['tx_queue_overflows'] or x['rx_queue_overflows']:raise ValueError('Queue overflow')
   finals[node]=x
 if set(finals)!={0,1,2,3}:raise ValueError('Incomplete final node coverage')
 offered=sum(x['offered'] for x in finals.values());delivered=sum(x['delivered'] for x in finals.values());receipts=sum(x['receipts'] for x in finals.values())
 # Relays also log accepted receipts; the endpoint is source node zero only.
 receipts=finals[0]['receipts']
 if (offered,delivered,receipts)!=(a['offered'],a['delivered'],a['source_receipts']) or offered!=60:raise ValueError('Endpoint mismatch')
 tx=sum(x['tx']/x['hz'] for x in finals.values());listen=sum(x['listen']/x['hz'] for x in finals.values())
 if abs(tx-a['total_tx_state_s'])>1e-9:raise ValueError('TX audit mismatch')
 for state in a['radio_state_seconds']:
  x=finals[state['node']]
  if abs(x['tx']/x['hz']-state['tx_s'])>1e-9 or abs(x['listen']/x['hz']-state['listen_s'])>1e-9:raise ValueError('Per-node state mismatch')
 row=dict(case_id=folder.name,seed=a['seed'],attack=a['attack'],timing=a['timing'],arm=a['arm'],offered=offered,delivered=delivered,source_receipts=receipts,delivery=delivered/offered,receipt_fraction=receipts/offered,tx_seconds=tx,listen_seconds=listen,tx_fraction=tx/(tx+listen))
 for ratio in [.5,1,2,3]:row['normalized_energy_s_r'+str(ratio)]=listen+ratio*tx
 rows.append(row);hashes[folder.name]={'decompressed_log_sha256':sha,'audit_sha256':hashlib.sha256((folder/'audit.json').read_bytes()).hexdigest()}
if seen!=expected or len(rows)!=600:raise ValueError('Incomplete declared case coverage')
groups=collections.defaultdict(list)
for row in rows:groups[(row['attack'],row['timing'],row['arm'])].append(row)
summary=[]
for (attack,timing,arm),values in sorted(groups.items()):
 summary.append(dict(attack=attack,timing=timing,arm=arm,runs=len(values),**{key:statistics.mean(v[key] for v in values) for key in ['delivery','receipt_fraction','tx_seconds','listen_seconds','tx_fraction','normalized_energy_s_r0.5','normalized_energy_s_r1','normalized_energy_s_r2','normalized_energy_s_r3']}))
O.mkdir(parents=True,exist_ok=True)
with (O/'run_metrics.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
result=dict(status='passed_600_capture_and_radio_state_rechecks',runs=600,nodes_verified=2400,offered_packets=sum(r['offered'] for r in rows),classification=plan['classification'],physical_validation=False,physical_current_measured=False,new_simulations_executed=0,plan_sha256=hashlib.sha256((D/'plan.json').read_bytes()).hexdigest(),summary=summary,interpretation=plan['boundaries'],energy_model='E_radio = V * I_listen * (T_listen + r*T_tx), r=I_tx/I_listen. Coefficient has units seconds, not joules; CPU and other components excluded.')
(O/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');(O/'capture_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='summary'},indent=2))
