"""Build the two static articles. Run with Python 3; no dependencies required."""
from pathlib import Path
from html import escape
import json
import re
from robofail_visuals import expanded_cases, visibility_experiment

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'data/report.json').read_text())
PUB = json.loads((ROOT / 'data/publication.json').read_text())
RBM_CASES = json.loads((ROOT / 'data/rbm-cases.json').read_text())['cases']
ROBOFAIL_CASES = json.loads((ROOT / 'data/robofail-cases.json').read_text())['cases']
VISIBILITY_PATH = ROOT / 'data/robofail-visibility.json'
VISIBILITY = json.loads(VISIBILITY_PATH.read_text()) if VISIBILITY_PATH.exists() else None
CONFIRMED = json.loads((ROOT / 'data/confirmed-blog.json').read_text())
IMAGE_SIZES = json.loads((ROOT / 'data/media-dimensions.json').read_text())
LANG = 'zh'
REFERENCE_LABELS = {
    'astra': (1, 'OpenAI: GPT-6 Astra'),
    'robometer': (2, 'Robometer'),
    'rbm': (3, 'RBM-EVAL-OOD'),
    'reflect': (4, 'REFLECT / RoboFail'),
    'rynnvalue': (5, 'RynnValue'),
    'sol': (6, 'OpenAI: GPT-5.6 Sol'),
    'deepseek': (7, 'DeepSeek-V4.1-Flash'),
    'aha': (8, 'AHA'),
    'guardian': (9, 'Guardian'),
    'primo': (10, 'PRIMO'),
    'unexpected': (11, 'An Unexpected Robot Policy'),
    'astranomy': (12, 'Astranomy'),
    'embodied': (13, 'Systematically Exploring GPT-6 Astra as Embodied Policies'),
}

def t(zh, en):
    return zh if LANG == 'zh' else en

def model_label(name):
    return re.sub(r'\s+(?:low|max)\b', '', name).replace('DpskV4.1-flash', 'DeepSeek-V4.1-Flash')


def p(zh, en, cls=''):
    return f'<p class="{cls}">{t(zh, en)}</p>'

def h3(id, zh, en):
    return f'<h3 id="{id}" data-toc>{t(zh, en)}</h3>'

def section(id, zh, en, body, cls='', heading_id=''):
    alias = f' id="{heading_id}"' if heading_id else ''
    return f'<section id="{id}" class="{cls}" data-toc><h2{alias}>{t(zh, en)}</h2>{body}</section>'

def result_section(id, zh, en, body, heading_id=''):
    # Result topics are h3; their internal headings are h4. Keep stable anchors.
    body = re.sub(r'<(/?)h3\b', r'<\1h4', body)
    alias = f' id="{heading_id}"' if heading_id else ''
    return f'<section id="{id}" class="result-topic" data-toc><h3{alias}>{t(zh, en)}</h3>{body}</section>'


def citations(content):
    def link(match):
        key = match.group(1)
        number, title = REFERENCE_LABELS[key]
        return f'<sup class="citation"><a href="#ref-{key}" aria-label="{escape(title)}">[{number}]</a></sup>'
    return re.sub(r'\[\[cite:([a-z-]+)\]\]', link, content)


def source_label(source):
    if source == 'study':
        return t('本研究', 'This study')
    key = ('rbm' if 'website' in source else 'robometer') if source.startswith('Robometer') else ('rynnvalue' if source.startswith('RynnValue') else 'aha')
    return escape(source) + f'[[cite:{key}]]'


def table(headers, rows, caption):
    head = ''.join(f'<th scope="col">{h}</th>' for h in headers)
    body = ''
    for row in rows:
        cells = ''.join(f'<th scope="row">{v}</th>' if i == 0 else f'<td>{v if v is not None else "—"}</td>' for i, v in enumerate(row))
        body += f'<tr>{cells}</tr>'
    return f'<div class="table-scroll" role="region" aria-label="{escape(caption)}" tabindex="0"><table><caption>{caption}</caption><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'

def detail(zh, en, body):
    return f'<details class="research-detail"><summary>{t(zh, en)}</summary>{body}</details>'

def figure(src, alt, caption):
    return f'<figure class="figure"><button type="button" data-zoom aria-label="{t("放大", "Enlarge")}: {escape(alt)}"><img loading="lazy" src="{src}" alt="{escape(alt)}"></button><figcaption>{caption}<span class="zoom-label" aria-hidden="true">{t("放大", "Enlarge")} ↗</span></figcaption></figure>'

def video(id, title):
    return f'<figure><video controls playsinline muted preload="none" poster="assets/rbm/{id}-poster.jpg" src="assets/rbm/{id}-replay.mp4" aria-label="{escape(title)}"></video><figcaption>{title}</figcaption></figure>'

def confirmed(name):
    """Render reviewed bilingual prose and cases; raw model responses are shared verbatim."""
    content = CONFIRMED[name][LANG]
    # Reuse the remote design's scrollable tables on narrow screens.
    content = re.sub(r'(<table class="case-table">.*?</table>)', r'<div class="table-scroll" role="region" tabindex="0">\1</div>', content, flags=re.S)
    return content


def ranking_chart():
    r = DATA['ranking_decomposition']
    labels = [t('正确顺序', 'Correct order'), t('平分', 'Tie'), t('颠倒', 'Inversion')]
    out = '<div class="stack-key">' + ''.join(f'<span><i></i>{x}</span>' for x in labels) + '</div>'
    for i, label in enumerate([t('零样本', 'Zero-shot'), t('三参考轨迹 ICL', 'Three-reference ICL')]):
        values = [r[k][i] for k in ['correct_strict_order_weight_pct', 'tie_weight_pct', 'inversion_weight_pct']]
        desc = ' · '.join(f'{l} {v:.2f}%' for l, v in zip(labels, values))
        bars = ''.join(f'<span style="width:{v}%"></span>' for v in values)
        out += f'<div class="stack-heading"><strong>{label}</strong><span>τa {r["tau_a"][i]:.4f}</span></div><div class="outcome-stack" role="img" aria-label="{desc}">{bars}</div><p class="stack-values">{desc}</p>'
    cap = t('图 4. 与报告得分一致的加权成对结果，非独立轨迹对的未加权计数。τa 等于正确顺序权重减去颠倒权重。', 'Figure 4. Weighted pair outcomes consistent with the reported scores, not unweighted counts of independent pairs. τa equals the correct-order weight minus the inversion weight.')
    return f'<figure class="study-figure">{out}<figcaption>{cap}</figcaption></figure>'

def diagnosis():
    return f'''<figure class="diagnosis"><div class="diagnosis-header"><span>ROBOFAIL · 57 {t('个问题', 'questions')}</span><div class="switch" role="group" aria-label="{t('选择评测条件', 'Evaluation condition')}"><button type="button" data-condition="0" aria-pressed="true">{t('零样本', 'Zero-shot')}</button><button type="button" data-condition="1" aria-pressed="false">{t('五示例 ICL', 'Five-example ICL')}</button></div></div>
    <div class="diagnosis-body" aria-live="polite" aria-atomic="true"><div class="accuracy"><b><span id="accuracy">64.91</span><small>%</small></b><span>{t('整体准确率', 'Overall accuracy')}</span><div class="diag-numbers"><div>{t('失败召回率', 'Failure recall')}<strong id="recall">94.12%</strong></div><div>{t('正确判断', 'Correct answers')}<strong id="correct">37 / 57</strong></div><div>{t('误报', 'False alarms')}<strong id="false-alarms">18</strong></div><div>{t('漏检', 'Misses')}<strong id="misses">2</strong></div></div></div>
    <div class="matrix" role="group" aria-label="{t('混淆矩阵', 'Confusion matrix')}"><span></span><span class="label">{t('预测成功', 'Predicted success')}</span><span class="label">{t('预测失败', 'Predicted failure')}</span><span class="label">{t('实际成功', 'Reference success')}</span><div class="cell"><b data-cell>5</b>{t('正确成功', 'Correct success')}</div><div class="cell error"><b data-cell>18</b>{t('误报', 'False alarm')}</div><span class="label">{t('实际失败', 'Reference failure')}</span><div class="cell error"><b data-cell>2</b>{t('漏检', 'Miss')}</div><div class="cell"><b data-cell>32</b>{t('正确失败', 'Correct failure')}</div></div></div>
    <figcaption>{t('图 5. 同一组 57 个问题上的成败判断。失败为正类；误报指实际成功但预测失败，漏检指实际失败但预测成功。这是离线分类，未测量在线报警时间。', 'Figure 5. Classification on the same 57 questions, treating failure as positive. A false alarm is a reference success predicted as failure; a miss is a reference failure predicted as success. This is offline classification, not a timestamped online alarm.')}</figcaption></figure>'''

