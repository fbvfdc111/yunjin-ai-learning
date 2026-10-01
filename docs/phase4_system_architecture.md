# Phase 4 系统架构说明

## 1. 冻结路线

```text
用户上传图像
  ├─ 本地可解释 fallback（已实测，不上传）
  └─ OpenAI 多模态 provider（可选，待 Key/模型配置）
          ↓
视觉观察 / AI 推测（分区保存）
          ↓
检索关键词 + 用户人工确认候选元素
          ↓
本地结构化知识库 → 事实条目 → source_id → 证据等级/URL
          ↓
证据约束文化解释 + Official Evidence Database 对象 metadata
          ↓
AI 文化助手继续提问 / 证据不足拒答
```

## 2. 数据层

- `data/knowledge/knowledge_base.json`：每条文化事实具有稳定 ID、主题、事实文本、关键词、来源 ID、证据等级和可关联的官网对象术语。
- `data/knowledge/sources.json` / `sources.csv`：来源标题、机构、URL、访问日期、类型、证据等级和使用限制。
- `data/metadata/official_metadata.csv`：Phase 2/3 的 95 个官网对象，仅作为 Official Evidence Database。Phase 4 不改写授权字段、不移动图片、不把像素用于训练或默认展示。
- `data/metadata/phase3_level2_candidate_knowledge_labels.csv`：12 个 Candidate Knowledge Labels，仅用于检索组织。

证据等级：A 为联合国/国家级官方非遗资料；B 为官方文化机构研究或解读；C 为本项目可追溯数据治理记录。等级表示来源类型与本项目用法，不等于事实永恒不变，也不替代专家审核。

## 3. 视觉层

`local_cv` fallback 使用 Pillow 真实计算主要色群、平均饱和度、边缘变化代理值、水平/垂直镜像相似度。它不识别工艺、对象、年代或动物植物，不把数值称为置信度。

OpenAI provider 采用可插拔接口：仅当用户主动选择且 `OPENAI_API_KEY`、`OPENAI_VISION_MODEL` 同时存在时调用。提示词限制输出为可观察内容，对疑似元素使用不确定表述，并禁止输出年代、工艺、名称、真伪、归属与概率。模型输出仍须人工复核。

## 4. 检索与解释层

检索器使用明确关键词、中文双字片段与标题匹配进行可复现打分，不依赖在线向量数据库。返回的是知识条目及其 source_id；文化助手只编排检索到的事实。得分不足时固定返回“证据不足”，不调用自由生成补全事实。

视觉检索可加入用户人工确认的候选元素。系统会把“观察/推测”和“来源事实”分开显示，避免把模型输出反向包装为知识证据。

## 5. 界面层

Streamlit 提供：首页、AI识锦、AI文化助手、数据与可信AI说明。AI识锦页串联上传、观察、人工确认、检索、解释、来源和对象 metadata；文化助手允许继续提问。

## 6. 安全与合规边界

- 最大上传 10 MB，仅接受 JPG/JPEG/PNG，并实际解码。
- 本地 fallback 不上传图片；第三方 provider 的外部传输在界面明确提示。
- 官网授权不明图片不在 Phase 4 页面展示。
- 不训练模型，不生成或声称存在分类性能。
- 不把 Digital Twin、Immersive Learning、Community Participation 写成已实现。
