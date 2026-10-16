"""Validate completeness and integrate actual timestamped current samples.
No synthetic fixture is accepted as physical validation evidence by default.
"""
import argparse,csv,json,math
from pathlib import Path

def validate(samples):
    if len(samples)<2:raise ValueError('at least two physical current samples required')
    values=[]
    for r in samples:
        if r['provenance']!='physical':raise ValueError('physical provenance required')
        t,v,i=map(float,[r['time_s'],r['voltage_v'],r['current_a']])
        if not all(math.isfinite(x) for x in [t,v,i]) or v<=0 or i<0:raise ValueError('invalid current/voltage/time')
        values.append((t,v*i))
    if any(b[0]<=a[0] for a,b in zip(values,values[1:])):raise ValueError('timestamps must strictly increase')
    return sum((b[0]-a[0])*(b[1]+a[1])/2 for a,b in zip(values,values[1:]))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--current-csv',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    with args.current_csv.open() as f:energy=validate(list(csv.DictReader(f)))
    args.output.write_text(json.dumps(dict(measured_energy_j=energy,scope='current integration only; provenance labels are operator assertions, not independent attestation'),indent=2))
if __name__=='__main__':main()
