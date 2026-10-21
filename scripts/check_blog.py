"""Check reviewed content, bilingual invariants, local links, and reproducible generation."""
from pathlib import Path
from html.parser import HTMLParser
from html import unescape
from urllib.parse import urlsplit, unquote
import hashlib, json, re, subprocess, sys
ROOT = Path(__file__).resolve().parents[1]
class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.ids=[]; self.images=[]; self.refs=[]; self.media=[]; self.headings=[]; self.heading=None; self.parts=[]; self.paragraphs=[]; self.para=None; self.section_stack=[]; self.section_parents={}; self.section_media={}; self.feed(text)
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag=='section':
            ident=d.get('id')
            self.section_parents[ident]=self.section_stack[-1] if self.section_stack else None
            self.section_media[ident]=[]
            self.section_stack.append(ident)
        if d.get('id'): self.ids.append(d['id'])
        if tag=='img' and d.get('src'):self.images.append(d)
        for attr in ['href','src','poster']:
            if d.get(attr): self.refs.append(d[attr])
        for attr in ['aria-labelledby','aria-describedby']:
            for ident in d.get(attr,'').split(): self.refs.append('#'+ident)
        if tag in ['video','source'] and d.get('src'):
            self.media.append(d['src'])
            for ident in self.section_stack:self.section_media[ident].append(d['src'])
        if re.fullmatch('h[1-6]',tag):self.heading=tag;self.parts=[]
        if tag=='p':self.para=[]
    def handle_data(self,text):
        if self.heading:self.parts.append(text)
        if self.para is not None:self.para.append(text)
    def handle_endtag(self,tag):
        if tag=='section':self.section_stack.pop()
        if tag==self.heading:self.headings.append(''.join(self.parts).strip());self.heading=None
        if tag=='p' and self.para is not None:self.paragraphs.append(''.join(self.para));self.para=None
