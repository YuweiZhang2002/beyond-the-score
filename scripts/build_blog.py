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
    'flora': (14, 'NVIDIA Flora-Rewarder'),
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
        [t('参考标签 → 模型判断', 'Reference → prediction'), t('零样本', 'Zero-shot'), t('五示例 ICL', 'Five-example ICL')],
        rows, t('同一组 57 个问题的成败判断：23 个成功，34 个失败。', 'Outcome judgments on the same 57 questions: 23 successes and 34 failures.')) + '</div>'

def rouge_chart():
    r = DATA['rouge_decomposition']
    out = '<div class="stack-key rouge-key">' + ''.join(f'<span><i></i>{x}</span>' for x in [t('正确成功项', 'Correct-success term'), t('失败解释项', 'Failure-explanation term')]) + '</div>'
    for i, label in enumerate([t('零样本', 'Zero-shot'), t('外部五示例', 'External five-example')]):
        values = [r['success_terms'][i], r['failure_explanation_terms'][i]]
        bars = ''.join(f'<span style="width:{v / .55 * 100}%">{v:.4f}</span>' for v in values)
        desc = f'{label}: {values[0]:.4f} + {values[1]:.4f}'
        out += f'<div class="stack-heading"><strong>{label}</strong><span>{t("综合得分", "Composite score")} {DATA["table7_robofail_errors"]["composite_rouge_l"][i]:.3f}</span></div><div class="rouge-stack" role="img" aria-label="{desc}">{bars}</div>'
    cap = t('图 6. 综合 ROUGE-L 的组成：正确成功项贡献了大部分增量。', 'Figure 6. Components of composite ROUGE-L: correct success judgments account for most of the gain.')
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
    protocol_details += p('<strong>RBM 排序协议。</strong>采用 RBM 的质量标签顺序与 Kendall τa 指标[[cite:robometer]]，本次运行包含 567 条轨迹、41 个来源–任务组。<a href="https://github.com/robometer/robometer/blob/main/robometer/data/samplers/eval/progress_policy_ranking.py" target="_blank" rel="noopener">官方采样器</a>按任务和质量标签选取轨迹，数量可配置；567 是本次运行的样本数，不是基准固定规模。', '<strong>RBM ranking protocol.</strong> We use RBM’s quality-label order and Kendall τa metric[[cite:robometer]], with 567 trajectories across 41 source–task groups in this run. The <a href="https://github.com/robometer/robometer/blob/main/robometer/data/samplers/eval/progress_policy_ranking.py" target="_blank" rel="noopener">official sampler</a> selects trajectories by task and quality label with configurable counts; 567 is this run’s sample count, not a fixed benchmark size.')
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
    protocol_details += p('<strong>结果来源。</strong>图中 [S] 为本研究，[P]、[W]、[R]、[A] 分别为 Robometer 论文、项目网站、RynnValue 与 AHA。RBM 排序与“不同质量”偏好沿用官方采样和指标规则；随机种子、模型接口与引用版本见 2.1.3。RoboFail 的文献对照使用不同问题集合，范围见 2.4。', '<strong>Result sources.</strong> Chart tags [S], [P], [W], [R], and [A] denote this study, the Robometer paper, its project website, RynnValue, and AHA. RBM ranking and different-quality preference follow official sampling and metric rules; Section 2.1.3 records seeds, model interfaces, and cited versions. RoboFail literature comparisons use different question sets, as described in Section 2.4.')

    protocol_details += '<div id="positive-case-protocol">' + p('<strong>案例对照。</strong>四组正例为评测后的说明性选例，不用于估计整体错误率。Astra 与 DeepSeek 使用相同任务、轨迹、提示和输入图像，不接收参考质量标签；偏好案例保留实际 A/B 顺序。两者推理配置与计算预算未匹配：Astra 为 low、输出上限 512 token，DeepSeek 为 max、上限 32768 token。未进行 A/B 交换复测，也没有匹配的 Robometer 逐条输出。', '<strong>Case comparisons.</strong> The four positive examples are selected post hoc for illustration, not to estimate overall error rates. Astra and DeepSeek receive identical tasks, trajectories, prompts, and input images without reference quality labels; preference cases retain the actual A/B order. Reasoning settings and compute budgets are unmatched: Astra uses low effort with a 512-token output limit, while DeepSeek uses max effort with a 32768-token limit. No swapped-order repeat or matched per-example Robometer output is available.') + '</div>'

    protocol_details += p('<strong>回放与曲线。</strong>2.1 的排序与偏好案例回放各轨迹的 8 张模型输入图像，每秒 1 张，封面取最后一张；新增正例在 32 张保存帧中的采样位置为 0 / 4 / 9 / 13 / 18 / 22 / 27 / 31。2.2 的进度案例将 32 张保存帧按每秒 4 帧回放，评分位置为 0 / 7 / 15 / 23 / 31；起点由协议设为 0，其余四点为模型预测。以上回放均非原速视频，采样位置不是秒数。曲线连线仅辅助阅读，中间位置没有额外预测或人工标注。', '<strong>Replays and curves.</strong> Ranking and preference cases in Section 2.1 replay eight model-input images per trajectory at one image per second, using the last image as the poster. The added positive cases sample positions 0 / 4 / 9 / 13 / 18 / 22 / 27 / 31 from 32 stored frames. Progress cases in Section 2.2 replay 32 stored frames at four frames per second, with scores at positions 0 / 7 / 15 / 23 / 31. The initial zero is protocol-set; the other four points are predictions. These replays do not preserve original timing, and sample indices are not seconds. Lines guide the eye without adding predictions or human annotations between samples.')
    protocol_details += p('<strong>进度案例。</strong>正向案例从已有评分记录中事后选取，展示模型评分随观测的变化。其分数并非人工标注的完成率；当前公开材料没有这些轨迹上 DeepSeek 或 Robometer 的对应预测。', '<strong>Progress cases.</strong> Positive cases are selected post hoc from existing scoring records to illustrate how predictions change with observations. Scores are not human-annotated completion percentages; the current public materials contain no matched DeepSeek or Robometer predictions for these trajectories.')

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
    body += p('结果显示，<strong>执行质量比较是 Astra 在本研究中表现突出的能力，但这种能力没有转化为同样可靠的完成判断和失败诊断。</strong>零样本排序 Kendall τ<sub>a</sub> 达到 <strong>0.8166</strong>，高于专用模型 Robometer 的已报告数值 0.655[[cite:robometer]] 和 RynnValue-8B 的 0.675[[cite:rynnvalue]]；直接偏好准确率为 <strong>92.4%</strong>。在 RoboFail 上，零样本与五示例条件的准确率分别为 <strong>64.91% 和 85.96%</strong>，失败漏检却由 <strong>2 个增至 6 个</strong>；综合解释得分增量的 <strong>89.3%</strong> 来自正确成功项。因此，当前证据支持将 Astra 用于离线执行质量比较，但<strong>它仍会误判任务是否完成、漏掉真实失败；更高的解释总分也不足以证明失败原因诊断可靠</strong>。本文尚未验证这些评价能否带来策略学习或闭环执行的提升。', 'Our results identify <strong>execution-quality comparison as a strength of Astra in this study, but this ability does not translate into equally reliable completion judgments or failure diagnosis.</strong> Zero-shot ranking reaches Kendall τ<sub>a</sub> = <strong>0.8166</strong>, numerically above the published values of 0.655 for the specialized Robometer model[[cite:robometer]] and 0.675 for RynnValue-8B[[cite:rynnvalue]]; direct preference accuracy is <strong>92.4%</strong>. On RoboFail, zero-shot and five-example accuracy is <strong>64.91% and 85.96%</strong>, respectively, yet missed failures increase from <strong>2 to 6</strong>; <strong>89.3%</strong> of the composite explanation-score gain comes from correct success judgments. The evidence therefore supports Astra for offline execution-quality comparison, but <strong>it still misjudges completion and misses real failures, and higher composite explanation scores do not establish reliable diagnosis of failure causes</strong>. Whether these assessments improve policy learning or closed-loop execution remains untested.')
    out += section('overview', 'Introduction', 'Introduction', body)

    out += study_design()
    result_topics = ''


    body = p('我们使用 RBM 的机器人轨迹，比较通用多模态模型评价执行质量的能力。评测涵盖 GPT-6 Astra[[cite:astra]]、GPT-5.6-sol[[cite:sol]] 和 DeepSeek-V4.1-Flash[[cite:deepseek]]，包括对单条轨迹独立评分，以及同时观察两条轨迹后直接判断偏好。总体结果呈现三种模型的差异；案例分析以 Astra 为代表，检查评分和解释如何对应实际执行。', 'We use RBM robot trajectories to compare how general-purpose multimodal models evaluate execution quality. We test GPT-6 Astra[[cite:astra]], GPT-5.6-sol[[cite:sol]], and DeepSeek-V4.1-Flash[[cite:deepseek]] on independent trajectory scoring and direct preference judgments with two trajectories shown together. Aggregate results compare the three models; detailed cases use Astra as a representative to examine how scores and explanations relate to the observed executions.')
    body += p('以下呈现零样本结果；上下文示例对照见第 2.3 节。案例视频均为模型输入帧的回放，非原速视频。', 'We present zero-shot results here and compare context examples in Section 2.3. Case videos replay model-input frames, not original-speed video.', 'fine')
    body += h3('ranking-results', '2.1.1 轨迹质量排序', '2.1.1 Trajectory quality ranking')
    body += confirmed('ranking')
    body += h3('preference-results', '2.1.2 直接偏好判断', '2.1.2 Direct preference')
    body += confirmed('preference')
    body += h3('literature', '2.1.3 与已有工作的比较', '2.1.3 Comparison with prior work')
    body += p('<strong>通用多模态模型已表现出可与专用模型竞争的离线评价能力。</strong>在沿用 Robometer 官方采样与指标规则的评测中，Astra 的零样本排序 τa 为 0.8166、偏好准确率为 92.4%，高于 Robometer 报告的 0.655 和 82.5%[[cite:robometer]]；排序结果也高于 RynnValue-8B 的 0.675[[cite:rynnvalue]]。这些结果说明，通用模型在不追加本次任务专项训练的条件下，已能有效比较机器人执行质量。这里的结论针对离线评价，不等同于训练奖励的有效性。', '<strong>General-purpose multimodal models show competitive offline evaluation capability relative to specialized models.</strong> Under Robometer’s official sampling and metric rules, Astra achieves zero-shot ranking τa of 0.8166 and preference accuracy of 92.4%, above Robometer’s reported 0.655 and 82.5%[[cite:robometer]]; its ranking also exceeds RynnValue-8B’s reported 0.675[[cite:rynnvalue]]. These results show that general-purpose models can effectively compare robot execution quality without additional task-specific training for this evaluation. This conclusion concerns offline evaluation, not the effectiveness of their scores as training rewards.')
    body += p('<strong>评价标准的模糊性仍是两类模型都需要面对的问题。</strong>总体分数或偏好标签不能完整表达目标完成、操作约束与末态质量之间的区别。前述案例表明，当这些判据未被明确给出时，与参考不一致可能包含标准上的分歧，不能全部解释为模型能力不足。因此，对通用模型和专用模型的比较都需要更全面的评价体系：显式定义任务相关的 rubric，分别检查各项要求，再按统一规则汇总。这样的分析有助于区分感知错误、执行质量差异和判据权衡，而不是仅凭一个总分归因。', '<strong>Ambiguity in evaluation criteria remains a problem for both model classes.</strong> Overall scores and preference labels do not fully distinguish goal attainment, execution constraints, and final-state quality. The preceding cases show that, when these criteria are unspecified, reference disagreement may include differences in evaluative standards rather than model limitations alone. Comparing general-purpose and specialized models therefore requires a more comprehensive evaluation framework: explicit task-relevant rubrics, assessment of each requirement, and a common aggregation rule. This would help distinguish perceptual errors, differences in execution quality, and trade-offs among criteria instead of attributing them from a single score.')
    comparison_details = p('排序与“不同质量”偏好评测复用 Robometer 官方采样和指标规则，使用 seed=44。571 条缓存轨迹中，4 条属于仅含成功样本的任务，按官方规则排除后得到 567 条；偏好配对按每来源最多 500 对采样，共 1,192 对。两项指标均按六来源等权汇总。', 'Ranking and different-quality preference evaluation reuse Robometer’s official sampling and metric rules with seed=44. Of 571 cached trajectories, four belong to tasks with only successful examples and are excluded by the official rule, leaving 567. Preference sampling uses up to 500 pairs per source, yielding 1,192 pairs. Both metrics use equal weighting across the six sources.')
    comparison_details += p('当前官方默认 seed 为 42，原论文历史清单不可得，故不称为逐条样本复现。双方均匀取 8 帧；Astra 通过提示词输出评分或 A/B，Robometer 使用训练后的 progress/preference head，图像编码与内部处理不同。正文引用 Robometer v1 的 τa=0.655；v2 对应值约为 0.643。', 'The current official default seed is 42; the original paper’s historical manifests are unavailable, so this is not a sample-by-sample reproduction. Both sample eight frames uniformly. Astra returns prompted scores or A/B choices, whereas Robometer uses trained progress/preference heads, with different image encoding and internal processing. We cite Robometer v1’s τa=0.655; the corresponding v2 value is approximately 0.643.')
    body += detail('采样、指标与引用版本', 'Sampling, metrics, and cited versions', comparison_details)
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
    body += figure('assets/figures/04_robofail_icl.png', t('RoboFail 成败分类准确率：本研究与 AHA 报告结果', 'RoboFail outcome accuracy: this study and AHA-reported results'), t('成败分类准确率。文献结果来自 AHA 报告[[cite:aha]]，与本研究分组展示；具体问题集合尚未逐项对齐。', 'Outcome classification accuracy. Literature results are from the AHA report[[cite:aha]] and shown separately; exact question sets have not been matched item by item.'))
    body += diagnosis()
    body += p('两种条件返回的模型标识存在差异，后端快照一致性尚未确认，因此不能将全部差值归因于示例。', 'Returned model identifiers differ between conditions, and backend snapshot consistency is unconfirmed; the full difference cannot be attributed to the examples.', 'fine')
    error_details = p('误报率从 78.26% 降至 8.70%，漏检率从 5.88% 升至 17.65%，失败召回率从 94.12% 降至 82.35%。始终回答“失败”的标签分布参照准确率为 34 / 57 = 59.65%。这些结果是离线分类，不涉及在线报警时间或干预成本。', 'The false-alarm rate falls from 78.26% to 8.70%, while the miss rate rises from 5.88% to 17.65% and failure recall falls from 94.12% to 82.35%. An always-failure reference achieves 34 / 57 = 59.65% accuracy from the label distribution alone. These are offline classification results, without measurements of alarm timing or intervention costs.')
    error_details += p('五个外部示例与测试轨迹不重叠；这一条件不保证环境、机器人形态、近重复样本或预训练数据独立。两组请求使用相同模型名和推理配置，但返回的模型标识不同，仍需在固定后端下复核示例效应。', 'The five external demonstrations are disjoint from test trajectories; this does not establish independence of environments, embodiments, near-duplicates, or pretraining data. Requests use the same model name and reasoning configuration, but returned model identifiers differ. The effect of demonstrations therefore requires verification with a fixed backend.')
    body += detail('分类指标与示例设置', 'Classification metrics and demonstration setup', error_details)
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

    body = p('五示例条件的综合 ROUGE-L 从 0.185 升至 0.499，但约 <strong>89.3% 的增量来自成功子任务被正确识别</strong>。总分的增长主要反映成功识别的改善，不能等同于失败原因解释的同等进步。', 'Composite ROUGE-L rises from 0.185 to 0.499 with five examples, but about <strong>89.3% of the gain comes from correctly recognizing successful subtasks</strong>. Most of the gain reflects better success recognition, rather than an equivalent improvement in explanations of failure causes.')
    body += p('AHA 的综合评分规则[[cite:aha]]同时计入正确成功判断与失败解释的文本重合度，因此需要分开查看两项贡献。', 'AHA’s composite scoring rule[[cite:aha]] combines correct success judgments with textual overlap for failure explanations, so the two contributions need to be examined separately.')
    scoring_details = p('五示例条件的综合 ROUGE-L 从 0.185 增加到 0.499。这个指标不只衡量失败解释。按 AHA 评测规则[[cite:aha]]，正确成功回答计 1 分，正确失败回答按解释与参考答案的词干化 ROUGE-L F1 计分，成败标签错误则计 0 分。所有问题得分相加后除以 57。评分使用原始英文回答，不使用本文的中文转述。', 'Composite ROUGE-L rises from 0.185 to 0.499 in the five-example condition. This metric does not measure failure explanations alone. Under the AHA rules[[cite:aha]], a correct success answer receives 1; a correct failure receives stemmed ROUGE-L F1 against the reference explanation; and a label disagreement receives 0. Scores are summed and divided by 57. Evaluation uses the original English answers, not the Chinese paraphrases in this article.')
    scoring_details += f'<div class="formula" role="math" aria-label="{t("综合得分等于正确成功数加上正确失败的解释分数总和，再除以57", "Composite score equals correct successes plus summed explanation scores for correctly detected failures, divided by 57")}">R = ({t("正确成功数 + 正确失败的解释分数之和", "correct successes + summed explanation scores for correct failures")}) / 57</div>'
    body += figure('assets/figures/05_robofail_icl.png', t('包含 AHA 及其他 baseline 的综合 ROUGE-L 对比', 'Composite ROUGE-L including AHA and other baselines'), t('综合 ROUGE-L 对比；文献结果沿用各自协议。', 'Composite ROUGE-L comparison; literature results retain their own protocols.'))
    body += rouge_chart()
    scoring_details += p('正确成功项从 0.0877 增至 0.3684，增量约为 16 / 57 = 0.2807，占报告总增量 0.3144 的约 89.3%。失败解释项从 0.0969 增至 0.1305，占剩余约 10.7%。因此，0.499 不能读作“49.9% 的失败解释正确”；大部分增量来自识别成功，而非失败解释项。', 'The correct-success term rises from 0.0877 to 0.3684. Its increase, 16 / 57 ≈ 0.2807, accounts for about 89.3% of the reported total gain of 0.3144. The failure-explanation term rises from 0.0969 to 0.1305, accounting for the remaining 10.7%. A score of 0.499 therefore does not mean that 49.9% of failure explanations are correct. Most of the gain comes from recognizing success.')
    scoring_details += p('组成图的两条形使用相同的 0–0.55 刻度，两项均以 57 为分母。分项与总分分别取整，末位可能有舍入差异。', 'Both bars in the decomposition chart use the same 0–0.55 scale, with each component divided by 57. Components and totals are rounded separately and may differ in the last decimal.')
    body += detail('综合评分规则与分项计算', 'Composite scoring rule and component calculations', scoring_details)
    body += p('解释项还取决于哪些失败被检测到，以及回答与参考文本的词汇重合度。它无法独立区分语义正确的改写和措辞相似但原因错误的回答。要评价失败原因是否可信，需要额外的语义核验与物理证据。', 'The explanation term also depends on which failures are detected and on lexical overlap with reference text. It does not independently distinguish a correct paraphrase from a similarly worded but incorrect diagnosis. Assessing the stated cause requires additional semantic review and physical evidence.')
    body += p('前面的<a class="inline-link" href="#robofail-cases">抓旋钮与切片案例</a>具体展示了标签与解释需要分别检验。词汇重合度和总体分数的变化，都不能替代对单次判断所引证据的核查。', 'The earlier <a class="inline-link" href="#robofail-cases">knob and slicing cases</a> show why labels and explanations need separate review. Neither lexical overlap nor aggregate score changes replace checking the evidence cited for an individual judgment.')
    result_topics += result_section('explanations', '2.5 失败解释与得分', '2.5 Failure explanations and scores', body)
    out += section('results', '2. 结果', '2. Results', result_topics)

    body = h3('conclusions', '3.1 研究结论', '3.1 Findings')
    body += p('<strong>通用多模态模型能够提供有竞争力的机器人行为评价。</strong>在沿用官方采样与指标规则的 RBM 评测中，Astra 的排序 τa 为 0.8166、偏好准确率为 92.4%，均高于所引用的 Robometer 报告值；RoboFail 五示例条件的成败准确率达到 85.96%。这些结果表明，即使不针对本次任务进行额外微调，通用模型已有的视觉理解与推理能力也能支持较强的离线行为评价。', '<strong>General-purpose multimodal models can provide competitive evaluations of robot behavior.</strong> On RBM, using the official sampling and metric rules, Astra achieves a ranking τa of 0.8166 and preference accuracy of 92.4%, both above the cited Robometer results. On RoboFail, five-example outcome accuracy reaches 85.96%. These findings show that a general-purpose model’s existing visual understanding and reasoning capabilities can support strong offline behavior evaluation without additional fine-tuning for these tasks.')
    body += p('<strong>评价能力并不随示例或总体分数一致提高。</strong>加入示例后，进度 VOC 从 93.6 升至 94.2，排序 τa 却从 0.8166 降至 0.7953；RoboFail 五示例条件减少了成功误报，却增加了失败漏检。进度相关性较高仍可能伴随错误的终点估计，综合 ROUGE-L 的提高也主要来自成功识别。因而，当前结果支持使用这些模型比较离线行为，却不足以支持直接将其分数作为可靠的完成判定、失败解释或策略优化奖励。', '<strong>Examples and higher aggregate scores do not improve every aspect of evaluation.</strong> With examples, progress VOC rises from 93.6 to 94.2 while ranking τa falls from 0.8166 to 0.7953. The five-example RoboFail condition reduces false alarms on successful subtasks but misses more failures. High progress correlation can coexist with inaccurate endpoint estimates, and most of the composite ROUGE-L gain comes from success recognition. The results support comparing offline behavior with these models, but do not establish their scores as reliable completion checks, failure explanations, or policy-optimization rewards.')
    body += p('<strong>部分评价分歧需要通过明确判据来解决。</strong>任务描述未必规定释放、稳定性等终态要求，也未必规定多个质量维度的优先级。单一分数或偏好标签会压缩这些差异，使标准不一致与模型判断错误难以区分。后续评价应采用明确的多维 rubric，分别核对任务目标、过程约束与终态质量，并检验分项判断与独立标注的一致性。', '<strong>Some evaluation disagreements require more explicit criteria.</strong> Task descriptions may leave final-state requirements such as release and stability unspecified, as well as priorities among quality dimensions. A single score or preference label compresses these distinctions, making criterion mismatch difficult to separate from model error. Future evaluations should use explicit multidimensional rubrics for task goals, execution constraints, and final-state quality, and compare criterion-level judgments against independent annotations.')
    body += h3('limitations', '3.2 研究局限与未来工作', '3.2 Limitations and future work')
    body += p('本研究评价的是固定离线轨迹，模型覆盖与样本规模有限。57 个 RoboFail 问题来自 15 组轨迹，轨迹对也共享任务与样本；重复调用波动和抽样不确定性尚未量化。后续需要固定模型后端、控制示例选择，并在更多任务与独立样本上检验结果的稳定性。', 'This study evaluates fixed offline trajectories with limited model coverage and sample sizes. The 57 RoboFail questions come from 15 trajectory groups, and trajectory pairs share tasks and samples. Repeat-call variation and sampling uncertainty remain unquantified. Future work should fix model backends, control demonstration selection, and assess stability across more tasks and independent samples.')
    body += p('定性案例用于分析判断依据，不代表各类问题的发生频率。现有结果尚不能完全区分观测不足、评价标准歧义与模型错误。对有争议的案例，应通过多位标注者的独立复核和更明确的分项标准检验分歧；对接触、稳定性等仅靠图像难以确认的状态，则需结合额外视角或传感器证据。', 'Qualitative cases examine the evidence behind judgments rather than estimate how often each problem occurs. The results do not fully separate limited observations, ambiguous criteria, and model errors. Disputed cases call for independent review by multiple annotators and clearer criterion-level standards. Contact, stability, and other states that images alone cannot resolve may require additional viewpoints or sensor evidence.')
    body += '<h4 id="next-steps">' + t('强化学习验证：评价能力能否转化为策略提升？', 'Reinforcement learning: can evaluation capability improve a policy?') + '</h4>'
    body += p('下一步将检验两条路径：将经校准的进度或成败判断作为奖励，以及用轨迹偏好训练奖励模型后再优化策略。实验将固定策略初始化、训练算法与环境交互预算，与稀疏环境奖励和专用 critic 对照，报告多随机种子下的成功率、样本效率及模型调用成本。最终成功由独立于评价模型的环境标准或人工复核判定。', 'We will test two pathways: using calibrated progress or outcome judgments as rewards, and training a reward model from trajectory preferences before policy optimization. Experiments will fix policy initialization, training algorithms, and environment-interaction budgets, compare against sparse environment rewards and specialized critics, and report success rates, sample efficiency, and model-query costs across random seeds. Final success will be judged by environment criteria or human review independent of the evaluation model.')
    body += p('闭环验证还需检查策略分布变化与奖励利用：模型是否会给伪完成状态或无效行为高分，策略是否会主动利用这些错误。失败解释对恢复行为或数据选择的价值也需单独消融。本文尚未开展上述强化学习实验，因此不报告策略提升或样本效率收益。', 'Closed-loop validation must also examine distribution shifts and reward exploitation: whether apparent completion or ineffective behavior receives high scores, and whether policies learn to exploit these errors. The value of failure explanations for recovery or data selection requires separate ablations. These reinforcement-learning experiments have not yet been conducted, so this article reports no policy gains or sample-efficiency improvements.')
    out += section('outlook', '3. 讨论与展望', '3. Discussion and outlook', body)
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
        ('flora', 'https://huggingface.co/nvidia/Flora-Rewarder', 'NVIDIA. Flora-Rewarder', t('官方模型说明，rubric 分项评分接口。', 'Official model card; rubric scoring interface.')),
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
        ('outlook','3. 讨论与展望','3. Discussion and outlook',False), ('conclusions','3.1 研究结论','3.1 Findings',True), ('limitations','3.2 研究局限与未来工作','3.2 Limitations and future work',True),
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
