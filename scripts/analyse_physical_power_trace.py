"""Integrate operator-supplied SI-unit power traces; never certify provenance."""
import argparse,csv,json,math,hashlib
from pathlib import Path

def integrate(rows,max_gap_s=None):
 previous=None;first=None;energy=0.;samples=0
 for row in rows:
  t,v,i=(float(row[k]) for k in ('time_s','voltage_v','current_a'))
  if not all(math.isfinite(x) for x in (t,v,i)) or v<=0 or i<0:raise ValueError('Nonfinite or invalid voltage/current')
  if previous is not None:
   dt=t-previous[0]
   if dt<=0:raise ValueError('Timestamps must strictly increase')
   if max_gap_s is not None and dt>max_gap_s:raise ValueError('Unrecorded acquisition gap exceeds declared limit')
   energy+=dt*(previous[1]+v*i)/2
  else:first=t
  previous=(t,v*i);samples+=1
 if samples<2:raise ValueError('At least two physical samples required')
 duration=previous[0]-first
 return dict(energy_j=energy,duration_s=duration,mean_power_w=energy/duration,samples=samples)

def main():
 p=argparse.ArgumentParser();p.add_argument('--trace',type=Path,required=True);p.add_argument('--metadata',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 m=json.loads(a.metadata.read_text())
 required=['board_model','board_serial','meter_model','meter_serial','calibration_record','supply_boundary','firmware_sha256','packet_capture_sha256','sampling_rate_hz','operator','acquired_at']
 if any(k not in m or m[k] in ('',None) for k in required):raise ValueError('Incomplete acquisition metadata')
 for k in ['firmware_sha256','packet_capture_sha256']:
  if len(m[k])!=64 or any(c not in '0123456789abcdef' for c in m[k]):raise ValueError('Invalid artifact SHA256')
 if not math.isfinite(float(m['sampling_rate_hz'])) or float(m['sampling_rate_hz'])<=0:raise ValueError('Invalid sampling rate')
 gap=float(m.get('max_sample_gap_s',2/float(m['sampling_rate_hz'])))
 if not math.isfinite(gap) or gap<=0:raise ValueError('Invalid maximum acquisition gap')
 with a.trace.open(newline='') as f:result=integrate(csv.DictReader(f),gap)
 result['max_sample_gap_s']=gap
 result.update(status='trace_integrity_passed',physical_validation_certified=False,provenance='operator-provided, not independently established by this script',metadata=m,trace_sha256=hashlib.sha256(a.trace.read_bytes()).hexdigest())
 a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
