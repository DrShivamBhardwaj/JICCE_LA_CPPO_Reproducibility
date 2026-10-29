"""Run only the frozen case list. Captures/failures are retained; no selective retry."""
from pathlib import Path
import argparse,json,hashlib,subprocess,os,shutil,time,gzip,xml.etree.ElementTree as E,concurrent.futures,multiprocessing
from prepare import project,export
R=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent;OUT=R/'outputs/generalization_v2';B=R/'build/generalization_v2'

def verify():
    p=json.loads((D/'protocol.json').read_text())
    if len(p['cases']) != p['expected_runs'] or len({c['case_id'] for c in p['cases']})!=p['expected_runs']:
        raise ValueError('pre-registered case coverage mismatch')
    if p['status']!='DESIGN_FROZEN_EXECUTION_NOT_STARTED' or p['geometry_blocks']!=24:raise ValueError('design metadata mismatch')
    return p

def execute(task):
    case,preflight=task
    from audit import audit_run
    area='preflight' if preflight else 'runs';folder=OUT/area/case['case_id'];folder.mkdir(parents=True,exist_ok=False)
    workspace=B/'projects'/case['case_id'];project(workspace,case,B/f"weights_{case['checkpoint']}.h")
    tree=E.parse(R/'hardware/cooja_feedback/pilot.csc');sim=tree.find('simulation');sim.find('randomseed').text=str(case['seed']);sim.find('radiomedium/success_ratio_rx').text=str(case['rx_probability']);mt=sim.find('motetype');mt.find('source').text=str(workspace/'feedback.c');mt.find('commands').text='make feedback.cooja TARGET=cooja CONTIKI='+str(B/'contiki')
    for mote,xy in zip(mt.findall('mote'),case['positions']):
        pos=mote.find('interface_config/pos');pos.set('x',str(xy[0]));pos.set('y',str(xy[1]))
    script=tree.find('plugin/plugin_config/script');script.text=script.text.replace('CONFIG 0 0 0 0',f"CONFIG {case['mode']} {case['proof']} {int(case['attacker']!=0)} {case['timing']}")
    config=folder/'simulation.csc';tree.write(config,encoding='UTF-8',xml_declaration=True);(folder/'case.json').write_text(json.dumps(case,indent=2)+'\n')
    java=shutil.which('java');env=os.environ.copy();started=time.monotonic();command=[java,'-Xmx512m','--enable-native-access=ALL-UNNAMED','-jar',str(B/'cooja/build/libs/cooja.jar'),'--no-gui','--no-log-color','--contiki',str(B/'contiki'),'--cooja',str(B/'cooja'),'--logdir',str(folder),str(config)]
    try:
        with (folder/'console.log').open('w') as log:result=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
        if result.returncode:raise RuntimeError('Cooja exit '+str(result.returncode))
        images=list((workspace/'build/cooja').glob('mtype*.cooja'))
        if len(images)!=1:raise RuntimeError('native image ambiguity')
        image=images[0].read_bytes();(folder/'native_mote.so.gz').write_bytes(gzip.compress(image,mtime=0));report=audit_run(folder,case);report.update(case_id=case['case_id'],native_image_sha256=hashlib.sha256(image).hexdigest(),wall_seconds=round(time.monotonic()-started,3));(folder/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
        for name in ['COOJA.testlog','console.log']:
            f=folder/name;raw=f.read_bytes();packed=gzip.compress(raw,mtime=0)
            if gzip.decompress(packed)!=raw:raise RuntimeError('compression integrity')
            (folder/(name+'.gz')).write_bytes(packed);f.unlink()
        shutil.rmtree(workspace)
        return dict(case_id=case['case_id'],status='audited',preflight=preflight)
    except Exception as error:
        (folder/'FAILURE.json').write_text(json.dumps({'status':'failed_retained','reason':repr(error)},indent=2)+'\n');raise


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');parser.add_argument('--execute',action='store_true');parser.add_argument('--workers',type=int,default=2);a=parser.parse_args();protocol=verify();print('Verified frozen source and',protocol['expected_runs'],'cases',flush=True)
    if a.verify_only:return
    if not a.execute:raise SystemExit('Choose --verify-only or --execute')
    OUT.mkdir(parents=True,exist_ok=True);B.mkdir(parents=True,exist_ok=True)
    for checkpoint in sorted({c['checkpoint'] for c in protocol['cases']}):export(checkpoint,B/f'weights_{checkpoint}.h')
    pre=[dict(protocol['cases'][0]),dict(protocol['cases'][2])]
    for i,c in enumerate(pre):c['case_id']='technical_'+str(i);execute((c,True))
    records=[]
    # Each process owns its auditor/model globals; no cross-case thread races.
    with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers,mp_context=multiprocessing.get_context('spawn')) as pool:
        pending=[pool.submit(execute,(case,False)) for case in protocol['cases']]
        for future in concurrent.futures.as_completed(pending):
            records.append(future.result());(OUT/'progress.json').write_text(json.dumps({'completed':len(records),'expected':protocol['expected_runs']},indent=2)+'\n');print('Audited cases',len(records),flush=True)
    verify()
    if len(records)!=protocol['expected_runs']:raise RuntimeError('incomplete execution')
    (OUT/'execution_complete.json').write_text(json.dumps({'status':'all_frozen_cases_executed_and_audited','cases':len(records),'preflight_excluded':len(pre),'protocol_sha256':hashlib.sha256((D/'protocol.json').read_bytes()).hexdigest()},indent=2)+'\n')
if __name__=='__main__':main()
