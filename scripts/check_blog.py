"""Check reviewed content, bilingual invariants, local links, and reproducible generation."""
from pathlib import Path
from html.parser import HTMLParser
from html import unescape
from urllib.parse import urlsplit, unquote
import hashlib, json, re, subprocess, sys
ROOT = Path(__file__).resolve().parents[1]
class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.visible_text=[]; self.progress_panels=[]; self.ids=[]; self.images=[]; self.refs=[]; self.media=[]; self.headings=[]; self.heading=None; self.parts=[]; self.paragraphs=[]; self.para=None; self.section_stack=[]; self.section_parents={}; self.section_media={}; self.feed(text)
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if 'data-progress-compare' in d: self.progress_panels.append(d)
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
        self.visible_text.append(text)
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
rbm=json.loads((ROOT/'data/rbm-cases.json').read_text())
robo=json.loads((ROOT/'data/robofail-cases.json').read_text())
visibility=json.loads((ROOT/'data/robofail-visibility.json').read_text())
positive=json.loads((ROOT/'data/rbm-positive-cases.json').read_text())
positive_cases=positive['cases']
assert [(c['slug'], c['stage']) for c in positive_cases] == [
    ('ranking-drawer','policy_ranking'), ('ranking-banana','policy_ranking'),
    ('preference-button','quality_preference'), ('preference-red-bin','quality_preference')]
assert positive['completion']['astra']=={'status':'complete','stages':18,'completed_samples':2284}
assert positive['completion']['deepseek']=={'status':'complete','stages':12,'completed_samples':1759}
assert len(positive['sample_manifests'])==12 and all(m['identical'] for m in positive['sample_manifests'])
assert positive['protocol']['labels_sent_to_model'] is False
expected_scores=[([1,0],[0.2,0.3]),([1,0],[0.5,1])]
for c,(astra,deepseek) in zip(positive_cases[:2],expected_scores):
    assert [j['prediction']['model_answer']['score'] for j in c['judgments']['astra']]==astra
    assert [j['prediction']['model_answer']['score'] for j in c['judgments']['deepseek']]==deepseek
assert [[t['quality_label'] for t in c['trajectories']] for c in positive_cases]==[
    ['successful','failure'],['successful','suboptimal'],['suboptimal','successful'],['failure','successful']]
for c in positive_cases:
    for model in ['astra','deepseek']:
        for j in c['judgments'][model]:
            assert json.loads(j['original_final_output'])==j['prediction']['model_answer']
            assert j['request_sha256_reconstructed']==j['prediction']['request_sha256']
            assert j['line']>0 and j['response_file'] in positive['source_files_sha256']
    if c['stage']=='quality_preference':
        assert c['reference_winner']=='B'
        for model,winner,correct in [('astra','B',1),('deepseek','A',0)]:
            r=c['judgments'][model][0]['prediction']
            assert r['model_answer']['winner']==winner and r['preference_pred']==correct
            assert r['display_order']=={t['display']:t['id'] for t in c['trajectories']}
            assert r['metadata']['chosen_metadata']['id']==r['display_order']['B']
    for trajectory in c['trajectories']:
        assert [f['stored_index'] for f in trajectory['input_frames']]==[0,4,9,13,18,22,27,31]
        for frame in trajectory['input_frames']:
            assert hashlib.sha256((ROOT/frame['path']).read_bytes()).hexdigest()==frame['sha256']
        for kind in ['poster','video']:
            assert hashlib.sha256((ROOT/trajectory[kind]).read_bytes()).hexdigest()==trajectory[kind+'_sha256']
        assert (ROOT/trajectory['poster']).read_bytes()==(ROOT/trajectory['input_frames'][-1]['path']).read_bytes()
