# Beyond the Score · Simple AI

Astra 能否成为机器人的“评审员”？涵盖机器人执行质量、任务进度、失败识别与解释的完整研究博客。

- index.html / en.html：完整中文和英文研究博客，2026-10-15 更新；切换语言时保留当前章节。
- blog.css / blog.js：响应式样式、目录、图表放大和混淆矩阵切换。
- evidence.html：保留的交互证据页，文章和资源区提供入口；主要案例同时嵌入正文。
- data/：结构化评测结果、指标定义及保存的案例。
- assets/figures/：五张完整 baseline 对比图；含 ICL 的排序与进度图集中在 RBM ICL 小节。进度图只修正 VOC 标签，数值未改；独立绘图源保存在 assets/figures/source/03_progress.tex。
- data/publication.json：作者顺序、机构、更新日期和发布状态。
- scripts/build_blog.py：从结果数据与 data/confirmed-blog.json 的已审阅双语文案生成文章，运行 `python3 scripts/build_blog.py` 更新两页。不要只修改生成的 HTML。

网站部署使用已生成的静态 HTML/CSS/JavaScript，无需服务器端构建，可通过 GitHub Pages 发布。

作者：Jinhao Zhang、Yuwei Zhang、Weitao Zhou、xxx、xxx（后两项为占位）。Code 和 arXiv 暂标为 coming soon。资源区保留技术报告、原始博客稿及交互证据入口。

本地预览：`python3 scripts/serve_preview.py`，然后访问 http://localhost:9879/ 。该服务器支持视频 Range 请求，浏览器才能正确执行曲线定位；只监听本机，不发布网站。

内容依据已核验的 2026-09-23 评测记录、2026-10-14 博客稿和既有案例扩写。此版本未增加新的聚合实验结果。报告 PDF 与原始 Markdown 未修改，仍可从资源区访问。

本版补充 action policy 与 critic 的研究动机、benchmark 选择、各评估维度的重要性、指标公式、文献比较范围和非学习解析参照；案例移入对应结果章节。强化学习部分为后续计划，尚无闭环训练或策略收益结果。

## 整合版内容

以远程 df62e42 为结构基线，保留双语目录、作者配置、方法公式和文献对照；已审阅正文在 data/confirmed-blog.json 中维护。两种语言共享媒体、数字与逐字模型原文。

每种语言保留 12 组 RBM Case Study、18 段配对输入帧回放与 11 段其他视频，共 29 段，无重复引用；RoboFail 共有 6 个源视频案例。零样本结果与案例先于独立 RBM ICL 小节；RoboFail 的 ICL、连续结果段、六例分析与可见证据补充实验位于后续成败章节。既有香蕉重试轨迹 T011 已补入进度章节，并与蓝杯案例一同突出 Astra 对任务状态的正确识别；保留原始预测、采样回放说明和事后选例限制。新增的四组排序/偏好正例具有逐样本 DeepSeek 对照，进度案例不据此声称胜过其他模型。

偏好准确率按六来源等权计算：先算各来源正确比例，再取等权平均，不能直接以总体正确数除以 1,192。VOC 显示值为相关系数乘 100，图表标签写 VOC；开瓶案例显示 90.51 / 95.36，与原数据的未缩放值等价。

所有视频注明评测输入与读者回放的差别；六个视频案例来自已有记录，不独立验证物理原因。下列可见证据实验是单独新增的模型请求。

验证：运行 `python3 scripts/check_blog.py` 检查生成一致性、双语锚点、29 段媒体、正例精确分数/选择、原文与本地链接。

图片的固有尺寸记录在 data/media-dimensions.json，生成器写入 width/height，避免延迟加载使语言切换和目录定位偏移。新增图片时同步更新尺寸记录。

## 2026-10-20 RoboFail 可视化补充

