"""Build the two static articles. Run with Python 3; no dependencies required."""
from pathlib import Path
from html import escape
import json
import re
from robofail_visuals import expanded_cases, visibility_experiment
from progress_charts import render_progress_video

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'data/report.json').read_text())
PUB = json.loads((ROOT / 'data/publication.json').read_text())
RBM_CASES = json.loads((ROOT / 'data/rbm-cases.json').read_text())['cases']
ROBOFAIL_CASES = json.loads((ROOT / 'data/robofail-cases.json').read_text())['cases']
VISIBILITY_PATH = ROOT / 'data/robofail-visibility.json'
VISIBILITY = json.loads(VISIBILITY_PATH.read_text()) if VISIBILITY_PATH.exists() else None
CONFIRMED = json.loads((ROOT / 'data/confirmed-blog.json').read_text())
IMAGE_SIZES = json.loads((ROOT / 'data/media-dimensions.json').read_text())
REFERENCES = json.loads((ROOT / 'data/references.json').read_text())
LANG = 'zh'
REFERENCE_LABELS = {
    'astra': (1, 'OpenAI: gpt-6-astra'),
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
    'embodied': (13, 'Systematically Exploring gpt-6-astra as Embodied Policies'),
    'flora': (14, 'NVIDIA Flora-Rewarder'),
}

def t(zh, en):
    return zh if LANG == 'zh' else en

def model_label(name):
    name = re.sub(r'(?<![\w-])(?:GPT-6 Astra|Astra)(?![\w-])', 'gpt-6-astra', name)
    return re.sub(r'\s+(?:low|max)\b', '', name).replace('DpskV4.1-flash', 'DeepSeek-V4.1-Flash').replace('5 examples', 'ICL (5 examples)')


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
    summary_alias = ' id="literature"' if id == 'quality-results' else ''
    summary_number = {'quality-results': '2.1.4', 'progress-results': '2.2.3', 'failure': '2.3.4', 'explanations': '2.4.3'}[id]
    summary = (f'<h4 id="{id}-summary" data-toc>{summary_number} {t("小结", "Summary")}</h4>'
               f'<div class="section-summary"{summary_alias}><p>{CONFIRMED["summary_" + id][LANG]}</p>'
               f'<p>{CONFIRMED["analysis_" + id][LANG]}</p></div>')
    return f'<section id="{id}" class="result-topic" data-toc><h3{alias}>{t(zh, en)}</h3>{body}{summary}</section>'


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
    content = re.sub(r'\[\[progress-video:([A-Z][0-9]+)\]\]', lambda match: render_progress_video(next(case for case in RBM_CASES if case['id'] == match.group(1)), LANG), content)
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
    r = DATA['table7_robofail_errors']
    rows = [[t('准确率', 'Accuracy'), *[f'{v:.2f}%' for v in r['accuracy_pct']]]]
    for key, zh, en in [
        ('correct_success', '成功 → 成功', 'Success → success'),
        ('false_alarms', '成功 → 失败（误报）', 'Success → failure (false alarm)'),
        ('misses', '失败 → 成功（漏检）', 'Failure → success (miss)'),
        ('correct_failure', '失败 → 失败', 'Failure → failure'),
    ]:
        rows.append([t(zh, en), *r[key]])
    return '<div id="outcome-counts">' + table(
        [t('参考标签 → 模型判断', 'Reference → prediction'), t('零样本', 'Zero-shot'), t('ICL（5 个示例）', 'Five-example ICL')],
        rows, t('同一组 57 个问题的成败判断：23 个成功，34 个失败。', 'Outcome judgments on the same 57 questions: 23 successes and 34 failures.')) + '</div>'

def rouge_chart():
    r = DATA['rouge_decomposition']
    out = '<div class="stack-key rouge-key">' + ''.join(f'<span><i></i>{x}</span>' for x in [t('成功识别项', 'Success-recognition term'), t('失败解释项', 'Failure-explanation term')]) + '</div>'
    for i, label in enumerate([t('零样本', 'Zero-shot'), t('ICL（5 个外部示例）', 'External five-example ICL')]):
        values = [r['success_terms'][i], r['failure_explanation_terms'][i]]
        bars = ''.join(f'<span style="width:{v / .55 * 100}%">{v:.4f}</span>' for v in values)
        desc = f'{label}: {values[0]:.4f} + {values[1]:.4f}'
        out += f'<div class="stack-heading"><strong>{label}</strong><span>{t("综合得分", "Composite score")} {DATA["table7_robofail_errors"]["composite_rouge_l"][i]:.3f}</span></div><div class="rouge-stack" role="img" aria-label="{desc}">{bars}</div>'
    cap = t('图 6. 综合 ROUGE-L 的组成：成功识别项贡献了大部分增量。', 'Figure 6. Components of composite ROUGE-L: correct success judgments account for most of the gain.')
    return f'<figure class="study-figure">{out}<div class="chart-axis full"><span>0</span><span>0.55</span></div><figcaption>{cap}</figcaption></figure>'

