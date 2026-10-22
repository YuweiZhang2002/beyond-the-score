"""Render exact recorded progress samples beside their existing replay videos."""
from html import escape
import json

LABELS = {
    'Q0041': ('cup-success', ('成功放入水槽', 'Successfully placed in the sink'), ('初始', '接近蓝杯', '接触杯沿', '举至槽外', '放入并释放'), ('Initial', 'Approach cup', 'Contact rim', 'Lift to sink edge', 'Place and release')),
    'Q0039': ('cup-slip', ('杯子滑落在槽外', 'Cup slips outside the sink'), ('初始', '接近', '抓取定位', '移至槽边', '槽外滑落'), ('Initial', 'Approach', 'Grasp position', 'Move to sink edge', 'Slip outside sink')),
    'Q0037': ('wrong-object', ('搬动了错误物体', 'The wrong object is moved'), ('初始', '接近工作区', '未移动蓝杯', '拿起错误物体', '蓝杯仍未移动'), ('Initial', 'Approach workspace', 'Blue cup unmoved', 'Lift wrong object', 'Blue cup still unmoved')),
    'T011': ('banana-retry', ('受挫后重试成功', 'Successful retry after a setback'), ('初始', '首次接近', '退回且未取走', '再次接近', '香蕉放到绿盘'), ('Initial', 'First approach', 'Withdraw without pickup', 'Approach again', 'Banana on green plate')),
}


def render_progress_video(case, lang):
    zh = lang == 'zh'
    pick = lambda a, b: a if zh else b
    slug, titles, zh_events, en_events = LABELS[case['id']]
    title, events = titles[0 if zh else 1], zh_events if zh else en_events
    indices, values = case['sampleIndices'], case['progress']
    assert len(indices) == len(values) == 5 and values[0] == 0
    assert indices == [0, 7, 15, 23, 31] and case['storedFrameCount'] == 32 and case['playbackFps'] == 4
    x = lambda sample: 48 + sample / 31 * 348
    y = lambda value: 210 - value * 160
    chart_title = pick('Astra 预测进度', 'Astra predicted progress')
    description = pick('采样位置与进度：', 'Stored sample and progress: ') + '；'.join(f'{i}: {v:.2f}' for i, v in zip(indices, values))
    description += pick('。起点由协议设为 0，其余为模型预测；连线仅辅助阅读。', '. The initial zero is protocol-set; other points are model predictions. Lines are visual guides only.')
    svg = [f'<svg class="progress-svg" viewBox="0 0 440 270" role="img" aria-labelledby="{slug}-chart-title {slug}-chart-desc">', f'<title id="{slug}-chart-title">{escape(title)} · {chart_title}</title>', f'<desc id="{slug}-chart-desc">{escape(description)}</desc>']
    svg += [f'<text class="progress-axis-title" x="48" y="20">{pick("预测进度（0–1）", "Predicted progress (0–1)")}</text>']
    for tick in [0, .25, .5, .75, 1]:
        svg += [f'<line class="progress-grid" x1="48" x2="396" y1="{y(tick):.2f}" y2="{y(tick):.2f}"/>', f'<text class="progress-tick" x="38" y="{y(tick)+4:.2f}" text-anchor="end">{tick:g}</text>']
    svg += ['<line class="progress-baseline" x1="48" x2="396" y1="210" y2="210"/>']
    for sample in indices:
        svg += [f'<text class="progress-tick" x="{x(sample):.2f}" y="231" text-anchor="middle">{sample}</text>']
    svg += [f'<text class="progress-axis-title" x="222" y="257" text-anchor="middle">{pick("已保存采样位置（非秒）", "Stored sample index (not seconds)")}</text>']
    points = ' '.join(f'{x(i):.2f},{y(v):.2f}' for i, v in zip(indices, values))
    svg += [f'<polyline class="progress-line" points="{points}"/>', '<line class="progress-playhead" data-progress-cursor x1="48" x2="48" y1="39" y2="210"/>']
    for n, (sample, value) in enumerate(zip(indices, values)):
        svg += [f'<g data-progress-point="{sample}" class="progress-point{" is-active" if n == 0 else ""}"><circle class="progress-halo" cx="{x(sample):.2f}" cy="{y(value):.2f}" r="10"/><circle class="progress-dot{" is-fixed" if n == 0 else ""}" cx="{x(sample):.2f}" cy="{y(value):.2f}" r="4.5"/><text class="progress-value" x="{x(sample):.2f}" y="{y(value)-13:.2f}" text-anchor="middle">{value:.2f}</text></g>']
    svg += ['</svg>']
    buttons = []
    for n, (sample, value, event) in enumerate(zip(indices, values, events)):
        aria = pick(f'定位到采样位置 {sample}：{event}，进度 {value:.2f}', f'Seek to stored sample {sample}: {event}, progress {value:.2f}')
        buttons.append(f'<button type="button" data-progress-seek="{sample}" aria-label="{escape(aria)}" aria-pressed="{str(n == 0).lower()}"><span>{sample} · {value:.2f}</span><small>{escape(event)}</small></button>')
    caption_attr = ''
    caption = escape(title)
    if case['id'] == 'T011':
        caption_attr = ' id="banana-retry-caption"'
        caption = pick('MIT Franka · 香蕉转移任务 · 公开标签：成功。32 张已保存图像按每秒 4 帧回放，不是原始执行时长；模型每次只依据截至当时的观测。', 'MIT Franka · Banana transfer · Public label: successful. Replay of 32 stored frames at 4 fps, not the original execution timing; each prediction uses only observations available up to that point.')
    footer = pick('空心起点为协议设定，非模型预测。连线仅辅助阅读，不代表中间帧有额外预测或人工标注。', 'The hollow initial point is protocol-set, not predicted. Lines guide the eye; they do not add predictions or human annotations between samples.')
    instruction = pick('点选下方采样点可定位视频；橙色竖线随回放移动。', 'Select a sample below to seek the video; the orange cursor follows replay.')
    initial_status = pick('回放帧 0 · 最近采样位置 0 · 协议起点 0.00', 'Replay frame 0 · Nearest sample 0 · Protocol initial value 0.00')
    return f'''<div class="progress-compare" data-progress-compare data-progress-indices="{','.join(map(str, indices))}" data-progress-values="{','.join(f'{v:.2f}' for v in values)}" data-progress-fps="{case['playbackFps']}" data-progress-frames="{case['storedFrameCount']}">
    <figure class="progress-video"><video controls playsinline muted preload="none" poster="{case['poster']}" src="{case['video']}" aria-label="{escape(title)}" aria-describedby="{slug}-playback-note"></video><figcaption{caption_attr}>{caption}</figcaption></figure>
    <div class="progress-chart"><p class="progress-chart-title">{chart_title}</p>{''.join(svg)}<div class="progress-samples" role="group" aria-label="{pick('定位到对应采样画面', 'Seek to a sampled observation')}">{''.join(buttons)}</div><p class="progress-playback-status" data-progress-status>{initial_status}</p><p class="progress-chart-note" id="{slug}-playback-note">{instruction} {footer}</p></div></div>'''
