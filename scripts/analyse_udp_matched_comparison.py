"""Prespecified per-fixture paired diagnostic endpoint and publication figure."""
import gzip
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'outputs/udp_matched_comparison'
trace=p/'trace.jsonl'
paths=[trace] if trace.exists() else sorted(p.glob('trace_part*.jsonl'))
rows=([json.loads(x) for path in paths for x in path.read_text().splitlines()] if paths else [json.loads(x) for x in gzip.open(p/'trace.jsonl.gz','rt')])
df=pd.DataFrame(rows)
run=df.groupby(['seed','target_selector','arm']).agg(delivery=('sink_witness','mean'),parameters=('model_parameters','first'),initial_choice=('chosen_node','first'),fault_target=('faulty_node','first')).reset_index()
run['initial_exposure']=run.initial_choice==run.fault_target
run.to_csv(p/'run_summary.csv',index=False)
paired=run.groupby(['seed','arm']).delivery.mean().unstack()
paired['attention_minus_mlp']=paired.attention-paired.capacity_mlp
paired.to_csv(p/'paired_seed_summary.csv')
d=paired.attention_minus_mlp.to_numpy()
ci=stats.t.interval(.95,len(d)-1,loc=d.mean(),scale=stats.sem(d))
report=dict(n_fixtures=len(d),attention_delivery=float(paired.attention.mean()),mlp_delivery=float(paired.capacity_mlp.mean()),mean_difference=float(d.mean()),ci95=[float(x) for x in ci],paired_t_p=float(stats.ttest_1samp(d,0).pvalue),attention_parameters=int(run[run.arm=='attention'].parameters.iloc[0]),mlp_parameters=int(run[run.arm=='capacity_mlp'].parameters.iloc[0]))
(p/'paired_analysis.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
for shard in range(12):
    (p/f'trace_part{shard+1:02d}.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows[shard*300:(shard+1)*300]))
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(7.2,3.1),layout='constrained')
    for _,r in paired.iterrows():
        axes[0].plot([0,1],[r.capacity_mlp,r.attention],color='#89949e',alpha=.55,lw=.8)
    axes[0].scatter(np.zeros(len(paired)),paired.capacity_mlp,color='#356a9a',s=12,label='MLP')
    axes[0].scatter(np.ones(len(paired)),paired.attention,color='#b46832',s=12,label='Attention')
    axes[0].set(xticks=[0,1],xticklabels=['Capacity MLP','Attention'],ylabel='Sink delivery fraction',ylim=(-.03,1.03),title='(a) Paired fixture outcomes')
    axes[1].scatter(paired.index,d,color='#356a9a',s=16)
    axes[1].axhline(0,color='black',lw=.8)
    axes[1].axhline(d.mean(),color='#b46832',lw=1.2)
    axes[1].set(xlabel='Fixture seed',ylabel='Attention − MLP',title='(b) Delivery difference')
    axes[1].ticklabel_format(axis='x',style='plain',useOffset=False)
    for ax in axes:
        ax.spines[['top','right']].set_visible(False)
        ax.grid(axis='y',alpha=.2)
    fig.savefig(p/'paired_delivery.svg');fig.savefig(p/'paired_delivery.png',dpi=300)
    plt.close(fig)
except ImportError:
    print('Plot omitted: matplotlib unavailable')