expected_videos=15+len(robo['cases'])+2*len(positive_cases)
checks={}
for name,text in pages.items():
    p=parsed[name]
    assert not re.search(r'\b(?:Q\d{4}|T\d{3})\b', ' '.join(p.visible_text)), (name, 'internal case ID in reader-visible article text')
    assert len(p.progress_panels) == 4, (name, 'expected four paired progress charts')
    chart_cases = [next(c for c in rbm['cases'] if c['id']==case_id) for case_id in ['Q0041','Q0039','Q0037','T011']]
    for panel, case in zip(p.progress_panels, chart_cases):
        assert list(map(int,panel['data-progress-indices'].split(','))) == case['sampleIndices']
        assert list(map(float,panel['data-progress-values'].split(','))) == case['progress']
        assert int(panel['data-progress-fps']) == case['playbackFps']
        assert int(panel['data-progress-frames']) == case['storedFrameCount']
    assert text.count('data-progress-seek=') == 20
    assert text.count('class="progress-dot is-fixed"') == 4
    assert '[[progress-video:' not in text
    assert len(p.ids)==len(set(p.ids)),f'{name}: duplicate ids'
    assert all(int(i.get('width',0))>0 and int(i.get('height',0))>0 for i in p.images),f'{name}: missing intrinsic image size'
    assert len(p.media)==expected_videos and len(set(p.media))==expected_videos,(name,p.media)
    assert len([x for x in p.media if 'assets/case-studies/' in x])==18
    assert len([h for h in p.headings if h.startswith('Case Study')])==13 # 12 RBM + combined RoboFail group
    assert not re.search(r'\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b',' '.join(p.visible_text))
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
    labels={'zh':{'successful':'成功','suboptimal':'次优','failure':'失败'},'en':{'successful':'success','suboptimal':'suboptimal','failure':'failure'}}
    assert text.count('class="positive-case"')==4
    for case in positive_cases:
        slug=case['slug']
        match=re.search(r'<div class="positive-case" data-positive-case="'+slug+r'">(.*?)<!-- /positive-case -->',text,re.S)
        assert match,(name,slug,'missing positive case')
        block=match.group(1)
        compact=re.sub(r'>\s+<','><',block)
        assert f'id="{slug}-case"' in block
        assert [t['video'] for t in case['trajectories']]==Page(block).media
        for model in ['astra','deepseek']:
            for i,j in enumerate(case['judgments'][model]):
                answer=j['prediction']['model_answer']
                assert answer['reason'] in unescape(block),(name,slug,'missing original reason')
                model_name='Astra' if model=='astra' else 'DeepSeek-V4.1-Flash'
                result=(f'{case["trajectories"][i]["display"]} · {answer["score"]:.2f}' if case['stage']=='policy_ranking' else ('实际选择 ' if lang=='zh' else 'Actual choice ')+answer['winner'])
                assert f'<dt>{model_name} · {result}</dt>' in block
        if case['stage']=='policy_ranking':
            for i,t in enumerate(case['trajectories']):
                scores=[case['judgments'][m][i]['prediction']['model_answer']['score'] for m in ['astra','deepseek']]
                assert f'<tr><th scope="row">{t["display"]} · {labels[lang][t["quality_label"]]}</th><td>{scores[0]:.2f}</td><td>{scores[1]:.2f}</td></tr>' in compact
        else:
            for t in case['trajectories']:
                assert ('参考标签：' if lang=='zh' else 'Reference label: ')+labels[lang][t['quality_label']] in block
        assert ('模型输入的 8 帧回放。' if lang == 'zh' else 'Replay of the eight model-input frames.') in block
    assert all(x in text for x in ['positive-case-protocol','32768','512','0 / 4 / 9 / 13 / 18 / 22 / 27 / 31'])
    assert 'data/rbm-positive-cases.json' not in text
    assert 'positive-case-protocol' not in text.split('<section id="quality-results"', 1)[1].split('<section id="progress-results"', 1)[0]
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
    assert len(p.section_media['progress-results'])==4
    assert all(anchor in p.ids for anchor in ['bluecup-case','banana-retry-case'])
    assert progress.count('assets/rbm/t011-replay.mp4')==1
    for case in rbm['cases']:
        if case['id']=='T011':
            assert case['sampleIndices']==[0,7,15,23,31] and case['progress']==[0,0.15,0,0.15,1]
            for reason in case['reasons'][1:]:assert reason in unescape(progress),(name,'missing retry rationale')
        elif case['id'] in ['Q0041','Q0039','Q0037']:
            assert case['reasons'][-1] in unescape(progress),(name,'missing cup rationale')
    assert len(p.section_media['progress-icl'])==1
    assert len(p.section_media['failure'])==len(robo['cases'])
    assert all(x in progress for x in ['93.6','105','Case Study'])
    assert all(x not in progress for x in ['94.2','0.7953','95.36','0.1312','assets/figures/03_progress.png'])
    assert all(x in icl for x in ['94.2','0.7953','95.36','0.1312'])
    assert not any(x in text for x in ['Progress and context','Progress estimation and context examples','进度与上下文','进度估计与上下文示例'])
    quality=text.split('<section id="quality-results"',1)[1].split('<section id="progress-results"',1)[0]
    assert 'assets/figures/01_ranking.png' not in quality and '0.7953' not in quality
    assert quality.count('assets/figures/01_ranking_zero_shot.png') == 1
    assert quality.index('id="ranking-drawer-case"') < quality.index('id="banana-case"')
    assert quality.index('id="ranking-banana-case"') < quality.index('id="banana-case"')
    assert quality.index('id="preference-button-case"') < quality.index('id="separate-cups-case"')
    assert quality.index('id="preference-red-bin-case"') < quality.index('id="separate-cups-case"')
    assert all(f'data-positive-case="{c["slug"]}"' in quality for c in positive_cases)
    assert len(p.section_media['quality-results'])==18
    assert quality.index('assets/figures/01_ranking_zero_shot.png') < quality.index('id="banana-case"')
    assert all(value in quality for value in ['0.8166', '0.7500', '0.5300', 'DeepSeek-V4.1-Flash'])
    assert text.count('assets/figures/02_preference.png')==1
    failure=text.split('id="failure"', 1)[1].split('id="explanations"', 1)[0]
    assert 'id="outcome-counts"' in failure and 'data-condition=' not in failure
    assert all(value in failure for value in ['64.91%', '85.96%', '66.1%', '19.9'])
    assert text.index('id="conclusions"') < text.index('id="limitations"') < text.index('id="next-steps"')
    assert not any(x in text for x in ['AHA 改编', 'AHA adaptation', '[[cite:'])
    for key in ['astra','sol','deepseek','robometer','rbm','reflect','rynnvalue','aha','guardian','primo']:
        assert f'href="#ref-{key}"' in text,(name,key,'missing inline citation')
    assert 'A<sub>pref</sub> = (100 / 6)' in text
    assert text.count('href="assets/Beyond-the-Score.pdf"')==1
    checks[name]={'unique_videos':expected_videos,'paired_input_replays':18,'rbm_cases':12,'positive_ranking_cases':2,'positive_preference_cases':2,'verified_positive_request_hashes':12,'robofail_cases':len(robo['cases']),'new_experimental_responses':12,'local_references_checked':len(p.refs),'raw_answers_preserved':True,'reader_visible_internal_ids_removed':True,'exact_progress_charts':4,'sample_seek_buttons':20,'parallel_outcome_table':True,'five_results_subsections':True}
assert parsed['index.html'].ids==parsed['en.html'].ids
assert parsed['index.html'].media==parsed['en.html'].media
# A rebuild must reproduce both committed-to-disk artifacts exactly.
before={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in pages}
r=subprocess.run([sys.executable,str(ROOT/'scripts/build_blog.py')],cwd=ROOT,capture_output=True,text=True,check=True)
after={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in pages}
assert before==after,'Generated pages are stale'
print(json.dumps({'passed':True,'pages':checks,'bilingual_ids_and_media_match':True,'rebuild_identical':True,'sha256':after},ensure_ascii=False,indent=2))
