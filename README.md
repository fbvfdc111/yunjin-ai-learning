# Phase 6.2 比赛试用记录版

本轮在 Phase 6.1 基础上做最小增量：保留 AI探锦、Dots/OpenAI 接口、本地 fallback、
AI文化助手和六阶段数字织机原有能力；新增数字织机阶段知识测验、正确答案解释和匿名本地学习结果记录。

新增记录文件位置：

```text
data/learning_results/anonymous_quiz_results.ndjson
```

记录字段只包含匿名会话标识、阶段、所选答案、正确答案、是否答对、当前完成步骤数和时间戳。
不记录姓名、联系方式、IP、上传图片、API payload 或用户自由文本。该记录仅用于 10 月 30 日比赛前的小范围真实试用证据，
不能夸大为长期学习成效、识别准确率或教学效果评估。

新增验收命令：

```powershell
python -m pytest tests -q
python scripts/phase62_vision_acceptance.py
```

`phase62_vision_acceptance.py` 固定检查：南京云锦样例、其他织锦样例、无关几何图片在无 API Key 时均回退 local_cv，
且不输出南京云锦归属、年代、真伪等鉴定结论；边界问题由 AI文化助手返回“证据不足”。

---

# Phase 6.1 比赛展示版

本轮仅优化首页学习路径、数字织机 SVG 与人类可读状态面板；六状态逻辑和文化证据不变。
当前定位：**知识驱动、状态驱动的南京云锦织造教学型数字孪生原型**。

当前状态见 `status_current.yaml`；`status.yaml` 是保留的历史阶段记录，其旧字段不代表当前能力。
本轮实际测试与核验见 `docs/phase61_validation.json`、`docs/phase61_delivery_report.md`。
用户侧 Phase 6.1 Windows 人工展示对比验收仍待进行。以下保留原 README 内容作为历史上下文。

---

# 南京云锦智能识别与数字化传承 - Phase 6 数字织机

## Phase 6 独立交付版（2026-09-07）

当前实现的是**知识驱动、状态驱动的南京云锦织造教学型数字孪生原型**。
唯一代码基线为 `yunjin_ai_mvp_phase5_round3_core_20260907.zip`，SHA-256：
`4866434272C083C24F65EEDDEBA26F1D1147F084ED9A349CECAC0058DA76AAE6`。
原 ZIP 未修改；以下历史阶段说明用于保留项目沿革，不改变 Phase 6 的唯一基线。

导航：**首页｜AI探锦｜数字织机｜AI文化助手｜数据与可信AI**。

数字织机抽取图案设计、挑花结本、织造准备、拽花工提经、织手织造、织造成纹六个教学状态。
它们不是南京云锦百余道工序的完整流程，也不是正式操作规程。

### 运行与体验

在解压后的本项目目录运行（Python 3.10+，Streamlit 1.63+）：

```powershell
python -m pip install -r requirements.txt
python -m pip install pytest
python -m streamlit run app.py
```

进入“数字织机”，默认按顺序体验。点击“执行当前步骤”先更新运行时 `TwinState`，SVG 再读取状态重绘。
完成当前步骤后可点“下一步”；“织造成纹”每次显示一段，三段全显示后完成，段数仅为界面设计。
“自由探索”可选择任一状态，但不会自动执行前置步骤；回到顺序模式时定位到最早未完成步骤。
重复执行已完成步骤会增加重播次数，并重播显示效果；经线强调组与纬向提示方向也会按教学状态变化。
“数字孪生状态”区域常驻显示阶段、模式、已执行状态、当前教学值和最近变化，可展开查看完整状态对象。
“重新开始体验”重置教学状态；“减少动态效果”保留最终图形并关闭过渡效果。
同一会话切页后保留教学状态；刷新建立新会话、关闭标签页或重启服务后不保证保留。

每个状态的“向AI文化助手继续提问”按钮沿用原有跳转与预填逻辑；到助手后点击“获取可信回答”。
没有第二套聊天系统，也不会因教学交互自动调用视觉 API。

### 可信边界与验证

**交互示意｜非织机机械结构精确仿真**。
当前数字状态由用户交互驱动，而非实体织机传感器驱动。
当前没有实体传感器、实体织机实时数据同步、物理参数仿真或专家级机械结构验证。
物理实体—数字模型的实时双向同步属于后续工作。
SVG 使用自绘几何符号，不展示授权 unknown 的官网图片，不模拟真实花本编码或机械参数。
缺少统一岗位证据的环节显示资料不足。工艺事实逐条引用 Round 3 知识库；教学说明与事实证据分开。

