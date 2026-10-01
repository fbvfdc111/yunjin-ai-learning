# Phase 5 Round 3“南京云锦核心化”交付报告

完成日期：2026-09-07  
基线：`yunjin_ai_mvp_phase5_round2_acceptance_final_20260906.zip`  
基线 SHA-256：`DA4A630A84FB0D421F38EA1B2FFE1F3514F62470047F235827924C3D82767604`

## 1. 交付范围

本轮从 Round 2 ZIP 建立独立工作目录，Round 2 原 ZIP 未被改写。实施以
`南京云锦知识补全研究_20260906.md` 和 `yunjin_knowledge_research.json`
为证据输入，不以知识条目数量为指标。最终正式库包含25条知识和12个来源；25是证据筛选后的结果，
不是配额，也不作为后续版本必须维持的数量。

Round 2 原15条知识按研究结论处理：7条保留并继续收紧边界、5条补强、3条替换或拆分。
新增内容覆盖妆花、织金、库锦、库缎、分类口径差异、挑花结本、主要制作流程，以及龙、凤、牡丹、
鹤、寿、灵芝的南京云锦直接资料或官方对象名称证据。

## 2. 知识结构与回答边界

`knowledge_base.json` 改为逐事实 `claims` 结构。每条事实独立绑定来源和以下证据范围：

- `direct_yunjin`：直接谈南京云锦的来源。
- `official_object_name`：只证明官方名称或目录资料中出现某词。
- `general_cultural_background`：跨媒介或一般传统文化背景。
- `governance_methodology`：数据治理和使用边界。

`general_cultural_background` 在结构校验、视觉检索和界面展示三个层面单独处理：
相关条目的 `visual_retrieval` 必须为 `disabled`，不会被视觉结果自动召回；文化助手回答时逐事实显示
“一般传统文化背景”，不能被合并为某件南京云锦对象的确定寓意。

四大品种没有被包装成唯一分类标准。知识条目同时保留三类、四类和另列金宝地等来源口径，
比较只覆盖来源支持的织造或表现维度，不增加高低等级、价格、固定色数或统一日产量。

## 3. 47件官方对象关系

新增 `data/knowledge/official_object_knowledge_map.json`，覆盖全部47件南京云锦对象：

- 47条对象关系记录；
- 19件对象的正式名称命中本轮10个核心词；
- 共建立35条显式关系；
- 其余28件均保存未关联原因；
- 库锦相关对象保持为空，因为47条正式名称中没有“库锦”。

关系固定为 `official_name_mentions` + `official_object_name`，且匹配词必须逐字出现在正式名称中。
运行时不再扫描 `craft_name`、`pattern_name` 候选字段来自动补关系。对象关系只用于学习和证据导航，
不表示图像鉴定、模型分类、训练标签或具体寓意。

## 4. 产品调整

### AI探锦

原“AI识锦”改名为“AI探锦”。Dots、OpenAI、local_cv、多模态请求、Base64 data URL、
压缩与回退逻辑均未修改。视觉自动召回只允许符合门槛的直接文化知识；官方对象名称证据只在用户主动选择
文化主题后参与探索；一般文化背景完全禁止视觉自动召回。

选择控件改为“希望继续探索的文化主题（可选）”，明确该选择不是对图片内容的人工确认。
官方对象表只显示对象编号、官网名称、名称命中词、关系依据、目录核验和授权状态。

### AI文化助手

回答从整条拼接改为逐事实输出，每条事实显示证据范围和自己的来源。混合问题可以同时显示
“官方对象名称/目录资料”和“一般传统文化背景”，但两者不互相证明。没有 answer_terms 直接覆盖的问题
继续返回“证据不足”，不调用大模型补写文化事实。

## 5. Round 2 保护与治理核验

离线核验结果：

- Official Evidence Database：95；
- 南京云锦：47；
- 其他织锦：48；
- `authorization_status=unknown`：95；
- `usable_for_training=true`：0；
- `data/official`：145个文件，与重新解压的 Round 2 基线逐文件 SHA-256 对比，差异0；
- 未生成监督训练、Accuracy、Precision、Recall、F1、Loss、混淆矩阵或模型权重；
- 本轮未调用真实 Dots 或 OpenAI API。

受保护文件与 Round 2 一致：

| 文件 | SHA-256 |
| --- | --- |
| `src/yunjin_ai/vision.py` | `F1CCDB58311E63588466431B440235417D6F5595D31E4917C55B55DEC2FDEA09` |
| `tests/test_phase4_dots.py` | `B18DCE6BA889B5D3B064111A7A1D4A27BBF0F2552FDC5126AF66DC1F1ABDDCF7` |
| `data/metadata/official_metadata.csv` | `915F8C4C9605D912DA7ED8B8307957B4D000DEAED679BA250D4670BD49788823` |
| `data/metadata/official_level2_candidate_labels.csv` | `F326EC87F79CEF1E0B474D3515B8954B1460F7C0735A7C2E6750B15A93790C9B` |
| `docs/phase2_audit_results.json` | `8FDADF9470E85DA063883A55B39F398FDB9D6EF82609647508C94FAAA8052C39` |

Round 2 原 ZIP 复核 SHA-256：
`DA4A630A84FB0D421F38EA1B2FFE1F3514F62470047F235827924C3D82767604`。

## 6. 测试与健康检查

最终离线复跑结果：

- Pytest：49 passed；
- 子场景：29 passed；
- `phase4_health_check.py`：通过；
- `phase5_health_check.py`：通过；
- `phase5_round2_health_check.py`：通过；
- `phase5_round3_health_check.py`：通过。

Round 3 新测试覆盖：逐事实来源和证据范围、一般背景禁止视觉召回、对象名称证据需要用户选题、
八个核心问题、分类口径差异、47件关系全覆盖、正式名称逐字匹配、95/47/48/0治理不变量、
受保护文件 SHA-256 和 Streamlit AppTest 页面回归。

详细机器可读结果见 `docs/phase5_round3_health_check_result.json`。

## 7. 未完成的人工验收项

以下不阻塞本次离线交付，需在 Windows 本机完成：

1. **Streamlit浏览器实际运行验收：未完成的人工验收项。** 需手动核对首页、AI探锦、AI文化助手、
   数据与可信AI四页，以及不同问题连续切换后的排版、来源折叠区和对象关系表。
2. **真实Dots Base64冒烟测试：未完成的人工验收项。** 本轮未使用真实 Key、未发送图片、未调用外部 API。
   需手动确认 requested provider、actual provider、`base64_data_url` 和 fallback reason 显示正确。
3. **OpenAI provider真实调用：未验证项。** 它不是默认 provider，本轮只确认受保护代码和 mock 测试保持通过。

## 8. 仍存在的知识缺口

- 库锦没有可关联的现有47件官方对象ID；不把“锦”“天华锦”或“金宝地”自动映射为库锦。
- 鹤、寿、灵芝在所列具体南京云锦对象中的确定寓意仍为空。
- 《清一品文官补仙鹤》的完整服制制度解释仍为空；只保留2011年当代研发作品的目录身份。
- 百余道工序的完整编号列表、操作规程、工艺参数和完整装造步骤仍为空。
- 宝灯的文化寓意仍为空。
- 7条艺术精品网页标题的当次原网页复核仍未完成，只保留项目现有C级记录。
- 95件官网图片训练授权仍为 `unknown`，不可转为训练数据。
- 名称关系没有升级为图像级验证；本轮没有对47件对象逐图进行纹样或工艺鉴定。

