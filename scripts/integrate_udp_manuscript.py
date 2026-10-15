"""Integrate verified software evidence without upgrading claims to deployment proof."""
from pathlib import Path
import re,json,copy
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.table import Table
from docx.text.paragraph import Paragraph
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'publication/updated_evidence'
OUT.mkdir(parents=True,exist_ok=True)
FIG=OUT/'figures';FIG.mkdir(exist_ok=True)
import runpy
runpy.run_path(str(ROOT/'scripts/build_udp_publication_figure.py'))
SOURCE=ROOT/'publication/JICCE_LA_CPPO_Revised_Manuscript.docx'
d=Document(SOURCE)
original_math=len(d.element.xpath('.//m:oMath'))
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
def save(fig,name):
 for suffix in ['svg','pdf','eps']:fig.savefig(FIG/f'{name}.{suffix}',bbox_inches='tight')
 fig.savefig(FIG/f'{name}.png',dpi=900,bbox_inches='tight');plt.close(fig)
h=ROOT/'data/historical_af_v3';s=pd.read_csv(h/'seed_summary.csv');tr=pd.read_csv(h/'training_log.csv');ep=pd.read_csv(h/'episode_metrics.csv')
policies=['af_v3_mlp_cppp','af_v3_attention_cppp'];labels=['Same-width MLP','Attention'];colors=['#555555','#21618c']
fig,ax=plt.subplots(figsize=(6.2,2.7),layout='constrained')
for policy,label,color in zip(policies,labels,colors):
 x=tr[tr.policy==policy].groupby('update').mean_episode_reward.agg(['mean','sem'])
 ax.plot(x.index,x['mean'],label=label,color=color,marker='o',ms=3)
 ax.fill_between(x.index,x['mean']-stats.t.ppf(.975,29)*x['sem'],x['mean']+stats.t.ppf(.975,29)*x['sem'],color=color,alpha=.13)
ax.set(xlabel='Training update',ylabel='Mean episode reward');ax.legend(frameon=False,loc='lower center',bbox_to_anchor=(.5,1.02),ncol=2);save(fig,'fig2')
for number,metric,ylabel in [(3,'class_0_mean_delay_ms','Class 0 delivered delay (ms)'),(4,'class_0_delay_violation_rate','Class 0 total violation (%)')]:
 fig,ax=plt.subplots(figsize=(6.2,2.7),layout='constrained')
 for policy,label,color in zip(policies,labels,colors):
  x=s[s.policy==policy].sort_values('seed');ax.plot(x.seed,x[metric]*(100 if number==4 else 1),label=label,color=color,marker='o',ms=3,lw=.8)
 ax.set(xlabel='Evaluation seed',ylabel=ylabel);ax.ticklabel_format(axis='x',style='plain',useOffset=False);ax.legend(frameon=False,loc='lower center',bbox_to_anchor=(.5,1.02),ncol=2);save(fig,f'fig{number}')
fig,ax=plt.subplots(figsize=(6.2,2.7),layout='constrained')
x=ep[(ep.traffic_class==0)&ep.delivered.astype(bool)]
for i,(policy,label,color) in enumerate(zip(policies,labels,colors)):
 counts=x[x.policy==policy].hops.value_counts(normalize=True).sort_index();ax.bar(counts.index+(i-.5)*.32,counts.values,width=.32,label=label,color=color)
ax.set(xlabel='Delivered route hop count',ylabel='Fraction of delivered class 0 packets');ax.legend(frameon=False,loc='lower center',bbox_to_anchor=(.5,1.02),ncol=2);save(fig,'fig5')
# Replace embedded raster plots with regenerated raw-data artwork.
for i in range(2,6):
 rel=next(rel for rel in d.part.rels.values() if rel.reltype.endswith('/image') and str(rel.target_part.partname).endswith(f'image{i}.png'))
 rel.target_part._blob=(FIG/f'fig{i}.png').read_bytes()
for p in d.paragraphs:
 if p.text.startswith('Fig. 2.'):
  p.text='Fig. 2. Training reward across 30 historical seeds. Shading shows pointwise 95% t intervals.'
 if p.text.startswith('Fig. 5.'):
  p.text='Fig. 5. Pooled hop-count composition of delivered Class 0 packets in the historical experiment.'