```powershell
python -m pytest tests -q
python scripts/phase4_health_check.py
python scripts/phase5_health_check.py
python scripts/phase5_round2_health_check.py
python scripts/phase5_round3_health_check.py
python scripts/phase6_health_check.py
python scripts/phase6_health_check.py --protection-only
```

若原 Round 3 ZIP 可用，还可加 `--baseline-zip "原ZIP的路径"` 核对 ZIP、逐文件清单及 AI探锦/AI文化助手代码块。
健康检查只读并输出 JSON；没有运行训练或真实外部 API。
交付说明见 `docs/phase6_delivery_report.md`，结果见 `docs/phase6_test_results.txt`、
`docs/phase6_health_check_result.json` 与 `docs/phase6_protection_result.json`。

---

## Phase 5 Round 3 独立交付版（2026-09-06）

本版本从 Round 2 稳定 ZIP 独立建立，未覆盖 Round 2。知识库按逐条事实重构，并明确区分
`direct_yunjin`、`official_object_name`、`general_cultural_background` 和
`governance_methodology`。四大品种保留三类、四类及另列金宝地等来源口径差异。

47件南京云锦官方对象均进入显式关系表。对象与知识的关系只表示官方名称或目录资料中出现相应词语，
不表示图像鉴定、模型分类或训练标签。授权状态仍全部为 `unknown`，不可转为训练数据。

AI探锦只允许直接南京云锦知识自动参与视觉线索检索；官方对象名称知识需要用户主动选择文化主题，
一般传统文化背景完全禁止视觉自动召回。AI文化助手逐条显示事实范围和对应来源。

Dots Base64、多模态视觉 provider、回退链、请求格式与保护测试均保持 Round 2 状态。

## Round 2 基线说明

本版本以 Phase 5 Round 1 ZIP `yunjin_ai_mvp_phase5_round1_productized_20260906.zip`（SHA-256 `8AB32E360CAEDBB06251E0DD9D4028A4665C7E4337E2E77BB83997E423889AFF`）为唯一基线增量开发，不覆盖 Round 1 或 Phase 4 交付。

Round 2 根据真实浏览器验收修复了三类问题：视觉场景词不再误触发 KB015 数据治理条目；AI文化助手先执行 answerability/relevance gate；页面改用稳定的原生分段导航、表单提交和固定回答容器。Dots prompt、Base64 transport、provider 架构、OpenAI 和 local_cv 均保持不变。

技术路线正式冻结为：

```text
Multimodal Vision AI → Cultural Knowledge Retrieval
→ Evidence-grounded Explanation → AI Cultural Guide
```

当前合法可直接训练的南京云锦对象仍为 **0**。本阶段不进行监督分类训练，不生成 Accuracy、Precision、Recall、F1、Loss、混淆矩阵或模型权重。95 个官网对象继续作为 `Official Evidence Database`，全部 `authorization_status=unknown`，界面只展示对象 metadata，不展示这些授权不明的官网图片。

### 用户现在可以完成

1. 上传自己的 JPG/JPEG/PNG 图片，默认使用 Dots `dots3-note-prev` 进行多模态视觉观察。
2. Dots 未配置或调用失败时，明确回退到无需 API 的本地可解释视觉 fallback。
3. 将纹样、构图、色彩和视觉关键词分区展示，并明确专业鉴定边界。
4. 只用达到门槛的视觉关键词或人工确认主题检索本地文化知识、证据等级与来源。
5. 从 AI探锦一键带入建议问题，继续向 AI文化助手学习；无证据时系统明确回答“证据不足”。

### 快速运行

建议使用 Python 3.10+，在项目根目录执行：

```powershell
python -m pip install -r requirements.txt
python scripts/phase4_health_check.py
python scripts/phase5_health_check.py
python scripts/phase5_round2_health_check.py
python -m unittest discover -s tests -v
python -m streamlit run app.py
```

浏览器打开 Streamlit 输出的本地地址。主流程为：

```text
AI探锦 → 上传图片 → 开始 AI 分析 → 浏览相关文化知识/证据
→ AI文化助手继续提问
```

### 可选 OpenAI 多模态 provider

复制 `.env.example` 中的变量到你的安全环境配置（不要提交 Key）：

