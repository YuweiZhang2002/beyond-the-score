"""Render additional source-grounded RoboFail illustrations and fresh experiments."""
from html import escape


def outcome(case, response, t):
    failure = response["answer"].strip().lower().startswith("no")
    if failure == (case["reference_label"] == "Failure"):
        return t("标签一致", "Label matches")
    return t("误报", "False alarm") if failure else t("漏检", "Missed failure")


def expanded_cases(cases, t, ids):
    """Render each selected case once, under its relevant evaluation question."""
    added = [next(c for c in cases if c["id"] == ident) for ident in ids]
    out = '<div class="robofail-extra">'
    notes = {
        55: ("抓取炉灶旋钮", "Grasp the stove knob",
             "参考判为失败，原因是夹爪未闭合。原测评中，零样本判失败但强调抓取位置，五示例条件则判成功。下面比较减少观测后，两种条件的判断是否改变。",
             "The reference labels a failure because the gripper does not close. In the original evaluation, zero-shot predicts failure but emphasizes grasp location; five-shot predicts success. Below, we examine how these judgments change when observations are withheld."),
        36: ("切胡萝卜", "Slice the carrot",
             "参考判为成功，原测评的两种条件却都以未看到分离的切片为由判失败。下面检查这一分歧是否随着观测补全而消失。",
             "The reference labels success, but both original conditions predict failure because they do not see a separated slice. Below, we examine whether the disagreement disappears with the full observations."),
        50: ("按咖啡机按钮：误报得到纠正", "Coffee-machine button: a corrected false alarm",
             "零样本将缺少可见激活迹象解释为失败，5-shot 则给出与公开成功标签一致的判断。这个例子展示成功识别的改善，但不能单凭回答确定按钮实际接触或机器内部状态。",
             "Zero-shot treats the absence of visible activation as failure; five-shot agrees with the released success label. This illustrates improved success recognition, without establishing button contact or the machine's internal state from the answer alone."),
        33: ("拿刀：相同失败标签，不同原因", "Picking up a knife: the same failure label, different reasons",
             "两个条件都识别出失败，但零样本解释为未抓住刀，5-shot 则指出拿了勺子而不是刀，后者与参考中的“操作对象错误”更直接对应。标签一致并不意味着解释相同。",
             "Both conditions detect failure. Zero-shot describes a failed knife grasp, whereas five-shot names a spoon instead of the knife, corresponding more directly to the reference's wrong-object explanation. Agreement on the label does not imply agreement on the reason."),
        2: ("抓取苹果：共同识别成功", "Picking up an apple: agreement on success",
            "两种条件都回答成功，与该子任务的公开标签一致。该例提供一个正确成功判断的对照；它只涉及当前抓取子任务，不代表整个后续轨迹成功。",
            "Both conditions answer success, matching the released subtask label. This is a correct-success contrast case; it concerns the current grasp, not the success of the entire subsequent trajectory."),
        49: ("放入碗中：识别动作仍可能漏掉任务错误", "Placing in a bowl: recognizing an action can still miss a task error",
             "参考将失败归因于操作对象错误。零样本虽回答失败，却解释为尚未释放草莓；5-shot 回答放置成功，从而漏掉公开失败标签。但问题只写“放入碗中”，没有明确应放哪个对象；因此，这个分歧还涉及任务信息是否充分，不能只归为视觉辨识错误。",
             "The reference attributes failure to the wrong object. Zero-shot predicts failure but cites an unreleased strawberry; five-shot calls the placement successful and misses the released failure label. However, the question only says “place in the bowl” without specifying the required object. The disagreement also concerns whether the task information is sufficient, rather than visual recognition alone."),
    }
    for c in added:
        note = notes.get(c["id"], (c["task"], c["task"], "", ""))
        out += f'<article class="robo-expanded-case" id="robo-case-{c["id"]}"><h4>{escape(t(note[0],note[1]))}</h4><p>{escape(t(note[2],note[3]))}</p><div class="case-video-grid">'
        out += f'<figure><video controls playsinline muted preload="none" src="{c["video"]}" poster="{c["poster"]}" aria-label="{escape(c["task"])}"></video><figcaption>'
        out += t("原始轨迹回放，保持原速；该连续视频未输入模型。", "Source episode replay at original speed; this continuous video was not supplied to the model.") + "</figcaption></figure>"
        out += f'<figure><button type="button" data-zoom aria-label="{t("放大观测帧","Enlarge observed frames")}"><img loading="lazy" src="{c["observation_contact_sheet"]}" alt="{t("实际输入中的可见观测帧，按时间排序","Visible observations from the actual input, in temporal order")}"></button><figcaption>' + t("输入观测帧，按原顺序展示；为便于阅读重新排版，完整原图见下方。", "Observed input tiles in original order, rearranged for readability; the exact montage is linked below.") + "</figcaption></figure></div>"
        out += '<details class="method-detail"><summary>' + t("参考答案与两种条件的模型原文", "Reference and original responses under both conditions") + "</summary>"
        out += "<p><strong>" + t("公开参考", "Released reference") + f' · {t("失败", "Failure") if c["reference_label"]=="Failure" else t("成功","Success")}</strong></p><blockquote lang="en">{escape(c["ground_truth"])}</blockquote>'
        for i, r in enumerate(c["responses"]):
            out += "<p><strong>" + (t("零样本", "Zero-shot") if i == 0 else t("外部 5-shot", "External 5-shot")) + " · " + outcome(c, r, t) + f'</strong></p><blockquote lang="en">{escape(r["answer"])}</blockquote>'
        out += "</details>"
        out += f'<details class="research-detail"><summary>{t("原始输入与证据边界", "Exact input and evidence boundary")}</summary><p><a class="inline-link" href="{c["original_input_image"]}" target="_blank" rel="noopener">{t("查看完整原始输入拼图", "Open the exact original input montage")} ↗</a></p><p lang="en">{escape(c["question"].removeprefix("<image>").strip())}</p><p>'
        out += t("视频对应关系通过观测帧的像素匹配与视觉检查核验。关键帧位置不是人工失败区间，也不是模型报警时间；模型解释不构成独立的物理原因验证。", "Video identity was checked by pixel matching and visual inspection. Observation positions are neither human failure intervals nor model alarm times. Model explanations do not independently verify physical causes.") + "</p></details>"
        if c["id"] in (55, 36):
            gif = f'assets/robofail/case-{c["id"]:03d}-keyframes.gif'
            alias = ' id="robofail-keyframe-gifs"' if c["id"] == 55 else ''
            out += f'<details class="method-detail"{alias}><summary>' + t("查看评测关键帧动图", "View the evaluation-keyframe GIF") + f'</summary><img loading="lazy" src="{gif}" alt="{escape(c["task"])}"><p class="fine">' + t("按输入顺序每秒回放一帧；回放时长不代表执行时间。", "Input frames replay in order at one frame per second; playback duration is not execution time.") + '</p></details>'
        out += "</article>"
    return out + "</div>"


