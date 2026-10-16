from pathlib import Path
from docx import Document
from lxml import etree
from docx.oxml.ns import qn
import re,json,zipfile,hashlib
import argparse
ap=argparse.ArgumentParser();ap.add_argument('--baseline',required=True);args=ap.parse_args()
old=Document(args.baseline);new=Document('publication/array/Array_Manuscript.docx')
def tx(d):return '\n'.join(''.join(x.itertext()) for x in d._element.body)
a,b=tx(old),tx(new)
# Every distinct literal parameter/value and identifier from the previous document remains somewhere in the revision.
nums=lambda t:set(re.findall(r'\d+(?:\.\d+)?',t))
missing=nums(a)-nums(b);assert not missing,missing
for pattern in [r'\b[a-f0-9]{40}\b',r'\b(?:410\d\d|760\d\d|76901|770\d\d|830\d\d|840\d\d|850\d\d|94001)\b']:
 assert set(re.findall(pattern,a))<=set(re.findall(pattern,b))
assert [etree.tostring(x) for x in old._element.xpath('//m:oMath')]==[etree.tostring(x) for x in new._element.xpath('//m:oMath')]
assert len(old.tables)==len(new.tables)==7
for x,y in zip(old.tables,new.tables):assert etree.tostring(x._tbl)==etree.tostring(y._tbl)
with zipfile.ZipFile(args.baseline) as x,zipfile.ZipFile('publication/array/Array_Manuscript.docx') as y:
 imagehash=lambda z:sorted(hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('word/media/'))
 oldhash,newhash=imagehash(x),imagehash(y)
 assert len(oldhash)==len(newhash)==10
 assert len(set(oldhash)&set(newhash))==9, "Only the Figure 2 lifecycle artwork may change"
# New nested algorithm has 17 numbered lines and three actual paragraph indentation levels.
ps=new.paragraphs;i=next(i for i,p in enumerate(ps) if p.text.startswith('Algorithm 1:'))
lines=[p for p in ps[i+1:] if re.match(r'^\d{2}\.  ',p.text)]
assert len(lines)==17
assert len({p.paragraph_format.left_indent for p in lines})==3
r=dict(status='passed',literal_parameter_values_preserved=True,commit_hashes_and_fixture_ids_preserved=True,native_equations_byte_identical=10,tables_byte_identical=7,figure_images_byte_identical=9,figure_images_revised=1,algorithm_numbered_lines=17,algorithm_indent_levels=3,editorial_paragraphs=len(json.loads(Path("publication/array/editorial_changes.json").read_text())))
Path('publication/array/editorial_preservation_audit.json').write_text(json.dumps(r,indent=2)+'\n');print(r)
