from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path(__file__).resolve().parents[2]/'outputs/cooja_radio_energy_v1'
a=json.loads((D/'analysis.json').read_text());s=a['summary'];arms=['censored','censored_proof','active','naive','frozen'];labels=['Censored','Censored + proof','Active','Naive','Frozen'];colors=['#0072B2','#009E73','#D55E00','#CC79A7','#666666']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','pdf.fonttype':42})
fig,axs=plt.subplots(2,2,figsize=(9,6),layout='constrained')
for i,attack in enumerate([0,1]):
 for j,timing in enumerate([0,1]):
  ax=axs[i,j];data={r['arm']:r for r in s if r['attack']==attack and r['timing']==timing}
  for arm,label,color in zip(arms,labels,colors):
   row=data[arm];ax.scatter(row['tx_seconds'],100*row['delivery'],s=52,color=color,label=label)
  ax.set(xlabel='Summed node TX time (s/run)',ylabel='Sink delivery (%)',title=f'{"Attack" if attack else "Benign"}; {"scheduled" if timing else "native"}')
  ax.grid(alpha=.2);ax.set_ylim(0,105)
handles,legend=axs[0,0].get_legend_handles_labels();fig.legend(handles,legend,loc='outside lower center',ncols=5,frameon=False)
for ext in ['png','pdf','svg']:fig.savefig(D/f'radio_delivery.{ext}',dpi=300)
plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(9,3.5),layout='constrained')
ratios=[.5,1,2,3]
for ax,timing in zip(axs,[0,1]):
 data={r['arm']:r for r in s if r['attack']==1 and r['timing']==timing};base=data['censored']
 for arm,label,color in zip(arms,labels,colors):
  row=data[arm];v=[100*((row['listen_seconds']+r*row['tx_seconds'])/(base['listen_seconds']+r*base['tx_seconds'])-1) for r in ratios]
  ax.plot(ratios,v,marker='o',lw=1.6,color=color,label=label)
 ax.axhline(0,color='black',lw=.7);ax.grid(alpha=.2);ax.set(xlabel='Assumed TX/listen current ratio',ylabel='Radio-only energy vs censored (%)',title='Scheduled timing' if timing else 'Native timing');ax.set_xticks(ratios)
handles,legend=axs[0].get_legend_handles_labels();fig.legend(handles,legend,loc='outside lower center',ncols=5,frameon=False)
for ext in ['png','pdf','svg']:fig.savefig(D/f'assumed_current_sensitivity.{ext}',dpi=300)
