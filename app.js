'use strict';
const $ = (s, root = document) => root.querySelector(s);
const $$ = (s, root = document) => [...root.querySelectorAll(s)];
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let report, cases, failureCases, visibility, selectedCase, selectedObservation = 0;

function pressed(selector, value, key) {
  $$(selector).forEach(button => button.setAttribute('aria-pressed', String(button.dataset[key] === String(value))));
}

const metricInfo = {
  voc: {column:2, title:'Progress VOC ×100', max:100, ticks:['0','25','50','75','100'],
    description:'Correlation with a time reference across 105 successful trajectories. This is not the percentage of correctly judged stages.',
    callout:'93.6 → 94.2 with ICL', note:'Progress ICL supplies one same- or similar-task training trajectory. Small aggregate gains can conceal worse endpoint estimates.', format:v=>v.toFixed(1)},
  rank: {column:3, title:'Independent ranking · Kendall τ-a', max:1, ticks:['0','0.25','0.50','0.75','1.00'],
    description:'Each trajectory is scored separately. Ordering is assessed across 567 trajectories in 41 source–task groups; predicted ties lose credit.',
    callout:'+0.0666 over Sol', note:'Within-study zero-shot point estimates. Ranking ICL uses three training references and lowers τ-a to 0.7953.', format:v=>v.toFixed(4)},
  pref: {column:4, title:'Direct pairwise preference · accuracy (%)', max:100, ticks:['0','25','50','75','100'],
    description:'Both trajectories are visible in one request. Accuracy is reported over 1,192 fixed pairs; pair composition is incompletely documented.',
    callout:'92.4% correct choices', note:'A different interface from independent scoring. No ICL preference result is reported. External preference sets are not matched.', format:v=>v.toFixed(1)+'%'}
};
function renderMetric(key) {
  const metric = metricInfo[key];
  pressed('[data-metric]', key, 'metric');
  $('#metric-title').textContent = metric.title;
  $('#metric-description').textContent = metric.description;
  $('#metric-callout').textContent = metric.callout;
  $('#metric-note').textContent = metric.note;
  const names=['GPT-6 Astra · zero-shot','GPT-6 Astra · ICL','GPT-5.6 Sol · low','DeepSeek V4.1 Flash · max'];
  $('#metric-bars').innerHTML = report.table2_rbm.rows.slice(0,4).map((row,i) => row[metric.column] === null ? '' : `<div class="bar-row ${i===0?'primary':i===1?'icl':''}"><span class="bar-name">${names[i]}</span><div class="bar-track" aria-hidden="true"><div class="bar-fill" style="width:${row[metric.column]/metric.max*100}%"></div></div><span class="bar-number">${metric.format(row[metric.column])}</span></div>`).join('');
  $('#metric-axis').innerHTML = metric.ticks.map(t=>`<span>${t}</span>`).join('');
}

