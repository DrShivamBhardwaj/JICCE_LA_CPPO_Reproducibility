"""Reconcile the new manuscript table and preserve the preceding evidence."""
from pathlib import Path
import argparse,json,hashlib,zipfile
from lxml import etree
from docx import Document
r=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path);a=p.parse_args()
file=r/'publication/array/Array_Manuscript.docx';d=Document(file);assert len(d.tables)==10 and len(d.inline_shapes)==11
summary=json.loads((r/'outputs/cc2538_fast/receipt_profiles_summary.json').read_text());assert summary['status']=='passed_scoped_comparison'
for i,x in enumerate(summary['rows']):
 profile={'cc2538_v2':'FP32','cc2538_q22':'Q22','cc2538_fast':'Fast'}[x['profile']]
 expected=[profile+' / '+x['topology'],str(x['offered']),f"{x['delivered']} / {x['ed25519_receipts']}",f"{x['signed_delay_ms'][0]}–{x['signed_delay_ms'][1]}",str(x['signed_deadline_misses']),f"{x['fast_delay_ms'][0]}–{x['fast_delay_ms'][1]}" if 'fast_delay_ms' in x else '—',str(x['fast_deadline_misses']) if 'fast_deadline_misses' in x else '—']
 assert [c.text for c in d.tables[9].rows[i+1].cells]==expected
report=dict(status='passed',live_table_rows_reconciled=6,figures=11,tables=10,physical_validation=False,deadline_compliance=False)
if a.baseline:
 base=Document(a.baseline);assert len(base.tables)==9
 assert all(x._tbl.xml==y._tbl.xml for x,y in zip(base.tables,d.tables[:9]))
 def xmls(path):
  with zipfile.ZipFile(path) as z:
   tree=etree.fromstring(z.read('word/document.xml'))
   math=[etree.tostring(x,method='c14n') for x in tree.xpath('//*[local-name()="oMath"]')]
   media=sorted(hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('word/media/'))
  return math,media
 before,im0=xmls(a.baseline);after,im1=xmls(file);assert before==after and len(after)==10 and im0==im1
 report.update(preceding_nine_tables_unchanged=True,ten_native_equations_unchanged=True,preceding_eleven_images_unchanged=True,baseline_sha256=hashlib.sha256(a.baseline.read_bytes()).hexdigest())
(r/'publication/array/live_manuscript_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
