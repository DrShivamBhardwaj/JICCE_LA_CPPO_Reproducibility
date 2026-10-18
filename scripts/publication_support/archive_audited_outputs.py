"""Manifest an already audited workflow artifact for durable GitHub release storage."""
from pathlib import Path
import argparse,json,hashlib
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--run-id',required=True);p.add_argument('--source-commit',required=True);p.add_argument('--notes',type=Path,required=True);a=p.parse_args()
reports=[]
for file in a.root.rglob('analysis.json'):
    d=json.loads(file.read_text())
    if d.get('status') in ['completed_block_factorial_analysis','completed_compiler_only_pilot']:reports.append(d)
if len(reports)!=1:raise SystemExit('Require exactly one completed audited experimental analysis')
d=reports[0]
files={str(f.relative_to(a.root)):{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted(a.root.rglob('*')) if f.is_file()}
(a.root/'ARCHIVE_MANIFEST.json').write_text(json.dumps({'workflow_run':a.run_id,'source_commit':a.source_commit,'files':files,'physical_validation':False},indent=2)+'\n')
notes='Raw outputs and analysis from workflow '+a.run_id+' at source commit '+a.source_commit+'.\n\nAudit status: '+d['status']+'.\n'
if 'runs' in d:notes+='Declared evaluation runs: '+str(d['runs'])+'.\n'
if 'original_signed_deadline_complete' in d:notes+='Original signed deadline complete: '+str(d['original_signed_deadline_complete'])+'.\n'
notes+='\nPhysical RF/energy and production MCU security are not validated. Author approval and submission are separate requirements. Archive includes a SHA-256 manifest; hashes are integrity checks, not signatures.\n'
a.notes.write_text(notes)
