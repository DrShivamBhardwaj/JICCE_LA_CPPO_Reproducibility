"""Describe failover and candidate/shield contribution without efficacy inference."""
import csv
import json
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
p = ROOT/'outputs/udp_persistent_fault'
rows = [json.loads(x) for x in (p/'trace.jsonl').read_text().splitlines()]
summary = []
for seed in sorted({r['seed'] for r in rows}):
    run = [r for r in rows if r['seed']==seed]
    switched = [r for r in run if r['chosen_node']!=r['faulty_node']]
    first = switched[0] if switched else None
    if first is None:
        mechanism = 'no_failover'
    elif first['faulty_node'] not in first['candidate_ids']:
        mechanism = 'faulty_candidate_not_in_top_k'
    elif not first['mask'][first['candidate_ids'].index(first['faulty_node'])]:
        mechanism = 'faulty_candidate_masked'
    else:
        mechanism = 'policy_selected_other_available_candidate'
    summary.append(dict(seed=seed, source=run[0]['source'],faulty_node=run[0]['faulty_node'],
        first_failover_packet=(first['packet']+1 if first else ''),
        delivered=sum(r['sink_witness'] for r in run),mechanism=mechanism))
with (p/'run_summary.csv').open('w') as f:
    writer = csv.DictWriter(f,fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
counts = {m:sum(r['mechanism']==m for r in summary) for m in sorted({r['mechanism'] for r in summary})}
print(json.dumps(counts))
print('Median first failover packet among switching runs:',np.median([r['first_failover_packet'] for r in summary if r['first_failover_packet']!='']))
for shard in range(3):
    (p/f'trace_part{shard+1}.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows[shard*300:(shard+1)*300]))
