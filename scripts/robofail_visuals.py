"""Render RoboFail cases and their stored observation comparisons."""
from html import escape


def outcome(case, response, t):
    failure = response['answer'].strip().lower().startswith('no')
    if failure == (case['reference_label'] == 'Failure'):
        return t('判断正确', 'Correct judgment')
    return t('误报', 'False alarm') if failure else t('漏检', 'Missed failure')


def expanded_cases(cases, t, ids, fold=True):
    notes = {
        55: ('抓取炉灶旋钮', 'Grasping the stove knob',
             '参考答案为失败：夹爪未闭合。零样本判为失败，理由是抓取位置不对；五示例条件判为成功。',
             'The reference identifies failure because the gripper does not close. Zero-shot predicts failure but cites grasp location; the five-example condition predicts success.'),
        36: ('切胡萝卜', 'Slicing a carrot',
             '参考答案为成功；零样本和五示例条件均因未看到分离的切片而判为失败。',
             'The reference labels success; both zero-shot and five-example conditions predict failure because no separated slice is visible.'),
        50: ('按咖啡机按钮', 'Pressing the coffee-machine button',
             '零样本因未看到激活迹象而判为失败，五示例回答则与成功标签一致。',
             'Zero-shot predicts failure because activation is not visible; the five-example response matches the success label.'),
        33: ('拿刀时的对象错误', 'Picking up a knife: identifying the wrong object',
             '参考答案将这次失败归因于操作对象错误。',
             'The reference attributes this failure to manipulating the wrong object.'),
        2: ('抓取苹果', 'Picking up an apple',
            '两种条件都正确识别了抓取成功。',
            'Both conditions correctly recognize a successful grasp.'),
        49: ('放碗时的对象要求', 'Placing in a bowl: an unspecified target object',
             '参考答案将失败归因于对象错误。零样本却解释为草莓尚未释放，五示例回答放置成功。输入问题只写“放入碗中”，没有指定应放哪个对象。',
             'The reference attributes failure to the wrong object. Zero-shot instead cites an unreleased strawberry, while the five-example response calls placement successful. The input question says only “place in the bowl,” without specifying the object.'),
    }
    out = '<div class="robofail-extra">'
    for ident in ids:
        c = next(c for c in cases if c['id'] == ident)
        zh, en, zh_note, en_note = notes[ident]
        out += f'<article class="robo-expanded-case" id="robo-case-{ident}"><h4 class="case-title">' + t('Case Study：', 'Case Study: ') + escape(t(zh, en)) + '</h4><p>' + t(zh_note, en_note) + '</p>'
        out += f'<div class="case-video-grid"><figure><video controls playsinline muted preload="none" src="{c["video"]}" poster="{c["poster"]}" aria-label="{escape(c["task"])}"></video><figcaption>' + t('原始轨迹', 'Original trajectory') + '</figcaption></figure>'
        out += f'<figure><button type="button" data-zoom aria-label="{t("放大观测帧", "Enlarge observations")}"><img loading="lazy" src="{c["observation_contact_sheet"]}" alt="{t("按时间排列的模型输入观测", "Model observations in temporal order")}"></button><figcaption>' + t('模型输入的关键帧', 'Keyframes supplied to the model') + '</figcaption></figure></div>'
        if fold:
            out += '<details class="method-detail"><summary>' + t('查看输入与模型回答', 'View input and model responses') + '</summary>'
        out += '<p><strong>' + t('参考答案', 'Reference answer') + ' · ' + (t('失败', 'Failure') if c['reference_label']=='Failure' else t('成功', 'Success')) + f'</strong></p><blockquote lang="en">{escape(c["ground_truth"])}</blockquote>'
        for i, r in enumerate(c['responses']):
            out += '<p><strong>' + (t('零样本', 'Zero-shot') if i == 0 else t('五示例', 'Five examples')) + ' · ' + outcome(c, r, t) + f'</strong></p><blockquote lang="en">{escape(r["answer"])}</blockquote>'
        out += f'<p><a href="{c["original_input_image"]}" target="_blank" rel="noopener">' + t('原始输入拼图 ↗', 'Original input montage ↗') + f'</a></p><p lang="en">{escape(c["question"].removeprefix("<image>").strip())}</p>'
        if ident in (55,36):
            alias = ' id="robofail-keyframe-gifs"' if ident == 55 else ''
            out += f'<p{alias}><a href="assets/robofail/case-{ident:03d}-keyframes.gif">' + t('关键帧回放 ↗', 'Keyframe replay ↗') + '</a></p>'
        if fold:
            out += '</details>'
        out += '</article>'
    return out + '</div>'


