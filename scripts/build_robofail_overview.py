"""Render the RoboFail accuracy comparison from the existing report; no new scores."""
from pathlib import Path
import json, os, shutil, struct, subprocess, tempfile
ROOT = Path(__file__).resolve().parents[1]
rows = json.loads((ROOT / 'data/report.json').read_text())['table5_robofail_aha']['rows']
names = {r[0]: r[0] for r in rows}
names.update({'Astra / zero-shot': 'gpt-6-astra / Zero-shot', 'Astra / 5 examples': 'gpt-6-astra / ICL (5 examples)'})
study = sorted([r for r in rows if r[1]=='study'], key=lambda r:-r[2])
external = sorted([r for r in rows if r[1]!='study'], key=lambda r:-r[2])
s = (ROOT/'assets/figures/source/03_progress.tex').read_text().split('\\fill[cardbg')[0]
s += r'''\fill[cardbg,rounded corners=7pt] (-.4,2) rectangle (18.15,-10.85);
\node[anchor=west,font=\sffamily\bfseries\Large] at (0,1.42) {RoboFail | Subtask success and failure};
\node[anchor=west,font=\sffamily\small,text=black!65] at (0,.82) {Outcome classification | Accuracy (\%) $\uparrow$};
\node[anchor=west,font=\sffamily\bfseries\small] at (0,.1) {General-purpose multimodal models | This study};
'''
def bar(row,y,group):
    color=('iclbar' if '5 examples' in row[0] else 'astrabar') if group=='study' else 'mutedbar'
    return '\n'.join([
        rf'\node[anchor=west,font=\sffamily\small] at (0,{y:.2f}) {{{names[row[0]]}}};',
        rf'\fill[trackbg] (7.25,{y-.19:.2f}) rectangle (16.8,{y+.19:.2f});',
        rf'\fill[{color}] (7.25,{y-.19:.2f}) rectangle ({7.25+9.55*row[2]/100:.6f},{y+.19:.2f});',
        rf'\node[anchor=east,font=\sffamily\bfseries] at (17.7,{y:.2f}) {{{row[2]:.2f}}};',
    ])+'\n'
for i,row in enumerate(study): s+=bar(row,-.55-.72*i,'study')
for v in [0,25,50,75,100]:
    s+=rf'\node[text=black!60,font=\scriptsize] at ({7.25+9.55*v/100},-1.85) {{{v}}};'+'\n'
s+=r'''\draw[black!20] (0,-2.25) -- (17.7,-2.25);
\node[anchor=west,font=\sffamily\bfseries\small] at (0,-2.7) {Published references | AHA report | Sorted within this group};
'''
for i,row in enumerate(external): s+=bar(row,-3.35-.64*i,'external')
for v in [0,25,50,75,100]:
    s+=rf'\node[text=black!60,font=\scriptsize] at ({7.25+9.55*v/100},-9.15) {{{v}}};'+'\n'
s+=r'''\node[anchor=west,text=black!65,font=\small] at (0,-9.8) {Study: 57 questions (23 successes, 34 failures). Five external demonstrations for ICL.};
\node[anchor=west,text=black!65,font=\small] at (0,-10.3) {Published values: AHA, Tables 3/4. Exact question sets have not been matched.};
\end{tikzpicture}
\end{document}
'''
source=ROOT/'assets/figures/source/04_robofail_icl.tex'; source.write_text(s)
png=ROOT/'assets/figures/04_robofail_icl.png'
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
