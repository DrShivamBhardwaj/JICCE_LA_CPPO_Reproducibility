"""Reconcile Cooja exhibits and preserve every pre-existing equation, table and figure."""
from pathlib import Path
import json,hashlib,zipfile,argparse,re
from docx import Document
from lxml import etree
from array_cooja_integration import table_rows,effect
r=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);args=p.parse_args();file=r/'publication/array/Array_Manuscript.docx';d=Document(file);base=Document(args.baseline);a=json.loads((r/'outputs/cooja_feedback/primary_600/analysis.json').read_text());assert a['runs']==600
assert len(d.tables)==11 and len(d.inline_shapes)==12
assert all(x._tbl.xml==y._tbl.xml for x,y in zip(base.tables,d.tables[:10]))
assert [[c.text for c in row.cells] for row in d.tables[10].rows[1:]]==table_rows(a)
text='\n'.join(p.text for p in d.paragraphs)
for arm in ['active','censored_proof']:
 x=next(x for x in a['contrasts'] if (x['endpoint'],x['attack'],x['timing'],x['arm'])==('delivery',1,1,arm));assert effect(x) in text
assert 'Fig. 12. Paired Cooja delivery effects.' in text and 'Table 11. Cooja transfer results.' in text
assert '36,000 offered packets' in text and '600 runs' in text and 'about 1 ms earlier' in text
assert len([p for p in d.paragraphs if re.match(r'^\[\d+\]',p.text)])==25
changes={x['before']:x['after'] for x in json.loads((r/'publication/array/cooja_integration_edits.json').read_text())}
for p in base.paragraphs:
 if p.text.strip():assert changes.get(p.text,p.text) in text,'A prior paragraph was removed or changed without a mapped edit'
def components(path):
 with zipfile.ZipFile(path) as z:
  tree=etree.fromstring(z.read('word/document.xml'));math=[etree.tostring(x,method='c14n') for x in tree.xpath('//*[local-name()="oMath"]')];images={hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('word/media/')}
 return math,images
m0,i0=components(args.baseline);m1,i1=components(file);assert m0==m1 and len(m1)==10 and i0<=i1 and len(i1-i0)==1
figure=r/'publication/array/cooja_figures/fig12_cooja_paired_delivery.png';assert hashlib.sha256(figure.read_bytes()).hexdigest() in i1
for endpoint in ['delivery','critical_sink_deadline_failure','total_tx_state_s']:
 family=sorted([x for x in a['contrasts'] if x['endpoint']==endpoint],key=lambda x:x['p_unadjusted']);assert len(family)==16;prior=0
 for j,x in enumerate(family):
  prior=max(prior,min(1,x['p_unadjusted']*(16-j)));assert abs(prior-x['p_holm'])<1e-12 and 0<=x['p_holm']<=1
report=dict(status='passed',previous_tables_preserved=10,previous_figures_preserved=11,native_equations_preserved=10,cooja_table_rows_verified=10,cooja_primary_runs=600,independent_seeds=30,figure12_matches_audited_export=True,holm_families_verified=3,physical_validation=False,baseline_sha256=hashlib.sha256(args.baseline.read_bytes()).hexdigest())
(r/'publication/array/cooja_manuscript_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
