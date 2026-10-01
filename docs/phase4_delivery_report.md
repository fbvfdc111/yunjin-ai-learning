# Phase 4 交付与实测报告

## 基线与保护

- 唯一基线 ZIP：`yunjin_ai_mvp_phase3_legal_data_20260904.zip`
- ZIP SHA-256：`CEA7461342E51AB7E22E3C9F6AA39D7A68B671645771B5C3BFF5E4CD543CC9C7`
- ZIP 条目：303；解压后文件：294；目录：35。
- Phase 4 开发前生成了逐文件 SHA-256 基线清单；交付前复核为 0 个基线文件缺失。既有文件增量修改仅限 README、requirements、status、app 与包版本说明；Phase 2/3 的治理数据、证据文件和既有测试未改写。机器可读摘要见 `docs/phase4_baseline_integrity.json`。

## 已实现

- Streamlit 四页式 MVP 与完整主流程。
- 15 条带来源 ID/证据等级的结构化知识条目；7 条来源记录及 CSV 审阅表。
- 95 个 Official Evidence Database 对象的只读 metadata 关联。
- 本地 `local_cv` 视觉 fallback；可选 OpenAI Responses API 图像 provider。
- 本地证据检索、文化解释、继续提问与证据不足拒答。
- 系统架构、AIC 创新点草稿、Phase 5 待办与运行说明。

## 当前实测记录

- Python 编译检查：通过。
- 单元测试：10 项通过（包含原 Phase 2/3 6 项与 Phase 4 4 项）。
- 健康检查：15 条知识、7 个来源、95 个官网对象；95 个授权均为 unknown、0 个可训练；知识引用校验无错误；本地视觉 fallback 与“妆花是什么”证据回答成功。
- OpenAI provider：当前环境未配置 `OPENAI_API_KEY` / `OPENAI_VISION_MODEL`，未调用、未声称成功。
- Streamlit 进程启动：通过（显式关闭工作区默认 development mode 后监听 `127.0.0.1:8765`）。
- HTTP 验证：根页面 `200`、`/_stcore/health` 为 `200 / ok`。
- 客户端渲染：标题、四个页签、免责声明、95/47/48/0 指标全部可见，浏览器控制台无错误。
- 文化助手交互：输入“妆花是什么？”后返回知识库回答、`S03`/`S06` 来源及授权 `unknown` 的相关对象 metadata，浏览器控制台无错误。

## 未实现 / 待配置

- 外部多模态 API 的真实调用与供应商侧可用性测试。
- 监督分类、权重、Accuracy、Precision、Recall、F1、Loss、混淆矩阵（按路线明确不做）。
- 专家内容审签、真实用户测试、用户数量、应用效果与专家评价。
- Digital Twin、Immersive Learning、Community Participation。

## 文化知识来源

使用 UNESCO 非遗项目页、中国非物质文化遗产网的项目页/专题页/文章、中国国家博物馆研究文章，以及 Phase 3 候选标签与 Official Evidence Database 本地证据表。完整 URL、访问日期、使用范围和证据等级见 `data/knowledge/sources.csv`。