for q in d.paragraphs:
 if q.text.startswith('Each line in Figures 3 and 4 links the two policies'):
  q.text=q.text.replace('Each line in Figures 3 and 4 links the two policies for one matched seed on a co-primary endpoint.', 'Figures 3 and 4 show seedwise outcomes for both policies on the co-primary endpoints.')
# Trim abstract and distinguish the evidence layers.
abstract=('Routing decisions in wireless sensor networks depend on energy, deadlines and uncertain forwarding behavior. '
'We evaluate a local-attention constrained PPO router with class-specific service debt and Bayesian forwarding risk. '
'A historical 30-seed comparison improved reliability but failed its joint superiority criterion. '
'In a separate capacity-matched validation, attention increased critical-class delivered delay by 0.821 ms and reduced total violations by 1.522 percentage points; neither co-primary contrast was significant after Holm correction. '
'Actual UDP feedback then connected received forwarding acknowledgments to frozen-policy decisions. In an exploratory shared-target fault diagnostic across 30 new fixtures, attention delivered 85.39% of packets and a capacity-matched MLP delivered 32.22%, a paired difference of 53.17 percentage points (95% CI 35.31–71.02). '
'These fixed-state localhost results establish software integration under targeted relay failures. They do not establish live intrusion detection, realistic multihop wireless performance, absolute service-budget satisfaction or a general attention advantage.')
d.paragraphs[7].text=abstract
# Remove unverified evaluation detail from the literature matrix; retain supported scope.
for row in d.tables[0].rows[1:-1]:
 row.cells[5].text='Method positioning; no cross-paper numerical comparison'
# Context distinguishes old unequal-capacity evidence from the new comparison.
for p in d.paragraphs:
 if p.text=='The unequal parameter counts limit attribution of any effect to representation alone.':
  p.text='The historical same-width comparison has unequal parameter counts. The separate capacity-matched validation controls this difference approximately.'
 if p.text.startswith('LA-CPPO shares candidate encoding and scoring across rows'):
  p.text='LA-CPPO shares candidate encoding and scoring across rows and pools the critic input symmetrically. A fixed-slot MLP receives the same serialized state. The historical comparison matches hidden width; the independent validation approximately matches total parameter count. Neither design matches every computational or architectural property.'
# Insert a software-integration subsection within the existing new validation section.
anchor=next(p for p in d.paragraphs if p.text=='10. Discussion')
new=[]
def add(text,style=None):
 p=d.add_paragraph(text,style);new.append(p._p);return p
add('9.1 Packet feedback and frozen policy integration','Heading 2')
add('The software feedback adapter sends an actual UDP datagram to the selected relay and accepts an acknowledgment only from the intended endpoint with matching sequence and nonce. A separate sink socket witnesses downstream receipt before the relay acknowledges forwarding. The acknowledgment or timeout updates the Bayesian posterior before the next observation and policy inference. No attack label or fault-target identifier is supplied to the policy. Nonces prevent packet confusion but do not authenticate peers. Expected link PDR remains model-derived. In the simulator, a hop outcome is credited to the current transmitting node; in the UDP diagnostic, a downstream receipt is credited to the selected relay after its relay-to-sink forwarding. The observation point differs, so the diagnostic is an interface-transfer test rather than a bitwise reproduction of simulator feedback.')
add('A preliminary periodic-fault fixture changed policy probabilities but produced no next-hop changes in 360 attempts. A subsequent persistent initial-relay fault diagnostic used all 30 frozen attention checkpoints and 30 fresh fixtures. Twenty-five fixtures selected an alternative relay; five did not. In the 25 first-switch decisions, the faulty relay remained a candidate and was unmasked. These exploratory diagnostics motivated the separately specified capacity comparison below; they are not confirmatory trials.')
add('9.2 Shared target capacity comparison','Heading 2')
add('Thirty fresh topology seeds, 73001–73030, were paired with the existing attention and capacity-MLP checkpoints, 41001–41030. Each fixture used two shared fault targets: the relay initially preferred by attention and the relay initially preferred by the MLP. Both controllers faced both targets for 30 attempts each. No model was retrained or selected after the outcomes. Source position, energy, queues and QoS state stayed fixed within each run; only forwarding-risk posteriors evolved. The relay fault was persistent and targeted, rather than a sample from a random malicious-node distribution.')
add('The two target choices coincided in 26 fixtures. We averaged their outcomes within fixture before paired inference, retaining n = 30 rather than treating the 120 executed runs as independent experiments. Both policies initially chose the faulty relay in 56 of their 60 scenarios. Mean sink delivery was 85.39% for attention and 32.22% for the capacity-matched MLP. The paired difference was 53.17 percentage points (95% Student-t interval, 35.31–71.02; two-sided paired p = 1.246 × 10⁻⁶). Attention performed better in 21 fixtures, tied in eight and worse in one. Table 10 and Fig. 7 report these diagnostic outcomes.')
add('Table 10. Shared-target UDP diagnostic across 30 paired fixtures.')
t=d.add_table(rows=1,cols=4);new.append(t._tbl)
for c,v in zip(t.rows[0].cells,['Policy','Parameters','Executed runs','Mean delivery %']):c.text=v
for vals in [['Capacity MLP','63,554','60','32.22'],['Attention','63,368','60','85.39']]:
 for c,v in zip(t.add_row().cells,vals):c.text=v
