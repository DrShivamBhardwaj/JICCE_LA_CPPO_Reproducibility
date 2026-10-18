"""Continue a frozen study in isolated native build directories; no outcome-based selection."""
from pathlib import Path
import json,hashlib,subprocess,os,shutil,time,threading,concurrent.futures,xml.etree.ElementTree as E
r=Path(__file__).resolve().parents[1];out=r/'outputs/cooja_feedback/primary_600';protocol=json.loads((out/'protocol.json').read_text());runs=json.loads((out/'runs.json').read_text());lock=threading.Lock();started=len(runs)
for p,sha in protocol['sources_sha256'].items():assert hashlib.sha256((r/p).read_bytes()).hexdigest()==sha,'Frozen source changed: '+p
expected=[]
for seed in protocol['seeds']:
 for attack in protocol['attacks']:
  for timing in protocol['timings']:
   for arm,(mode,proof) in protocol['arms'].items():expected.append((seed,attack,timing,arm,mode,proof))
finished={(x['seed'],x['attack'],x['timing'],x['arm']) for x in runs};todo=[x for x in expected if x[:4] not in finished]
# An interrupted, unrecorded run is retained explicitly rather than silently overwritten.
for seed,attack,timing,arm,mode,proof in todo:
 folder=out/f'seed{seed}_attack{attack}_timing{timing}_{arm}'
 if folder.exists():
  archive=out/'interrupted';archive.mkdir(exist_ok=True);dest=archive/folder.name;assert not dest.exists();shutil.move(folder,dest);(dest/'EXCLUDED.json').write_text(json.dumps({'reason':'Runner interrupted solely to switch to isolated parallel scheduling before this run was recorded; no outcome-based exclusion. Same configuration is rerun in its canonical directory.'},indent=2)+'\n')
contiki=r/'build/contiki-feedback';cooja=Path('/Users/shivambhardwaj/Research/contiki-ng/tools/cooja');java=Path('/opt/homebrew/opt/openjdk@25/bin/java');base=r/'hardware/cooja_feedback';workers=4
(out/'execution_supplement.json').write_text(json.dumps({'workers':workers,'already_completed':started,'purpose':'Independent OS processes with isolated native build directories; experimental arms/seeds/inputs unchanged','path_only_makefile_changes':['absolute vendor/include/Q22 paths','absolute compatibility-header path'],'continuation_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'interrupted_runs_retained':True},indent=2)+'\n')
env=os.environ.copy();env['JAVA_HOME']=str(java.parent.parent);env['PATH']=str(java.parent)+':/opt/homebrew/opt/make/libexec/gnubin:'+env['PATH']
def worker(w):
 project=r/'build/cooja_feedback_workers'/f'worker{w}';project.mkdir(parents=True,exist_ok=True)
 for p in base.iterdir():
  if p.is_file() and p.suffix in ['.h','.c']:shutil.copyfile(p,project/p.name)
 make=(base/'Makefile').read_text().replace('$(CURDIR)/../cooja_receipt_transport/native-compat.h',str(r/'hardware/cooja_receipt_transport/native-compat.h')).replace('PROJECTDIRS += ../cortex_m3_validation/vendor ../cortex_m3_validation/include ../cc2538_q22','PROJECTDIRS += '+str(r/'hardware/cortex_m3_validation/vendor')+' '+str(r/'hardware/cortex_m3_validation/include')+' '+str(r/'hardware/cc2538_q22'));(project/'Makefile').write_text(make)
 for seed,attack,timing,arm,mode,proof in todo[w::workers]:
  folder=out/f'seed{seed}_attack{attack}_timing{timing}_{arm}';folder.mkdir();tree=E.parse(base/'pilot.csc');sim=tree.find('simulation');sim.find('randomseed').text=str(seed);mt=sim.find('motetype');mt.find('source').text=str(project/'feedback.c');mt.find('commands').text='make feedback.cooja TARGET=cooja CONTIKI='+str(contiki);s=tree.find('plugin/plugin_config/script');s.text=s.text.replace('CONFIG 0 0 0 0',f'CONFIG {mode} {proof} {attack} {timing}');cfg=folder/'simulation.csc';tree.write(cfg,encoding='UTF-8',xml_declaration=True)
  build=project/'build/cooja';before={str(x):x.stat().st_mtime_ns for x in build.glob('mtype*.cooja')} if build.exists() else {};cmd=[str(java),'-Xmx512m','--enable-native-access=ALL-UNNAMED','-jar',str(cooja/'build/libs/cooja.jar'),'--no-gui','--no-log-color','--contiki',str(contiki),'--cooja',str(cooja),'--logdir',str(folder),str(cfg)];start=time.monotonic()
  with (folder/'console.log').open('w') as log:ret=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
  if ret.returncode:raise RuntimeError(folder.name+' failed; retained logs')
  images=[x for x in build.glob('mtype*.cooja') if before.get(str(x))!=x.stat().st_mtime_ns];assert len(images)==1;shutil.copyfile(images[0],folder/'native_mote.dylib');rec=dict(seed=seed,attack=attack,timing=timing,arm=arm,mode=mode,proof=proof,returncode=ret.returncode,folder=str(folder.relative_to(r)),native_image_sha256=hashlib.sha256((folder/'native_mote.dylib').read_bytes()).hexdigest(),wall_seconds=round(time.monotonic()-start,3),worker=w)
  with lock:runs.append(rec);(out/'runs.json').write_text(json.dumps(runs,indent=2)+'\n');print(len(runs),folder.name,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
 futures=[pool.submit(worker,w) for w in range(workers)]
 for f in futures:f.result()
assert len(runs)==len(expected)==600 and len({(x['seed'],x['attack'],x['timing'],x['arm']) for x in runs})==600
for p,sha in protocol['sources_sha256'].items():assert hashlib.sha256((r/p).read_bytes()).hexdigest()==sha
(out/'execution_complete.json').write_text(json.dumps(dict(status='all_declared_runs_executed',runs=600,independent_audit_pending=True),indent=2)+'\n');print('EXECUTION COMPLETE',flush=True)
