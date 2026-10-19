"""Prepare unsent exact-version review requests; never records or infers consent."""
from pathlib import Path
import argparse,json,hashlib,re,subprocess
from docx import Document
R=Path(__file__).resolve().parents[1];P=R/'publication/array'
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--paper-commit',required=True);args=ap.parse_args();commit=args.paper_commit
    if not re.fullmatch(r'[0-9a-f]{40}',commit):raise ValueError('Require exact published manuscript commit')
    sha=lambda f:hashlib.sha256((P/f).read_bytes()).hexdigest()
    version={'repository_commit':commit,'manuscript_pdf_sha256':sha('Array_Manuscript.pdf'),'manuscript_docx_sha256':sha('Array_Manuscript.docx'),'status':'permissions_reported_by_corresponding_author_new_exact_version_not_independently_confirmed','coauthor_messages_sent':False}
    for filename in ['Array_Manuscript.pdf','Array_Manuscript.docx']:
        actual=subprocess.check_output(['git','show',commit+':publication/array/'+filename],cwd=R)
        if hashlib.sha256(actual).hexdigest()!=sha(filename):raise ValueError('Commit does not contain this manuscript: '+filename)
    title=next(p.text for p in Document(P/'Array_Manuscript.docx').paragraphs if p.style.name=='Title')
    register=json.loads((P/'Approval_evidence_register_TEMPLATE.json').read_text())
    if any(author['final_version_approved'] is not None for author in register['authors']):raise ValueError('Preserve actual approval evidence before preparing a changed version')
    register.update({k:version[k] for k in ['repository_commit','manuscript_pdf_sha256','status']});(P/'Approval_evidence_register_TEMPLATE.json').write_text(json.dumps(register,indent=2)+'\n')
    for name,email,filename in [('Abhishek Kumar Pandey','abhishek.pandey2@bennett.edu.in','Coauthor_review_request_Abhishek_Kumar_Pandey_DRAFT.txt'),('Abhinandan Tripathi','abhinandan282@bit.ac.in','Coauthor_review_request_Abhinandan_Tripathi_DRAFT.txt')]:
        text=f'''DRAFT — NOT SENT. This request is not author consent.
To: {email}
Subject: Exact-version manuscript review requested — controlled feedback benchmark

Dear Dr. {name},

Please review “{title}” and its proposed submission to Array.

Exact manuscript commit: {commit}
PDF SHA-256: {version['manuscript_pdf_sha256']}
Word SHA-256: {version['manuscript_docx_sha256']}
PDF: https://github.com/DrShivamBhardwaj/JICCE_LA_CPPO_Reproducibility/blob/{commit}/publication/array/Array_Manuscript.pdf

The revision adds a separately frozen 1,440-run matched-factorial Cooja study, counterbalanced relay identities and attacker positions, direct diagnostics of the censored–frozen equality, and unsuccessful O3 and LTO compiler deadline optimizations. The current version also adds a retrospective radio-state/current-ratio sensitivity analysis of all 600 historical Cooja runs. Historical studies and failures remain separate. Physical RF/current and production device security remain unvalidated; original signed-receipt deadlines still have 68/200 misses. The manuscript does not claim a universal switching threshold or neural-policy superiority.

The corresponding author has reported your permission and declared equal contribution, no funding and no competing interests. Please review that statement and your metadata. Explicitly approve this exact version or specify changes, and confirm funding/competing-interest disclosures, exclusivity and any related or overlapping manuscripts/preprints. Review the AI-use declaration and responsibility for the data, code and figures. Approval must identify this version; substantive later changes require renewed review.

No submission has been made. No response, consent, signature or contribution is inferred by this draft.

Regards,
Shivam Bhardwaj
Corresponding author
'''
        (P/filename).write_text(text)
    x=json.loads((P/'external_validation_access_check.json').read_text());x.update(review_package_commit=commit,manuscript_pdf_sha256=version['manuscript_pdf_sha256']);(P/'external_validation_access_check.json').write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
    if (P/'Author_permission_register.json').exists():
        actual=json.loads((P/'Author_permission_register.json').read_text())
        actual['prior_package_pdf_sha256']=actual.get('manuscript_pdf_sha256')
        actual.update(repository_commit=commit,manuscript_pdf_sha256=version['manuscript_pdf_sha256'],manuscript_docx_sha256=version['manuscript_docx_sha256'],current_version_review_basis='Permissions reported by corresponding author; independent exact-version coauthor review not asserted')
        (P/'Author_permission_register.json').write_text(json.dumps(actual,indent=2)+'\n')
    (P/'author_review_version.json').write_text(json.dumps(version,indent=2)+'\n')
if __name__=='__main__':main()