p=d.add_paragraph();p.add_run().add_picture(str(FIG/'fig7.png'),width=Cm(16));new.append(p._p)
add('Fig. 7. Shared-target UDP delivery. Each fixture averages two fault-target strata; lines join paired controller outcomes.')
add('9.3 Verification and interpretation limits','Heading 2')
add('Across 3,600 attempts, the sink witnessed 2,117 deliveries and 1,483 attempts timed out. The adapter and sink witness agreed on every recorded outcome. A separate verifier reconstructed the observations, risk posteriors, checkpoint hashes, policy probabilities and selected actions for all records. All 47 repository tests passed. This verifies internal software consistency; it is not an external packet-capture or authenticated observer audit.')
add('The UDP payload is a seven-byte fixture message plus JSON metadata, not the simulator’s 4,000-bit application packet. Relays communicate directly with the localhost sink regardless of radio reachability. The 20 ms timeout is a harness setting, not a measured wireless deadline. MAC contention, fading, sleep currents, acknowledgment energy and distributed authentication are absent. The positive diagnostic therefore supports a feedback-responsive frozen routing pipeline in this targeted fixture, while the earlier nominal co-primary results remain unchanged.')
for el in new:anchor._p.addprevious(el)
# Update prior wording whose scope predates UDP evidence.
for p in d.paragraphs:
 if p._p in new:continue
 if p.text.startswith('Forwarding observations still come directly from simulator outcomes'):
  p.text='In the nominal simulation study, forwarding observations come from simulator outcomes. The separate UDP diagnostics below validate packet/feedback software integration but retain synthetic link features and omit realistic radio overhead.'
 if p.text.startswith('LA-CPPO combines a candidate-equivariant actor, invariant critics'):
  p.text='LA-CPPO combines shared candidate scoring, invariant critics, service debt and forwarding-risk estimates. The historical joint superiority gate failed, and neither nominal capacity-matched co-primary contrast was significant after Holm correction. Risk removal reduced reliability. A separate targeted UDP diagnostic showed higher delivery for attention than the capacity MLP and verified packet-to-feedback-to-policy integration. Its fixed-state localhost design does not establish physical wireless effectiveness, live IDS accuracy or absolute constraint satisfaction. The evidence supports further deployment-relevant evaluation rather than a universal attention advantage.'
 # Historical table becomes XI; preserve the newly inserted table X.
 if 'Table 10' in p.text:p.text=p.text.replace('Table 10','Table 11')
# Restore math paragraphs accidentally avoided below: replacements above only touched table text.
# Reset algorithm step numbering independently and retain indentation.
for table in d.tables:
 if table.cell(0,0).text.startswith('Algorithm'):
  table.cell(0,0).text=table.cell(0,0).text.replace('Algorithm - ','Algorithm ')
  count=0
  for p in table.cell(1,0).paragraphs:
   if not p.text or p.text.startswith(('Input:','Output:')):continue
   count+=1;text=p.text
   p.style=d.styles['Normal']
   pr=p._p.get_or_add_pPr()
   for n in list(pr.findall(qn('w:numPr'))):pr.remove(n)
   p.text=f'{count}. '+text