def rouge_chart():
    r = DATA['rouge_decomposition']
    out = '<div class="stack-key rouge-key">' + ''.join(f'<span><i></i>{x}</span>' for x in [t('正确成功项', 'Correct-success term'), t('失败解释项', 'Failure-explanation term')]) + '</div>'
    for i, label in enumerate([t('零样本', 'Zero-shot'), t('外部五示例', 'External five-example')]):
        values = [r['success_terms'][i], r['failure_explanation_terms'][i]]
        bars = ''.join(f'<span style="width:{v / .55 * 100}%">{v:.4f}</span>' for v in values)
        desc = f'{label}: {values[0]:.4f} + {values[1]:.4f}'
        out += f'<div class="stack-heading"><strong>{label}</strong><span>{t("综合得分", "Composite score")} {DATA["table7_robofail_errors"]["composite_rouge_l"][i]:.3f}</span></div><div class="rouge-stack" role="img" aria-label="{desc}">{bars}</div>'
    cap = t('图 6. 综合 ROUGE-L 的组成，两项均以 57 为分母。两条形使用相同的 0–0.55 刻度。分项和总分分别取整，末位可能有舍入差异。', 'Figure 6. Components of composite ROUGE-L, both divided by 57. Both bars use a 0–0.55 scale. Components and totals are rounded separately and may differ in the last decimal.')
    return f'<figure class="study-figure">{out}<div class="chart-axis full"><span>0</span><span>0.55</span></div><figcaption>{cap}</figcaption></figure>'

