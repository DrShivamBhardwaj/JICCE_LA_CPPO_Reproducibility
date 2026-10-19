"""Finalize only the rendered, visually reviewed follow-up manuscript."""
from pathlib import Path
import json,hashlib,csv,re,zipfile
from docx import Document
R=Path(__file__).resolve().parents[1];P=R/'publication/array'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
review=json.loads((P/'followup_visual_review.json').read_text());audit=json.loads((P/'remediation_manuscript_audit.json').read_text());d=Document(P/'Array_Manuscript.docx')
assert review['status']=='passed_page_by_page_review' and review['docx_sha256']==sha(P/'Array_Manuscript.docx') and review['pdf_sha256']==sha(P/'Array_Manuscript.pdf') and audit['final_docx_sha256']==review['docx_sha256']
assert len(d.tables)==13 and len(d.inline_shapes)==16
for index,profile in enumerate(['mcu_deadline_v1','mcu_deadline_v2']):
 a=json.loads((R/'outputs'/profile/'analysis.json').read_text())
 for j,row in enumerate(a['rows']):
  expected=['O3' if index==0 else 'O3 + LTO',row['topology'].title(),'–'.join(map(str,row['signed_delay_ms'])),str(row['signed_deadline_misses'])+' / '+str(row['offered']),str(row['mcu_decisions'])]
  assert [c.text for c in d.tables[12].rows[1+2*index+j].cells]==expected
text='\n'.join(p.text for p in d.paragraphs);assert 'contributed equally to this work.' in text and 'The authors declare no competing interests.' in text
checks=json.loads((P/'document_checks.json').read_text());checks.update(pages=34,rendered_pages=34,abstract_words=217,figures=16,tables=13,inline_exhibits={'figures_in_body':16,'tables_in_body':13,'algorithm_in_body':1},all_pages_visually_verified=True,visual_review='Changed pages inspected; unchanged pages checked for pixel identity against reviewed baseline',full_suite_rerun_this_revision=False,previous_full_suite_passed=142,docx_sha256=review['docx_sha256'],pdf_sha256=review['pdf_sha256'],equal_contribution_declared=True,no_competing_interests_declared=True,author_permissions_reported_by_corresponding_author=True,coauthor_approval_independently_certified=False,lto_signed_deadline_misses=68,cooja_radio_reanalysis_runs=600)
(P/'document_checks.json').write_text(json.dumps(checks,indent=2)+'\n')
summary='The current manuscript contains 34 reviewed pages, a 217-word abstract, 16 figures, 13 tables, 25 references and 10 preserved native equations. Section 5.12 integrates the separately frozen LTO failure and the exploratory reanalysis of all 600 retained historical Cooja runs. Original experimental and statistical families remain separate.'
limits='O3 and LTO each retain 68/200 signed deadline misses. Physical RF/current and production MCU security remain unvalidated. The linked desktop is offline and official Array guide access returns 403; authenticated portal requirements remain unchecked. Exclusivity and overlap declarations have not been supplied. No submission or coauthor message was sent.'
authors='The corresponding author reports permission from all three authors and supplies equal-contribution, no-funding and no-competing-interest statements. These statements are recorded with their provenance; direct coauthor correspondence and unspecified CRediT roles are not invented.'
(P/'README.md').write_text('# Array manuscript review package\n\n'+summary+'\n\n'+authors+'\n\n'+limits+'\n\nFiles: `Array_Manuscript.docx`, `Array_Manuscript.pdf`, editable highlights, the cover-letter draft and `Array_Figures_PNG_PDF_SVG.zip` (48 exports). Reproduce the follow-up with `scripts/integrate_final_followup.py`, the document renderer, both manuscript audits and `scripts/finalize_followup_package.py` after actual visual review. Raw compiler evidence is under `outputs/mcu_deadline_v2`; radio-state evidence is under `outputs/cooja_radio_energy_v1`. See `followup_integration_audit.json`, `followup_visual_review.json`, `document_checks.json` and `docs/REMEDIATION_COMPLETION_REPORT.md`.\n')
for filename in ['SUBMISSION_STATUS.md','ARRAY_TARGET_AND_VIRTUAL_STATUS.md','PENDING_VALIDATION_REGISTER.md']:
 (R/'docs'/filename).write_text('# Current manuscript and validation status\n\n'+summary+'\n\n'+authors+'\n\n'+limits+'\n\nSee [the completion record](REMEDIATION_COMPLETION_REPORT.md). Physical measurements cannot be replaced by native Cooja state counters or assumed current ratios.\n')