```powershell
$env:OPENAI_API_KEY="你的 Key"
$env:OPENAI_VISION_MODEL="你账户中可用且支持图像输入的模型 ID"
python -m streamlit run app.py
```

工程使用 Responses API 的图像输入，并将 `store=False`。只有用户在界面主动选择 OpenAI provider 后，图片才会发送给 API。API Key、模型访问、费用和网络均需使用方自行配置；本次交付环境未配置 Key，因此该调用状态是“待配置/未实测”，不会伪造成功。接口实现依据 [OpenAI Responses API 官方文档](https://developers.openai.com/api/reference/cli/resources/responses/methods/create)。

### 默认 Dots Studio 多模态视觉 provider

在 PowerShell 中配置：

```powershell
$env:DOTS_API_KEY="你的 Key"
$env:DOTS_BASE_URL="https://note3-prev-api.askdiandian.com"
$env:DOTS_VISION_MODEL="dots3-note-prev"
python -m streamlit run app.py
```

Dots 使用 `POST /v1/chat/completions`、`api-key` 请求头和 OpenAI Chat Completions 风格的多模态 `messages[].content`。请求固定设置 `stream=false`、`max_tokens=700`、`chat_template_kwargs.enable_thinking=false`，图片细节为 `medium`。系统提示词只允许输出主体/纹样、构图、色彩、重复/对称、检索关键词和限制，禁止仅凭图片确定是否为南京云锦、具体工艺、年代、文物名称、真伪或作者/制造者。

**本地上传 Base64 路径**：选择 `dots` 时，公网 `http/https` 图片 URL 优先；URL 留空后上传 JPG/JPEG/PNG，工程会在内存中构造 `data:<mime-type>;base64,<base64-data>` 并直接放入 `image_url.url`。JPG/JPEG 使用 `image/jpeg`，PNG 使用 `image/png`。不会发送本地路径，也不会上传到任何第三方图床。

Streamlit 接受的原始上传上限为 10 MB。Dots 发送前会把最长边限制在 2048 px，并在必要时压缩到最多 4 MB；压缩只作用于内存副本，不改写项目知识库、数据集或用户原文件。若服务端返回“不支持 data URL”“invalid image URL”或其他错误，页面在技术详情中保留服务端错误正文并显示：requested provider、actual provider、`public_url` / `base64_data_url` / `local_cv` transport 和 fallback reason，然后自动回退 `local_cv`。

Dots 返回值只作为视觉观察和本地知识库检索关键词；文化解释仍由 `data/knowledge` 的 evidence-grounded 检索生成，Dots 不会绕开知识库补写文化事实。**Dots Base64 本地图片调用已由用户在实际运行环境完成真实验证**：页面显示实际 provider 为 `dots:dots3-note-prev`、`image_transport=base64_data_url`，该次调用无 fallback。自动化测试仍全部使用 mock HTTP 与假 Key，不会消耗真实 Dots API。用户侧一次成功调用只验证调用链可运行，不代表模型准确率、识别效果或系统性能已经得到评测。

### Phase 4 / Phase 5 新增结构

```text
data/knowledge/
├─ knowledge_base.json        # 分层事实、逐事实来源、回答词与视觉检索模式
├─ official_object_knowledge_map.json # 47件对象的显式名称关系或未关联原因
├─ sources.json               # 程序读取的来源/证据表
└─ sources.csv                # 便于人工审阅的等价表
src/yunjin_ai/
├─ knowledge.py               # 加载、校验、通用检索、视觉线索门槛检索
├─ vision.py                  # 本地 fallback + 可选 OpenAI / Dots provider
├─ guide.py                   # 证据约束回答与无证据拒答
└─ product.py                 # 视觉结果分组、建议问题与页面联动
tests/
├─ test_phase4_knowledge.py
├─ test_phase4_vision.py
├─ test_phase4_dots.py        # mock HTTP，不使用真实 API Key
├─ test_phase5_product.py     # 检索门槛、结果整理、联动与 UI 回归
└─ test_phase5_round2_acceptance.py # 真实验收问题回归
scripts/phase4_health_check.py
scripts/phase5_health_check.py
scripts/phase5_round2_health_check.py
docs/
├─ phase4_system_architecture.md
├─ phase4_aic_innovation_draft.md
├─ phase4_delivery_report.md
├─ phase5_round1_delivery_report.md
├─ phase5_round2_delivery_report.md
└─ phase5_todo.md
```

### 真实性与边界

- 本地 fallback 是真实运行的传统图像统计/规则观察，不是南京云锦分类 AI，也不输出概率式置信度。
- OpenAI provider 是可运行接口，但本次未配置 API Key，因而未声称调用成功。
- Dots provider 已完成公网 URL、JPEG/PNG Base64 data URL、响应解析、错误正文保留与 `local_cv` 回退的 mock 自动化测试；用户另在实际运行环境完成一次真实 Base64 成功调用验证。
- 真实调用验证只证明 `dots:dots3-note-prev` + `base64_data_url` 链路成功且该次无 fallback，不是模型准确率或系统性能验证。
- 文化助手是本地 evidence-grounded retrieval，不允许脱离知识库自由补写文化事实。
- “AI 推测”“视觉观察”“来源支持的文化事实”在界面分区显示。
- Digital Twin、Immersive Learning、Community Participation 尚未实现，仅列入后续阶段。

> **本系统用于文化学习与数字化传承，不构成文物、工艺或真伪专业鉴定。**

---

## 以下为原 Phase 3 README（完整保留）

# 南京云锦智能识别与数字化传承 - AIC Phase 3 合规数据版

## Phase 3 冻结结论（2026-09-04）

- Phase 2 的 95 个官网对象原样定位为 **Official Evidence Database**：南京云锦 47、其他织锦 48，授权均保持 `unknown`，不进入正式训练。
- 本轮核查 22 条开放数据候选。开放许可且标签仍指向南京云锦的对象仅 1 个，但存在强场景/来源捷径，当前可直接训练为 **0**。
- 其他织锦开放许可候选 12 个，经对象性、分辨率、文字/标尺及人工联系表复核后，当前可直接训练为 **3**。
- 两类不平衡且来源与类别完全相关，正式训练门槛未通过；没有训练、权重或实验指标。
- 技术路线冻结为 **Multimodal AI + Cultural Knowledge Base**；CLIP 只作为后续检索/零样本探索，不宣称监督分类性能。

Phase 3 主交付见 `docs/phase3_open_data_survey_report.md`、`docs/phase3_legal_data_register.xlsx`、`data/metadata/phase3_open_data_candidates.csv` 和 `docs/phase3_aic_data_compliance_draft.md`。

---

## Phase 2 保留成果

本工程落实“数据真实性 > 标签可靠性 > 算法可实现性 > 演示效果”。第二阶段已访问南京云锦博物馆官网，整理官方清册、网页证据、对象级 metadata、模型候选图、Level 2 候选标签和训练门槛。**本阶段没有启动训练**：官网标签证据数量已足够，但使用授权与图像质量尚未同时达标。

## 当前真实状态

- 官网对象级记录：95 个，其中确认南京云锦 47、确认其他织锦 48、未知 0。
- 有官网类别证据：95 个；可解码候选图：95 张。
- 最短边至少 224 像素：14 张（南京云锦 6、其他织锦 8）。
- 授权/版权状态：95 个均为 `unknown`。官网页脚版权声明不等于训练及再发布授权。
- 可直接用于训练：0；Accuracy / Precision / Recall / F1 / Loss / 混淆矩阵均为**待训练 / 待验证**。
- Level 2 只建立官网名称文本支持的候选标签表，不训练多标签模型。

第一阶段原始截图仍完整保留：

- 原始截图：40 张（batch_2 32，batch_3 8）。
- 由“用户确认的项目采集背景 + 截图标题中的云锦工艺语义”共同支持的南京云锦正类：5 张（中等置信）。
- 截图标题直接确认的其他织锦：7 张（高置信）。
- Level 1 类别仍未知：28 张。
- 可作为 Level 1 标签证据：12 张。
- 可直接用于训练：0 张。
- 训练、验证、测试指标：**待训练 / 待验证**。

全部 40 张都属于用户确认的“南京云锦项目相关素材”采集范围，但“项目相关”不等于每张都是南京云锦正类。现有截图普遍包含标题或编号，直接送入分类器会造成文字标签泄漏；部分档案记录还存在同源多视图和近重复。所有原图因此都保留在 `reference`，不以“约 40 张”等同于“40 个独立训练样本”。

## 目录

```text
yunjin_ai_mvp/
├─ app.py                         # Streamlit 演示
├─ inference.py                   # 有真实 checkpoint 时才运行
├─ train_level1.py                # 二分类训练入口，含数据门槛
├─ train_level2.py                # 多标签数据门槛与扩展接口
├─ configs/default.yaml
├─ data/
│  ├─ raw/batch_2, batch_3        # 原始截图，不改名
│  ├─ metadata/metadata.csv       # 证据型主表
│  ├─ metadata/file_manifest.csv  # 哈希、尺寸、字节数
│  ├─ processed/                  # 后续清洁裁切/标准化产物
│  └─ splits/splits.csv           # 当前仅表头模板
├─ docs/
│  ├─ dataset_audit_report.md
│  ├─ category_stats.csv
│  ├─ data_supplement_plan.md
│  ├─ model_training_plan.md
│  ├─ competition_gap_checklist.md
│  └─ label_policy.md
├─ scripts/
│  ├─ audit_dataset.py
│  ├─ prepare_data.py
│  └─ create_splits.py
└─ src/yunjin_ai/
```

## 快速验证

建议使用 Python 3.10+：

```powershell
python -m pip install -r requirements.txt
python scripts/audit_dataset.py
python scripts/prepare_data.py
python scripts/create_splits.py --template-on-insufficient
python -m unittest discover -s tests -v
streamlit run app.py
```

`prepare_data.py` 默认只处理 `usable_for_training=true` 的行；当前应输出 0 张，这是预期结果。`--include-nontrainable` 只用于界面或流水线演示，不能改变训练资格。

## 训练入口的保护机制

```powershell
python train_level1.py
python train_level2.py
```

当前两个命令都应在数据门槛处停止，并明确说明缺口；不会生成 checkpoint、Accuracy、Precision、Recall、F1、Loss 或混淆矩阵。补充数据并经专家审签、版权确认、文字去除、同源分组后，才可把 metadata 中相应行改为训练用途并生成正式 split。

## 标签规则

1. 分别记录素材采集范围、截图直接证据、组合分类证据和最终监督标签。
2. 用户确认的南京云锦项目采集背景可与标题中的“妆花/织金”等语义构成组合证据，但不会覆盖标题明确写出的其他织锦属性。
3. 不按颜色、构图或个人视觉判断推断纹样、工艺、年代或文物名称。
4. `unknown` 是合法且优先于猜测的取值。
5. `source_group_id` 相同的记录必须进入同一个 split。
6. 可靠标签与训练资格分别管理：12 张有 Level 1 标签证据，但因版权和泄漏问题仍不可直接训练。

## 第二阶段新增目录

```text
data/official/
├─ evidence/source_pdfs/          # 官网原始清册 PDF
├─ evidence/catalog_pages/        # 含名称、登记号与图片的完整证据页
├─ evidence/webpage_screenshots/  # 网页分段截图，覆盖页面首/中/尾
├─ model_images_candidates/       # 从清册提取的低分辨率主体缩略图
└─ web_images/                    # 官网直接下载的网页主体图
data/metadata/
├─ official_metadata.csv
└─ official_level2_candidate_labels.csv
docs/
├─ phase2_official_collection_report.md
├─ phase2_data_audit_report.md
├─ phase2_training_decision.md
├─ phase2_aic_evidence.md
├─ phase2_official_stats.csv
├─ phase2_audit_results.json
└─ phase2_duplicate_review.csv
```

重建与复核：

```powershell
python scripts/build_official_dataset.py
python scripts/audit_official_dataset.py
python scripts/create_official_splits.py --template-on-insufficient
python -m unittest discover -s tests -v
streamlit run app.py
```

授权和质量门槛通过后，官网数据训练入口为：

```powershell
python train_level1.py --schema official --metadata data/metadata/official_metadata.csv --splits data/splits/official_splits.csv
```

当前运行会在数据门槛处停止，不会产生伪模型或伪指标。

## 材料边界

第一阶段两批 ZIP 共 40 张截图。本阶段新增两份 AIC 附件并按评分项复核。官网只发现版权所有声明，没有发现机器学习训练、作品再发布或竞赛提交的明确许可，因此正式训练前仍需取得书面授权或由馆方提供可用数据。

## 详细交付

- 数据审查：`docs/dataset_audit_report.md`
- 数据统计：`docs/category_stats.csv`
- 补数计划：`docs/data_supplement_plan.md`
- 训练计划：`docs/model_training_plan.md`
- 参赛差距：`docs/competition_gap_checklist.md`
- 官网采集：`docs/phase2_official_collection_report.md`
- 官网数据审查：`docs/phase2_data_audit_report.md`
- 训练决定：`docs/phase2_training_decision.md`
- AIC 实施证据：`docs/phase2_aic_evidence.md`