def study_design():
    body = h3('benchmark-choice', '1.1 评价任务与数据集', '1.1 Evaluation tasks and benchmarks')
    body += p('我们从三个方面考察通用多模态模型评价机器人行为的能力：能否比较不同执行的质量，能否根据已观测的执行过程估计任务进度，以及能否判断子任务成败并解释失败。我们使用 RBM[[cite:robometer]][[cite:rbm]] 开展轨迹排序、成对偏好与进度评测，并使用 RoboFail[[cite:reflect]] 考察成败判断与解释。在此基础上，我们进一步研究上下文示例与可见观测如何影响模型的评价。', 'We examine three aspects of general-purpose multimodal models’ ability to evaluate robot behavior: comparing execution quality, estimating task progress from the execution observed so far, and judging subtask outcomes and explaining failures. We use RBM[[cite:robometer]][[cite:rbm]] for trajectory ranking, pairwise preference, and progress evaluation, and RoboFail[[cite:reflect]] for outcome judgment and explanation. We further investigate how in-context examples and visible observations affect these evaluations.')
    def task_cell(zh, en, dataset):
        return t(zh, en) + f'<span class="protocol-dataset">{dataset}</span>'

    def io_cell(zh_input, en_input, zh_output, en_output):
        return '<span class="protocol-io"><b>' + t('输入', 'Input') + '</b>' + t(zh_input, en_input) + '</span><span class="protocol-io"><b>' + t('输出', 'Output') + '</b>' + t(zh_output, en_output) + '</span>'

    protocol_table = table([t('评价任务', 'Evaluation task'), t('输入与输出', 'Inputs and outputs'), t('评测样本', 'Evaluation samples'), t('评价指标', 'Metrics')], [
        [task_cell('轨迹质量排序', 'Trajectory quality ranking', 'RBM-EVAL-OOD'), io_cell('任务描述；每条轨迹采样 8 帧', 'Task description; eight sampled frames per trajectory', '独立评分后，在来源–任务组内排序', 'Independent scores, ranked within each source–task group'), t('567 条轨迹<br>41 个来源–任务组', '567 trajectories<br>41 source–task groups'), 'Kendall τ<sub>a</sub> ↑'],
        [task_cell('直接偏好判断', 'Direct preference judgment', 'RBM'), io_cell('同一任务的两条轨迹；每条采样 8 帧', 'Two trajectories for the same task; eight sampled frames each', '选择较优轨迹', 'Choice of the better trajectory'), t('1,192 组轨迹对', '1,192 trajectory pairs'), t('准确率 ↑<span class="protocol-note">六来源等权</span>', 'Accuracy ↑<span class="protocol-note">Six sources, equally weighted</span>')],
        [task_cell('任务进度估计', 'Task progress estimation', 'RBM-EVAL-OOD'), io_cell('任务描述；截至当前的采样观测；此前评分', 'Task description; observations sampled up to the current time; previous scores', '进度评分（0–1）与简要理由', 'Progress score (0–1) and brief rationale'), t('105 条成功轨迹<br>每条轨迹预测 4 次', '105 successful trajectories<br>Four predictions per trajectory'), t('VOC ↑<br>时间参考 MSE ↓', 'VOC ↑<br>Time-reference MSE ↓')],
        [task_cell('成败判断与解释', 'Outcome judgment and explanation', t('RoboFail', 'RoboFail')), io_cell('子任务问题；关键帧拼图', 'Subtask question; keyframe montage', '成败标签与失败解释', 'Outcome label and failure explanation'), t('57 个问题／15 组轨迹<br>23 个成功／34 个失败', '57 questions / 15 trajectory groups<br>23 successes / 34 failures'), t('准确率 ↑<br>失败召回率 ↑<br>误报率／漏检率 ↓<br>综合 ROUGE-L ↑', 'Accuracy ↑<br>Failure recall ↑<br>False-alarm / miss rate ↓<br>Composite ROUGE-L ↑')],
    ], t('评价任务与实验设置概览。↑／↓ 分别表示指标越高／越低越好。', 'Overview of evaluation tasks and experimental settings. ↑ / ↓ indicate higher / lower is better.'))
    protocol_table = protocol_table.replace('<table>', '<table class="study-protocol-table">', 1).replace('</caption>', '</caption><colgroup><col class="protocol-task"><col class="protocol-interface"><col class="protocol-samples"><col class="protocol-metrics"></colgroup>', 1)
    protocol_details = '<div id="evaluation-questions">' + protocol_table + '</div>'
    protocol_details += p('<strong>RoboFail 协议。</strong>RoboFail 由 REFLECT 提出[[cite:reflect]]。本文采用 AHA 提供的问答评测形式[[cite:aha]]，在本研究记录的 57 个问题上评估；该问题集合不等同于原始数据集的全部内容，也不假定与其他文献的评测子集完全一致。', '<strong>RoboFail protocol.</strong> RoboFail was introduced by REFLECT[[cite:reflect]]. We use the question–answer evaluation format provided by AHA[[cite:aha]] on the 57 questions recorded in this study. This set is not the entire original dataset and is not assumed to match other publications’ evaluation subsets exactly.')

    body += h3('comparison-protocol', '1.2 模型配置与评测条件', '1.2 Model configurations and evaluation conditions')
    body += p('我们以 GPT-6 Astra[[cite:astra]] 为主要研究对象，通过提示提供任务与观测，不进行额外的评价任务微调。RBM 评测另包含 GPT-5.6-sol[[cite:sol]] 和 DeepSeek-V4.1-Flash[[cite:deepseek]] 的零样本比较。', 'Our primary subject is GPT-6 Astra[[cite:astra]], supplied with task descriptions and observations through prompts, without additional evaluation-task fine-tuning. The RBM evaluation also includes zero-shot comparisons with GPT-5.6-sol[[cite:sol]] and DeepSeek-V4.1-Flash[[cite:deepseek]].')
    body += p('我们在进度估计、独立排序与 RoboFail 成败判断中比较零样本和上下文示例条件，并在两个 RoboFail 案例上改变可见观测，考察评价对输入信息的敏感性。不同任务分别评估；文献结果作为背景参照，与本研究实测结果区分呈现。', 'We compare zero-shot and in-context conditions for progress estimation, independent ranking, and RoboFail outcome judgment. We also vary the visible observations in two RoboFail cases to examine sensitivity to input information. Tasks are evaluated separately, and published results are presented as contextual references, distinct from our measurements.')

    protocol_details += p('<strong>模型配置。</strong>我们以 GPT-6 Astra[[cite:astra]] 为主要研究对象，通过提示提供任务与观测，不进行额外的评价任务微调。RBM 的进度、独立排序与直接偏好任务另包含 GPT-5.6-sol 和 DeepSeek-V4.1-Flash 的零样本比较；RoboFail 的本研究结果包含 Astra 的零样本与外部五示例条件。', '<strong>Model configurations.</strong> Our primary subject is GPT-6 Astra[[cite:astra]]. Tasks and observations are supplied through prompts, without additional evaluation-task fine-tuning. RBM progress, independent ranking, and direct preference also include zero-shot comparisons with GPT-5.6-sol and DeepSeek-V4.1-Flash. Our RoboFail results cover Astra under zero-shot and external five-example conditions.')
    protocol_details += p('<strong>上下文示例。</strong>Astra 的示例条件按评价任务分别设置：', '<strong>In-context examples.</strong> Astra receives task-specific context conditions:')
    protocol_details += '<ul>' + ''.join('<li>' + t(zh, en) + '</li>' for zh, en in [
        ('<strong>进度估计：</strong>一条相同或相近任务的训练轨迹，附六个阶段评分。', '<strong>Progress estimation:</strong> one training trajectory of the same or a similar task, with six stage scores.'),
        ('<strong>独立排序：</strong>随机选取高、中、低分训练轨迹各一条，不要求与测试任务相同；中等参考分数不等于测试集的“次优”标签。', '<strong>Independent ranking:</strong> one randomly selected training trajectory at each of three score levels—high, middle, and low—without requiring a task match. The middle reference score is not the test set’s suboptimal label.'),
        ('<strong>RoboFail：</strong>五个固定的外部图像–问题–答案示例，报告为与测试轨迹不重叠。', '<strong>RoboFail:</strong> five fixed external image–question–answer demonstrations, reported disjoint from test trajectories.'),
    ]) + '</ul>'
    protocol_details += p('直接偏好没有 ICL 结果。各条件的上下文长度与计算预算未匹配；RoboFail 虽请求相同模型名与推理配置，返回后端标识仍存在差异，快照一致性尚未确认，因此不能把零样本与五示例的差异全部归因于示例。', 'No ICL result is available for direct preference. Context length and compute budgets are not matched. On RoboFail, returned backend identifiers differ despite the same requested model name and reasoning configuration; snapshot consistency is unconfirmed, so the zero-shot versus five-example difference cannot be attributed entirely to examples.', 'method-note')
    protocol_details += p('<strong>观测遮蔽。</strong>在两个既有 RoboFail 案例上，我们另做三种可见帧条件 × 两种提示条件的探索性实验，共 12 次新请求，每个条件仅一次。保留原问题并遮蔽后续观测；少帧条件没有对应的时间级真值，不计算准确率。这部分独立于原 57 问题评测，用于观察回答对可见信息的敏感性。', '<strong>Observation masking.</strong> On two existing RoboFail cases, we separately explore three visibility levels and two prompting conditions, making 12 new requests with one response per condition. We retain the original question and mask later observations. Partial inputs have no corresponding temporal ground truth and receive no accuracy score. This supplement is separate from the original 57-question evaluation and examines response sensitivity to visible information.')
    protocol_details += p('<strong>比较范围。</strong>本研究直接评估的模型配置与文献结果分别标示。Robometer、RynnValue、AHA 等文献数值未在当前样本与输入上复测，训练、提示和聚合方式也可能不同，因此仅作为背景参照，不能据此作同协议排名。图中 [S] 表示本研究，[P]、[W]、[R]、[A] 分别对应 Robometer 论文、其网站、RynnValue 与 AHA；不同版本与缺失结果均按原记录保留。', '<strong>Comparison scope.</strong> We distinguish directly evaluated configurations from published results. Literature values from Robometer, RynnValue, AHA, and other methods were not rerun on our samples and inputs; training, prompts, and aggregation may also differ. They provide context rather than a matched-protocol ranking. Chart tags [S], [P], [W], [R], and [A] denote this study, the Robometer paper, its website, RynnValue, and AHA, respectively. Versions and missing results are retained as recorded.')

    metrics = ''
    metrics += p('进度评测的起点 0 由协议设定，与四次模型预测共同构成五个评分位置；统计时使用同一时间参考。', 'The progress protocol fixes the initial score at zero. Together with four model predictions, this gives five evaluation positions against the same time reference.', 'fine')
    metrics += p('<strong>独立排序：Kendall τa，越高越好。</strong>在同一来源–任务组内，参考质量顺序为成功 &gt; 次优 &gt; 失败。对纳入评分的轨迹对，预测顺序正确计 +1、颠倒计 −1、预测平分计 0；参考质量相同的对不应被人为指定高低，其纳入方式沿用评分器。组内得分可写成 (C − D) / N，其中 C、D 是正确与颠倒的对数，N 是协议纳入的对数。平分保留在分母中，因此不能通过给所有轨迹相同分数获得较高 τa。跨组汇总需要沿用评分器的纳入规则与权重；本文保留报告聚合值，不把加权分解当成独立轨迹对的原始计数。', '<strong>Independent ranking: Kendall τa, higher is better.</strong> Within a source–task group, the reference quality order is success &gt; suboptimal &gt; failure. For pairs included by the scoring protocol, a correct order contributes +1, an inversion −1, and a predicted tie 0. Reference-quality ties must not be given an invented order; their inclusion follows the scorer. A group score can be written as (C − D) / N, where C and D count concordant and discordant pairs and N is the protocol’s pair count. Ties remain in the denominator, so assigning every trajectory the same score cannot yield a high τa. Aggregation must preserve the scorer’s inclusion rules and weights. We retain reported aggregates rather than interpret weighted decompositions as raw independent-pair counts.')
    metrics += p('<strong>直接偏好：六来源等权准确率，越高越好。</strong>先在每个来源内计算选对较优执行的比例，再对六个来源的准确率取等权平均。记来源 s 的正确选择数为 cₛ、评测对数为 nₛ，六个来源合计 1,192 组固定对；不能将全部正确数直接除以 1,192 代替这一汇总。两条轨迹同时进入模型，与先各自评分再比较的独立排序不同。τa 不是准确率，0.8166 不能直接写成 81.66% 的偏好判断正确。', '<strong>Direct preference: equal-source accuracy, higher is better.</strong> Compute the fraction of correct choices within each source, then average the six source accuracies equally. Let cₛ be correct choices and nₛ the evaluated pairs in source s; the six sources contain 1,192 fixed pairs in total. Pooling all correct choices and dividing by 1,192 is not this aggregation. Both trajectories are visible together, unlike independently scored ranking. τa is not accuracy: 0.8166 does not mean 81.66% of preference choices are correct.')
    metrics += '<div class="formula" role="math">A<sub>pref</sub> = (100 / 6) Σ<sub>s=1</sub><sup>6</sup> (cₛ / nₛ)</div>'
    metrics += p('<strong>进度：VOC 与时间参考 MSE。</strong><a class="inline-link" href="https://robometer.github.io/" target="_blank" rel="noopener">RBM 的 VOC 定义</a>使用 Pearson 相关系数。对一条轨迹，在评估位置 i 记预测为 pᵢ，归一化帧位置对应的时间参考为 tᵢ，先计算二者的相关性；正文按 ×100 展示，越高越好。MSE 则检查预测数值与同一时间参考的距离，越低越好。', '<strong>Progress: VOC and time-reference MSE.</strong> The <a class="inline-link" href="https://robometer.github.io/" target="_blank" rel="noopener">RBM definition of VOC</a> uses Pearson correlation. For one trajectory, let pᵢ be the prediction at evaluation position i and tᵢ the time reference from normalized frame position. Compute their correlation; the article reports it on a ×100 scale, higher being better. MSE measures numerical distance from the same time reference, lower being better.')
    metrics += '<div class="formula" role="math">r = Σᵢ(pᵢ − p̄)(tᵢ − t̄) / √[Σᵢ(pᵢ − p̄)² · Σᵢ(tᵢ − t̄)²]<br>VOC = 100 × r<br>MSE = (1 / m) Σᵢ(pᵢ − tᵢ)²</div>'
    metrics += p('m 是评估位置数。逐轨迹得分的跨来源汇总仍需遵循原评分器权重，不能凭总样本数假定所有轨迹等权。时间参考不是人工标注的语义完成度；高相关性允许分数整体偏低，也可能与错误终点判断并存。预测恒定时 Pearson 相关性未定义，应按评分器约定处理，不能自行记成 0。开瓶案例保存的五个预测与时间参考可直接复算出其报告 VOC 和 MSE。', 'Here m is the number of evaluation positions. Cross-source aggregation of per-trajectory scores still requires the original scorer’s weights; total sample counts do not establish equal trajectory weighting. The time reference is not a human annotation of semantic completion. High correlation can coexist with consistently low scores or a wrong endpoint judgment. Pearson correlation is undefined for a constant prediction and needs the scorer’s convention, not an invented zero. The five stored predictions and time references in the bottle example reproduce its reported VOC and MSE.', 'fine')
    metrics += p('<strong>成败分类：准确率、失败召回率、误报率和漏检率。</strong>以失败为正类：TP 是正确识别的失败，FN 是漏掉的失败，TN 是正确识别的成功，FP 是把成功误判为失败。准确率为 (TP + TN) / 57；失败召回率为 TP / 34；误报率为 FP / 23；漏检率为 FN / 34。四项都以百分比报告。它们评估的是回答，不是机器人实际执行成功率。', '<strong>Outcome classification: accuracy, failure recall, false-alarm rate, and miss rate.</strong> Treat failure as positive: TP is a correctly detected failure, FN a missed failure, TN a correctly recognized success, and FP a success predicted as failure. Accuracy is (TP + TN) / 57; failure recall is TP / 34; false-alarm rate is FP / 23; and miss rate is FN / 34. All four are reported as percentages. They score the answers, not the robot’s execution success rate.')
    metrics += p('<strong>失败解释：AHA 综合 ROUGE-L，越高越好。</strong>标签错误计 0；正确成功计 1；正确失败按原始英文解释与参考答案的词干化 ROUGE-L F1 计分。对后一项，令 L 为两个词元序列的最长公共子序列长度，P = L / 生成词元数，R = L / 参考词元数，F1 = 2PR / (P + R)，无重合时为 0。将 57 个问题的得分求和后除以 57。该综合指标混合了成功识别与失败文本重合度，第 2.5 节会拆开报告，避免把它读成解释准确率。', '<strong>Failure explanations: AHA composite ROUGE-L, higher is better.</strong> A wrong label receives 0, a correct success receives 1, and a correct failure receives stemmed ROUGE-L F1 between the original English explanation and reference. For the latter, let L be the longest common subsequence length of the token sequences: P = L / generated-token count, R = L / reference-token count, and F1 = 2PR / (P + R), with zero for no overlap. Sum scores over 57 questions and divide by 57. The composite mixes success recognition and failure-text overlap. Section 2.5 separates them rather than treating the composite as explanation accuracy.')
    metrics += p('非学习参照可以帮助判断指标本身是否足够。下表只列由定义或当前标签数量推导的参照，不是新增模型实验，也不混入实测排行。现有材料没有人工评审员、手写视觉规则或传感器阈值方法在同一输入上的独立实测结果，因此不能声称已经超过这些方法。公开质量标签和成败标注在这里是评分参照，不是一次人工评审员对照实验。', 'Non-learning references help test what a metric establishes. The following values are deductions from definitions or the current label counts, not new model experiments, and are not mixed into measured rankings. The available material contains no matched evaluation of human judges, hand-written visual rules, or sensor-threshold methods, so we cannot claim superiority over them. Released quality and outcome labels are scoring references, not results from a human-judge comparator experiment.')
    metrics += table([t('非学习参照', 'Non-learning reference'),t('可推导的结果', 'Deducible result'),t('它说明什么', 'Interpretation')],[
        [t('所有轨迹给同分', 'Give every trajectory the same score'),'τa = 0',t('不提供质量区分；预测平分没有正贡献。', 'No quality discrimination; predicted ties add no positive contribution.')],
        [t('二选一均匀随机猜测', 'Uniform random binary choice'),t('期望准确率 50%', 'Expected accuracy 50%'),t('仅适用于两个选项中恰有一个正确答案的设定；不是一次实测。', 'Applies only when exactly one of two choices is correct; not a measured run.')],
        [t('RoboFail 一律回答失败', 'Always predict failure on RoboFail'),'34 / 57 = 59.65%',t('失败召回率 100%，误报率 100%；显示只看召回率的局限。', 'Failure recall 100%, false-alarm rate 100%; recall alone is insufficient.')],
        [t('直接输出时间参考', 'Output the time reference itself'),'VOC = 100; MSE = 0',t('非恒定参考下的理论值；使用了评分目标，不证明视觉理解或任务完成判断。', 'Theoretical values for a nonconstant reference; using the scoring target does not establish visual or completion understanding.')],
    ],t('非学习参照：解析推导，未作为实验运行。', 'Non-learning references: analytical deductions, not experimental runs.'))
    body += detail('完整评测协议、指标定义与解析参照', 'Full evaluation protocol, metric definitions, and analytical references', protocol_details + metrics).replace('<details class="research-detail">', '<details id="metrics" class="research-detail">', 1)
    return section('setup', '1. 研究设置', '1. Study design', body)

