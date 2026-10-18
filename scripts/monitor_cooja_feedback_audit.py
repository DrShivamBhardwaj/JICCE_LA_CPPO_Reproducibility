"""Audit completed immutable captures while the frozen experiment executes."""
from pathlib import Path
import json,time,hashlib,sys
from audit_cooja_feedback_quantized import audit_run
r=Path(__file__).resolve().parents[1];out=r/'outputs/cooja_feedback/primary_600';done={};started=time.monotonic()
while len(done)<600:
 try:runs=json.loads((out/'runs.json').read_text())
 except json.JSONDecodeError:time.sleep(.1);continue
 for run in runs:
  key=run['folder']
  if key in done:continue
  folder=r/key;assert hashlib.sha256((folder/'native_mote.dylib').read_bytes()).hexdigest()==run['native_image_sha256']
  d=audit_run(folder);assert d['config']=={k:run[k] for k in ['mode','proof','attack','timing']};d.update(seed=run['seed'],arm=run['arm'],attack=run['attack'],timing=run['timing']);(folder/'audit.json').write_text(json.dumps(d,indent=2)+'\n');done[key]=d
  (out/'audit_progress.json').write_text(json.dumps({'independently_audited_runs':len(done),'target_runs':600},indent=2)+'\n');print(len(done),folder.name,flush=True)
 if len(done)<600:time.sleep(2)
(out/'audit_complete.json').write_text(json.dumps({'status':'all_declared_runs_independently_audited','runs':600,'wall_seconds':round(time.monotonic()-started,2)},indent=2)+'\n');print('AUDIT COMPLETE',flush=True)
