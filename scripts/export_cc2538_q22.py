"""Export a declared fixed-point approximation; check integer overflow bounds."""
from pathlib import Path
import torch,numpy as np,json,hashlib,subprocess,ctypes,struct,math
r=Path(__file__).resolve().parents[1];out=r/'outputs/cc2538_q22';out.mkdir(exist_ok=True);d=r/'hardware/cc2538_q22';ck=r/'outputs/jicce_validation/checkpoints/attention_41001.pt'
w=torch.load(ck,map_location='cpu',weights_only=True);arrays={k:np.rint(v.numpy().astype(np.float64)*2**22).astype(np.int64) for k,v in w.items() if k.startswith(('ctx_encoder','cand_encoder','query.','key.','actor_bias'))}
assert sum(a.size for a in arrays.values())==44161
parts=['/* Q22 frozen actor weights; generated from hashed checkpoint. */']
for name,a in arrays.items():
 assert np.abs(a).max()<2**31
 parts.append('static const int32_t q_'+name.replace('.','_')+'['+str(a.size)+']={'+','.join(map(str,a.ravel()))+'};')
lut=np.rint(np.tanh(np.linspace(-8,8,8193))*2**22).astype(np.int64);parts.append('static const int32_t tanh_lut[8193]={'+','.join(map(str,lut))+'};')
(d/'q22_weights.h').write_text('\n'.join(parts)+'\n')
bounds={}
for name,a in arrays.items():
 if a.ndim==2:
  in_bound=32 if name.startswith(('ctx_encoder.0','cand_encoder.0')) else 1
  sums=np.abs(a).sum(axis=1)*int(in_bound*2**22)
  bias=arrays.get(name.replace('weight','bias'))
  if bias is not None:sums+=np.abs(bias)*2**22
  assert int(sums.max())<2**63 and int((sums.max()+2**21)//2**22)<2**31
  bounds[name]=int((sums.max()+2**21)//2**22)
qb=bounds['query.weight'];kb=bounds['key.weight'];assert 96*qb*kb<2**63
assert (96*qb*kb//2**22)*428079<2**63
(d/'native.c').write_text('#include "actor.h"\nint evaluate(const float*x,const unsigned char*m,float*y){return actor(x,m,y);}\n')
subprocess.run(['cc','-O2','-shared','-fPIC',str(d/'native.c'),'-o',str(r/'build/q22_actor.dylib')],check=True)
lib=ctypes.CDLL(str(r/'build/q22_actor.dylib'));f=lib.evaluate;f.argtypes=[ctypes.POINTER(ctypes.c_float),ctypes.POINTER(ctypes.c_ubyte),ctypes.POINTER(ctypes.c_float)]
errors=[];count=0
for folder in ['chain_100','choice_100']:
 for p in (r/'outputs/cc2538_v2'/folder).glob('uart_*.jsonl'):
  for line in p.read_text().splitlines():
   if not line.startswith('{') or not line.endswith('}'):continue
   v=json.loads(line)
   if v['event']!='local_decision':continue
   x=np.array(struct.unpack('!93f',bytes.fromhex(v['obs_hex'])),dtype=np.float32);mask=np.zeros(8,np.uint8);mask[:len(v['ids'])]=1;y=np.zeros(8,np.float32)
   selected=f(x.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),mask.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte)),y.ctypes.data_as(ctypes.POINTER(ctypes.c_float)))
   original=np.array(struct.unpack('!8f',bytes.fromhex(v['logits_hex'])));assert v['ids'][selected]==v['peer'];errors.extend(abs(y[mask.astype(bool)]-original[mask.astype(bool)]));count+=1
assert max(errors)<1e-4
for bad in [float('nan'),float('inf'),33.,-33.]:
 test=np.zeros(93,np.float32);test[0]=bad;mask=np.ones(8,np.uint8);result=np.zeros(8,np.float32)
 assert f(test.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),mask.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte)),result.ctypes.data_as(ctypes.POINTER(ctypes.c_float)))==-1
empty=np.zeros(8,np.uint8);test=np.zeros(93,np.float32);result=np.zeros(8,np.float32)
assert f(test.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),empty.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte)),result.ctypes.data_as(ctypes.POINTER(ctypes.c_float)))==-1
report=dict(status='passed_native_reference',checkpoint_sha256=hashlib.sha256(ck.read_bytes()).hexdigest(),parameters=44161,fractional_bits=22,tanh_lut_points=8193,input_bound=32,overflow_bounds=bounds,dot_accumulator_bound=96*qb*kb,reference_decisions=count,max_logit_error=float(max(errors)),tolerance=1e-4,nonfinite_and_out_of_range_rejections=4,empty_mask_rejected=True,scope='Fixed-point approximation on retained observations; not exhaustive action equivalence or MCU timing validation')
(out/'export.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='overflow_bounds'},indent=2))