def article():
    takeaways = [
        t('<strong>Astra 能区分不同质量的机器人执行。</strong>零样本排序 τa 为 0.8166，直接偏好准确率为 92.4%；在本研究的三个通用模型配置中，这两项结果的点估计最高。', '<strong>Astra distinguishes execution quality without task-specific fine-tuning.</strong> Zero-shot ranking τa is 0.8166 and direct preference accuracy is 92.4%, the highest point estimates among the three general-purpose configurations tested here.'),
        t('<strong>上下文示例对不同判断的影响并不一致。</strong>进度 VOC 从 93.6 升至 94.2，排序 τa 却从 0.8166 降至 0.7953。开瓶案例中，更高的进度相关性还伴随更差的终点估计。', '<strong>Context examples have mixed effects.</strong> Progress VOC rises from 93.6 to 94.2, while ranking τa falls from 0.8166 to 0.7953. In a bottle-opening example, higher progress correlation also accompanies a worse endpoint estimate.'),
        t('<strong>RoboFail 准确率提高，但失败召回率下降。</strong>五示例条件的准确率为 85.96%，零样本为 64.91%；误报由 18 个降至 2 个，漏检由 2 个增至 6 个。后端版本一致性未确认，不能将差异完全归因于示例。', '<strong>Higher RoboFail accuracy comes with lower failure recall.</strong> Accuracy is 85.96% with five examples versus 64.91% zero-shot. False alarms fall from 18 to 2, but misses rise from 2 to 6. Backend consistency is unconfirmed, so the difference cannot be attributed solely to examples.'),
        t('<strong>综合解释分数的增量主要来自成功判断。</strong>ROUGE-L 从 0.185 升至 0.499，其中约 89.3% 的增量来自正确成功项；这一变化不等于失败原因解释的同等改善。', '<strong>Most of the composite explanation-score gain comes from success recognition.</strong> ROUGE-L rises from 0.185 to 0.499; about 89.3% of the gain comes from the correct-success term, rather than the failure-explanation term.'),
    ]
    out = section('takeaways', 'Key takeaways · 主要发现', 'Key takeaways', '<ul>' + ''.join(f'<li>{x}</li>' for x in takeaways) + '</ul>', 'key-takeaways')

    body = p('机器人系统需要评价自身的行为：判断任务推进了多少、比较不同执行的质量，以及识别和解释失败。通用多模态模型能够联合处理视觉观测与任务描述，并通过上下文接收评价要求和示例，为这些判断提供了一种无需额外任务微调的途径。我们研究：<strong>通用多模态模型已有的视觉理解与推理能力，能在多大程度上支持对机器人行为的评价？这些能力如何随评价任务、观测信息与上下文示例而变化？</strong>', 'Robot systems need to evaluate their own behavior: assess how far a task has progressed, compare the quality of different executions, and identify and explain failures. General-purpose multimodal models can jointly process visual observations and task descriptions, while receiving evaluation criteria and examples through context, offering a way to make these judgments without additional task-specific fine-tuning. We ask: <strong>To what extent can the existing visual understanding and reasoning capabilities of general-purpose multimodal models support the evaluation of robot behavior? How do these capabilities vary across evaluation tasks, available observations, and in-context examples?</strong>')
    body += p('本文以 GPT-6 Astra[[cite:astra]] 为主要研究对象，在 RBM[[cite:robometer]][[cite:rbm]] 和 RoboFail[[cite:reflect]] 上开展实证评估。我们考察轨迹质量评分、直接偏好判断、任务进度估计，以及子任务成败判断与解释，分别衡量模型比较执行、追踪任务推进和识别失败的能力。我们进一步比较零样本与上下文示例条件下的表现，并通过观测遮蔽的探索性案例，考察可见信息变化时模型回答的变化。', "We conduct an empirical study with GPT-6 Astra[[cite:astra]] as our primary subject on RBM[[cite:robometer]][[cite:rbm]] and RoboFail[[cite:reflect]]. We examine trajectory quality scoring, direct preference judgments, task progress estimation, and subtask success and failure judgments with explanations, assessing the model's ability to compare executions, track task progression, and recognize failures. We further compare zero-shot performance with conditions that provide in-context examples, and use exploratory observation-masking cases to examine how responses change with the available visual information.")
    body += p('结果显示，<strong>执行质量比较是 Astra 在本研究中表现突出的能力，但这种能力没有转化为同样可靠的完成判断和失败诊断。</strong>零样本排序 Kendall τ<sub>a</sub> 达到 <strong>0.8166</strong>，高于专用模型 Robometer 的已报告数值 0.655[[cite:robometer]] 和 RynnValue-8B 的 0.675[[cite:rynnvalue]]；直接偏好准确率为 <strong>92.4%</strong>。这一跨研究数值比较尚未对齐全部样本与输入协议。进度 VOC 为 93.6，低于 Robometer 报告的 94.8；加入示例后，排序 τ<sub>a</sub> 反而降至 0.7953，开瓶案例的进度相关性提高却伴随更差的终点估计。在 RoboFail 上，零样本与五示例条件的准确率分别为 <strong>64.91% 和 85.96%</strong>，失败漏检却由 <strong>2 个增至 6 个</strong>；综合解释得分增量的 <strong>89.3%</strong> 来自正确成功项。因此，当前证据支持将 Astra 用于离线执行质量比较，但<strong>它仍会误判任务是否完成、漏掉真实失败；更高的解释总分也不足以证明失败原因诊断可靠</strong>。本文尚未验证这些评价能否带来策略学习或闭环执行的提升。', 'Our results identify <strong>execution-quality comparison as a strength of Astra in this study, but this ability does not translate into equally reliable completion judgments or failure diagnosis.</strong> Zero-shot ranking reaches Kendall τ<sub>a</sub> = <strong>0.8166</strong>, numerically above the published values of 0.655 for the specialized Robometer model[[cite:robometer]] and 0.675 for RynnValue-8B[[cite:rynnvalue]]; direct preference accuracy is <strong>92.4%</strong>. This cross-study numerical comparison does not align all samples and input protocols. Progress VOC is 93.6, below Robometer’s reported 94.8. With examples, ranking τ<sub>a</sub> instead falls to 0.7953, while a bottle-opening case shows higher progress correlation alongside worse endpoint estimation. On RoboFail, zero-shot and five-example accuracy is <strong>64.91% and 85.96%</strong>, respectively, yet missed failures increase from <strong>2 to 6</strong>; <strong>89.3%</strong> of the composite explanation-score gain comes from correct success judgments. The evidence therefore supports Astra for offline execution-quality comparison, but <strong>it still misjudges completion and misses real failures, and higher composite explanation scores do not establish reliable diagnosis of failure causes</strong>. Whether these assessments improve policy learning or closed-loop execution remains untested.')
    out += section('overview', 'Introduction', 'Introduction', body)

    out += study_design()
    result_topics = ''


    body = p('为了检验 Astra 能否判断机器人执行得好不好、任务完成了多少，我们使用 RBM 的机器人轨迹进行评估。RBM-EVAL-OOD 包含来自六个数据来源的真实机器人轨迹，覆盖成功、次优和失败等执行情况。我们在其中测试了单条轨迹评分和执行过程中的进度估计，另用 1,192 组固定 RBM 轨迹对测试直接偏好判断。', 'We use RBM robot trajectories to test whether Astra can judge execution quality and task progress. RBM-EVAL-OOD includes real robot trajectories from six sources with successful, suboptimal, and failed executions. We evaluate independent trajectory scores and progress on this support, and direct preference on a further 1,192 fixed RBM pairs.')
    body += p('以下先呈现零样本结果与案例。文献数值沿用各自评测协议，用作背景，不能据此作同协议排名；上下文示例的对照集中在第 2.3 节。', 'We first present zero-shot results and cases. Published values retain their own evaluation protocols and provide context, rather than a matched-protocol ranking. Context-example comparisons are grouped in Section 2.3.', 'fine')
    body += h3('ranking-results', '2.1.1 轨迹质量排序', '2.1.1 Trajectory quality ranking')
    body += confirmed('ranking')
    body += h3('preference-results', '2.1.2 直接偏好判断', '2.1.2 Direct preference')
    body += confirmed('preference')
    body += h3('literature', '2.1.3 与已有工作的比较', '2.1.3 Comparison with prior work')
    body += p('RynnValue-8B[[cite:rynnvalue]] 报告排序 τa 为 0.675；Robometer 论文版[[cite:robometer]]报告 τa 为 0.655、偏好准确率为 82.5%、进度 VOC 为 94.8。Astra 的排序与偏好数值较高，但进度 VOC 低于这一 Robometer 记录。', 'RynnValue-8B[[cite:rynnvalue]] reports ranking τa of 0.675. The Robometer paper[[cite:robometer]] reports τa of 0.655, preference accuracy of 82.5%, and progress VOC of 94.8. Astra’s ranking and preference values are numerically higher, while its progress VOC is lower than this Robometer record.')
    body += p('这些文献值没有在本研究的样本上复测。RynnValue 描述了 976 条 OOD 轨迹，而这里评分的是 567 条；外部偏好评测在每个 OOD 来源使用 500 组不同质量轨迹对，本研究则使用组成未完全记录的 1,192 组固定对。样本、输入与聚合方式未对齐，不能据此得出统一协议下的领先结论。', 'These literature values were not rerun on our samples. RynnValue describes a 976-trajectory OOD suite, whereas this study scores 567 trajectories. External preference evaluation uses 500 different-quality pairs per OOD source; our study uses 1,192 fixed pairs with incompletely documented composition. Sample, input, and aggregation differences prevent a matched-protocol superiority claim.')
    body += p('在本研究的三个零样本通用模型配置中，Astra 的三项指标点估计均最高。相对 GPT-5.6-sol，排序 τa 高 0.0666，偏好准确率高 1.7 个百分点，进度 VOC 高 0.1。数值差距最明显的是独立质量排序。当前没有重复调用方差或置信区间，因此这些差异不作统计显著性解释。', 'Astra has the highest point estimate on all three metrics among the three zero-shot general-purpose configurations tested here. Relative to GPT-5.6-sol, the gaps are 0.0666 in ranking τa, 1.7 percentage points in preference accuracy, and 0.1 in progress VOC. The clearest numerical separation is in independent ranking. Repeat-call variance and confidence intervals are unavailable, so these differences are descriptive rather than significance claims.')
    result_topics += result_section('quality-results', '2.1 轨迹质量与偏好', '2.1 Trajectory quality and preference', re.sub(r'<(/?)h4\b', r'<\1h5', body))

    # Preserve prior fragment URLs within the consolidated Results section.
    result_topics += result_section('progress-results', '2.2 任务进度估计', '2.2 Task progress estimation', confirmed('progress'), heading_id='context')

    body = confirmed('icl')
    more = p('逐轨迹变化并不一致：105 条轨迹中，58 条的 VOC 提高、35 条下降、12 条不变；58 条 VOC 提高的轨迹中，有 11 条的 MSE 变差。总体时间参考 MSE 从 0.0402 降至 0.0390。在报告的香蕉转移任务中，19 条轨迹有 18 条下降、1 条不变。这些是聚合统计，不能用单个案例代替。', 'Changes differ across trajectories: of 105, VOC improves on 58, declines on 35, and is unchanged on 12. Of the 58 improvements, 11 have worse MSE. Aggregate time-reference MSE falls from 0.0402 to 0.0390. In the reported banana-transfer task, 18 of 19 trajectories decline and one is unchanged. These aggregate counts cannot be replaced by an individual case.')
    more += p('排序的 41 个来源–任务组中，8 组提高、10 组下降、23 组不变。下面按与报告得分一致的成对权重拆解正确顺序、平分与颠倒，不将其当作独立轨迹对的原始计数。它说明得分如何变化，尚不能确定示例影响判断的具体机制。', 'Among 41 source–task ranking groups, eight improve, ten decline, and 23 remain unchanged. The breakdown below uses pair weights consistent with the reported score, rather than raw counts of independent pairs. It explains how the score changes without identifying the mechanism by which examples affect judgment.')
    more += ranking_chart()
    body += detail('逐轨迹变化与排序分解', 'Trajectory-level changes and ranking decomposition', more)
    rows = [[escape(model_label(r[0])), source_label(r[1]), f'{r[2]:.1f}' if r[2] is not None else None, f'{r[3]:.4f}' if r[3] is not None else None, f'{r[4]:.1f}' if r[4] is not None else None] for r in DATA['table2_rbm']['rows']]
    more = table([t('配置', 'Configuration'), t('来源', 'Source'), 'VOC ↑', 'τa ↑', t('偏好 % ↑', 'Preference % ↑')], rows, t('完整 RBM 结果：保留不同来源、版本及示例条件。', 'Full RBM results, retaining sources, versions, and context conditions.'))
    more += p('Robometer 论文版[[cite:robometer]]与网站版[[cite:rbm]]分别报告 VOC 94.8 / 94.0、τa 0.655 / 0.643，分别保留，不合并。名称中的 RBM-1M 和 RoboReward data 指训练数据。空项表示没有核实的数值；ICL 不作为额外模型，也不与零样本结果择优拼接。各文献数值未在本研究的样本和协议上复测。', 'The Robometer paper[[cite:robometer]] and website[[cite:rbm]] report VOC of 94.8 / 94.0 and τa of 0.655 / 0.643, respectively; both versions are retained. RBM-1M and RoboReward data refer to training data. Missing values are not imputed. ICL is neither an additional model nor selectively combined with zero-shot results. Literature values were not rerun on this study’s samples and protocol.')
    body += detail('完整结果数值与来源', 'Complete result values and sources', more)
    result_topics += result_section('progress-icl', '2.3 上下文示例的影响（ICL）', '2.3 Effects of in-context examples (ICL)', body, heading_id='progress-icl-title')

    body = confirmed('robofail_results')
    body += p('上述文献数值未在本研究的 57 个问题上复测，精确问题集合未对齐；它们作为背景单独列示。', 'The literature values above were not rerun on our 57 questions, and exact question sets are unaligned; they are listed separately as context.', 'fine')
    body += figure('assets/figures/04_robofail_icl.png', t('包含 AHA 及其他 baseline 的成败分类对比', 'Outcome classification including AHA and other baselines'), t('本研究与 AHA 文献成败分类完整图。保留 AHA-7B/13B、GPT-4o、LLaVA、Qwen-VL 与 Gemini 记录；本研究和文献用分隔线区分，精确问题集合尚未对齐。', 'Full study and AHA-literature classification chart, retaining AHA-7B/13B, GPT-4o, LLaVA, Qwen-VL, and Gemini records. Study and literature blocks are separated; exact question sets remain unaligned.'))
    body += diagnosis()
    body += p('一个不读取图像的参照是所有问题都回答“失败”：根据当前标签数量，它会答对 34 / 57，准确率为 59.65%。零样本比这一参照高 5.26 个百分点，但以漏掉 2 个失败换来了识别 5 个成功。这个由标签分布算出的对照说明，准确率需要与两类错误一起读，不能只看“检测到了多少失败”。', 'An image-free reference always answers “failure.” From the current label counts, it gets 34 / 57 correct, or 59.65%. Zero-shot is 5.26 percentage points higher, recognizing five successes while missing two failures. This label-count deduction shows why accuracy must be read alongside both error types, rather than failure detection alone.')
    body += p('成功样本的误报率从 78.26% 降到 8.70%，失败样本的漏检率则从 5.88% 升到 17.65%。五示例条件更善于认可成功，但更容易漏掉失败。实际应用中如何取舍，需要考虑误报干预和失败漏检的成本；本研究没有测量这些成本。', 'The false-alarm rate on successful subtasks falls from 78.26% to 8.70%, while the miss rate on failures rises from 5.88% to 17.65%. The five-example condition recognizes success more often, but also misses more failures. The practical choice depends on the costs of unnecessary intervention and missed failures, which are not measured here.')
    body += p('这一比较仍有两项限制。五个示例报告为与测试轨迹不重叠，但不保证环境、机器人形态、近重复样本或预训练数据独立。另外，两种条件请求相同模型名和推理配置，返回模型标识却存在差异，后端快照一致性尚未确认。因此，观察到的差值不能作为 ICL 的独立因果效应。', 'Two limitations apply. The five demonstrations are reported as disjoint from test trajectories, which does not establish environment, embodiment, near-duplicate, or pretraining independence. Also, returned model identifiers differ despite the same requested model name and reasoning configuration. Backend snapshot consistency is unconfirmed, so the observed difference does not isolate a causal effect of ICL.', 'method-note')
    more = table([t('配置', 'Configuration'), t('来源', 'Source'), t('准确率 % ↑', 'Accuracy % ↑'), 'ROUGE-L ↑'], [[escape(model_label(r[0])), source_label(r[1]), f'{r[2]:.2f}', f'{r[3]:.3f}'] for r in DATA['table5_robofail_aha']['rows']], t('本研究与 AHA 文献记录；精确问题集合对齐未验证。', 'This study and published AHA records; exact question alignment is unverified.'))
    more += p('外部结果未在本研究的 57 个问题上重跑或独立重评分。AHA-13B 的 Vicuna 与 Llama-2 版本单独保留。文献中的零分按原记录呈现，不解释为模型本身完全没有相关能力。', 'External results were not rerun or independently rescored on our 57 questions. The Vicuna and Llama-2 variants of AHA-13B remain separate. Published zero scores are retained without interpreting them as intrinsic inability.')
    more += p('Guardian[[cite:guardian]] 使用 153 个执行样本与 30 个规划样本；PRIMO[[cite:primo]] 使用 Cosmos 筛选的 100 个样本。它们与本研究的评测范围不同，且没有 Astra 在这两套数据上的结果。下列文献记录分别列示，不与本研究的 85.96% 合并排名。', 'Guardian[[cite:guardian]] uses 153 execution and 30 planning examples; PRIMO[[cite:primo]] uses 100 Cosmos-curated examples. These supports differ from ours, and no Astra result is available on either. The literature records below remain separate from our 85.96% result.')
    more += table([t('配置', 'Configuration'), t('执行准确率 %', 'Execution accuracy %'), t('规划准确率 %', 'Planning accuracy %')], DATA['table6_other_adaptations']['guardian']['rows'], t('Guardian v4，Tables 1/2。+GF 表示使用 GuardianFail-36k 训练。', 'Guardian v4, Tables 1/2. +GF denotes training on GuardianFail-36k.'))
    more += table([t('配置', 'Configuration'), t('准确率 %', 'Accuracy %')], DATA['table6_other_adaptations']['primo']['rows'], 'PRIMO, Table 3 / Appendix A.3.')
    body += detail('完整结果与不同 RoboFail 评测版本', 'Full results and distinct RoboFail adaptations', more)
    body += confirmed('robofail_bridge')
    body += confirmed('robofail_cases')
    slicing = next(c for c in ROBOFAIL_CASES if c['id'] == 36)
    raw = '<blockquote><strong>' + t('参考答案', 'Reference answer') + '</strong><p lang="en">' + escape(slicing['ground_truth']) + '</p></blockquote>'
    raw += ''.join('<blockquote><strong>' + t('零样本', 'Zero-shot') + '</strong><p lang="en">' + escape(r['answer']) + '</p></blockquote>' if i == 0 else '<blockquote><strong>' + t('五示例', 'Five-example') + '</strong><p lang="en">' + escape(r['answer']) + '</p></blockquote>' for i, r in enumerate(slicing['responses']))
    body += detail('切片案例的参考与模型原文', 'Slicing reference and original responses', raw)
    body += p('这两例在评测后选取，用于检查标签与理由的分歧，不用于估计错误频率。模型文字并不能证明参考标签有误，也不独立验证其声称的物理原因。', 'These post-hoc examples examine disagreements in labels and reasons, not error frequencies. Model text neither establishes that a reference label is wrong nor independently verifies a stated physical cause.', 'fine')
    body += expanded_cases(ROBOFAIL_CASES, t)
    body += visibility_experiment(VISIBILITY, ROBOFAIL_CASES, t)
    result_topics += result_section('failure', '2.4 子任务成败判断', '2.4 Subtask success and failure', re.sub(r'<(/?)h4\b', r'<\1h5', body))

    body = p('五示例条件的综合 ROUGE-L 从 0.185 增加到 0.499。这个指标不只衡量失败解释。按 AHA 评测规则[[cite:aha]]，正确成功回答计 1 分，正确失败回答按解释与参考答案的词干化 ROUGE-L F1 计分，成败标签错误则计 0 分。所有问题得分相加后除以 57。评分使用原始英文回答，不使用本文的中文转述。', 'Composite ROUGE-L rises from 0.185 to 0.499 in the five-example condition. This metric does not measure failure explanations alone. Under the AHA rules[[cite:aha]], a correct success answer receives 1; a correct failure receives stemmed ROUGE-L F1 against the reference explanation; and a label disagreement receives 0. Scores are summed and divided by 57. Evaluation uses the original English answers, not the Chinese paraphrases in this article.')
    body += f'<div class="formula" role="math" aria-label="{t("综合得分等于正确成功数加上正确失败的解释分数总和，再除以57", "Composite score equals correct successes plus summed explanation scores for correctly detected failures, divided by 57")}">R = ({t("正确成功数 + 正确失败的解释分数之和", "correct successes + summed explanation scores for correct failures")}) / 57</div>'
    body += figure('assets/figures/05_robofail_icl.png', t('包含 AHA 及其他 baseline 的综合 ROUGE-L 对比', 'Composite ROUGE-L including AHA and other baselines'), t('综合 ROUGE-L 完整图。保留原有文献 baseline；分数同时包含成功识别与失败解释项，不能读作解释正确率。', 'Full composite ROUGE-L chart retaining the original literature baselines. The score includes both success recognition and failure explanations; it is not explanation accuracy.'))
    body += rouge_chart()
    body += p('正确成功项从 0.0877 增至 0.3684，增量约为 16 / 57 = 0.2807，占报告总增量 0.3144 的约 89.3%。失败解释项从 0.0969 增至 0.1305，占剩余约 10.7%。因此，0.499 不能读作“49.9% 的失败解释正确”；大部分增量来自识别成功，而非失败解释项。', 'The correct-success term rises from 0.0877 to 0.3684. Its increase, 16 / 57 ≈ 0.2807, accounts for about 89.3% of the reported total gain of 0.3144. The failure-explanation term rises from 0.0969 to 0.1305, accounting for the remaining 10.7%. A score of 0.499 therefore does not mean that 49.9% of failure explanations are correct. Most of the gain comes from recognizing success.')
    body += p('解释项还取决于哪些失败被检测到，以及回答与参考文本的词汇重合度。它无法独立区分语义正确的改写和措辞相似但原因错误的回答。要评价失败原因是否可信，需要额外的语义核验与物理证据。', 'The explanation term also depends on which failures are detected and on lexical overlap with reference text. It does not independently distinguish a correct paraphrase from a similarly worded but incorrect diagnosis. Assessing the stated cause requires additional semantic review and physical evidence.')
    body += p('前面的<a class="inline-link" href="#robofail-cases">抓旋钮与切片案例</a>具体展示了标签与解释需要分别检验。词汇重合度和总体分数的变化，都不能替代对单次判断所引证据的核查。', 'The earlier <a class="inline-link" href="#robofail-cases">knob and slicing cases</a> show why labels and explanations need separate review. Neither lexical overlap nor aggregate score changes replace checking the evidence cited for an individual judgment.')
    result_topics += result_section('explanations', '2.5 失败解释与得分', '2.5 Failure explanations and scores', body)
    out += section('results', '2. 结果', '2. Results', result_topics)

    body = p('这些结果支持将 Astra 用作机器人行为离线评估的研究对象：它能在当前样本上区分执行质量，跟踪进度变化，并识别不少失败。与此同时，示例对各项指标的影响不同。进度评估需要同时检查终点判断，排序需要检查平分，成败分类需要分别报告误报与漏检，解释则需要超出词汇重合度的验证。', 'These results support further study of Astra for offline robot assessment: it distinguishes execution quality, tracks progress, and detects many failures in the evaluated samples. The effects of examples nevertheless differ across metrics. Progress evaluation should include endpoint judgments; ranking should include ties; classification should report false alarms and misses separately; and explanations need validation beyond lexical overlap.')
    body += h3('limitations', '3.1 研究局限', '3.1 Limitations')
    body += p('<strong>评测范围。</strong>实验没有用评审反馈训练或控制策略，没有测量强化学习样本效率、在线失败定位、恢复行为或闭环成功率。离线得分尚不能证明可靠的接触状态推理、因果失败诊断或奖励模型部署安全性。', '<strong>Scope.</strong> No policy is trained or controlled using the critic. We do not measure reinforcement-learning sample efficiency, online failure localization, recovery, or closed-loop success. Offline scores do not establish reliable contact-state reasoning, causal diagnosis, or reward-model deployment safety.')
    body += p('<strong>强化学习适用性尚未验证。</strong>当前实验没有将 Astra 输出作为奖励开展强化学习，也没有检验偏好反馈能否训练出更有效的奖励模型。离线轨迹上的相关性或排序结果，不能保证在策略更新、分布变化和主动寻找高奖励行为时仍然有效。这是后续闭环实验必须回答的问题。', '<strong>Suitability for reinforcement learning remains untested.</strong> We have not trained a policy with Astra rewards or tested whether its preferences produce a more effective learned reward model. Correlation and ranking on fixed offline trajectories do not establish reliability during policy updates, distribution shifts, or active reward seeking. This is a central question for the planned closed-loop experiments.')
    body += p('<strong>统计与实验控制。</strong>57 个 RoboFail 问题来自 15 组轨迹，排序对也可能共享轨迹与任务。当前记录没有量化重复调用波动或抽样不确定性，小幅差异不能解释为已确定的提升。RoboFail 后端差异和示例选择影响仍需单独控制。', '<strong>Statistics and experimental control.</strong> The 57 RoboFail questions share 15 trajectory groups, and ranking pairs may share trajectories and tasks. Repeat-call variation and sampling uncertainty are not quantified, so small differences are not established improvements. RoboFail backend differences and example-selection effects also require separate control.')
    body += p('<strong>标签与案例。</strong>定性案例在评测后选取，不用于判断主要错误类型的频率。标签歧义、观测不足和模型错误都可能影响结果；缺少独立盲评时，不能凭模型解释判定参考标签错误。本文保留原有公开标签。', '<strong>Labels and cases.</strong> Qualitative cases were selected post hoc and do not estimate the prevalence of failure types. Label ambiguity, limited visual evidence, and model error can all affect outcomes. Without independent blind review, model rationales do not establish that a reference label is wrong. We retain the released labels.')
    more = p('现有材料包含评估规模、示例构造、聚合结果和部分案例。完整独立复现仍需补齐六个来源与样本清单、偏好划分组成、输入帧身份和分辨率、完整提示词与示例身份、请求及返回模型版本、运行日期、输出预算与采样设置，以及解析、拒答、重试和缺失输出规则。', 'The available materials provide evaluation counts, demonstration constructions, aggregates, and selected cases. Full independent reproduction still requires source and sample manifests, preference split composition, input-frame identities and resolution, complete prompts and demonstration identities, requested and returned model versions, run dates, output budgets and sampling settings, and parsing, refusal, retry, and missing-output rules.')
    more += p('还需要评分器版本、聚合权重、并列分数约定与逐样本预测，以便审计得分，并在保留轨迹或来源–任务依赖的条件下估计不确定性。补齐材料不会自动消除后端或示例选择的混杂影响，材料缺失本身也不证明底层实验无效。', 'Scorer versions, aggregation weights, tie conventions, and per-sample predictions are also needed for score audits and uncertainty estimates that preserve trajectory or source–task dependence. Completing the release would not itself resolve backend or example-selection confounds; missing materials are also not evidence that the underlying experiments are invalid.')
    body += detail('复现材料的范围', 'Reproducibility status', more)
    body += h3('next-steps', '3.2 后续验证：用 critic 反馈开展强化学习', '3.2 Next: reinforcement learning with critic feedback')
    body += p('我们计划把 Astra 的评审输出接入强化学习，检验“能评价已有轨迹”是否能转化为“能帮助策略学得更好”。首先核对模型快照、提示、输入与示例选取规则，在重复调用和独立标注中检查稳定性；随后固定策略初始化、训练算法和环境交互预算，比较不同反馈来源。', 'We plan to use Astra’s assessments in reinforcement learning to test whether evaluating existing trajectories translates into better policy learning. We will first verify model snapshots, prompts, inputs, and demonstration selection, checking stability through repeated calls and independent annotation. We will then fix policy initialization, the training algorithm, and the environment interaction budget while comparing feedback sources.')
    body += p('<strong>奖励与偏好两条路径。</strong>一条路径把经验证的进度或成功判断转为策略优化的奖励信号；另一条路径使用轨迹偏好监督奖励模型，再用于策略学习。我们会分别比较这些信号，检查是否需要校准，避免把同一指标上的高分直接等同于更有效的奖励。文本失败解释是否能指导恢复或数据选择，也需要独立消融，而不能由 ROUGE-L 推断。', '<strong>Reward and preference pathways.</strong> One path converts validated progress or success judgments into rewards for policy optimization. Another uses trajectory preferences to supervise a reward model for policy learning. We will compare the signals separately and test calibration rather than assume that a high offline score makes an effective reward. Whether failure explanations help recovery or data selection requires separate ablations, not an inference from ROUGE-L.')
    body += p('<strong>对照与评价。</strong>在可用的任务上，加入稀疏环境奖励、手写规则或传感器成功判定，以及可复现的学习型 critic 作为对照；同时比较是否使用上下文示例和不同反馈接口。报告成功率随环境交互步数的学习曲线、达到给定成功率的样本需求、多随机种子的不确定性，以及模型调用量、时延和费用。最终成功必须由独立于 Astra 的环境标准或人工复核判定，避免让评审员同时充当奖励来源和唯一裁判。', '<strong>Controls and evaluation.</strong> Where available, controls will include sparse environment rewards, hand-written rules or sensor-based success checks, and reproducible learned critics. We will also compare context conditions and feedback interfaces. Evaluation will report success-versus-interaction learning curves, samples needed to reach a given success level, uncertainty across random seeds, and query count, latency, and cost. Final success must be determined by environment criteria or human review independent of Astra, rather than making it both the reward source and sole evaluator.')
    body += p('<strong>闭环中的错误。</strong>强化学习会改变策略访问的状态分布，也可能学会利用评审漏洞。因此还要检查新策略是否通过无效动作、伪完成状态或冗长行为取得高奖励，并追踪误报与漏检如何影响学习和恢复。上述强化学习实验尚未完成，本文目前不报告策略提升或样本效率收益。', '<strong>Errors in the loop.</strong> Reinforcement learning changes the states a policy visits and may exploit critic errors. We will check whether ineffective actions, apparent completion, or unnecessarily long behavior earn high rewards, and track how false alarms and misses affect learning and recovery. These reinforcement-learning experiments have not been completed; this article does not report policy gains or sample-efficiency improvements.')

    out += section('outlook', '3. 讨论与局限', '3. Discussion and limitations', body)
    out += resources()
    return out

