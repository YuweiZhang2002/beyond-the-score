"""Render additional source-grounded RoboFail illustrations and fresh experiments."""
from html import escape


def outcome(case, response, t):
    failure = response["answer"].strip().lower().startswith("no")
    if failure == (case["reference_label"] == "Failure"):
        return t("标签一致", "Label matches")
    return t("误报", "False alarm") if failure else t("漏检", "Missed failure")


def expanded_cases(cases, t):
    added = [c for c in cases if c["id"] not in (55, 36)]
    if not added:
        return ""
    out = '<div class="robofail-extra"><h3 id="robofail-gallery" data-toc>' + t("更多案例：从误报纠正到失败漏检", "More cases: corrected alarms and missed failures") + "</h3>"
    out += "<p>" + t("以下补充案例来自同一批已保存的 zero-shot 与外部 5-shot 测评。每例并排展示源视频、模型实际看到的观测帧、公开参考和模型原文。它们是事后挑选的定性案例，不改变 57 个问题的总体分数。", "These additional cases use the same saved zero-shot and external five-shot evaluations. Each pairs the source replay and observed input frames with the released reference and verbatim responses. They are post-hoc illustrations and do not change the aggregate scores on 57 questions.") + "</p>"
    notes = {
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
             "参考将失败归因于操作对象错误。零样本虽回答失败，却解释为尚未释放草莓；5-shot 回答放置成功，从而漏掉公开失败标签。这提示应把动作是否发生与任务对象是否正确分开核查。",
             "The reference attributes failure to the wrong object. Zero-shot predicts failure but cites an unreleased strawberry; five-shot calls the placement successful and misses the released failure label. Whether an action occurred and whether it involved the correct task object need separate checks."),
    }
    for c in added:
        note = notes.get(c["id"], (c["task"], c["task"], "", ""))
        out += f'<article class="robo-expanded-case" id="robo-case-{c["id"]}"><h4>{escape(t(note[0],note[1]))}</h4><p>{escape(t(note[2],note[3]))}</p><div class="robo-case-columns"><div>'
        out += f'<figure><video controls playsinline muted preload="none" src="{c["video"]}" poster="{c["poster"]}" aria-label="{escape(c["task"])}"></video><figcaption>'
        out += t("原始轨迹回放，保持原速；该连续视频未输入模型。", "Source episode replay at original speed; this continuous video was not supplied to the model.") + "</figcaption></figure>"
        out += f'<figure><button type="button" data-zoom aria-label="{t("放大观测帧","Enlarge observed frames")}"><img loading="lazy" src="{c["observation_contact_sheet"]}" alt="{t("实际输入中的可见观测帧，按时间排序","Visible observations from the actual input, in temporal order")}"></button><figcaption>' + t("输入观测帧，按原顺序展示；为便于阅读重新排版，完整原图见下方。", "Observed input tiles in original order, rearranged for readability; the exact montage is linked below.") + "</figcaption></figure></div><div>"
        out += "<p><strong>" + t("公开参考", "Released reference") + f' · {t("失败", "Failure") if c["reference_label"]=="Failure" else t("成功","Success")}</strong></p><blockquote lang="en">{escape(c["ground_truth"])}</blockquote>'
        for i, r in enumerate(c["responses"]):
            out += "<p><strong>" + (t("零样本", "Zero-shot") if i == 0 else t("外部 5-shot", "External 5-shot")) + " · " + outcome(c, r, t) + f'</strong></p><blockquote lang="en">{escape(r["answer"])}</blockquote>'
        out += "</div></div>"
        out += f'<details class="research-detail"><summary>{t("原始输入与证据边界", "Exact input and evidence boundary")}</summary><p><a class="inline-link" href="{c["original_input_image"]}" target="_blank" rel="noopener">{t("查看完整原始输入拼图", "Open the exact original input montage")} ↗</a></p><p lang="en">{escape(c["question"].removeprefix("<image>").strip())}</p><p>'
        out += t("视频对应关系通过观测帧的像素匹配与视觉检查核验。关键帧位置不是人工失败区间，也不是模型报警时间；模型解释不构成独立的物理原因验证。", "Video identity was checked by pixel matching and visual inspection. Observation positions are neither human failure intervals nor model alarm times. Model explanations do not independently verify physical causes.") + "</p></details></article>"
    return out + "</div>"