def study_design():
    global SUPPLEMENT_PROTOCOL
    body = h3('benchmark-choice', '1.1 评价任务与数据集', '1.1 Evaluation tasks and benchmarks')
    body += p('我们使用 RBM[[cite:robometer]][[cite:rbm]] 评估轨迹质量排序、成对偏好与进度估计，使用 RoboFail[[cite:reflect]] 评估子任务成败判断与失败解释。', 'We evaluate trajectory ranking, pairwise preference, and progress estimation on RBM[[cite:robometer]][[cite:rbm]], and subtask outcomes and failure explanations on RoboFail[[cite:reflect]].')
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
    protocol_details += p('<strong>RBM 排序协议。</strong>采用 RBM 的质量标签顺序与 Kendall τa 指标[[cite:robometer]]，本次运行包含 567 条轨迹、41 个来源–任务组。<a href="https://github.com/robometer/robometer/blob/main/robometer/data/samplers/eval/progress_policy_ranking.py" target="_blank" rel="noopener">官方采样器</a>按任务和质量标签选取轨迹，数量可配置；567 是本次运行的样本数，不是基准固定规模。', '<strong>RBM ranking protocol.</strong> We use RBM’s quality-label order and Kendall τa metric[[cite:robometer]], with 567 trajectories across 41 source–task groups in this run. The <a href="https://github.com/robometer/robometer/blob/main/robometer/data/samplers/eval/progress_policy_ranking.py" target="_blank" rel="noopener">official sampler</a> selects trajectories by task and quality label with configurable counts; 567 is this run’s sample count, not a fixed benchmark size.')
    protocol_details += p('<strong>RoboFail 协议。</strong>RoboFail 由 REFLECT 提出[[cite:reflect]]。本文采用 AHA 提供的问答评测形式[[cite:aha]]，在本研究记录的 57 个问题上评估；该问题集合不等同于原始数据集的全部内容，也不假定与其他文献的评测子集完全一致。', '<strong>RoboFail protocol.</strong> RoboFail was introduced by REFLECT[[cite:reflect]]. We use the question–answer evaluation format provided by AHA[[cite:aha]] on the 57 questions recorded in this study. This set is not the entire original dataset and is not assumed to match other publications’ evaluation subsets exactly.')

    body += h3('comparison-protocol', '1.2 模型配置与评测条件', '1.2 Model configurations and evaluation conditions')
    body += p('我们以 gpt-6-astra[[cite:astra]] 为主要研究对象，通过提示提供任务与观测，不进行额外的评价任务微调。RBM 评测另包含 GPT-5.6-sol[[cite:sol]] 和 DeepSeek-V4.1-Flash[[cite:deepseek]] 的零样本比较。', 'Our primary subject is gpt-6-astra[[cite:astra]], supplied with task descriptions and observations through prompts, without additional evaluation-task fine-tuning. The RBM evaluation also includes zero-shot comparisons with GPT-5.6-sol[[cite:sol]] and DeepSeek-V4.1-Flash[[cite:deepseek]].')
    body += p('进度估计、独立排序与 RoboFail 另设上下文学习（ICL）条件；两个 RoboFail 案例还比较了不同观测帧数下的回答。', 'Progress estimation, independent ranking, and RoboFail also include in-context learning (ICL). Two RoboFail cases additionally compare responses across different numbers of observed frames.')

    protocol_details += p('<strong>上下文示例。</strong> gpt-6-astra 的示例条件按评价任务分别设置：', '<strong>In-context examples.</strong> gpt-6-astra receives task-specific context conditions:')
    protocol_details += '<ul>' + ''.join('<li>' + t(zh, en) + '</li>' for zh, en in [
        ('<strong>进度估计：</strong>一条相同或相近任务的训练轨迹，附六个阶段评分。', '<strong>Progress estimation:</strong> one training trajectory of the same or a similar task, with six stage scores.'),
        ('<strong>独立排序：</strong>随机选取高、中、低分训练轨迹各一条，不要求与测试任务相同；中等参考分数不等于测试集的“次优”标签。', '<strong>Independent ranking:</strong> one randomly selected training trajectory at each of three score levels—high, middle, and low—without requiring a task match. The middle reference score is not the test set’s suboptimal label.'),
        ('<strong>RoboFail：</strong>从另外五条原始 RoboFail 真实轨迹中人工选取并构造五个外部图像–问题–答案示例（2 个成功、3 个失败），并非从训练集随机抽样。所有测试问题复用同一组及顺序；来源与标注方式见<a href="#robofail-icl-provenance">五示例说明</a>。', '<strong>RoboFail:</strong> five external image–question–answer demonstrations manually selected and constructed from five other original real-robot RoboFail episodes (two successes, three failures), not randomly sampled from a training split. Every test question uses the same examples and order; see the <a href="#robofail-icl-provenance">demonstration provenance</a>.'),
    ]) + '</ul>'
    protocol_details += p('直接偏好仅评估零样本。', 'Direct preference is evaluated only in the zero-shot setting.', 'method-note')
    protocol_details += p('<strong>观测遮蔽。</strong>两个 RoboFail 案例分别使用前 1 帧、前 2 帧与全部观测，在零样本和 ICL 条件下各请求一次，共 12 次。少帧条件没有时间级真值，只比较模型回答。', '<strong>Observation masking.</strong> Two RoboFail cases use the first frame, first two frames, or all observations, with one request per zero-shot and five-example ICL condition, for 12 requests. Partial observations have no time-specific labels; we compare responses without scoring accuracy.')
    protocol_details += p('<strong>结果来源。</strong>图中 [S] 为本研究，[P]、[W]、[R]、[A] 分别为 Robometer 论文、项目网站、RynnValue 与 AHA。RBM 排序与“不同质量”偏好沿用官方采样和指标规则；随机种子、模型接口与引用版本见 2.1 的折叠说明。RoboFail 的文献对照使用不同问题集合，范围见 2.3。', '<strong>Result sources.</strong> Chart tags [S], [P], [W], [R], and [A] denote this study, the Robometer paper, its project website, RynnValue, and AHA. RBM ranking and different-quality preference follow official sampling and metric rules; the details in Section 2.1 record seeds, model interfaces, and cited versions. RoboFail literature comparisons use different question sets, as described in Section 2.3.')

    protocol_details += '<div id="positive-case-protocol">' + p('<strong>案例对照。</strong>四组正例为评测后的说明性选例，不用于估计整体错误率。gpt-6-astra 与 DeepSeek 使用相同任务、轨迹、提示和输入图像，不接收参考质量标签；偏好案例保留实际 A/B 顺序。两者推理配置与计算预算未匹配：gpt-6-astra 为 low、输出上限 512 token，DeepSeek 为 max、上限 32768 token。未进行 A/B 交换复测，也没有匹配的 Robometer 逐条输出。', '<strong>Case comparisons.</strong> The four positive examples are selected post hoc for illustration, not to estimate overall error rates. gpt-6-astra and DeepSeek receive identical tasks, trajectories, prompts, and input images without reference quality labels; preference cases retain the actual A/B order. Reasoning settings and compute budgets are unmatched: gpt-6-astra uses low effort with a 512-token output limit, while DeepSeek uses max effort with a 32768-token limit. No swapped-order repeat or matched per-example Robometer output is available.') + '</div>'

    protocol_details += p('<strong>回放与曲线。</strong>2.1 的排序与偏好案例回放各轨迹的 8 张模型输入图像，每秒 1 张，封面取最后一张；新增正例在 32 张保存帧中的采样位置为 0 / 4 / 9 / 13 / 18 / 22 / 27 / 31。2.2 的进度案例将 32 张保存帧按每秒 4 帧回放，评分位置为 0 / 7 / 15 / 23 / 31；起点由协议设为 0，其余四点为模型预测。以上回放均非原速视频，采样位置不是秒数。曲线连线仅辅助阅读，中间位置没有额外预测或人工标注。', '<strong>Replays and curves.</strong> Ranking and preference cases in Section 2.1 replay eight model-input images per trajectory at one image per second, using the last image as the poster. The added positive cases sample positions 0 / 4 / 9 / 13 / 18 / 22 / 27 / 31 from 32 stored frames. Progress cases in Section 2.2 replay 32 stored frames at four frames per second, with scores at positions 0 / 7 / 15 / 23 / 31. The initial zero is protocol-set; the other four points are predictions. These replays do not preserve original timing, and sample indices are not seconds. Lines guide the eye without adding predictions or human annotations between samples.')

    metrics = ''
    metrics += p('进度评测的起点 0 由协议设定，与四次模型预测共同构成五个评分位置；统计时使用同一时间参考。', 'The progress protocol fixes the initial score at zero. Together with four model predictions, this gives five evaluation positions against the same time reference.', 'fine')
    metrics += p('<strong>独立排序：Kendall τa。</strong>同一来源–任务组内，参考顺序为成功 &gt; 次优 &gt; 失败。按官方评分器纳入轨迹对，预测顺序正确计 +1、颠倒计 −1、平分计 0；组内得分为 (C − D) / N。先对任务取平均，再对六个来源等权平均。', '<strong>Independent ranking: Kendall τa.</strong> Within each source–task group, the reference order is success &gt; suboptimal &gt; failure. For pairs included by the official scorer, correct orders contribute +1, inversions −1, and ties 0, giving (C − D) / N. Scores are averaged across tasks and then equally across the six sources.')
    metrics += p('<strong>直接偏好：六来源等权准确率。</strong>先计算每个来源内选对较优执行的比例，再对六个来源取平均。cₛ 为来源 s 的正确选择数，nₛ 为该来源的评测对数，共 1,192 对。', '<strong>Direct preference: equal-source accuracy.</strong> Accuracy is computed within each source and then averaged equally across six sources. Here cₛ is the number of correct choices and nₛ the number of evaluated pairs in source s, with 1,192 pairs in total.')
    metrics += '<div class="formula" role="math">A<sub>pref</sub> = (100 / 6) Σ<sub>s=1</sub><sup>6</sup> (cₛ / nₛ)</div>'
    metrics += p('<strong>进度：VOC 与时间参考 MSE。</strong><a class="inline-link" href="https://robometer.github.io/" target="_blank" rel="noopener">RBM 的 VOC 定义</a>使用 Pearson 相关系数。对一条轨迹，在评估位置 i 记预测为 pᵢ，归一化帧位置对应的时间参考为 tᵢ，先计算二者的相关性；正文按 ×100 展示，越高越好。MSE 则检查预测数值与同一时间参考的距离，越低越好。', '<strong>Progress: VOC and time-reference MSE.</strong> The <a class="inline-link" href="https://robometer.github.io/" target="_blank" rel="noopener">RBM definition of VOC</a> uses Pearson correlation. For one trajectory, let pᵢ be the prediction at evaluation position i and tᵢ the time reference from normalized frame position. Compute their correlation; the article reports it on a ×100 scale, higher being better. MSE measures numerical distance from the same time reference, lower being better.')
    metrics += '<div class="formula" role="math">r = Σᵢ(pᵢ − p̄)(tᵢ − t̄) / √[Σᵢ(pᵢ − p̄)² · Σᵢ(tᵢ − t̄)²]<br>VOC = 100 × r<br>MSE = (1 / m) Σᵢ(pᵢ − tᵢ)²</div>'
    metrics += p('m 为评估位置数，跨来源汇总沿用官方评分器。时间参照是归一化帧位置，并非人工标注的语义完成度。', 'Here m is the number of evaluation positions; cross-source aggregation follows the official scorer. The reference is normalized frame position, not human-annotated semantic completion.', 'fine')
    metrics += p('<strong>成败分类：准确率、失败召回率、误报率和漏检率。</strong>以失败为正类：TP 是正确识别的失败，FN 是漏掉的失败，TN 是正确识别的成功，FP 是把成功误判为失败。准确率为 (TP + TN) / 57；失败召回率为 TP / 34；误报率为 FP / 23；漏检率为 FN / 34。四项都以百分比报告。它们评估的是回答，不是机器人实际执行成功率。', '<strong>Outcome classification: accuracy, failure recall, false-alarm rate, and miss rate.</strong> Treat failure as positive: TP is a correctly detected failure, FN a missed failure, TN a correctly recognized success, and FP a success predicted as failure. Accuracy is (TP + TN) / 57; failure recall is TP / 34; false-alarm rate is FP / 23; and miss rate is FN / 34. All four are reported as percentages. They score the answers, not the robot’s execution success rate.')
    metrics += p('<strong>失败解释：AHA 综合 ROUGE-L，越高越好。</strong>标签错误计 0；正确成功计 1；正确失败按原始英文解释与参考答案的词干化 ROUGE-L F1 计分。对后一项，令 L 为两个词元序列的最长公共子序列长度，P = L / 生成词元数，R = L / 参考词元数，F1 = 2PR / (P + R)，无重合时为 0。将 57 个问题的得分求和后除以 57。该综合指标混合了成功识别与失败文本重合度，第 2.4 节会拆开报告，避免把它读成解释准确率。', '<strong>Failure explanations: AHA composite ROUGE-L, higher is better.</strong> A wrong label receives 0, a correct success receives 1, and a correct failure receives stemmed ROUGE-L F1 between the original English explanation and reference. For the latter, let L be the longest common subsequence length of the token sequences: P = L / generated-token count, R = L / reference-token count, and F1 = 2PR / (P + R), with zero for no overlap. Sum scores over 57 questions and divide by 57. The composite mixes success recognition and failure-text overlap. Section 2.4 separates them rather than treating the composite as explanation accuracy.')
    metrics += p('下表列出由指标定义和标签数量推导的参照值。', 'The following reference values follow from the metric definitions and label counts.')
    metrics += table([t('非学习参照', 'Non-learning reference'),t('可推导的结果', 'Deducible result'),t('它说明什么', 'Interpretation')],[
        [t('所有轨迹给同分', 'Give every trajectory the same score'),'τa = 0',t('不提供质量区分；预测平分没有正贡献。', 'No quality discrimination; predicted ties add no positive contribution.')],
        [t('二选一均匀随机猜测', 'Uniform random binary choice'),t('期望准确率 50%', 'Expected accuracy 50%'),t('仅适用于两个选项中恰有一个正确答案的设定；不是一次实测。', 'Applies only when exactly one of two choices is correct; not a measured run.')],
        [t('RoboFail 一律回答失败', 'Always predict failure on RoboFail'),'34 / 57 = 59.65%',t('失败召回率 100%，误报率 100%；显示只看召回率的局限。', 'Failure recall 100%, false-alarm rate 100%; recall alone is insufficient.')],
        [t('直接输出时间参考', 'Output the time reference itself'),'VOC = 100; MSE = 0',t('非恒定参考下的理论值；使用了评分目标，不证明视觉理解或任务完成判断。', 'Theoretical values for a nonconstant reference; using the scoring target does not establish visual or completion understanding.')],
    ],t('非学习参照：解析推导，未作为实验运行。', 'Non-learning references: analytical deductions, not experimental runs.'))
    SUPPLEMENT_PROTOCOL = detail('评测设置与指标', 'Evaluation settings and metrics', protocol_details + metrics).replace('<details class="research-detail">', '<details id="metrics" class="research-detail">', 1)
    body += p('<a href="#metrics">评测设置与指标 ↗</a>', '<a href="#metrics">Evaluation settings and metrics ↗</a>')
    return section('setup', '1. 研究设置', '1. Study design', body)