function table(headers,rows) {
  return `<table><thead><tr>${headers.map(h=>`<th scope="col">${escapeHTML(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr class="${row.study?'study':''}">${row.values.map((cell,i)=>`<${i===0?'th scope="row"':'td'}${i>0?' class="num"':''}>${escapeHTML(cell === null?'—':cell)}</${i===0?'th':'td'}>`).join('')}</tr>`).join('')}</tbody></table>`;
}
function renderTables() {
  $('#rbm-table').innerHTML=table(['Configuration','VOC ×100 ↑','τ-a ↑','Preference % ↑'],report.table2_rbm.rows.map(r=>({study:r[1]==='study',values:[r[0],r[2]?.toFixed(1)??null,r[3]?.toFixed(4)??null,r[4]?.toFixed(1)??null]})));
  $('#robofail-table').innerHTML=table(['Configuration','Label accuracy % ↑','Composite ROUGE-L ↑'],report.table5_robofail_aha.rows.map(r=>({study:r[1]==='study',values:[r[0],r[2].toFixed(2),r[3].toFixed(3)]})));
  const adaptations=report.table6_other_adaptations;
  $('#guardian-table').innerHTML=table(['Guardian adaptation','Exec. %','Plan. %'],adaptations.guardian.rows.map(r=>({values:r})));
  $('#primo-table').innerHTML=table(['PRIMO adaptation','Accuracy %'],adaptations.primo.rows.map(r=>({values:r})));
}

function renderProgressChart(observation) {
  const c = selectedCase, x=i=>42+c.sampleIndices[i]/31*426, y=v=>170-v*130;
  const line=values=>values.map((v,i)=>`${i?'L':'M'}${x(i)},${y(v)}`).join(' ');
  const grid=[0,.5,1].map(v=>`<line class="chart-grid" x1="42" x2="468" y1="${y(v)}" y2="${y(v)}"/><text class="chart-text" x="28" y="${y(v)+4}" text-anchor="end">${v.toFixed(1)}</text>`).join('');
  const second=c.conditions?.[1];
  $('#progress-chart').innerHTML=`<svg viewBox="0 0 500 220" role="img" aria-label="Saved progress estimates for ${escapeHTML(c.task)}. Zero-shot: ${c.progress.join(', ')}${second?'. ICL: '+second.progress.join(', '):''}"><text class="chart-text" x="42" y="18">Estimated progress</text>${grid}${c.timeReference?`<path class="chart-ref" d="${line(c.timeReference)}"/>`:''}<path class="chart-line" d="${line(c.progress)}"/>${second?`<path d="${line(second.progress)}" fill="none" stroke="#b8491c" stroke-width="2.5"/>`:''}<line x1="${x(observation)}" x2="${x(observation)}" y1="35" y2="177" stroke="#087c76" stroke-dasharray="2 4" opacity=".5"/>${c.progress.map((v,i)=>`<circle cx="${x(i)}" cy="${y(v)}" r="${i===observation?6:3.5}" fill="#087c76" stroke="#f8f7f3" stroke-width="2"/>`).join('')}${c.sampleIndices.map((v,i)=>`<text class="chart-text" x="${x(i)}" y="192" text-anchor="middle">${v}</text>`).join('')}<text class="chart-text" x="250" y="214" text-anchor="middle">Stored frame index (not elapsed seconds)</text></svg>${second?'<div class="rouge-key"><span><i class="swatch" style="background:#087c76"></i>Zero-shot</span><span><i class="swatch" style="background:#b8491c"></i>ICL</span><span>Dashed: time reference</span></div>':''}`;
}
function selectObservation(index, seek=false) {
  selectedObservation=index;
  pressed('[data-observation]',index,'observation');
  const c=selectedCase;
  $('#reason-label').textContent=index===0?'INITIAL REFERENCE · FIXED AT ZERO':`MODEL OUTPUT · FRAME ${c.sampleIndices[index]}`;
  $('#progress-value').textContent=c.progress[index].toFixed(2);
  $('#progress-reason').textContent=c.reasons[index];
  if(c.conditions) {
    const quote=document.createElement('span');quote.style.display='block';quote.style.marginTop='10px';quote.textContent=`ICL (${c.conditions[1].progress[index].toFixed(2)}): ${c.conditions[1].reasons[index]}`;
    $('#progress-reason').append(quote);
  }
  renderProgressChart(index);
  if(seek) { const v=$('#trajectory-video');v.pause();v.currentTime=c.sampleIndices[index]/c.playbackFps; }
}
function selectCase(id) {
  selectedCase=cases.find(c=>c.id===id); const c=selectedCase;
  pressed('[data-case]',id,'case');
  const v=$('#trajectory-video');v.pause();v.src=c.video;v.poster=c.poster;v.load();
  $('#case-robot').textContent=`${c.source} · ${c.id}`;
  $('#case-quality').textContent=`REFERENCE: ${c.quality}`;
  $('#case-title').textContent=c.title;
  $('#case-task').textContent=c.task;
  $('#case-summary').textContent=c.summary;
  $('#case-provenance').textContent=`${c.relationToReport}. Requested ${c.modelRequested}, reasoning effort low. Five observed-prefix positions; initial zero is defined, not predicted. Lines connect saved estimates for readability, not continuous predictions. Public quality is a trajectory label; no human failure intervals are available.`;
  $('#checkpoints').innerHTML=c.sampleIndices.map((f,i)=>`<button data-observation="${i}" aria-pressed="${i===0}">Frame ${f}</button>`).join('');
  $$('#checkpoints button').forEach(b=>b.addEventListener('click',()=>selectObservation(Number(b.dataset.observation),true)));
  selectObservation(0);
}

function renderDiagnosis(condition) {
  pressed('[data-condition]',condition,'condition');
  const d=report.table7_robofail_errors,i=Number(condition);
  $('#confusion').innerHTML=`<div class="confusion-matrix"><span></span><span class="matrix-head">Predicted<br>success</span><span class="matrix-head">Predicted<br>failure</span><span class="matrix-row">Reference<br>success</span><div class="matrix-cell correct"><strong>${d.correct_success[i]}</strong><span>Correct success</span></div><div class="matrix-cell error"><strong>${d.false_alarms[i]}</strong><span>False alarms</span></div><span class="matrix-row">Reference<br>failure</span><div class="matrix-cell error"><strong>${d.misses[i]}</strong><span>Missed failures</span></div><div class="matrix-cell correct"><strong>${d.correct_failure[i]}</strong><span>Correct failure</span></div></div>`;
  const stats=[['Label accuracy',d.accuracy_pct[i].toFixed(2)+'%',`${d.correct_total[i]} / 57 correct answers`,'teal'],['Failure recall',d.failure_recall_pct[i].toFixed(2)+'%',`${d.correct_failure[i]} / 34 failures detected`,'teal'],['Missed failures',String(d.misses[i]),`${d.miss_rate_pct[i].toFixed(2)}% of reference failures`,'orange'],['False alarms',String(d.false_alarms[i]),`${d.false_alarm_rate_pct[i].toFixed(2)}% of reference successes`,'orange']];
  $('#diagnosis-stats').innerHTML=stats.map(s=>`<div class="diagnosis-stat"><span>${s[0]}</span><strong class="${s[3]}">${s[1]}</strong><small>${s[2]}</small></div>`).join('');
}
function renderRouge(){
  const r=report.rouge_decomposition;
  $('#rouge-chart').innerHTML=['Zero-shot','External 5-shot'].map((label,i)=>`<div class="rouge-row"><div><strong>${label}</strong><span>${report.table7_robofail_errors.composite_rouge_l[i].toFixed(3)}</span></div><div class="rouge-track" role="img" aria-label="${label}: correct-success component ${r.success_terms[i]}, failure-explanation component ${r.failure_explanation_terms[i]}"><span style="width:${r.success_terms[i]/.55*100}%">${r.success_terms[i].toFixed(4)}</span><span style="width:${r.failure_explanation_terms[i]/.55*100}%">${r.failure_explanation_terms[i].toFixed(4)}</span></div></div>`).join('')+'<div class="rouge-key"><span><i class="swatch" style="background:#087c76"></i>Correct success</span><span><i class="swatch" style="background:#9cae87"></i>Failure explanation</span></div><p class="caption">Both bars share a 0–0.55 scale. Components are rounded independently. Report Figure 7.</p>';
}

function selectFailure(id) {
  const c=failureCases.find(c=>c.id===Number(id));
  pressed('[data-failure]',id,'failure');
  const video=$('#failure-video');video.pause();video.src=c.video;video.poster=c.poster;video.load();
  $('#failure-task').textContent=c.task;$('#failure-id').textContent=`CASE ${c.id}`;
  $('#failure-keyframes').innerHTML=c.keyframes.map(f=>`<button data-seek="${f.matched_source_time_seconds}" aria-label="Seek input frame ${f.index}, ${f.matched_source_time_seconds.toFixed(1)} seconds"><img loading="lazy" src="${f.image}" alt="Input observation ${f.index}"><span>Frame ${f.index} · ${f.matched_source_time_seconds.toFixed(1)}s</span></button>`).join('');
  $$('[data-seek]').forEach(b=>b.addEventListener('click',()=>{video.pause();video.currentTime=Number(b.dataset.seek);}));
  $('#failure-answers').innerHTML=`<article class="answer-card reference"><div><span class="eyebrow">RELEASED REFERENCE</span><span class="tag">${escapeHTML(c.reference_label)}</span></div><p>${escapeHTML(c.ground_truth)}</p></article>`+c.responses.map(r=>{const failure=r.answer.trim().toLowerCase().startsWith('no');const correct=failure===(c.reference_label==='Failure');return `<article class="answer-card"><div><span class="eyebrow">ASTRA LOW · ${escapeHTML(r.condition)}</span><span class="answer-status ${correct?'match':''}">${correct?'Label matches':failure?'False alarm':'Missed failure'}</span></div><p>“${escapeHTML(r.answer)}”</p></article>`;}).join('')+`<p class="answer-note">${escapeHTML(c.interpretation||'Compare the quoted diagnoses with the released reference and the visible observations.')}</p>`;
  $('#failure-question').textContent=c.question.replace(/^<image>\s*/, '');
  $('#failure-input').src=c.original_input_image;$('#input-link').href=c.original_input_image;
}

function renderFailureGallery() {
  $('#failure-gallery').innerHTML=failureCases.map(c=>{
    const outcomes=c.responses.map(r=>{
      const failure=r.answer.trim().toLowerCase().startsWith('no');
      return failure===(c.reference_label==='Failure')?'Label matches':failure?'False alarm':'Missed failure';
    });
    return `<button class="failure-tile" data-failure="${c.id}" aria-pressed="false"><img src="${c.poster}" loading="lazy" alt="${escapeHTML(c.task)}"><span class="failure-tile-body"><span class="eyebrow">CASE ${c.id} · REFERENCE ${escapeHTML(c.reference_label)}</span><strong>${escapeHTML(c.task)}</strong><span class="tile-outcome">Zero-shot: ${outcomes[0]}<br>5-shot: ${outcomes[1]}</span></span></button>`;
  }).join('');
  $('#gallery-count').textContent=`${failureCases.length} cases · source videos, input observations, and saved answers`;
}

function selectVisibility(id, count) {
  const c=failureCases.find(c=>c.id===id);
  const rows=visibility.results.filter(r=>r.case_id===id);
  const levels=[...new Set(rows.map(r=>r.visible_frames))];
  const selected=rows.filter(r=>r.visible_frames===count);
  pressed('[data-visibility-case]',id,'visibilityCase');
  $('#visibility-task').textContent=c.task;
  $('#visibility-levels').innerHTML=levels.map(n=>{
    const responses=rows.filter(r=>r.visible_frames===n);
    return `<button data-visibility-level="${n}" aria-pressed="${n===count}"><strong>${n===rows[0].total_frames?'All '+n:n} frame${n===1?'':'s'}</strong><span>${responses.map(r=>`${r.condition==='zero'?'Zero-shot':'5-shot'}: ${r.label==='yes'?'Success':r.label==='no'?'Failure':'Unparsed'}`).join('<br>')}</span></button>`;
  }).join('');
  $$('[data-visibility-level]').forEach(b=>b.addEventListener('click',()=>selectVisibility(id,Number(b.dataset.visibilityLevel))));
  $('#visibility-input').src=selected[0].image;
  $('#visibility-input-link').href=selected[0].image;
  $('#visibility-evidence').textContent=`${count} of ${rows[0].total_frames} observed frames retained. ${count===rows[0].total_frames?'Full-visibility control, queried again in this experiment.':'Later observed tiles are withheld in white; the original question remains unchanged.'}`;
  $('#visibility-answers').innerHTML=selected.map(r=>`<article class="answer-card"><div><span class="eyebrow">${r.condition==='zero'?'ZERO-SHOT':'EXTERNAL 5-SHOT'} · FRESH RESPONSE</span><span class="tag">${r.label==='yes'?'Success':r.label==='no'?'Failure':'Unparsed'}</span></div><p>“${escapeHTML(r.answer)}”</p><small>Returned label: ${escapeHTML(r.returned_model)}</small></article>`).join('');
}

function renderVisibility() {
  if(!visibility||visibility.completed!==visibility.planned) return;
  $('#visibility-experiment').hidden=false;
  const ids=[...new Set(visibility.results.map(r=>r.case_id))];
  $('#visibility-cases').innerHTML=ids.map(id=>`<button data-visibility-case="${id}" aria-pressed="false">${escapeHTML(failureCases.find(c=>c.id===id).task)}</button>`).join('');
  $$('[data-visibility-case]').forEach(b=>b.addEventListener('click',()=>selectVisibility(Number(b.dataset.visibilityCase),1)));
  $('#visibility-summary').textContent=`${visibility.completed} fresh responses · 2 cases × 3 visibility levels × 2 prompting conditions · ${visibility.protocol.date}`;
  selectVisibility(ids[0],1);
}

async function initialize(){
  const data=window.REPORT_DATA;
  if(!Array.isArray(data)||data.length<3)throw new Error('Report data is unavailable');
  [report]=data;cases=data[1].cases;failureCases=data[2].cases;visibility=data[3];
  renderMetric('voc');renderTables();selectCase('Q0041');renderDiagnosis(0);renderRouge();renderFailureGallery();selectFailure(55);renderVisibility();
  $$('[data-metric]').forEach(b=>b.addEventListener('click',()=>renderMetric(b.dataset.metric)));
  $$('[data-case]').forEach(b=>b.addEventListener('click',()=>selectCase(b.dataset.case)));
  $$('[data-condition]').forEach(b=>b.addEventListener('click',()=>renderDiagnosis(Number(b.dataset.condition))));
  $$('[data-failure]').forEach(b=>b.addEventListener('click',()=>selectFailure(Number(b.dataset.failure))));
  $('#show-bottle').addEventListener('click',()=>{selectCase('T098');$('#trajectories').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'instant':'smooth'});});
  $('#trajectory-video').addEventListener('timeupdate',()=>{if(!selectedCase)return;const frame=Math.min(31,Math.floor($('#trajectory-video').currentTime*selectedCase.playbackFps+.001));let index=0;selectedCase.sampleIndices.forEach((f,i)=>{if(f<=frame)index=i;});if(index!==selectedObservation)selectObservation(index);});
  // Only one content video plays at once; a case switch always starts paused.
  $$('video').forEach(v=>v.addEventListener('play',()=>{$$('video').filter(other=>other!==v).forEach(other=>other.pause());}));
  document.documentElement.dataset.ready='true';
}
$('#copy-citation').addEventListener('click',async()=>{
  const citation=$('#citation').textContent;
  try {await navigator.clipboard.writeText(citation);$('#copy-status').textContent='Copied';}
  catch {const selection=window.getSelection();const range=document.createRange();range.selectNodeContents($('#citation'));selection.removeAllRanges();selection.addRange(range);$('#copy-status').textContent='Citation selected — copy with Ctrl/Cmd+C';}
});
initialize().catch(error=>{console.error(error);const notice=document.createElement('p');notice.className='load-error';notice.setAttribute('role','alert');notice.textContent='Interactive data could not load. Please reload this page, or read the complete results in the PDF below.';$('#results .wrap').prepend(notice);});
