"""Materialize the reference resume's effective formatting for portable editing."""
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree as ET
import json

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'output/resume/updated_resume.docx'
OUT = ROOT / 'output/resume/updated_resume_pdf_matched.docx'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
NS = {'w':W, 'a':A}
def q(local): return '{' + W + '}' + local
def elem(local, **attrs):
    e = ET.Element(q(local))
    for k,v in attrs.items(): e.set(q(k), str(v))
    return e
def replace_child(parent, child):
    old = parent.find(child.tag)
    if old is not None: parent.replace(old, deepcopy(child))
    else: parent.append(deepcopy(child))
def overlay(base, addition):
    if addition is None: return
    for child in addition:
        if ET.QName(child).localname in ('pStyle','rStyle'): continue
        old = base.find(child.tag)
        if old is not None and len(child)==0:
            for k,v in child.attrib.items(): old.set(k,v)
        else: replace_child(base, child)
def strip_theme(root):
    for e in root.iter():
        for attr in list(e.attrib):
            if 'theme' in ET.QName(attr).localname.lower(): del e.attrib[attr]
def explicit_font(rpr, size=None, bold=None):
    replace_child(rpr, elem('rFonts', ascii='Calibri', hAnsi='Calibri', eastAsia='Calibri', cs='Calibri'))
    replace_child(rpr, elem('color', val='000000'))
    if size is not None:
        replace_child(rpr, elem('sz', val=size))
        replace_child(rpr, elem('szCs', val=size))
    if bold is not None:
        replace_child(rpr, elem('b', val='1' if bold else '0'))
        replace_child(rpr, elem('bCs', val='1' if bold else '0'))
    strip_theme(rpr)

with ZipFile(SRC) as z: parts = {n:z.read(n) for n in z.namelist()}
styles = ET.fromstring(parts['word/styles.xml'])
doc = ET.fromstring(parts['word/document.xml'])
settings = ET.fromstring(parts['word/settings.xml'])
style_map = {s.get(q('styleId')):s for s in styles.findall(q('style'))}
defaults = styles.find(q('docDefaults'))
rdefaults = defaults.find('./w:rPrDefault/w:rPr', NS)
pdefaults = defaults.find('./w:pPrDefault/w:pPr', NS)

def chain(style_id):
    result=[]
    seen=set()
    while style_id and style_id not in seen:
        seen.add(style_id)
        style=style_map.get(style_id)
        if style is None: break
        result.append(style)
        b=style.find(q('basedOn'))
        style_id=b.get(q('val')) if b is not None else None
    return list(reversed(result))

def effective(style_id, kind, direct=None, char_style=None):
    target=ET.Element(q(kind))
    overlay(target, pdefaults if kind=='pPr' else rdefaults)
    for s in chain(style_id): overlay(target, s.find(q(kind)))
    if char_style:
        for s in chain(char_style): overlay(target, s.find(q(kind)))
    overlay(target, direct)
    return target

# Compute effective properties from the untouched source before changing defaults.
paragraph_data=[]
for p in doc.findall('.//w:body/w:p', NS):
    ppr=p.find(q('pPr'))
    sid=ppr.find(q('pStyle')) if ppr is not None else None
    style_id=sid.get(q('val')) if sid is not None else 'Normal'
    resolved=effective(style_id,'pPr',ppr)
    if sid is not None: resolved.insert(0,deepcopy(sid))
    for key,val in [('jc','left'),('keepNext','0'),('keepLines','0'),('widowControl','1')]:
        if resolved.find(q(key)) is None: resolved.append(elem(key,val=val))
    spacing=resolved.find(q('spacing'))
    if spacing is None:
        spacing=elem('spacing'); resolved.append(spacing)
    for key,val in [('before','0'),('after','0'),('line','240'),('lineRule','auto')]:
        if spacing.get(q(key)) is None: spacing.set(q(key),val)
    for key in ['beforeAutospacing','afterAutospacing']:
        spacing.set(q(key),'0')
    replace_child(resolved,elem('contextualSpacing',val='0'))
    runs=[]
    for run in p.findall(q('r')):
        rpr=run.find(q('rPr'))
        rstyle=rpr.find(q('rStyle')) if rpr is not None else None
        rid=rstyle.get(q('val')) if rstyle is not None else None
        rr=effective(style_id,'rPr',rpr,rid)
        sz=rr.find(q('sz'))
        b=rr.find(q('b'))
        explicit_font(rr,sz.get(q('val')) if sz is not None else '24', b is not None and b.get(q('val'),'1') not in ('0','false'))
        if rr.find(q('i')) is None: rr.append(elem('i',val='0'))
        runs.append((run,rr))
    paragraph_data.append((p,resolved,runs))

