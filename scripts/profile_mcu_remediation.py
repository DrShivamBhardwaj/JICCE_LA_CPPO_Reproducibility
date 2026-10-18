"""Descriptive stage profiles from the public O3 UART captures."""
from pathlib import Path
import json,collections,statistics
R=Path(__file__).resolve().parents[1];P=R/'outputs/mcu_deadline_v1'
def main():
    result=[]
    for topology in ['chain','choice']:
        v=json.loads((P/(topology+'_100')/'verification.json').read_text());groups=collections.defaultdict(list)
        for f in (P/(topology+'_100')).glob('uart_*.jsonl'):
            for line in f.read_text().splitlines():
                x=json.loads(line)
                if x['event']=='stage_time':groups[(x['node'],x['stage'])].append(x['elapsed_ms'])
        result.append({'topology':topology,'stages':[{'node':n,'stage':s,'count':len(a),'min_ms':min(a),'median_ms':statistics.median(a),'max_ms':max(a)} for (n,s),a in sorted(groups.items())],'misses_by_traffic':{str(t):sum(x['traffic']==t and x['receipt_delay_ms']>[90,350,1500][t] for x in v['emulated_receipt_delays']) for t in range(3)}})
    out={'classification':'Exploratory stage profiling of retained O3 pilot; emulator milliseconds, not physical timing or energy','rows':result}
    (P/'stage_profile.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