def visibility_experiment(data, cases, t):
    if not data or data["completed"] != data["planned"]:
        return ""
    out = '<div class="visibility-study"><h3 id="robofail-visibility" data-toc>' + t("补充实验：可见证据如何影响判断？", "Supplementary experiment: how does visible evidence affect judgments?") + "</h3>"
    out += "<p>" + t("我们对网页原有的旋钮抓取与胡萝卜切片两例补做了 12 次请求。每例保留前 1 帧、前 2 帧或全部已观测帧，分别使用 zero-shot 与相同的外部 5-shot，均请求 GPT-6 Astra。所有结果均为新请求，包含全部帧的对照条件。", "We made 12 fresh requests on the existing knob-grasping and carrot-slicing illustrations. For each case, retain the first frame, first two frames, or all observed frames, under zero-shot and the same external five-shot condition. Every request uses GPT-6 Astra, including a fresh full-visibility control.") + "</p>"
    out += '<p class="method-note">' + t("本实验于 2026 年 10 月 20 日新增，独立于上文正式测评。遮蔽后仍使用原来的回顾性问题；少帧条件没有对应的时间级真值，因此不计算准确率，也不解释为在线报警。每个条件仅请求一次，不能把变化完全归因于可见帧数量。", "Added October 20, 2026, separately from the benchmark above. Withheld-frame variants retain the original retrospective question. There is no time-specific ground truth for partial inputs, so we do not score their accuracy or interpret them as online alarms. With one response per condition, differences cannot be attributed solely to visible-frame count.") + "</p>"
    for idx in data["protocol"]["case_ids"]:
        case = next(c for c in cases if c["id"] == idx)
        rows = [r for r in data["results"] if r["case_id"] == idx]
        levels = sorted({r["visible_frames"] for r in rows})
        task = t("抓取炉灶旋钮", "Grasp the stove knob") if idx == 55 else t("切胡萝卜", "Slice the carrot") if idx == 36 else case["task"]
        out += f'<article class="visibility-case"><h4>{escape(task)}</h4>'
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
            out += '<details class="research-detail visibility-response"' + (" open" if n == levels[-1] else "") + "><summary>" + str(n) + t(" 帧：输入与两种条件的模型原文", " frames: input and both original responses") + "</summary>"
            out += f'<div class="experiment-input" tabindex="0" role="region" aria-label="{t("横向滚动查看实验输入","Scroll horizontally through the experimental input")}"><a href="{selected[0]["image"]}" target="_blank" rel="noopener"><img loading="lazy" src="{selected[0]["image"]}" alt="{t("未提供的后续观测帧以白色遮蔽；点击查看原尺寸","Withheld later observations are white; click for full resolution")}"></a></div>'
            for r in selected:
                out += "<p><strong>" + (t("零样本", "Zero-shot") if r["condition"] == "zero" else "External 5-shot") + f'</strong></p><blockquote lang="en">{escape(r["answer"])}</blockquote><p class="fine">' + t("返回模型标识：", "Returned model label: ") + escape(r["returned_model"]) + "</p>"
            out += "</details>"
        out += "</article>"
    out += "<p>" + t("这一小规模实验展示同一问题在不同证据量下的回答，而非提供新的基准排名。全部帧的新回答也可能与先前测评不同；采样变化及中转后端差异仍然存在。", "This small experiment shows answers under different amounts of evidence rather than a new benchmark ranking. Fresh full-input responses can also differ from earlier evaluations; sampling variation and relay-backend differences remain possible.") + "</p>"
    out += '<details class="research-detail"><summary>' + t("实验协议与完整记录", "Protocol and complete records") + "</summary><p>" + t("只将未提供的后续观测格置白；保留画布大小、格子位置、原始问题和五个外部示例。所有变体均将原 JPEG 解码后无损保存为 PNG，可见像素不变。未向模型提供测试答案或文件名。不因回答内容或质量重试。", "Only withheld later observation tiles are made white. Canvas size, tile positions, the original question, and five external demonstrations are retained. Every variant is a lossless PNG of decoded JPEG pixels. Neither the test answer nor its filename is sent. No answer-quality retries are performed.") + '</p><p><a class="inline-link" href="data/robofail-visibility.json" download>' + t("下载实验协议、12 条原始回答与 token 用量", "Download protocol, 12 original answers, and token usage") + " ↓</a></p></details></div>"
    return out