def visibility_experiment(data, cases, t):
    if not data or data["completed"] != data["planned"]:
        return ""
    out = '<div class="visibility-study"><h3 id="robofail-visibility" data-toc>' + t("2.3.3 补充观测能否改善判断？", "2.3.3 Do additional observations improve judgments?") + "</h3>"
    out += "<p>" + t("我们进一步对旋钮抓取与胡萝卜切片两例进行观测遮蔽。每例分别保留前 1 帧、前 2 帧或全部观测，在零样本与相同的五示例条件下各请求一次，共 12 次新回答；以下将原测评案例与这组对照放在一起。", "We further vary the visible observations for knob grasping and carrot slicing. Each case retains the first frame, first two frames, or all observations, with one new request under each zero-shot and five-example condition: 12 responses in total. Each original evaluation case is presented together with this comparison.") + "</p>"
    out += '<p class="fine">' + t("遮蔽条件沿用原来的回顾性问题，少帧输入没有对应的时间级真值，因此只比较回答，不计算准确率。每条件仅一次请求，不能据此确定观测量变化的因果效应。", "Withheld-frame conditions retain the original retrospective question and have no time-specific ground truth, so we compare responses without scoring accuracy. One request per condition does not establish a causal effect of observation count.") + "</p>"
    for idx in data["protocol"]["case_ids"]:
        case = next(c for c in cases if c["id"] == idx)
        rows = [r for r in data["results"] if r["case_id"] == idx]
        levels = sorted({r["visible_frames"] for r in rows})
        task = t("抓取炉灶旋钮", "Grasp the stove knob") if idx == 55 else t("切胡萝卜", "Slice the carrot") if idx == 36 else case["task"]
        out += '<article class="visibility-case">' + expanded_cases(cases, t, ids=(idx,))
        out += '<div class="visibility-matrix" role="group" aria-label="' + t("各条件下的模型判断", "Model judgments by condition") + '"><span></span>'
        for n in levels:
            out += "<strong>" + (t("全部 ", "All ") if n == rows[0]["total_frames"] else "") + str(n) + t(" 帧", " frames") + "</strong>"
        for condition in ("zero", "external5"):
            out += "<strong>" + (t("零样本", "Zero-shot") if condition == "zero" else "5-shot") + "</strong>"
            for n in levels:
                r = next(r for r in rows if r["condition"] == condition and r["visible_frames"] == n)
                out += f'<span class="visibility-label {r["label"]}">' + (t("成功", "Success") if r["label"] == "yes" else t("失败", "Failure") if r["label"] == "no" else t("未解析", "Unparsed")) + "</span>"
        out += "</div><p class=\"fine\">" + t("颜色仅表示模型回答“成功”或“失败”，不表示回答正确与否。", "Colors indicate the predicted outcome, not whether the answer is correct.") + "</p>"
        if idx == 55:
            out += "<p>" + t("旋钮抓取：零样本在 1、2、4 帧条件下均回答失败；5-shot 在前两种条件下回答失败，却在看到全部 4 帧后回答成功。全部帧条件下的 5-shot 回答再次漏掉了公开参考中的失败。这个案例提示，增加画面不一定伴随更可靠的最终判断。", "Knob grasping: zero-shot answers failure with 1, 2, and 4 frames. Five-shot answers failure with 1 and 2 frames, then success with all 4. Its full-visibility answer again misses the failure in the released reference. In this case, more observations do not coincide with a more reliable final judgment.") + "</p>"
        elif idx == 36:
            out += "<p>" + t("胡萝卜切片：两种提示条件在 1、2、3 帧下均回答失败。即使补足全部观测，两个回答仍与公开成功标签不符；这一误报没有在本次请求中随着画面补全而消失。模型解释主要诉诸“没有看到分离的切片”，但这并不能独立证明参考标注错误。", "Carrot slicing: both prompting conditions answer failure with 1, 2, and 3 frames. Even at full visibility, both disagree with the released success label; adding the remaining observations does not remove this false alarm in these calls. The explanations emphasize the absence of a visibly separated slice, which does not independently establish that the reference is wrong.") + "</p>"
        for n in levels:
            selected = [r for r in rows if r["visible_frames"] == n]
            out += '<details class="research-detail visibility-response"' + "><summary>" + str(n) + t(" 帧：输入与两种条件的模型原文", " frames: input and both original responses") + "</summary>"
            out += f'<div class="experiment-input" tabindex="0" role="region" aria-label="{t("横向滚动查看实验输入","Scroll horizontally through the experimental input")}"><a href="{selected[0]["image"]}" target="_blank" rel="noopener"><img loading="lazy" src="{selected[0]["image"]}" alt="{t("未提供的后续观测帧以白色遮蔽；点击查看原尺寸","Withheld later observations are white; click for full resolution")}"></a></div>'
            for r in selected:
                out += "<p><strong>" + (t("零样本", "Zero-shot") if r["condition"] == "zero" else "External 5-shot") + f'</strong></p><blockquote lang="en">{escape(r["answer"])}</blockquote><p class="fine">' + t("返回模型标识：", "Returned model label: ") + escape(r["returned_model"]) + "</p>"
            out += "</details>"
        out += "</article>"
    out += "<p>" + t("这一小规模实验展示同一问题在不同证据量下的回答，而非提供新的基准排名。全部帧的新回答也可能与先前测评不同；采样变化及中转后端差异仍然存在。", "This small experiment shows answers under different amounts of evidence rather than a new benchmark ranking. Fresh full-input responses can also differ from earlier evaluations; sampling variation and relay-backend differences remain possible.") + "</p>"
    out += '<details class="research-detail"><summary>' + t("实验协议与完整记录", "Protocol and complete records") + "</summary><p>" + t("只将未提供的后续观测格置白；保留画布大小、格子位置、原始问题和五个外部示例。所有变体均将原 JPEG 解码后无损保存为 PNG，可见像素不变。未向模型提供测试答案或文件名。不因回答内容或质量重试。", "Only withheld later observation tiles are made white. Canvas size, tile positions, the original question, and five external demonstrations are retained. Every variant is a lossless PNG of decoded JPEG pixels. Neither the test answer nor its filename is sent. No answer-quality retries are performed.") + '</p><p><a class="inline-link" href="data/robofail-visibility.json" download>' + t("下载实验协议、12 条原始回答与 token 用量", "Download protocol, 12 original answers, and token usage") + " ↓</a></p></details></div>"
    return out