def resources():
    links = [
        ('data/report.json', t('完整结果与指标定义', 'Result tables and metric definitions'), True),
        ('assets/Beyond-the-Score.pdf', t('技术报告', 'Technical report'), False),
        ('assets/Beyond-the-Score-blog.md', t('原始博客稿', 'Original blog manuscript'), True),
        ('evidence.html', t('交互证据与逐步预测', 'Interactive evidence and per-step predictions'), False),
        ('data/rbm-cases.json', t('轨迹案例数据', 'Trajectory case data'), True),
        ('data/robofail-cases.json', t('RoboFail 案例数据', 'RoboFail case data'), True),
    ]
    body = '<ul class="resource-links">' + ''.join(f'<li><a href="{url}" {"download" if download else ""}>{label} {"↓" if download else "↗"}</a></li>' for url, label, download in links) + '</ul>'
    refs = [
        ('astra', 'https://developers.openai.com/api/docs/models/gpt-6-astra', 'OpenAI. GPT-6 Astra', t('官方模型文档；用于模型身份引用。', 'Official model documentation; model identity reference.')),
        ('robometer', 'https://arxiv.org/abs/2603.02115v1', 'Robometer: Scaling General-Purpose Robotic Reward Models via Trajectory Comparisons', '2026. v1, Tables XIII, XVI, XVII.'),
        ('rbm', 'https://robometer.github.io/', 'RBM-EVAL-OOD / Robometer', t('评测数据入口与网站详细 OOD 表；网站值与论文值分别记录。', 'Evaluation-data release and detailed website OOD tables; website and paper values are recorded separately.')),
        ('reflect', 'https://arxiv.org/abs/2306.15724', 'Liu, Bahety, and Song. REFLECT: Summarizing Robot Experiences for Failure Explanation and Correction', t('CoRL 2023. RoboFail 原始来源。', 'CoRL 2023. Original source of RoboFail.')),
        ('rynnvalue', 'https://arxiv.org/abs/2608.09853v1', 'RynnValue: Scaling Robotic Value Foundation Models with Temporal Distance', '2026. Table 2, §4.2.'),
        ('sol', 'https://developers.openai.com/api/docs/models/gpt-5.6-sol', 'OpenAI. GPT-5.6 Sol', t('官方模型文档；用于模型身份引用。', 'Official model documentation; model identity reference.')),
        ('deepseek', 'https://www.deepseek.com/en/news/deepseek-v4-1-flash/', 'DeepSeek. Introducing DeepSeek-V4.1-Flash', t('2026 年 9 月 10 日官方发布。', 'Official release, September 10, 2026.')),
        ('aha', 'https://aha-vlm.github.io/', 'AHA: A Vision-Language-Model for Detecting and Reasoning over Failures in Robotic Manipulation', t('ICLR 2025. Tables 3/4；', 'ICLR 2025. Tables 3/4; ') + '<a href="https://github.com/NVlabs/AHA" target="_blank" rel="noopener">' + t('评测代码', 'Evaluation code') + '</a>; ' + t('评分实现记录版本：', 'recorded scoring-code revision: ') + '<code>0d39c0591566ddaf997be5822f3dead8e08501aa</code>.'),
        ('guardian', 'https://arxiv.org/html/2512.01946v4', 'Guardian', 'v4, Tables 1/2.'),
        ('primo', 'https://arxiv.org/html/2603.15600', 'PRIMO', 'Table 3, Appendix A.3.'),
        ('unexpected', 'https://arxiv.org/abs/2609.24170', 'An Unexpected Robot Policy', t('GPT-6 Astra 的 RoboDojo action-policy 评估。', 'RoboDojo evaluation of GPT-6 Astra as an action policy.')),
        ('astranomy', 'https://research.nvidia.com/labs/srl/projects/astranomy/', 'Astranomy', t('GPT-6 Astra 作为原生机器人策略的实证研究。', 'Empirical study of GPT-6 Astra as a native robot policy.')),
        ('embodied', 'https://arxiv.org/abs/2609.38537', 'Systematically Exploring the Capabilities of GPT-6 Astra as Embodied Policies', t('直接控制、策略协作和反馈适应的跨领域评估。', 'Cross-domain evaluation of direct control, policy cooperation, and feedback adaptation.')),
    ]
    body += '<ol class="references">' + ''.join(f'<li id="ref-{key}"><a href="{url}" target="_blank" rel="noopener">{name}</a>. {note}</li>' for key, url, name, note in refs) + '</ol>'
    body += p('完整 RBM 表还列出 GVL、VLAC、RoboReward、ReWiND、RL-VLM-F、TOPReward 与 Robo-Dopamine。其数值来自表内注明的 Robometer 论文或网站记录，不表示这些方法的原论文均评估了 RBM。', 'The full RBM table also includes GVL, VLAC, RoboReward, ReWiND, RL-VLM-F, TOPReward, and Robo-Dopamine. Their numbers come from the identified Robometer paper or website records; this does not imply that each method’s original paper evaluated RBM.', 'fine')
    body += detail('其他方法文献', 'Additional method references', '<ul class="references">' + ''.join(f'<li><a href="{url}" target="_blank" rel="noopener">{name}</a></li>' for url, name in [
        ('https://arxiv.org/abs/2509.15937','VLAC'), ('https://arxiv.org/abs/2601.00675','RoboReward'), ('https://arxiv.org/abs/2505.10911','ReWiND'), ('https://arxiv.org/abs/2402.03681','RL-VLM-F'), ('https://arxiv.org/abs/2602.19313','TOPReward'), ('https://arxiv.org/abs/2512.23703','Robo-Dopamine')]) + '<li>GVL: Vision Language Models Are In-Context Value Learners. ICLR, 2025.</li></ul>')
    body += p('实验与文献数值沿用已核验的 2026 年 9 月 23 日记录，结合 10 月 14 日中文稿和已有案例整理。网页更新不增加新的聚合实验结果，文献值不代表实时榜单。背景补充了截至 2026 年 10 月 15 日核对的 action-policy 工作，不将其策略成功率混入本文评测。', 'Experimental and literature values follow the verified September 23, 2026 record, incorporating the October 14 Chinese draft and existing cases. This webpage revision adds no new aggregate experiments. Literature values are a dated snapshot, not a live leaderboard. The background adds action-policy work checked through October 15, 2026; its policy success rates are not mixed into our evaluations.', 'fine')
    return section('resources', '数据与参考文献', 'Data and references', body)