for p,resolved,runs in paragraph_data:
    old=p.find(q('pPr'))
    if old is not None: p.replace(old,resolved)
    else: p.insert(0,resolved)
    for run,rr in runs:
        old=run.find(q('rPr'))
        if old is not None: run.replace(old,rr)
        else: run.insert(0,rr)

# Synchronize base and linked styles, so newly typed text stays consistent too.
normal_r=effective('Normal','rPr')
explicit_font(normal_r,'24',False)
normal_p=effective('Normal','pPr')
replace_child(normal_p, elem('spacing',before='0',after='40',line='259',lineRule='auto'))
defaults.find(q('rPrDefault')).replace(rdefaults,deepcopy(normal_r))
defaults.find(q('pPrDefault')).replace(pdefaults,deepcopy(normal_p))

for s in styles.findall(q('style')):
    rpr=s.find(q('rPr'))
    if rpr is not None:
        strip_theme(rpr)
        replace_child(rpr, elem('color',val='000000'))
        replace_child(rpr, elem('rFonts',ascii='Calibri',hAnsi='Calibri',eastAsia='Calibri',cs='Calibri'))
    for tag in ['autoRedefine']:
        for e in list(s.findall(q(tag))): s.remove(e)

for paragraph_id, char_id in [('Title','TitleChar'),('Heading1','Heading1Char'),('Heading2','Heading2Char')]:
    paragraph_style=style_map[paragraph_id]
    char_style=style_map[char_id]
    rr=effective(paragraph_id,'rPr')
    explicit_font(rr,'44' if paragraph_id=='Title' else '24',True)
    replace_child(paragraph_style,rr)
    replace_child(char_style,rr)
    # Explicit paragraph values mirror those written into the visible paragraphs.
    representative=next((pr for p,pr,_ in paragraph_data if (pr.find(q('pStyle')) is not None and pr.find(q('pStyle')).get(q('val'))==paragraph_id)),None)
    if representative is not None:
        pr=deepcopy(representative)
        for e in list(pr.findall(q('pStyle'))): pr.remove(e)
        # Per-entry date tabs remain directly set in document.xml.
        for e in list(pr.findall(q('tabs'))): pr.remove(e)
        replace_child(paragraph_style,pr)

# Lock theme font fallback to the PDF's font, and clear style-driven blue fallbacks.
theme=ET.fromstring(parts['word/theme/theme1.xml'])
for e in theme.findall('.//a:fontScheme/a:majorFont/a:latin',NS)+theme.findall('.//a:fontScheme/a:minorFont/a:latin',NS):
    e.set('typeface','Calibri')
for tag in ['accent1','accent2','accent3','accent4','accent5','accent6','hlink','folHlink']:
    e=theme.find('.//a:clrScheme/a:'+tag,NS)
    if e is not None:
        for c in list(e): e.remove(c)
        c=ET.SubElement(e,'{'+A+'}srgbClr'); c.set('val','000000')
for e in list(settings.findall(q('updateStyles'))): settings.remove(e)

def serialize(root):
    return ET.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
parts['word/styles.xml']=serialize(styles)
parts['word/document.xml']=serialize(doc)
parts['word/settings.xml']=serialize(settings)
parts['word/theme/theme1.xml']=serialize(theme)
with ZipFile(OUT,'w',ZIP_DEFLATED) as z:
    for name,data in parts.items(): z.writestr(name,data)

report={
    'output':str(OUT),
    'paragraphs_with_explicit_formatting':len(paragraph_data),
    'runs_with_explicit_font_color_size':sum(len(runs) for _,_,runs in paragraph_data),
    'linked_character_styles_normalized':['TitleChar','Heading1Char','Heading2Char'],
}
(ROOT/'tmp/resume/format_fix_report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