# IEEE-style bibliographic records from publisher metadata and supplied foundational records.
raw=json.loads((ROOT/'docs/reference_content_audit_source.json').read_text())
old_refs={int(re.match(r'\[(\d+)\]',p.text)[1]):p for p in d.paragraphs if re.match(r'^\[\d+\]',p.text)}
formatted={}
for i,row in enumerate(raw,1):
 original=old_refs[i].text
 if row.get('status')=='retrieved':
  authors=[]
  for person in row.get('author') or []:
   initials=' '.join(c+'.' for w in re.split(r'[\s-]+',person.get('given','')) if w for c in (re.findall(r'[A-Za-z]',w) if '.' in w or (w.isupper() and len(w)<=4) else [w[0]]))
   authors.append((initials+' '+person.get('family','')).strip())
  a=', '.join(authors[:-1])+', and '+authors[-1] if len(authors)>1 else (authors[0] if authors else original.split('. ')[0].split('] ')[-1])
  title=(row.get('title') or [''])[0];container=(row.get('container-title') or [''])[0]
  year=(row.get('published') or {'date-parts':[[int(re.findall(r'(?:19|20)\d{2}',original)[-1])]]})['date-parts'][0][0]
  details=''
  if row.get('volume'):details+=f", vol. {row['volume']}"
  if row.get('issue'):details+=f", no. {row['issue']}"
  if row.get('page'):details+=f", pp. {row['page'].replace('--','–')}"
  elif row.get('article-number'):details+=f", Art. no. {row['article-number']}"
  formatted[i]=f'{a}, “{title},” {container}{details}, {year}. DOI: {row["doi"]}.'
 else:
  body=re.sub(r'^\[\d+\] ','',original)
  parts=body.split('. ',1)
  authorparts=parts[0].split(', ')
  names=[]
  for name in authorparts:
   if name=='et al':names.append('et al.');continue
   words=name.split();initials=words[-1] if len(words)>1 else ''
   names.append(' '.join(c+'.' for c in initials)+' '+' '.join(words[:-1]))
  formatted[i]=', '.join(names)+', '+(parts[1] if len(parts)>1 else body)
# Explicit foundational entries avoid ambiguous automatic author parsing.
formatted.update({
3:'W. R. Heinzelman, A. Chandrakasan, and H. Balakrishnan, “Energy-efficient communication protocol for wireless microsensor networks,” in Proceedings of the Hawaii International Conference on System Sciences, 2000. DOI: 10.1109/HICSS.2000.926982.',
7:'R. S. Sutton and A. G. Barto, Reinforcement Learning An Introduction, 2nd ed. Cambridge, MA: MIT Press, 2018.',
8:'J. Schulman, F. Wolski, P. Dhariwal, A. Radford, and O. Klimov, “Proximal policy optimization algorithms,” arXiv:1707.06347, 2017.',
9:'J. Schulman, P. Moritz, S. Levine, M. I. Jordan, and P. Abbeel, “High-dimensional continuous control using generalized advantage estimation,” in Proceedings of ICLR, 2016. arXiv:1506.02438.',
10:'J. Achiam, D. Held, A. Tamar, and P. Abbeel, “Constrained policy optimization,” in Proceedings of ICML, vol. 70, pp. 22–31, 2017.',
11:'A. Vaswani et al., “Attention is all you need,” Advances in Neural Information Processing Systems, vol. 30, pp. 5998–6008, 2017.',
12:'M. Zaheer, S. Kottur, S. Ravanbakhsh, B. Poczos, R. Salakhutdinov, and A. J. Smola, “Deep sets,” Advances in Neural Information Processing Systems, vol. 30, pp. 3391–3401, 2017.',
13:'M. J. Neely, Stochastic Network Optimization with Application to Communication and Queueing Systems. Morgan and Claypool, 2010.'})
formatted.update({
14:'J. Yang, S. He, Y. Xu, L. Chen, and J. Ren, “A trusted routing scheme using blockchain and reinforcement learning for wireless sensor networks,” Sensors, vol. 19, no. 4, Art. no. 970, 2019. DOI: 10.3390/s19040970.',
16:'N. Manogaran, M. T. M. Raphael, R. Raja, A. K. Jayakumar, M. Nandagopal, B. Balusamy, and G. Ghinea, “Developing a novel adaptive double deep Q-learning-based routing strategy for IoT-based wireless sensor network with federated learning,” Sensors, vol. 25, no. 10, Art. no. 3084, 2025. DOI: 10.3390/s25103084.',
18:'Y. Song, J. Zhou, X. Li, and J. Liu, “Enabling robust and generalized DRL-driven routing optimization via exploration of graph neural networks,” IEEE Transactions on Cognitive Communications and Networking, vol. 11, no. 6, pp. 4281–4298, 2025. DOI: 10.1109/TCCN.2025.3544276.',
23:'A. Iqbal and M. F. Siddiqui, “Feasibility-aware reinforcement learning for reliable hop-constrained routing in wireless sensor networks,” Computers, Materials and Continua, vol. 89, no. 1, Art. no. 85, 2026. DOI: 10.32604/cmc.2026.084851.'})
# Move appendix narrative ahead of declarations, retaining all results.
declarations=next(p for p in d.paragraphs if p.text=='Declarations')
appendix_start=next(i for i,p in enumerate(d.paragraphs) if p.text.startswith('Appendix A Historical'))
appendix_paras=list(d.paragraphs[appendix_start:])
for p in appendix_paras:
 if p.text=='References':break
 if p.text.startswith('Table '):continue
 if p.text.startswith('Appendix A'):p.style=d.styles['Heading 1']
 declarations._p.addprevious(p._p)