pages={name:(ROOT/name).read_text() for name in ['index.html','en.html']}
parsed={name:Page(text) for name,text in pages.items()}
confirmed=json.loads((ROOT/'data/confirmed-blog.json').read_text())
report=json.loads((ROOT/'data/report.json').read_text())
robo=json.loads((ROOT/'data/robofail-cases.json').read_text())
visibility=json.loads((ROOT/'data/robofail-visibility.json').read_text())
expected_videos=14+len(robo['cases'])
checks={}
for name,text in pages.items():
    p=parsed[name]
    assert len(p.ids)==len(set(p.ids)),f'{name}: duplicate ids'
    assert all(int(i.get('width',0))>0 and int(i.get('height',0))>0 for i in p.images),f'{name}: missing intrinsic image size'
    assert len(p.media)==expected_videos and len(set(p.media))==expected_videos,(name,p.media)
    assert len([x for x in p.media if 'assets/case-studies/' in x])==10
    assert len([h for h in p.headings if h.startswith('Case Study')])==8 # 7 RBM + combined RoboFail group
    assert not any(re.search(r'\b(?:Q\d{4}|T\d{3}|055|036)\b',h) for h in p.headings)
    for ref in p.refs:
        u=urlsplit(ref)
        if u.scheme or u.netloc:continue
        target=ROOT/unquote(u.path) if u.path else ROOT/name
        assert target.is_file(),(name,ref,'missing file')
        if u.fragment and target.suffix=='.html':
            ids=parsed[target.name].ids if target.name in parsed else Page(target.read_text()).ids
            assert unquote(u.fragment) in ids,(name,ref,'missing anchor')
    lang='zh' if name=='index.html' else 'en'
    for block in confirmed.values():
        originals=re.findall(r'<dd lang="en">(.*?)</dd>',block['zh'],re.S)
        for answer in originals:assert unescape(answer) in unescape(text),(name,answer)
    for case in robo['cases']:
        for answer in [case['ground_truth']]+[r['answer'] for r in case['responses']]:assert answer in unescape(text),(name,answer)
    assert visibility['completed']==visibility['planned']==12
    assert len(visibility['results'])==12
    assert len({(r['case_id'],r['condition'],r['visible_frames']) for r in visibility['results']})==12
    for row in visibility['results']:
        assert row['answer'] in unescape(text),(name,'missing experimental response')
        assert row['returned_model'] in text
    assert len(re.findall(r'class="visibility-label ',text))==12
    assert 'VOC ×100' not in text and 'VOC（未缩放）' not in text and 'VOC (unscaled)' not in text
    assert all(str(n) in text for n in [93.6,94.2,0.8166,0.7953,92.4,64.91,85.96,89.3,90.51,95.36,0.0407,0.1312])
    icl=text.split('<section id="progress-icl"',1)[1].split('</section>',1)[0]
    assert 'RoboFail' not in icl and 'ROBOFAIL' not in icl
    assert icl.count('assets/figures/01_ranking.png')==1 and icl.count('assets/figures/03_progress.png')==1
    progress=text.split('<section id="progress-results"',1)[1].split('</section>',1)[0]
    assert p.section_parents['results'] is None
    for ident in ['quality-results','progress-results','progress-icl','failure','explanations']:
        assert p.section_parents[ident] == 'results',(name,ident,'must be a Results subsection')
        assert re.search(r'<a class="subsection" href="#'+ident+r'">',text),(name,ident,'missing Results subsection TOC link')
    assert len(p.section_media['progress-results'])==3
    assert len(p.section_media['progress-icl'])==1
    assert len(p.section_media['failure'])==len(robo['cases'])
    assert all(x in progress for x in ['93.6','105','Case Study'])
    assert all(x not in progress for x in ['94.2','0.7953','95.36','0.1312','assets/figures/03_progress.png'])
    assert all(x in icl for x in ['94.2','0.7953','95.36','0.1312'])
    assert not any(x in text for x in ['Progress and context','Progress estimation and context examples','进度与上下文','进度估计与上下文示例'])
    quality=text.split('<section id="quality-results"',1)[1].split('<section id="progress-results"',1)[0]
    assert 'assets/figures/01_ranking.png' not in quality and '0.7953' not in quality
    assert quality.count('assets/figures/01_ranking_zero_shot.png') == 1
    assert quality.index('assets/figures/01_ranking_zero_shot.png') < quality.index('id="banana-case"')
    assert all(value in quality for value in ['0.8166', '0.7500', '0.5300', 'DeepSeek-V4.1-Flash'])
    assert text.count('assets/figures/02_preference.png')==1
    merged=[x for x in p.paragraphs if all(n in x for n in ['85.96%','66.1%','0.185','0.499','0.290','89.3%'])]
    assert len(merged)==1 and all(n in merged[0] for n in ['18','2','6']),name
    assert not any(x in text for x in ['AHA 改编', 'AHA adaptation', '[[cite:'])
    for key in ['astra','sol','deepseek','robometer','rbm','reflect','rynnvalue','aha','guardian','primo']:
        assert f'href="#ref-{key}"' in text,(name,key,'missing inline citation')
    assert 'A<sub>pref</sub> = (100 / 6)' in text
    assert text.count('href="assets/Beyond-the-Score.pdf"')==1
    checks[name]={'unique_videos':expected_videos,'paired_input_replays':10,'rbm_cases':7,'robofail_cases':len(robo['cases']),'new_experimental_responses':12,'local_references_checked':len(p.refs),'raw_answers_preserved':True,'merged_robofail_paragraph':True,'five_results_subsections':True}
assert parsed['index.html'].ids==parsed['en.html'].ids
assert parsed['index.html'].media==parsed['en.html'].media
# A rebuild must reproduce both committed-to-disk artifacts exactly.
before={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in pages}
r=subprocess.run([sys.executable,str(ROOT/'scripts/build_blog.py')],cwd=ROOT,capture_output=True,text=True,check=True)
after={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in pages}
assert before==after,'Generated pages are stale'
print(json.dumps({'passed':True,'pages':checks,'bilingual_ids_and_media_match':True,'rebuild_identical':True,'sha256':after},ensure_ascii=False,indent=2))
