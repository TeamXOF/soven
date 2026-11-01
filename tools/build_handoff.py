"""Generate SOVEN DOCX snapshots from the maintained Markdown sources.

Requires python-docx. Run from any working directory; optional --root selects
the repository. Rendering/visual QA is a separate, required delivery step.
"""
import argparse,hashlib,json,re
from pathlib import Path
from datetime import datetime,timezone
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);args=parser.parse_args()
ROOT=args.root;PACK=ROOT/'analysis/soven';OUT=PACK/'documents';OUT.mkdir(parents=True,exist_ok=True)
groups=[
 ('01_SOVEN_Project_Context_and_Current_State.docx','SOVEN project context and current state',['01_PROJECT_CONTEXT.md','02_CURRENT_STATE.md']),
 ('02_SOVEN_Architecture_and_Engineering_Handoff.docx','SOVEN architecture and engineering handoff',['03_ARCHITECTURE.md']),
 ('03_SOVEN_Product_Requirements_and_Source_Review.docx','SOVEN product requirements and source review',['04_PRODUCT_REQUIREMENTS.md','05_SOURCE_REVIEW.md']),
 ('04_SOVEN_Meta_Integration_and_Privacy.docx','SOVEN Meta integration and privacy',['06_META_PROVIDER_PLAN.md','16_REASONING_PROVIDER_INTEGRATION.md']),
 ('05_SOVEN_Roadmap_and_Decisions.docx','SOVEN implementation roadmap and decisions',['07_IMPLEMENTATION_ROADMAP.md','10_DECISIONS_AND_HANDOFF.md','11_PRODUCT_DEFAULTS.md']),
 ('06_SOVEN_Validation_Operations_and_Brand.docx','SOVEN validation operations and brand',['08_VALIDATION_AND_OPERATIONS.md','09_BRAND_AND_REPOSITORY.md']),
]

def inline(paragraph,text):
    text=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'\1 (\2)',text)
    for part in re.split(r'(\*\*.*?\*\*|`[^`]+`)',text):
        if not part:continue
        run=paragraph.add_run(part[2:-2] if part.startswith('**') else part[1:-1] if part.startswith('`') else part)
        if part.startswith('**'):run.bold=True
        if part.startswith('`'):run.font.name='Consolas';run.font.size=Pt(10)

def add_markdown(doc,text):
    pending=[];code=False
    def flush():
        if pending:
            p=doc.add_paragraph();inline(p,' '.join(pending));pending.clear()
    for line in text.splitlines():
        if line.startswith('```'):flush();code=not code;continue
        if code:
            p=doc.add_paragraph();r=p.add_run(line);r.font.name='Consolas';r.font.size=Pt(9);continue
        if not line.strip():flush();continue
        heading=re.match(r'^(#{1,4})\s+(.*)',line)
        if heading:
            flush();doc.add_heading(re.sub(r'[^\w\s]',' ',heading[2]).strip(),level=min(3,len(heading[1])))
        elif re.match(r'^[-*]\s+',line):
            flush();p=doc.add_paragraph(style='List Bullet');inline(p,line[2:])
        elif re.match(r'^\d+\.\s+',line):
            flush();p=doc.add_paragraph(style='List Number');inline(p,re.sub(r'^\d+\.\s+','',line))
        else:pending.append(line)
    flush()