# Audit citation order across document blocks, including table cells.
ref_heading=next(p for p in d.paragraphs if p.text=='References')
blocks=[]
for el in d.element.body:
 if el is ref_heading._p:break
 if el.tag==qn('w:p'):blocks.append(Paragraph(el,d))
 elif el.tag==qn('w:tbl'):
  for row in Table(el,d).rows:
   for cell in row.cells:blocks.extend(cell.paragraphs)
def ids(text):
 return [n for piece in re.split(r'\s*,\s*',text) for n in (list(range(int(piece.split('-')[0]),int(piece.split('-')[1])+1)) if '-' in piece else [int(piece)])]
pattern=re.compile(r'\[([0-9]+(?:\s*[-–,]\s*[0-9]+)*)\]')
order=[]
for p in blocks:
 for m in pattern.finditer(p.text):
  values=ids(m[1].replace('–','-'))
  if not all(1<=n<=27 for n in values):continue
  for n in values:
   if n not in order:order.append(n)
assert set(order)==set(range(1,28)),order
mapping={n:i+1 for i,n in enumerate(order)}
for p in blocks:
 for run in p.runs:
  if run._r.xpath('.//m:oMath | .//w:drawing'):continue
  run.text=pattern.sub(lambda m:('['+', '.join(str(mapping[n]) for n in ids(m[1].replace('–','-')))+']') if all(n in mapping for n in ids(m[1].replace('–','-'))) else m[0],run.text)
