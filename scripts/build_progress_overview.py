"""Render the zero-shot VOC overview from the existing report; no new scores."""
from pathlib import Path
import json, os, shutil, struct, subprocess, tempfile
ROOT = Path(__file__).resolve().parents[1]
rows = json.loads((ROOT / 'data/report.json').read_text())['table2_rbm']['rows']
names = {
    'GPT-6 Astra low (zero-shot)': 'GPT-6 Astra',
    'GPT-5.6-sol low': 'GPT-5.6-sol',
    'DpskV4.1-flash max': 'DeepSeek-V4.1-Flash',
    'Robometer / RBM-1M (paper v1)': 'Robometer / RBM-1M [P]',
    'Robometer / RBM-1M (web)': 'Robometer / RBM-1M [W]',
    'Robometer / RoboReward data': 'Robometer / RoboReward data [P]',
    'RoboReward-4B': 'RoboReward-4B [P]',
    'RoboReward-8B': 'RoboReward-8B [P]',
    'RoboDopamine-8B (web)': 'RoboDopamine-8B [W]',
    'TOPReward / Qwen3-VL-8B': 'TOPReward / Qwen3-VL-8B [W]',
    'GVL / GPT-5-mini': 'GVL / GPT-5-mini [P]',
    'VLAC-8B': 'VLAC-8B [P]',
    'ReWiND / RBM-1M': 'ReWiND / RBM-1M [P]',
}
study = sorted([r for r in rows if r[1]=='study' and 'ICL' not in r[0] and r[2] is not None], key=lambda r:-r[2])
external = sorted([r for r in rows if r[1]!='study' and r[2] is not None], key=lambda r:-r[2])
s = (ROOT/'assets/figures/source/03_progress.tex').read_text().split('\\fill[cardbg')[0]
s += r'''\fill[cardbg,rounded corners=7pt] (-.4,2) rectangle (18.15,-12.15);
\node[anchor=west,font=\sffamily\bfseries\Large] at (0,1.42) {RBM | Zero-shot task progress estimation};
\node[anchor=west,font=\sffamily\small,text=black!65] at (0,.82) {Correlation with normalized time | VOC $\uparrow$ (Pearson $r$ $\times$ 100)};
\node[anchor=west,font=\sffamily\bfseries\small] at (0,.1) {General-purpose multimodal models | This study};
'''
def bar(row,y,group):
    color='astrabar' if row[0].startswith('GPT-6 Astra') else 'studybar' if group=='study' else 'mutedbar'
    return '\n'.join([
        rf'\node[anchor=west,font=\sffamily\small] at (0,{y:.2f}) {{{names[row[0]]}}};',
        rf'\fill[trackbg] (7.25,{y-.19:.2f}) rectangle (16.8,{y+.19:.2f});',
        rf'\fill[{color}] (7.25,{y-.19:.2f}) rectangle ({7.25+9.55*row[2]/100:.6f},{y+.19:.2f});',
        rf'\node[anchor=east,font=\sffamily\bfseries] at (17.7,{y:.2f}) {{{row[2]:.1f}}};',
    ])+'\n'
for i,row in enumerate(study): s+=bar(row,-.55-.72*i,'study')
for v in [0,25,50,75,100]:
    s+=rf'\node[text=black!60,font=\scriptsize] at ({7.25+9.55*v/100},-2.55) {{{v}}};'+'\n'
s+=r'''\draw[black!20] (0,-2.95) -- (17.7,-2.95);
\node[anchor=west,font=\sffamily\bfseries\small] at (0,-3.4) {Published references | Sorted within this group};
'''
for i,row in enumerate(external): s+=bar(row,-4.05-.64*i,'external')
for v in [0,25,50,75,100]:
    s+=rf'\node[text=black!60,font=\scriptsize] at ({7.25+9.55*v/100},-10.4) {{{v}}};'+'\n'
s+=r'''\node[anchor=west,text=black!65,font=\small] at (0,-11.05) {Study: 105 successful trajectories. Context-example results are shown in Section 2.3.};
\node[anchor=west,text=black!65,font=\small] at (0,-11.5) {[P] Robometer paper; [W] project website. Literature samples and protocols differ.};
\node[anchor=west,text=black!65,font=\small] at (0,-11.95) {VOC measures temporal correlation, not semantic completion accuracy.};
\end{tikzpicture}
\end{document}
'''
source=ROOT/'assets/figures/source/03_progress_zero_shot.tex'; source.write_text(s)
png=ROOT/'assets/figures/03_progress_zero_shot.png'
tex=os.environ.get('PDFLATEX') or shutil.which('pdflatex')
ppm=os.environ.get('PDFTOPPM') or shutil.which('pdftoppm')
if not tex or not ppm:
    raise SystemExit('Install TeX and Poppler, or set PDFLATEX and PDFTOPPM to their executable paths.')
with tempfile.TemporaryDirectory() as tmp:
    proc=subprocess.run([tex,'-interaction=nonstopmode','-halt-on-error',f'-output-directory={tmp}',str(source)],capture_output=True,text=True)
    if proc.returncode: raise RuntimeError(proc.stdout[-4000:])
    subprocess.run([ppm,'-png','-singlefile','-scale-to-x','1600','-scale-to-y','-1',str(Path(tmp)/(source.stem+'.pdf')),str(png.with_suffix(''))],check=True)
p=ROOT/'data/media-dimensions.json'; d=json.loads(p.read_text()); d[str(png.relative_to(ROOT))]=list(struct.unpack('>II',png.read_bytes()[16:24])); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print(f'Rendered {len(study)} study and {len(external)} literature entries: {png}')