def article():
    takeaways = [
        t('<strong>零样本执行质量比较具有竞争力。</strong>gpt-6-astra 在本研究的三个通用模型中排序与偏好得分最高，可与专用模型的报告结果竞争。', '<strong>Zero-shot execution-quality comparison is competitive.</strong> gpt-6-astra has the highest ranking and preference scores among the three general-purpose models tested and is competitive with published specialized-model results.'),
        t('<strong>上下文示例对不同任务的影响不同。</strong>进度 VOC 提高，轨迹排序 τa 却下降。', '<strong>In-context examples affect tasks differently.</strong> Progress VOC improves, while trajectory-ranking τa declines.'),
        t('<strong>总体成败准确率提高，但失败漏检增加。</strong>RoboFail 中，ICL 更准确地识别了成功执行，却将更多失败判为成功。', '<strong>Overall outcome accuracy improves, but more failures are missed.</strong> On RoboFail, ICL recognizes successful executions more accurately while also labeling more failures as successes.'),
        t('<strong>综合 ROUGE-L 的增量主要来自成功识别。</strong>失败解释项的提高较小，需要结合具体原因分析。', '<strong>Most of the composite ROUGE-L gain comes from success recognition.</strong> The failure-explanation term improves less and needs to be examined alongside the specific reasons given.'),
    ]
    out = section('takeaways', 'Key takeaways · 主要发现', 'Key takeaways', '<ul>' + ''.join(f'<li>{x}</li>' for x in takeaways) + '</ul>', 'key-takeaways')

    body = p('机器人系统需要评价自身的行为：判断任务推进了多少、比较不同执行的质量，以及识别和解释失败。通用多模态模型能够联合处理视觉观测与任务描述，并通过上下文接收评价要求和示例，为这些判断提供了一种无需额外任务微调的途径。我们研究：<strong>通用多模态模型已有的视觉理解与推理能力，能在多大程度上支持对机器人行为的评价？这些能力如何随评价任务、观测信息与上下文示例而变化？</strong>', 'Robot systems need to evaluate their own behavior: assess how far a task has progressed, compare the quality of different executions, and identify and explain failures. General-purpose multimodal models can jointly process visual observations and task descriptions, while receiving evaluation criteria and examples through context, offering a way to make these judgments without additional task-specific fine-tuning. We ask: <strong>To what extent can the existing visual understanding and reasoning capabilities of general-purpose multimodal models support the evaluation of robot behavior? How do these capabilities vary across evaluation tasks, available observations, and in-context examples?</strong>')
    body += p('本文以 gpt-6-astra[[cite:astra]] 为主要研究对象，在 RBM[[cite:robometer]][[cite:rbm]] 和 RoboFail[[cite:reflect]] 上开展实证评估。我们考察轨迹质量评分、直接偏好判断、任务进度估计，以及子任务成败判断与解释，分别衡量模型比较执行、追踪任务推进和识别失败的能力。我们进一步比较零样本与上下文示例条件下的表现，并通过观测遮蔽的探索性案例，考察可见信息变化时模型回答的变化。', "We conduct an empirical study with gpt-6-astra[[cite:astra]] as our primary subject on RBM[[cite:robometer]][[cite:rbm]] and RoboFail[[cite:reflect]]. We examine trajectory quality scoring, direct preference judgments, task progress estimation, and subtask success and failure judgments with explanations, assessing the model's ability to compare executions, track task progression, and recognize failures. We further compare zero-shot performance with conditions that provide in-context examples, and use exploratory observation-masking cases to examine how responses change with the available visual information.")
    body += p('结果显示，<strong>gpt-6-astra 的执行质量比较具有竞争力，但完成判断和失败诊断仍存在明显错误。</strong>零样本排序 Kendall τ<sub>a</sub> 为 <strong>0.8166</strong>，高于 Robometer 报告的 0.655[[cite:robometer]] 和 RynnValue-8B 的 0.675[[cite:rynnvalue]]；直接偏好准确率为 <strong>92.4%</strong>。RoboFail 成败准确率在加入五个示例后从 <strong>64.91% 提高至 85.96%</strong>，但失败漏检也有所增加。本文进一步分析这些分数对应的状态判断、质量要求和错误类型；尚未验证其对策略学习的帮助。', 'Our results show that <strong>gpt-6-astra is competitive at comparing execution quality, but still makes clear errors in completion judgment and failure diagnosis.</strong> Zero-shot ranking reaches Kendall τ<sub>a</sub> = <strong>0.8166</strong>, above the reported values of 0.655 for Robometer[[cite:robometer]] and 0.675 for RynnValue-8B[[cite:rynnvalue]]; direct preference accuracy is <strong>92.4%</strong>. Adding five examples raises RoboFail outcome accuracy from <strong>64.91% to 85.96%</strong>, while also increasing missed failures. We examine the state judgments, quality requirements, and error types behind these scores. Their benefit to policy learning remains untested.')
    out += section('overview', 'Introduction', 'Introduction', body)

    out += study_design()
    result_topics = ''


    body = p('本节比较三个多模态模型的独立轨迹评分与直接偏好判断，再通过案例分析 gpt-6-astra 的判断依据。', 'We compare the three multimodal models on independent trajectory scoring and direct preference, then examine gpt-6-astra’s judgments through cases.')
    body += '<p id="rbm-replay-note" class="fine">' + t('本节视频回放模型输入的 8 帧图像。', 'Videos in this section replay the eight model-input frames.') + '</p>'
    body += h3('ranking-results', '2.1.1 轨迹质量排序', '2.1.1 Trajectory quality ranking')
    body += confirmed('ranking')
    body += '<h4 id="ranking-context" class="case-title">' + t('上下文示例：逆序减少，平分增多', 'Context examples: fewer inversions, more ties') + '</h4>'
    body += confirmed('ranking_icl')
    ranking_details = p('41 个来源–任务组中，8 组提高、10 组下降、23 组不变。下图按评分器的成对权重分解正确顺序、平分与颠倒。', 'Of 41 source–task groups, eight improve, ten decline, and 23 are unchanged. The figure decomposes concordant, tied, and inverted pairs using the scorer’s pair weights.')
    body += detail('排序变化的分解', 'Breakdown of ranking changes', ranking_details + ranking_chart())
    body += h3('preference-results', '2.1.2 直接偏好判断', '2.1.2 Direct preference')
    body += confirmed('preference')
    comparison_details = p('排序与“不同质量”偏好评测复用 Robometer 官方采样和指标规则，使用 seed=44。571 条缓存轨迹中，4 条属于仅含成功样本的任务，按官方规则排除后得到 567 条；偏好配对按每来源最多 500 对采样，共 1,192 对。两项指标均按六来源等权汇总。', 'Ranking and different-quality preference evaluation reuse Robometer’s official sampling and metric rules with seed=44. Of 571 cached trajectories, four belong to tasks with only successful examples and are excluded by the official rule, leaving 567. Preference sampling uses up to 500 pairs per source, yielding 1,192 pairs. Both metrics use equal weighting across the six sources.')
    comparison_details += p('本研究 seed=44，当前官方默认值为 42。双方均匀取 8 帧；gpt-6-astra 通过提示输出评分或 A/B，Robometer 使用训练后的 progress/preference head。正文引用 Robometer v1 的 τa=0.655；v2 对应值约为 0.643。', 'This study uses seed=44; the current official default is 42. Both sample eight frames uniformly. gpt-6-astra produces prompted scores or A/B choices, while Robometer uses trained progress/preference heads. We cite Robometer v1’s τa=0.655; the corresponding v2 value is approximately 0.643.')
    body += detail('采样、指标与引用版本', 'Sampling, metrics, and cited versions', comparison_details)
    result_topics += result_section('quality-results', '2.1 轨迹质量与偏好', '2.1 Trajectory quality and preference', re.sub(r'<(/?)h4\b', r'<\1h5', body))

    body = h3('progress-zero', '2.2.1 零样本进度估计', '2.2.1 Zero-shot progress estimation')
    body += confirmed('progress')
    # Retain the former standalone ICL anchors at the relocated comparison.
    body += '<div id="progress-icl">' + h3('progress-icl-title', '2.2.2 上下文示例与完成判断', '2.2.2 Context examples and completion judgments')
    body += confirmed('progress_icl')
    more = p('105 条轨迹中，58 条 VOC 提高、35 条下降、12 条不变；58 条提高的轨迹中，有 11 条 MSE 变差。总体时间参考 MSE 从 0.0402 降至 0.0390。香蕉转移任务的 19 条轨迹中，18 条 VOC 下降、1 条不变。', 'Of 105 trajectories, VOC improves on 58, declines on 35, and is unchanged on 12; 11 of the 58 improvements have worse MSE. Aggregate time-reference MSE falls from 0.0402 to 0.0390. In banana transfer, VOC declines on 18 of 19 trajectories and is unchanged on one.')
    body += detail('逐轨迹进度变化', 'Trajectory-level progress changes', more)
    rows = [[escape(model_label(r[0])), source_label(r[1]), f'{r[2]:.1f}' if r[2] is not None else None, f'{r[3]:.4f}' if r[3] is not None else None, f'{r[4]:.1f}' if r[4] is not None else None] for r in DATA['table2_rbm']['rows']]
    more = table([t('配置', 'Configuration'), t('来源', 'Source'), 'VOC ↑', 'τa ↑', t('偏好 % ↑', 'Preference % ↑')], rows, t('完整 RBM 结果：保留不同来源、版本及示例条件。', 'Full RBM results, retaining sources, versions, and context conditions.'))
    more += p('Robometer 报告[[cite:robometer]]与网站[[cite:rbm]]分别给出 VOC 94.8 / 94.0、τa 0.655 / 0.643。RBM-1M 和 RoboReward data 指训练数据，空项表示未报告的数值。', 'The Robometer report[[cite:robometer]] and website[[cite:rbm]] give VOC of 94.8 / 94.0 and τa of 0.655 / 0.643, respectively. RBM-1M and RoboReward data identify training data; blank entries indicate unreported values.')
    body += detail('完整结果数值与来源', 'Complete result values and sources', more)
    body += '</div>'
    result_topics += result_section('progress-results', '2.2 任务进度估计', '2.2 Task progress estimation', re.sub(r'<(/?)h4\b', r'<\1h5', body), heading_id='context')

    body = h3('outcome-results', '2.3.1 总体表现与错误分布', '2.3.1 Overall performance and error distribution')
    body += '<div id="robofail-icl-provenance">' + confirmed('robofail_icl_summary')
    body += detail('五个示例的来源、固定顺序与标注方式', 'Sources, fixed order, and annotations of the five examples', confirmed('robofail_icl_details')) + '</div>'
    body += confirmed('robofail_results')
    body += figure('assets/figures/04_robofail_icl.png', t('RoboFail 成败分类准确率：本研究与 AHA 报告结果', 'RoboFail outcome accuracy: this study and AHA-reported results'), t('成败分类准确率。文献结果来自 AHA 报告[[cite:aha]]，与本研究分组展示；文献采用其各自的问题集合。', 'Outcome classification accuracy. Literature results are from the AHA report[[cite:aha]] and shown separately; published results use their respective question sets.'))
    body += diagnosis()
    error_details = p('误报率从 78.26% 降至 8.70%，漏检率从 5.88% 升至 17.65%，失败召回率从 94.12% 降至 82.35%。', 'The false-alarm rate falls from 78.26% to 8.70%, while the miss rate rises from 5.88% to 17.65% and failure recall falls from 94.12% to 82.35%.')
    error_details += p('按来源与画面核查，五条外部示例轨迹与测试轨迹不重叠；详细来源见<a href="#robofail-icl-provenance">五示例说明</a>。', 'Our source and visual audit found no overlap between the five demonstration episodes and test trajectories; see the <a href="#robofail-icl-provenance">demonstration provenance</a>.')
    more = table([t('配置', 'Configuration'), t('来源', 'Source'), t('准确率 % ↑', 'Accuracy % ↑'), 'ROUGE-L ↑'], [[escape(model_label(r[0])), source_label(r[1]), f'{r[2]:.2f}', f'{r[3]:.3f}'] for r in DATA['table5_robofail_aha']['rows']], t('本研究与 AHA 报告结果。', 'Results from this study and the AHA report.'))
    more += p('AHA-13B 的 Vicuna 与 Llama-2 版本分别列出；文献结果采用各自的评测样本。', 'The Vicuna and Llama-2 variants of AHA-13B are listed separately; published results use their respective evaluation samples.')
    more += p('Guardian[[cite:guardian]] 使用 153 个执行样本与 30 个规划样本，PRIMO[[cite:primo]] 使用 Cosmos 筛选的 100 个样本；两者单独列示。', 'Guardian[[cite:guardian]] uses 153 execution and 30 planning examples; PRIMO[[cite:primo]] uses 100 Cosmos-curated examples. Their results are listed separately.')
    more += table([t('配置', 'Configuration'), t('执行准确率 %', 'Execution accuracy %'), t('规划准确率 %', 'Planning accuracy %')], DATA['table6_other_adaptations']['guardian']['rows'], t('Guardian v4，Tables 1/2。+GF 表示使用 GuardianFail-36k 训练。', 'Guardian v4, Tables 1/2. +GF denotes training on GuardianFail-36k.'))
    more += table([t('配置', 'Configuration'), t('准确率 %', 'Accuracy %')], DATA['table6_other_adaptations']['primo']['rows'], 'PRIMO, Table 3 / Appendix A.3.')
    body += detail('完整结果与不同 RoboFail 评测版本', 'Full results and distinct RoboFail adaptations', error_details + more)
    body += h3('robofail-gallery', '2.3.2 成败误判的案例分析', '2.3.2 Cases of outcome misclassification')
    body += p('<strong>零样本识别出 34 个失败中的 32 个，却将 23 个成功中的 18 个误判为失败。</strong>以下案例展示这两类错误及 ICL 后的变化。', '<strong>Zero-shot detects 32 of 34 failures but labels 18 of 23 successes as failures.</strong> The cases below illustrate both types of error and their changes with ICL.')
    body += p('视频展示原始轨迹，模型输入为配图中的关键帧拼图与子任务问题。', 'Videos show the original trajectories; the model receives the accompanying keyframe montage and the subtask question.', 'fine')
    body += expanded_cases(ROBOFAIL_CASES, t, ids=(50, 49))
    body += detail('补充对照：两种条件都识别成功', 'Additional contrast: both conditions recognize success', expanded_cases(ROBOFAIL_CASES, t, ids=(2,), fold=False))
    body += '<span id="robofail-cases"></span>'
    body += visibility_experiment(VISIBILITY, ROBOFAIL_CASES, t)
    result_topics += result_section('failure', '2.3 子任务成败判断', '2.3 Subtask success and failure', re.sub(r'<(/?)h4\b', r'<\1h5', body))

    body = p('本节分析 2.3 中同一批回答的综合 ROUGE-L，并区分成功识别与失败解释的贡献。', 'We analyze composite ROUGE-L for the same responses as Section 2.3, separating the contributions of success recognition and failure explanation.')
    body += p('这里的 ICL 使用与成败判断完全相同的<a href="#robofail-icl-provenance">五个人工构造的外部示例</a>，没有为解释指标另选示例或重新请求模型。', 'ICL here uses exactly the same <a href="#robofail-icl-provenance">five manually constructed external demonstrations</a> as outcome classification; examples were not reselected and the model was not queried again for the explanation metric.', 'fine')
    body += h3('explanation-scores', '2.4.1 总体表现与基线比较', '2.4.1 Overall performance and baseline comparison')
    body += p('ICL 后的综合 ROUGE-L 为 <strong>0.499</strong>，零样本为 <strong>0.185</strong>。其中，成功识别项从 <strong>0.0877 增至 0.3684（+0.2807）</strong>，失败解释项从 <strong>0.0969 增至 0.1305（+0.0336）</strong>。', 'Composite ROUGE-L is <strong>0.499</strong> with five-example ICL versus <strong>0.185</strong> zero-shot. The success-recognition term rises from <strong>0.0877 to 0.3684 (+0.2807)</strong>, and the failure-explanation term from <strong>0.0969 to 0.1305 (+0.0336)</strong>.')
    body += p('gpt-6-astra 使用五个示例进行 ICL 后的综合得分高于 AHA 报告中的 AHA-13B Vicuna（0.290）、AHA-13B Llama-2（0.280）、AHA-7B（0.204）和 GPT-4o 的 ICL 结果（5 个示例，0.236）[[cite:aha]]。', 'gpt-6-astra’s five-example ICL composite score is above the AHA-reported values for AHA-13B Vicuna (0.290), AHA-13B Llama-2 (0.280), AHA-7B (0.204), and five-shot GPT-4o (0.236)[[cite:aha]].')
    scoring_details = p('综合 ROUGE-L 不只衡量失败解释。按 AHA 评测规则[[cite:aha]]，正确成功回答计 1 分，正确失败回答按解释与参考答案的词干化 ROUGE-L F1 计分，成败标签错误则计 0 分。所有问题得分相加后除以 57。评分使用原始英文回答，不使用本文的中文转述。', 'Composite ROUGE-L does not measure failure explanations alone. Under the AHA rules[[cite:aha]], a correct success answer receives 1; a correct failure receives stemmed ROUGE-L F1 against the reference explanation; and a label disagreement receives 0. Scores are summed and divided by 57. Evaluation uses the original English answers, not the Chinese paraphrases in this article.')
    scoring_details += f'<div class="formula" role="math" aria-label="{t("综合得分等于正确成功数加上正确失败的解释分数总和，再除以57", "Composite score equals correct successes plus summed explanation scores for correctly detected failures, divided by 57")}">R = ({t("正确成功数 + 正确失败的解释分数之和", "correct successes + summed explanation scores for correct failures")}) / 57</div>'
    body += figure('assets/figures/05_robofail_icl.png', t('包含 AHA 及其他 baseline 的综合 ROUGE-L 对比', 'Composite ROUGE-L including AHA and other baselines'), t('综合 ROUGE-L 对比；文献结果沿用各自协议。', 'Composite ROUGE-L comparison; literature results retain their own protocols.'))
    body += rouge_chart()
    scoring_details += p('成功识别项从 0.0877 增至 0.3684，增量约为 16 / 57 = 0.2807，占报告总增量 0.3144 的约 89.3%。失败解释项从 0.0969 增至 0.1305，占剩余约 10.7%。因此，0.499 不能读作“49.9% 的失败解释正确”；大部分增量来自识别成功，而非失败解释项。', 'The success-recognition term rises from 0.0877 to 0.3684. Its increase, 16 / 57 ≈ 0.2807, accounts for about 89.3% of the reported total gain of 0.3144. The failure-explanation term rises from 0.0969 to 0.1305, accounting for the remaining 10.7%. A score of 0.499 therefore does not mean that 49.9% of failure explanations are correct. Most of the gain comes from recognizing success.')
    body += detail('综合评分规则与分项计算', 'Composite scoring rule and component calculations', scoring_details)
    body += h3('explanation-cases', '2.4.2 失败解释得分与原因分析', '2.4.2 Explanation scores and failure reasons')
    body += p('<strong>失败解释项提高，但正确检出的失败数从 32 个降至 28 个。</strong>该分项将正确检出失败的解释 ROUGE-L 求和后除以全部 57 个问题；得分变化还需结合具体解释分析。', '<strong>The failure-explanation term improves even though correctly detected failures fall from 32 to 28.</strong> This term sums explanation ROUGE-L for correctly detected failures and divides by all 57 questions; the individual explanations help interpret the change.')
    body += expanded_cases(ROBOFAIL_CASES, t, ids=(33,))
    body += p('<a href="#robo-case-55">旋钮案例</a>中，零样本同样判对失败，但强调抓取位置，参考答案则强调夹爪未闭合。', 'In the <a href="#robo-case-55">knob case</a>, zero-shot also detects failure, but emphasizes grasp location while the reference identifies an unclosed gripper.')
    result_topics += result_section('explanations', '2.4 失败解释与得分', '2.4 Failure explanations and scores', re.sub(r'<(/?)h4\b', r'<\1h5', body))
    out += section('results', '2. 结果', '2. Results', result_topics)

    body = h3('conclusions', '3.1 主要发现', '3.1 Main findings')
    body += p('<strong>通用模型无需针对评价任务额外微调，也能完成有竞争力的机器人执行质量比较。</strong>gpt-6-astra 的零样本排序与偏好结果可与所引用的专用奖励模型竞争，GPT-5.6-sol 的排序也高于两项专用模型报告值。这表明，部分执行评价能力已能通过任务描述和视觉观测直接调用；不同通用模型的表现仍有差异。', '<strong>General-purpose models can competitively compare robot execution quality without additional evaluation-task fine-tuning.</strong> gpt-6-astra’s zero-shot ranking and preference results are competitive with the cited specialized reward models, and GPT-5.6-sol’s ranking also exceeds both reported specialized-model values. Some execution-evaluation capabilities can therefore be elicited directly through task descriptions and visual observations, although performance varies across general-purpose models.')
    body += p('<strong>模型能够将任务目标与物体状态联系起来，评价执行中的推进、失误和恢复。</strong>抽屉、按钮和红桶案例中的判断响应了关合、激活和桶盖回落等状态变化；蓝杯与香蕉案例的进度分数则在滑落或无效尝试后下降，在完成重试后回升。这些案例显示，评分可以反映任务相关事件，而不只是机械臂运动或时间流逝。', '<strong>The model can connect task goals to object states when assessing progress, mistakes, and recovery.</strong> Judgments in the drawer, button, and red-bin cases respond to closure, activation, and a lid falling shut. Progress scores in the blue-cup and banana cases fall after slipping or an ineffective attempt and recover after a successful retry. These cases show scores responding to task-relevant events rather than merely arm motion or elapsed time.')
    body += p('<strong>少量上下文示例明显改善了对成功执行的识别。</strong>加入五个示例后，23 个成功子任务的正确识别数从 5 个增至 21 个，无需更新模型参数。这为通过输入示例适配评价提供了实证依据；示例是否帮助模型确定“哪些证据足以判定成功”，是值得进一步验证的问题。', '<strong>A small set of in-context examples substantially improves recognition of successful executions.</strong> Adding five examples raises correct judgments on the 23 successful subtasks from 5 to 21, without updating model parameters. This provides empirical support for adapting evaluation through input examples. Whether they help the model determine what evidence is sufficient to judge success remains a question for further study.')
    body += h3('failure-modes', '3.2 评价错误与分歧', '3.2 Evaluation errors and disagreements')
    body += p('<strong>判对成败，不代表找对了失败原因。</strong><a href="#robo-case-33">拿刀案例</a>的两种回答都判为失败，但零样本只指出“没有抓住刀”，ICL 则指出“拿到的是勺子”；<a href="#robo-case-55">旋钮案例</a>也出现了失败标签正确、解释却与参考原因不同的情况。成败标签回答结果是否符合要求，错误对象、位置或未完成释放等信息，才可能帮助纠正行为，因此分类准确率不能代替原因评价。<a href="#progress-icl">开瓶</a>与<a href="#pencil-case-case">笔袋</a>的分歧则涉及更前面的状态识别：瓶盖是否分离、拉链是否打开，应与评价标准的分歧区分。', '<strong>Getting the outcome right does not mean identifying the right failure reason.</strong> Both responses in the <a href="#robo-case-33">knife case</a> identify failure, but zero-shot only reports a failed knife grasp, whereas ICL identifies a spoon. The <a href="#robo-case-55">knob case</a> likewise has a correct failure label with an explanation that differs from the reference. Outcome labels indicate whether requirements were met; details such as the wrong object, position, or an incomplete release may help correct behavior. Classification accuracy therefore cannot substitute for evaluating failure reasons. The <a href="#progress-icl">bottle</a> and <a href="#pencil-case-case">pencil-case</a> disagreements concern an earlier step—whether the cap has separated or the zipper is open—and should be distinguished from disagreements over evaluation criteria.')
    body += p('<strong>任务要求没有说清，也会造成评价分歧。</strong><a href="#robo-case-49">放碗问题</a>没有指定目标物体，参考却按对象错误判失败；<a href="#separate-cups-case">分杯案例</a>中，模型注意到了释放和侧倒，却作出与参考不同的选择；<a href="#green-bin-case">绿桶案例</a>还涉及开口幅度、释放与稳定保持。前者缺少目标信息，后两者需要明确质量要求及其优先级。评价模型既要看清执行，也要知道哪些状态必须满足、哪些只是更好的执行方式。Rubric 可分别评价对象、目标状态、释放和稳定性，再按预先明确的要求形成总体判断；不能从标签分歧反推标注者的权重。', '<strong>Unclear task requirements can also lead to disagreements.</strong> The <a href="#robo-case-49">bowl question</a> omits the target object, yet the reference marks failure for using the wrong one. In <a href="#separate-cups-case">cup separation</a>, the model notices both release and tipping but chooses differently from the reference. The <a href="#green-bin-case">green-bin case</a> involves opening width, release, and stability. The first lacks target information; the latter two require explicit quality criteria and priorities. An evaluator needs to know which states are mandatory and which merely indicate better execution. A rubric can assess the object, target state, release, and stability separately before applying predefined requirements to an overall judgment. Annotator weights cannot be inferred from label disagreements alone.')
    body += p('<strong>加入示例后，一些错误减少了，另一些却增加了。</strong>排序中的加权反序比例从 4.78% 降至 3.68%，平分却从 8.78% 升至 13.11%，最终 τa 下降：顺序排反更少，却更常未能区分质量等级。RoboFail 中，成功被误判为失败从 18 个降至 2 个，失败漏检却从 2 个增至 6 个。这提出了“示例是否改变评分尺度或成败判定倾向”的问题，尚不能确定变化机制。进度评测中还有 11 条轨迹的 VOC 提高而时间参照 MSE 变差；两者均以时间为参照，不能据此判断语义进度是否更准确。综合 ROUGE-L 的增量同样应按组成解释，本研究中主要来自成功识别。', '<strong>Adding examples reduces some errors but increases others.</strong> Weighted ranking inversions fall from 4.78% to 3.68%, but ties rise from 8.78% to 13.11% and τa declines: fewer orders are reversed, yet more quality differences go unresolved. On RoboFail, successes labeled as failures fall from 18 to 2, while missed failures rise from 2 to 6. This raises the question of whether examples change the scoring scale or the tendency to judge success; the mechanism remains undetermined. In progress evaluation, 11 trajectories also have higher VOC but worse time-reference MSE. Both use time as the reference, so this does not establish whether semantic progress is more accurate. Composite ROUGE-L gains likewise need to be interpreted by component; here, most come from success recognition.')
    body += h3('limitations', '3.3 局限与未来工作', '3.3 Limitations and future work')
    body += p('本研究仅在 RBM 和 RoboFail 两个基准上开展验证，数据与任务覆盖有限。作为对照的专用模型通常针对这些基准所考察的评价任务进行了专门设计。目前仍缺乏跨数据集、跨任务和跨机器人平台的大范围验证。', 'This study evaluates models on only two benchmarks, RBM and RoboFail, with limited data and task coverage. The specialized baselines are typically designed specifically for the evaluation tasks covered by these benchmarks. Broad validation across datasets, tasks, and robot platforms is still lacking.')
    body += p('<strong id="next-steps">强化学习验证。</strong>下一步将比较直接使用校准后的进度或成败奖励，以及用轨迹偏好训练奖励模型两条路径。固定策略初始化、训练算法与交互预算，与稀疏环境奖励及专用 critic 对照，报告多随机种子下的成功率、样本效率和调用成本；由独立环境标准或人工复核判定成功，并检查新策略是否利用伪完成状态等评价漏洞。本文尚未开展这些闭环实验，不报告策略提升。', '<strong id="next-steps">Reinforcement-learning validation.</strong> We will compare calibrated progress or outcome rewards with reward models trained from trajectory preferences. With policy initialization, algorithms, and interaction budgets fixed, we will compare against sparse environment rewards and specialized critics, reporting success, sample efficiency, and query costs across seeds. Independent environment criteria or human review will determine success, while checks for reward exploitation will examine apparent completion and other critic errors. These closed-loop experiments have not yet been conducted; this article reports no policy gains.')
    out += section('outlook', '3. 讨论与展望', '3. Discussion and outlook', body)
    out += resources()
    return out