p=R/'docs/ARRAY_SUBMISSION_CHECKLIST.md';s=p.read_text();s=re.sub(r'The revised Word/PDF contain.*?Source figures are data-derived PNG/PDF/SVG exports\.',summary+' Source figures are data-derived PNG/PDF/SVG exports.',s,flags=re.S);s=s.replace('actual contribution roles','the supplied equal-contribution statement');s+='\n## Latest author declarations and integrated manuscript\n\n'+authors+'\n\n'+limits+'\n';p.write_text(s)
p=R/'docs/REMEDIATION_COMPLETION_REPORT.md';s=p.read_text();s+='\n## Final integrated package and supplied declarations\n\n'+summary+'\n\n'+authors+'\n\n'+limits+'\n';p.write_text(s)
p=R/'docs/REMEDIATION_REPRODUCTION.md';s=p.read_text();s+='\n## Final manuscript follow-up\n\nRun `python scripts/integrate_final_followup.py` against the retained C65 baseline specified in that script; it writes only the current manuscript and exhibits. Run `python scripts/audit_array_manuscript.py` and `python scripts/audit_array_remediation.py --baseline PATH_TO_F9_BASELINE.docx`. Render using the documents renderer and inspect changed pages. Run `python scripts/finalize_followup_package.py` only after recording actual visual review for the current hashes. Historical `finalize_remediation_package.py` rejects this newer layout to prevent stale counts from replacing it.\n';p.write_text(s)
p=R/'docs/REMEDIATION_CONCERN_MATRIX.csv'
with p.open(newline='') as f:reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
for row in rows:
 values=list(row.values())
 # Preserve the original matrix schema and append the current evidence to matching rows.
 for key,val in row.items():
  if val and 'all final approval fields remain null' in val:row[key]=authors+' Exclusivity/overlap and exact-version final approval remain separate unconfirmed fields.'
  if val and val.startswith('Completed evidence integrated; old 11 tables'):row[key]=summary
with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
p=R/'README.md';s=p.read_text();end=s.find('> Historical transport stage:');assert end>=0;p.write_text('## Current manuscript and validation\n\n'+summary+'\n\n'+authors+'\n\n'+limits+'\n\nSee [the manuscript package](publication/array/README.md).\n\n'+s[end:])
report=dict(status='completed_available_manuscript_and_declaration_work',resolved=['Equal contribution and no competing interests added','LTO and Cooja evidence integrated','34-page Word/PDF rendered and reviewed','16 figures and 13 tables reconciled'],implemented_but_unvalidated=['Production board key protection, provisioning, firmware authenticity and reset-safe sessions'],scientific_limitation=['Original signed endpoint remains 68/200 late after O3 and LTO','Always-on Cooja current sensitivity is a model, not physical energy'],blocked=['Physical RF/current acquisition: no accessible boards/instruments; desktop offline','Authenticated Array checks: guide 403; no accessible authenticated portal','Exclusivity/overlap declaration not supplied'],coauthor_permission_basis='Corresponding-author attestation',no_messages_or_submission_sent=True,docx_sha256=review['docx_sha256'],pdf_sha256=review['pdf_sha256'])
(P/'FINAL_COMPLETION_REPORT.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