- 四个新增视频案例：按咖啡机按钮、拾取刀具、抓取苹果、放入碗中；保留原来的抓旋钮和切片两例。各例提供真实源视频、观测帧、参考标签及 zero-shot / 外部 5-shot 原文。
- 独立可见证据实验：两例 × 三种保留帧数量 × 两种提示条件，共 12 次新的 Astra low 请求。保留原问题；少帧条件不计算准确率，不当作在线报警。
- 新请求输入 339,915 token、输出 414 token，总计 340,329；均直连、HTTP 200、无重试。每格一次，返回后端标识不同，不能做因果或统计显著性推断。
- 原 57 问题的指标和 PDF 未改变。中英文正文与交互证据页同步新增；英文原始回答原样保留。
- `data/robofail-visibility.json` 保存新实验协议、逐条回答、返回模型标识和用量。`scripts/robofail_visuals.py` 渲染新增部分；`scripts/build_evidence_data.py` 更新独立证据页数据。

重建：`python3 scripts/build_evidence_data.py`、`python3 scripts/build_blog.py`；校验：`python3 scripts/check_blog.py`。新增图片须更新 `data/media-dimensions.json`。

进度案例的视频与曲线逐一并排展示。曲线直接使用 data/rbm-cases.json 中的五个已记录数值；起点是协议设定，其余为 Astra 预测，不是人工逐帧完成率。采样点按钮按回放帧定位；横轴是已保存采样位置，不是执行秒数。读者可见正文与图注使用任务名称，不显示内部案例编号。

## 2026-10-21 排序与偏好正例（待审阅）

从远端 `026455fe44ef100cc6249912efcbf560c30f9e10` 建立独立工作目录，先通过 `git apply --check` 再应用交接包；全部 9 个附件文件逐字节还原后继续修改。未改动两个旧工作目录的文件，未推送、发布或调用付费模型。

- 独立排序：关抽屉（成功 / 失败），Astra 1.00 / 0.00，DeepSeek 0.20 / 0.30；香蕉搬运（成功 / 次优），Astra 1.00 / 0.00，DeepSeek 0.50 / 1.00。A/B 为正文轨迹标识，各轨迹实际独立评分。
- 直接偏好：按按钮（A 次优 / B 成功）和开红桶（A 失败 / B 成功），参考及 Astra 均选 B，DeepSeek 均选 A。A/B 为真实输入顺序，已核对 seed 44 的顺序翻转规则，不是由独立分数推导。
- 以上是事后选例，原失败分析、ICL、RoboFail、聚合指标及统计口径均保留。推理等级、输出上限、API 接口和计算预算不同；没有同一配对交换 A/B 后的复测，也未提供已核验的 Robometer 个案对照。

`data/rbm-positive-cases.json` 保存源文件与行号、轨迹及标签、配置差异、完整最终回答、响应文件哈希、重建请求哈希和输入帧哈希。输入 JPEG 与重建请求字节一致，封面为最后一张输入图；新增回放采用 8 张输入图、每张 1 秒，采样位置为 0/4/9/13/18/22/27/31，不是原速视频。图片尺寸已登记。

日常正文仍在 `data/confirmed-blog.json` 编辑，再运行 `python3 scripts/build_blog.py` 和 `python3 scripts/check_blog.py`。在保留 OpenWVM 原始评测记录的服务器上，运行 `python3 scripts/build_positive_evidence.py --check --openwvm ../OpenWVM` 可离线复核 12 个请求、64 张输入图和 12 份相同的样本清单；不带 `--check` 可重建证据与媒体（需 NumPy、Pillow、ffmpeg）。脚本不导入模型客户端，也不会发送模型请求。

浏览器验收：安装 Playwright 与 Chromium 后，启动上述本地预览，再运行 `python3 scripts/check_browser.py --output ../beyond-the-score-review-artifacts-20261021`。检查中英桌面/手机、320px 窄屏、29 段媒体、逐字理由展开、图片放大、语言锚点、80 次曲线采样定位及首次加载路径，并保存截图。