manifest=[]
for filename,title,sources in groups:
    compact=filename.startswith(('01_', '02_'))
    tight=filename.startswith('02_')
    doc=Document();sec=doc.sections[0]
    sec.page_width=Inches(8.5);sec.page_height=Inches(11)
    sec.top_margin=Inches(.7);sec.bottom_margin=Inches(.7);sec.left_margin=Inches(.8);sec.right_margin=Inches(.8)
    sec.header_distance=Inches(.25);sec.footer_distance=Inches(.3)
    for name in ['Normal','Title','Subtitle','Heading 1','Heading 2','Heading 3','List Bullet','List Number']:
        style=doc.styles[name];style.font.name='Aptos';style.font.color.rgb=RGBColor(0,0,0)
        style.paragraph_format.space_after=Pt(3 if tight else 4 if compact else 5);style.paragraph_format.line_spacing=1.0 if compact else 1.03
    doc.styles['Normal'].font.size=Pt(10.5 if compact else 11)
    for name,size in [('Title',26),('Heading 1',17),('Heading 2',13),('Heading 3',11)]:
        doc.styles[name].font.size=Pt(size);doc.styles[name].font.bold=True
        doc.styles[name].paragraph_format.space_before=Pt((8 if tight else 10 if compact else 12) if name!='Title' else 0)
        doc.styles[name].paragraph_format.keep_with_next=True
    h=sec.header.paragraphs[0];h.text='SOVEN   |   Project and engineering handoff';h.style=doc.styles['Normal']
    for r in h.runs:r.font.size=Pt(9);r.font.color.rgb=RGBColor(0,0,0)
    footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    footer.add_run('SOVEN   |   1 November 2026   |   ')
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
    for r in footer.runs:r.font.size=Pt(9)
    doc.add_paragraph(title,style='Title')
    doc.add_paragraph('A maintained project handoff for the SOVEN owner and next engineer. Working behavior and planned changes are identified separately.')
    p=doc.add_paragraph('Source files: '+', '.join(sources));p.paragraph_format.space_after=Pt(12)
    for r in p.runs:r.font.size=Pt(9)
    for source in sources:add_markdown(doc,(PACK/source).read_text(encoding='utf-8'))
    if filename.startswith('02_'):
        for paragraph in doc.paragraphs:
            if paragraph.text in {'Implemented multilingual foundation and next work', 'Account profiles and personal scopes'}:
                paragraph.paragraph_format.page_break_before=True
    # An exact delivery record is appended when available, without altering source assertions.
    if filename.startswith('06_'):
        for record_name in ['VALIDATION_RESULTS.json','DELIVERY_STATUS.json','FOUNDATION_VALIDATION.json','ACCOUNT_PROFILE_VALIDATION.json','UI_REDESIGN_VALIDATION.json']:
            if (PACK/record_name).exists():
                record=json.loads((PACK/record_name).read_text(encoding='utf-8'))
                doc.add_heading(record_name.replace('_',' ').replace('.json',''),level=1)
                for key,value in record.items():
                    p=doc.add_paragraph();p.add_run(key.replace('_',' ') + ': ').bold=True
                    p.add_run(json.dumps(value,ensure_ascii=False) if isinstance(value,(dict,list)) else str(value))
    doc.core_properties.title=title;doc.core_properties.author='SOVEN project team';doc.core_properties.subject='Project handoff and engineering status'
    doc.core_properties.created=datetime(2026,11,1,tzinfo=timezone.utc);doc.core_properties.modified=datetime(2026,11,1,tzinfo=timezone.utc)
    # Word's bundled default Title style can contain a blue paragraph rule.
    # Remove paragraph borders in styles and content, not just direct run color.
    for root in [doc.styles.element,doc.element]:
        for border in list(root.iter(qn('w:pBdr'))):border.getparent().remove(border)
    doc.save(OUT/filename)
    manifest.append({'document':'documents/'+filename,'title':title,'sources':[{'path':s,'sha256':hashlib.sha256((PACK/s).read_bytes().replace(b'\r\n',b'\n')).hexdigest()} for s in (sources + ([n for n in ['VALIDATION_RESULTS.json','DELIVERY_STATUS.json','FOUNDATION_VALIDATION.json','ACCOUNT_PROFILE_VALIDATION.json','UI_REDESIGN_VALIDATION.json'] if (PACK/n).exists()] if filename.startswith('06_') else []))],
                     'sha256':hashlib.sha256((OUT/filename).read_bytes()).hexdigest(),'render_review':'see DOCUMENT_QA.json'})
(PACK/'DOCUMENT_MANIFEST.json').write_text(json.dumps({'text_hash_format':'UTF-8 with CRLF normalized to LF; DOCX hashes use exact bytes','maintained_format':'Markdown','generated_format':'DOCX','source_date':'2026-11-01','documents':manifest},indent=2),encoding='utf-8')
print(json.dumps({'generated_documents':len(manifest),'output':str(OUT)}))
