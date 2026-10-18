"""Scientific plots from retained diagnostics and completed block-level analyses."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
R=Path(__file__).resolve().parents[1];O=R/'publication/array/remediation_figures';O.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','axes.titleweight':'bold','axes.labelcolor':'#263b49','text.color':'#263b49'})
def save(fig,name):
    for ext in ['png','pdf','svg']:fig.savefig(O/(name+'.'+ext),dpi=600,bbox_inches='tight',facecolor='white')
    f=O/(name+'.svg');f.write_text('\n'.join(x.rstrip() for x in f.read_text().splitlines())+'\n');plt.close(fig)

d=json.loads((R/'outputs/remediation_v1/archive_diagnostics/summary.json').read_text())
fig,axes=plt.subplots(2,1,figsize=(7.2,7.0),gridspec_kw={'height_ratios':[1,1.4]});fig.subplots_adjust(hspace=.55)
a=axes[0];labels=['Risk coordinates differ','Candidate order differs','Selected relay differs'];values=[d['risk_different_decisions'],d['candidate_order_disagreements'],d['action_disagreements']];a.barh(labels[::-1],values[::-1],color=['#81939f','#d57a44','#007f87'][::-1],height=.5)
a.set_xlim(0,d['matched_decisions']*1.16);a.set_xlabel('Matched decisions');a.set_title('(a) Censored versus frozen prior',loc='left',pad=12);a.grid(axis='x',alpha=.15);a.set_axisbelow(True)
for i,v in enumerate(values[::-1]):a.text(v+d['matched_decisions']*.018,i,f'{v:,} / {d["matched_decisions"]:,}',va='center',fontsize=9)
a.text(0,-.34,'Same archived packets and non-risk observation coordinates',transform=a.transAxes,fontsize=8,color='#566a76')
a=axes[1];arms=['active','naive','frozen','censored_proof','censored'];names=['Active proofs','Naive passive','Frozen prior','Censored + proofs','Censored passive'];groups=[next(x for x in d['deadline_groups'] if (x['attack'],x['timing'],x['arm'])==(0,1,arm)) for arm in arms];missing=np.array([x['critical_undelivered'] for x in groups]);late=np.array([x['critical_delivered_late'] for x in groups]);timely=np.array([x['critical_offered'] for x in groups])-missing-late;y=np.arange(5)
a.barh(y,timely,color='#007f87',label='Timely delivery');a.barh(y,late,left=timely,color='#d39a45',label='Delivered late');a.barh(y,missing,left=timely+late,color='#6d7e8a',label='Undelivered');a.set_yticks(y,names);a.invert_yaxis();a.set_xlim(0,670);a.set_xlabel('Critical packets across 30 runs');a.set_title('(b) Benign runs with scheduled delays',loc='left',pad=12);a.legend(loc='lower center',bbox_to_anchor=(.48,-.48),ncol=3,frameon=False,fontsize=8)
for i,(t,l,m) in enumerate(zip(timely,late,missing)):a.text(t+l*.5,i,str(l),ha='center',va='center',color='#293a42',fontsize=9);a.text(610,i,f'{m} lost',va='center',fontsize=8)
fig.text(.13,.01,'Descriptive archive counts; offline interventions and packets are not independent trial replicates.',fontsize=8,color='#566a76');save(fig,'fig13_feedback_diagnostics')

path=R/'outputs/remediation_v1/analysis.json'
if path.exists():
    result=json.loads(path.read_text())
    if result['status']!='completed_block_factorial_analysis':raise ValueError('Incomplete factorial analysis')
    fig,axes=plt.subplots(1,2,figsize=(7.2,4.0),sharex=True,sharey=True);effects=['negative_main','proof_main','interaction'];names=['Negative update','Proof generation','Interaction'];colors=['#007f87','#d57a44','#6b6a9b'];extents=[]
    for timing,ax in enumerate(axes):
        ax.axvline(0,color='#a8b3ba',lw=1,ls='--');ax.set_title('No added compute delay' if timing==0 else 'Scheduled processing delays',fontsize=10,pad=12)
        for j,key in enumerate(effects):
            x=next(x for x in result['contrasts'] if (x['endpoint'],x['timing'],x['contrast'])==('post_delivery',timing,key));lo,hi=np.array(x['ci95'])*100;mean=x['mean_difference']*100;vals=np.array(x['block_differences'])*100;ax.scatter(vals,np.full(12,j)+np.linspace(-.10,.10,12),s=13,color=colors[j],alpha=.4,zorder=2);ax.errorbar(mean,j,xerr=[[mean-lo],[hi-mean]],fmt='o',color=colors[j],capsize=4,lw=2,ms=6,zorder=3);ax.annotate(f'Holm p={x["p_holm"]:.3g}',(0,j),xytext=(0,-19),textcoords='offset points',ha='left',fontsize=7);extents.extend([lo,hi,*vals])
        ax.set_yticks(range(3),names);ax.set_ylim(2.55,-.55);ax.set_xlabel('Post-onset delivery effect\n(percentage points)');ax.grid(axis='x',alpha=.12);ax.set_axisbelow(True)
    bound=max(5,max(abs(x) for x in extents)*1.15)
    for ax in axes:ax.set_xlim(-bound,bound)
    fig.subplots_adjust(wspace=.15,bottom=.23,left=.20);fig.text(.20,.025,'Faint points: 12 geometry-block effects. Bars: pointwise paired 95% bootstrap intervals.\nHolm adjustment: the declared six-contrast primary family.',fontsize=8,color='#566a76');save(fig,'fig14_matched_feedback_effects')
print(O)