def visibility_experiment(data, cases, t):
    if not data or data['completed'] != data['planned']:
        return ''
    out = '<div class="visibility-study"><h3 id="robofail-visibility" data-toc>' + t('2.3.3 上下文学习（ICL）', '2.3.3 In-context learning (ICL)') + '</h3>'
    out += '<p>' + t('我们在待评子任务之前提供五个固定的外部示例，每个示例包含图像、子任务问题和参考答案，再让模型对待评子任务输出成败判断及文字解释。零样本条件不提供这些示例。', 'We provide five fixed external demonstrations before the test subtask, each consisting of an image, a subtask question, and a reference answer. The model then judges the test subtask’s success or failure and provides a textual explanation; the zero-shot condition omits these demonstrations.') + '</p>'
    out += '<p><strong>' + t('五示例条件减少了成功误报，但仍会漏掉失败。', 'The five-example condition produces fewer false alarms but still misses failures.') + '</strong>' + t('成功误报由 18 个降至 2 个，失败漏检由 2 个增至 6 个。旋钮和切片两例还比较了前 1 帧、前 2 帧与全部观测，每个条件请求一次。', 'False alarms fall from 18 to 2, while missed failures rise from 2 to 6. The knob and slicing cases also compare the first frame, first two frames, and all observations, with one request per condition.') + '</p>'
    for idx in data['protocol']['case_ids']:
        case = next(c for c in cases if c['id'] == idx)
        rows = [r for r in data['results'] if r['case_id'] == idx]
        levels = sorted({r['visible_frames'] for r in rows})
        out += '<article class="visibility-case">' + expanded_cases(cases,t,ids=(idx,))
        out += '<div class="visibility-matrix" role="group" aria-label="' + t('各条件的模型回答', 'Model responses by condition') + '"><span></span>'
        for n in levels:
            out += '<strong>' + (t('全部 ', 'All ') if n == rows[0]['total_frames'] else '') + str(n) + t(' 帧',' frames') + '</strong>'
        for condition in ('zero','external5'):
            out += '<strong>' + (t('零样本','Zero-shot') if condition=='zero' else t('五示例','Five examples')) + '</strong>'
            for n in levels:
                r = next(r for r in rows if r['condition']==condition and r['visible_frames']==n)
                out += f'<span class="visibility-label {r["label"]}">' + (t('成功','Success') if r['label']=='yes' else t('失败','Failure') if r['label']=='no' else t('未解析','Unparsed')) + '</span>'
        out += '</div>'
        if idx==55:
            out += '<p>' + t('五示例回答在前 1、2 帧时均为失败，看到全部 4 帧后改为成功；零样本在三种观测条件下均回答失败。', 'With five examples, the response changes from failure with one or two frames to success with all four. Zero-shot predicts failure at all three observation levels.') + '</p>'
        else:
            out += '<p>' + t('从 1 帧到全部 3 帧，两种条件始终回答失败，与成功标签不符。', 'From one frame to all three, both conditions consistently predict failure, disagreeing with the success label.') + '</p>'
        out += '<details class="research-detail visibility-response"><summary>' + t('查看不同帧数下的输入与回答','View inputs and responses at each frame count') + '</summary>'
        for n in levels:
            selected=[r for r in rows if r['visible_frames']==n]
            out += '<p><strong>'+str(n)+t(' 帧',' frames')+'</strong></p>'
            out += f'<div class="experiment-input" tabindex="0" role="region" aria-label="{t("横向滚动查看输入","Scroll horizontally through the input")}"><a href="{selected[0]["image"]}" target="_blank" rel="noopener"><img loading="lazy" src="{selected[0]["image"]}" alt="{t("该条件的输入拼图","Input montage for this condition")}"></a></div>'
            for r in selected:
                out += '<p><strong>'+(t('零样本','Zero-shot') if r['condition']=='zero' else t('五示例','Five examples'))+f'</strong></p><blockquote lang="en">{escape(r["answer"])}</blockquote>'
        out += '</details></article>'
    out += '<p class="fine"><a href="data/robofail-visibility.json" download>' + t('完整观测对照记录 ↓', 'Complete observation-comparison records ↓') + '</a></p></div>'
    return out