for p in old_refs.values():p._p.getparent().remove(p._p)
for old in order:d.add_paragraph(f'[{mapping[old]}] '+formatted[old])
# Roman main headings, alphabetic second level and table numerals.
def roman(n):
 out=''
 for value,symbol in [(1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),(100,'C'),(90,'XC'),(50,'L'),(40,'XL'),(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]:
  while n>=value:out+=symbol;n-=value
 return out
for p in d.paragraphs:
 if p.style.name=='Heading 1' and re.match(r'^\d+\.',p.text):
  m=re.match(r'^(\d+)\.\s*(.*)',p.text);p.text=roman(int(m[1]))+'. '+m[2]
 elif p.style.name=='Heading 2' and re.match(r'^\d+\.\d+',p.text):
  m=re.match(r'^(\d+)\.(\d+)\s*(.*)',p.text);p.text=chr(64+int(m[2]))+'. '+m[3]
 for run in p.runs:
  if run._r.xpath('.//m:oMath | .//w:drawing'):continue
  run.text=re.sub(r'Table (\d+)',lambda m:'Table '+roman(int(m[1])),run.text)
  run.text=re.sub(r'Section (\d+)(?:\.(\d+))?',lambda m:'Section '+roman(int(m[1]))+('.'+chr(64+int(m[2])) if m[2] else ''),run.text)
# Correct native equation integrity and spacing without flattening math.
assert len(d.element.xpath('.//m:oMath'))==original_math
# Format initial submission following accessible society instructions; current portal remains unchecked.
for section in d.sections:
 section.page_width=Cm(21);section.page_height=Cm(29.7)
 section.top_margin=section.bottom_margin=section.left_margin=section.right_margin=Cm(2.5)
for name in ['Normal','Body Text']:
 d.styles[name].font.name='Times New Roman';d.styles[name].font.size=Pt(9.5)
 d.styles[name].paragraph_format.line_spacing=2
for p in d.paragraphs:
 p.paragraph_format.page_break_before=False
 if not p.text.startswith(('Fig.','Table ')):p.paragraph_format.line_spacing=2
 if p.style.name.startswith('Heading'):p.paragraph_format.keep_with_next=True
 for run in p.runs:
  run.font.name='Times New Roman';run.font.color.rgb=RGBColor(0,0,0)
  if p.style.name not in ['Title','Heading 1','Heading 2','Heading 3']:run.font.size=Pt(9.5)
for t in d.tables:
 pr=t._tbl.tblPr
 for old in list(pr.findall(qn('w:tblBorders'))):pr.remove(old)
 borders=OxmlElement('w:tblBorders')
 for edge in ['top','bottom','insideH','left','right','insideV']:
  e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single' if edge in ['top','bottom','insideH'] else 'nil');e.set(qn('w:sz'),'4');borders.append(e)
 pr.append(borders)
 for row in t.rows:
  trpr=row._tr.get_or_add_trPr();trpr.append(OxmlElement('w:cantSplit'))
  for cell in row.cells:
   for p in cell.paragraphs:
    p.paragraph_format.line_spacing=1
    for run in p.runs:run.font.name='Times New Roman';run.font.size=Pt(8)
 for cell in t.rows[0].cells:
  for p in cell.paragraphs:
   for run in p.runs:run.bold=True
# Put tables/figures on separate end pages in accordance with the supplied template.
movable=[]
for el in list(d.element.body):
 if el.tag==qn('w:tbl') and not Table(el,d).cell(0,0).text.startswith('Algorithm'):
  previous=el.getprevious();caption=None
  if previous is not None and previous.tag==qn('w:p') and Paragraph(previous,d).text.startswith('Table '):caption=previous
  movable.append(('table',caption,el))
 elif el.tag==qn('w:p') and el.xpath('.//w:drawing'):
  following=el.getnext();caption=None
  if following is not None and following.tag==qn('w:p') and Paragraph(following,d).text.startswith('Fig.'):caption=following
  movable.append(('figure',caption,el))
for kind,caption,el in movable:
 for node in [el,caption]:
  if node is not None:node.getparent().remove(node)
for kind,caption,el in movable:
 p=d.add_paragraph();p.paragraph_format.page_break_before=True
 if kind=='table':
  if caption is not None:p._p.addnext(caption);caption.addnext(el)
  else:p._p.addnext(el)
 else:
  p._p.addnext(el)
  if caption is not None:el.addnext(caption)
# Keep figure and caption together; each table receives one end page where possible.
for p in d.paragraphs:
 if p._p.xpath('.//w:drawing'):p.paragraph_format.keep_with_next=True
 if p.text.startswith('Table '):p.paragraph_format.keep_with_next=True
for shape in d.inline_shapes:
 if shape.width>Cm(16):shape.height=int(shape.height*Cm(16)/shape.width);shape.width=Cm(16)
# Empty hard breaks inherited from the source can create large blanks.
for p in d.paragraphs:
 if not p.text and not p._p.xpath('.//w:drawing'):
  for br in list(p._p.xpath('.//w:br[@w:type="page"]')):br.getparent().remove(br)
d.save(OUT/'JICCE_LA_CPPO_Integrated_Review_Draft.docx')
import runpy
runpy.run_path(str(ROOT/'scripts/finalize_integrated_layout.py'))
# A concise, accurate reviewer evidence record, distinct from a promise of closure.
r=Document();r.add_heading('JICCE resubmission evidence record',0)
r.add_paragraph('Related decision JICCE-26-0057. The redesigned study replaces ROA and deep score replay with LA-CPPO and forwarding-risk feedback. The new results improve the evidence base but do not establish realistic wireless deployment effectiveness.')
for title,text in [
('Reviewer A major comment 1','Actual UDP datagrams now connect selected relays, independently witnessed sink receipt, Bayesian risk updates and subsequent frozen-policy inference. All 3,600 matched-comparison records passed reconstruction. Candidate features remain synthetic and relays reach the sink directly over localhost. MAC behavior, authenticated telemetry, radio energy and live IDS accuracy remain unvalidated. This concern is partly addressed, not closed.'),
('Reviewer A major comment 2','The redesigned model has no supervised node-ID-suffix partition. Training and evaluation use separate environment initialization. Nominal validation retains 30 evaluation seeds and four arms; the new diagnostic adds 30 fresh fixtures and frozen checkpoints. The 120 executed diagnostic runs are averaged to 30 fixture-level pairs. Twenty-six fixtures have duplicate target choices; the manuscript discloses this. Broad field generalization is not claimed.'),
('Reviewer A major comment 3','The original 0.074 percentage-point ROA gain is not used to justify the redesigned method. Nominal capacity-matched co-primary superiority remains unestablished after Holm correction. In the targeted shared-fault UDP diagnostic, attention delivery is 85.39% versus 32.22% for the matched-capacity MLP, difference 53.17 percentage points, 95% CI 35.31–71.02. This diagnostic does not replace the unfavorable nominal findings or establish a universal architecture advantage.'),
('Reviewer A minor comments','The revision uses Roman main section and table numbering, alphabetic subsections, a shortened abstract, native equations, independently restarted algorithm steps and IEEE-style numbered references in order of first appearance. Tables and figures are placed on separate end pages. Historical statistical plots were regenerated from raw data as vector SVG/PDF/EPS and 900-dpi PNG. The accessible society template is older; current portal requirements remain unchecked because author pages could not be retrieved.'),
('Reviewer B','The earlier favorable review applies to the earlier revision. It is not represented as endorsement of the redesigned method or subsequent experiments.'),
('Reproducibility and author checks','All 47 tests pass. Code, frozen checkpoints, raw outputs, protocols, paired analyses and checksums are public. The revised manuscript is a review draft, with native mathematical notation preserved. Before submission, the authors must confirm affiliation/contact details, declarations and the target submission category. No email or journal submission has been sent.')]:r.add_heading(title,1);r.add_paragraph(text)
for sec in r.sections:sec.page_width=Cm(21);sec.page_height=Cm(29.7);sec.top_margin=sec.bottom_margin=sec.left_margin=sec.right_margin=Cm(2.5)
for sty in ['Normal','Title','Heading 1']:r.styles[sty].font.name='Times New Roman';r.styles[sty].font.color.rgb=RGBColor(0,0,0)
r.styles['Normal'].font.size=Pt(10);r.styles['Normal'].paragraph_format.line_spacing=1.2
r.paragraphs[0].style=r.styles['Title']
r.styles['Title'].font.size=Pt(21)
for style in r.styles:
 for node in list(style.element.xpath('.//w:pBdr')):node.getparent().remove(node)
for p in r.paragraphs:
 for node in list(p._p.xpath('.//w:pBdr')):node.getparent().remove(node)
 if p.text=='Reviewer A major comment 3':p.paragraph_format.page_break_before=True
 if p.style.name=='Heading 1':p.paragraph_format.space_before=Pt(10);p.paragraph_format.space_after=Pt(4)
r.save(OUT/'JICCE_Updated_Reviewer_Evidence_Record.docx')
(ROOT/'docs/integration_document_audit.json').write_text(json.dumps(dict(original_native_math=original_math,retained_native_math=len(d.element.xpath('.//m:oMath')),abstract_word_count=len(abstract.split()),citation_order_mapping=mapping,reference_count=len(formatted),figure_count=len(d.inline_shapes)),indent=2))
print('Wrote two review documents; native math retained:',original_math)