def resources():
    body = SUPPLEMENT_PROTOCOL + p('<a href="assets/Beyond-the-Score.pdf">技术报告 ↗</a> · <a href="evidence.html">案例与逐步预测 ↗</a>', '<a href="assets/Beyond-the-Score.pdf">Technical report ↗</a> · <a href="evidence.html">Cases and step-by-step predictions ↗</a>')
    def reference_item(ref):
        note = ref['publication']
        if note == 'model-documentation':
            note = t('模型文档。', 'Model documentation.')
        return (f'<li id="ref-{ref["key"]}">{escape(ref["authors"].rstrip("."))}. '
                f'<a href="{escape(ref["url"], quote=True)}" target="_blank" rel="noopener">'
                f'{escape(ref["title"])}.</a> {escape(note)}</li>')
    body += '<ol class="references">' + ''.join(
        reference_item(ref) for ref in REFERENCES['references'] if ref['group'] == 'main') + '</ol>'
    body += detail('其他方法文献', 'Additional method references', '<ul class="references">' + ''.join(
        reference_item(ref) for ref in REFERENCES['references'] if ref['group'] == 'additional') + '</ul>')
    references = section('resources', '参考文献', 'References', body)
    bibtex = (ROOT / 'CITATION.bib').read_text().strip()
    citation = p('引用本文：', 'To cite this article:')
    citation += '<pre class="citation-block" tabindex="0" aria-label="BibTeX"><code>' + escape(bibtex) + '</code></pre>'
    return references + section('citation', '引用本文', 'Citation', citation)


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
    title = model_label(DATA['source']['title'])
    description = t('机器人轨迹质量、进度估计与失败诊断：gpt-6-astra 的离线评估结果、上下文示例分析与研究局限。', 'Offline evaluations of gpt-6-astra as a robot critic: trajectory quality, progress estimation, failure diagnosis, context examples, and limitations.')
    items = [
        ('takeaways', 'Key takeaways', 'Key takeaways', False), ('overview','Introduction','Introduction',False),
        ('setup','1. 研究设置','1. Study design',False),
        ('benchmark-choice','1.1 评价任务与数据集','1.1 Tasks and benchmarks',True), ('comparison-protocol','1.2 模型配置与评测条件','1.2 Configurations and conditions',True),
        ('results','2. 结果','2. Results',False),
        ('quality-results','2.1 轨迹质量与偏好','2.1 Quality and preference',True),
        ('progress-results','2.2 任务进度估计','2.2 Task progress estimation',True),
        ('failure','2.3 子任务成败判断','2.3 Subtask classification',True),
        ('explanations','2.4 失败解释与得分','2.4 Explanations and scores',True),
        ('outlook','3. 讨论与展望','3. Discussion and outlook',False), ('conclusions','3.1 主要发现','3.1 Main findings',True), ('failure-modes','3.2 评价错误与分歧','3.2 Evaluation errors and disagreements',True), ('limitations','3.3 局限与未来工作','3.3 Limitations and future work',True),
        ('resources','参考文献','References',False), ('citation','引用本文','Citation',False),
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
<h1><span class="title-name">Beyond the Score</span><span class="title-description">Early Evaluations of gpt-6-astra as a Robot Critic</span></h1>
<div class="author-block"><p class="authors">{authors}</p><p class="organization">{PUB['organization']}</p></div>
<div class="publication-links" aria-label="{t('研究材料','Research materials')}"><span class="unreleased">Code <small>(coming soon)</small></span><span class="unreleased">arXiv <small>(coming soon)</small></span></div></header>
{article()}
</article></div></main><footer class="footer wrap"><a class="brand" href="#top">SIMPLE<span>·AI</span></a><span>Beyond the Score · 2026</span><a href="#top">{t('返回顶部','Back to top')} ↑</a></footer>
<dialog id="figure-modal" aria-label="{t('图表大图','Expanded figure')}"><button id="close-figure" type="button" aria-label="{t('关闭大图','Close figure')}">×</button><img id="expanded-figure" alt=""><p id="figure-description"></p></dialog>
</body></html>'''

if __name__ == '__main__':
    for LANG, name in [('zh','index.html'),('en','en.html')]:
        content = reserve_image_space(citations(render()))
        counts = {'figcaption': [0, 0], 'caption': [0, 0]}
        detail_depth = [0]
        def number_caption(match):
            token = match.group(0)
            if token.startswith('<details'):
                detail_depth[0] += 1
                return token
            if token == '</details>':
                detail_depth[0] -= 1
                return token
            tag = match.group(1)
            folded = int(detail_depth[0] > 0)
            counts[tag][folded] += 1
            label = t('图', 'Figure') if tag == 'figcaption' else t('表', 'Table')
            number = ('S' if folded else '') + str(counts[tag][folded])
            text = re.sub(r'^(?:图|表|Figure|Table)\s*S?\d+[.。]\s*', '', match.group(2))
            return f'<{tag}>{label} {number}. {text}</{tag}>'
        content = re.sub(r'<details\b[^>]*>|</details>|<(figcaption|caption)>(.*?)</\1>', number_caption, content, flags=re.S)
        content = content.replace('><', '>\n<')
        (ROOT / name).write_text(content)
        print(f'Built {name}: {len(content.encode())} bytes')
