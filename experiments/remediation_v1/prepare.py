"""Construct isolated matched-control motes; never modify frozen firmware."""
from pathlib import Path
import json,shutil
import numpy as np
R=Path(__file__).resolve().parents[2]

def export(checkpoint,out):
    import torch
    w=torch.load(R/f'outputs/jicce_validation/checkpoints/attention_{checkpoint}.pt',map_location='cpu',weights_only=True)
    arrays={k:np.rint(v.numpy().astype(np.float64)*2**22).astype(np.int64) for k,v in w.items() if k.startswith(('ctx_encoder','cand_encoder','query.','key.','actor_bias'))}
    if sum(x.size for x in arrays.values())!=44161:raise ValueError('unexpected actor')
    bounds={};parts=[]
    for name,a in arrays.items():
        if np.abs(a).max()>=2**31:raise ValueError('weight bound')
        parts.append('static const int32_t q_'+name.replace('.','_')+'['+str(a.size)+']={'+','.join(map(str,a.ravel()))+'};')
        if a.ndim==2:
            ib=32 if name.startswith(('ctx_encoder.0','cand_encoder.0')) else 1;sums=np.abs(a).sum(1)*int(ib*2**22);bias=arrays.get(name.replace('weight','bias'))
            if bias is not None:sums+=np.abs(bias)*2**22
            if int(sums.max())>=2**63 or int((sums.max()+2**21)//2**22)>=2**31:raise ValueError('linear overflow bound')
            bounds[name]=int((sums.max()+2**21)//2**22)
    dot=96*bounds['query.weight']*bounds['key.weight']
    if dot>=2**63 or (dot//2**22)*428079>=2**63:raise ValueError('attention overflow bound')
    lut=np.rint(np.tanh(np.linspace(-8,8,8193))*2**22).astype(np.int64);parts.append('static const int32_t tanh_lut[8193]={'+','.join(map(str,lut))+'};')
    out.write_text('\n'.join(parts)+'\n')


def project(folder,case,weights):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);base=R/'hardware/cooja_feedback'
    for p in base.glob('*'):
        if p.suffix in ('.h','.c'):shutil.copyfile(p,folder/p.name)
    shutil.copyfile(R/'hardware/cc2538_q22/actor.h',folder/'actor.h');shutil.copyfile(weights,folder/'q22_weights.h')
    c=(folder/'feedback.c').read_text().replace('static const int xy[4][2]={{0,0},{45,15},{45,-15},{90,0}};', 'static const float xy[4][2]='+json.dumps(case['positions']).replace('[','{').replace(']','}')+';')
    c=c.replace('static unsigned app_id,feedback_mode,proof_enabled,attack_enabled,timing_mode,configured;',f"static unsigned app_id,feedback_mode,proof_enabled,attack_enabled,timing_mode,configured;\nstatic const unsigned attack_node={case['attacker']},attack_onset={case['onset']};")
    c=c.replace('receive_live(inbox[i].data,inbox[i].n,inbox[i].peer);','printf("{\\"event\\":\\"app_process_start\\",\\"node\\":%u,\\"kind\\":%u,\\"pid\\":%u,\\"now_ms\\":%u}\\n",node_id,inbox[i].data[1],inbox[i].n>=50?u32(inbox[i].data+22):0,milliseconds);receive_live(inbox[i].data,inbox[i].n,inbox[i].peer);')
    (folder/'feedback.c').write_text(c)
    h=(folder/'local_feedback.h').read_text().replace('node_id==1&&u32(body+2)>=20','node_id==attack_node&&u32(body+2)>=attack_onset')
    old='if(kind==4){if(size!=14){reject("proof_size");return;}feedback_evidence(u32(body+2),sender,1.f,"proof");return;}'
    new='''if(kind==4){if(size!=14||u16(body)!=0||u64(body+6)!=pair_session(0)){reject("proof_identity");return;}unsigned matched=0;for(unsigned j=0;j<16;j++)if(pending_live[j].used&&pending_live[j].source==u16(body)&&pending_live[j].session==u64(body+6)&&pending_live[j].pid==u32(body+2)&&pending_live[j].peer==sender)matched=1;if(!matched){reject("proof_route");return;}feedback_evidence(u32(body+2),sender,1.f,"proof");return;}'''
    if old not in h:raise ValueError('proof patch anchor')
    h=h.replace(old,new).replace('feedback_mode!=0||watches[i].acked!=1','(feedback_mode!=0&&feedback_mode!=2)||watches[i].acked!=1');(folder/'local_feedback.h').write_text(h)
    ledger=(folder/'feedback_ledger.h').read_text().replace('feedback_mode!=0||watches[i].acked!=1','(feedback_mode!=0&&feedback_mode!=2)||watches[i].acked!=1')
    (folder/'feedback_ledger.h').write_text(ledger)
    make=(base/'Makefile').read_text().replace('$(CURDIR)/../cooja_receipt_transport/native-compat.h',str(R/'hardware/cooja_receipt_transport/native-compat.h')).replace('PROJECTDIRS += ../cortex_m3_validation/vendor ../cortex_m3_validation/include ../cc2538_q22','PROJECTDIRS += '+str(R/'hardware/cortex_m3_validation/vendor')+' '+str(R/'hardware/cortex_m3_validation/include'))
    (folder/'Makefile').write_text(make)