def reserve_image_space(content):
    """Reserve image layout before lazy loading so deep links retain their position."""
    def sized(match):
        tag = match.group(0)
        source = re.search(r'src="([^"]+)"', tag)
        if not source or ' width=' in tag:
            return tag
        path = source.group(1).split('?', 1)[0]
        if path not in IMAGE_SIZES:
            return tag
        width, height = IMAGE_SIZES[path]
        return tag[:-1] + f' width="{width}" height="{height}">'
    return re.sub(r'<img\b[^>]*>', sized, content)


def render():
    filename = 'index.html' if LANG == 'zh' else 'en.html'
    title = DATA['source']['title']
    description = t('机器人轨迹质量、进度估计与失败诊断：GPT-6 Astra 的离线评估结果、上下文示例分析与研究局限。', 'Offline evaluations of GPT-6 Astra as a robot critic: trajectory quality, progress estimation, failure diagnosis, context examples, and limitations.')
    items = [
        ('takeaways', 'Key takeaways', 'Key takeaways', False), ('overview','Introduction','Introduction',False),
        ('setup','1. 研究设置','1. Study design',False),
        ('benchmark-choice','1.1 评价任务与数据集','1.1 Tasks and benchmarks',True), ('comparison-protocol','1.2 模型配置与评测条件','1.2 Configurations and conditions',True),
        ('results','2. 结果','2. Results',False),
        ('quality-results','2.1 轨迹质量与偏好','2.1 Quality and preference',True),
        ('progress-results','2.2 任务进度估计','2.2 Task progress estimation',True),
        ('progress-icl','2.3 上下文示例的影响','2.3 Effects of context examples',True),
        ('failure','2.4 子任务成败判断','2.4 Subtask classification',True),
        ('explanations','2.5 失败解释与得分','2.5 Explanations and scores',True),
        ('outlook','3. 讨论与局限','3. Discussion and limitations',False), ('limitations','3.1 研究局限','3.1 Limitations',True), ('next-steps','3.2 强化学习验证','3.2 Reinforcement learning',True),
        ('resources','数据与参考文献','Data and references',False),
    ]
    toc = ''.join(f'<a class="{"subsection" if sub else ""}" href="#{id}">{t(zh,en)}</a>' for id, zh, en, sub in items)
    langs = ''.join('<a data-language-link href="{}" lang="{}" hreflang="{}"{}>{}</a>'.format(file, lang, lang, ' aria-current="page"' if LANG == code else '', label) for code, lang, file, label in [('zh','zh-CN','index.html','中文'),('en','en','en.html','English')])
    author_meta = ''.join(f'<meta name="citation_author" content="{escape(a)}">' for a in PUB['authors'] if a != 'xxx')
    authors = ', '.join(f'<span>{escape(a)}</span>' for a in PUB['authors'])
    return f'''<!doctype html>
<html lang="{t('zh-CN','en')}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · Simple AI</title><meta name="description" content="{description}"><meta name="theme-color" content="#f8f7f3">
{author_meta}<meta property="og:title" content="{title}"><meta property="og:description" content="{description}"><meta property="og:type" content="article">
<link rel="alternate" hreflang="zh-CN" href="index.html"><link rel="alternate" hreflang="en" href="en.html"><link rel="icon" href="assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="blog.css"><script src="blog.js" defer></script></head>
<body><a class="skip" href="#takeaways">{t('跳到正文','Skip to article')}</a>
<header class="header"><div class="wrap header-inner"><a class="brand" href="#top" aria-label="Simple AI">SIMPLE<span>·AI</span></a><span class="research">RESEARCH</span><nav class="language-switch" aria-label="{t('语言','Language')}">{langs}</nav></div></header><div id="reading-progress" aria-hidden="true"></div>
<main id="top"><div class="wrap article-shell"><aside class="toc" aria-label="{t('文章目录','Table of contents')}"><p>{t('目录','Contents')}</p><nav>{toc}</nav></aside><article class="article">
<header class="article-title"><p class="publication-meta">RESEARCH BLOG <span>·</span> <time datetime="{PUB['updated']}">{t('2026 年 10 月 15 日','October 15, 2026')}</time></p>
<h1><span class="title-name">Beyond the Score</span><span class="title-description">Early Evaluations of GPT-6 Astra as a Robot Critic</span></h1>
<div class="author-block"><p class="authors">{authors}</p><p class="organization">{PUB['organization']}</p></div>
<div class="publication-links" aria-label="{t('研究材料','Research materials')}"><span class="unreleased">Code <small>(coming soon)</small></span><span class="unreleased">arXiv <small>(coming soon)</small></span></div></header>
{article()}
</article></div></main><footer class="footer wrap"><a class="brand" href="#top">SIMPLE<span>·AI</span></a><span>Beyond the Score · 2026</span><a href="#top">{t('返回顶部','Back to top')} ↑</a></footer>
<dialog id="figure-modal" aria-label="{t('图表大图','Expanded figure')}"><button id="close-figure" type="button" aria-label="{t('关闭大图','Close figure')}">×</button><img id="expanded-figure" alt=""><p id="figure-description"></p></dialog>
</body></html>'''

if __name__ == '__main__':
    for LANG, name in [('zh','index.html'),('en','en.html')]:
        content = reserve_image_space(citations(render()))
        for tag, label in [('figcaption', t('图', 'Figure')), ('caption', t('表', 'Table'))]:
            count = [0]
            def number_caption(match):
                count[0] += 1
                text = re.sub(r'^(?:图|表|Figure|Table)\s*\d+[.。]\s*', '', match.group(1))
                return f'<{tag}>{label} {count[0]}. {text}</{tag}>'
            content = re.sub(f'<{tag}>(.*?)</{tag}>', number_caption, content, flags=re.S)
        content = content.replace('><', '>\n<')
        (ROOT / name).write_text(content)
        print(f'Built {name}: {len(content.encode())} bytes')
