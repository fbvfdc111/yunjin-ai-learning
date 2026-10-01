# Phase 5 第一轮参赛产品化交付记录

日期：2026-09-06

## 本轮定位

本轮没有重建项目，也没有训练分类器。工作基于 Phase 4 + Dots Base64 工作副本，围绕评委和普通用户可理解的产品流程，统一为：

```text
用户上传图片 → AI视觉理解 → 可信文化知识检索
→ 证据约束解释 → AI文化助手继续学习
```

## 已完成

- 首页将产品价值、三项核心能力和完整学习链路放到第一层，95 个官网对象及训练阻断事实移到“项目数据基础”。
- AI识锦默认使用 Dots；provider、公网 URL、endpoint、transport 和 fallback 原因均收纳在技术详情中。
- Dots 视觉结果按纹样与主体、构图、色彩和视觉关键词整理，固定展示专业鉴定边界。
- 新增视觉线索专用检索：泛化词不触发具体纹样知识，只检索直接关键词匹配并设置最低分数；人工确认主题权重更高。
- 没有达到门槛时明确显示“当前视觉线索不足以匹配到高可信度的文化知识”。
- AI识锦根据已检索文化主题生成学习问题，可切换到 AI文化助手并预填问题；问题措辞不把“相关文化知识”改写成图片鉴定结论。
- AI文化助手继续使用本地 evidence-grounded RAG，分区显示回答、来源、证据等级和后续问题；证据不足时不调用大模型补写。
- 数据与可信AI页保留全部数据治理结论，并将专业字段和 provider 细节放入折叠区域。

## Dots 真实验证状态

自动化测试继续使用 mock HTTP 和假 Key，不调用真实 Dots API。用户已在实际运行环境完成一次真实 Base64 本地图片调用，页面显示：

- `provider=dots:dots3-note-prev`
- `image_transport=base64_data_url`
- fallback：无

该记录证明一次真实调用链成功，不代表模型准确率、识别效果或系统性能已经通过评测。

## 未改变的治理结论

- Official Evidence Database：95
- 南京云锦：47；其他织锦：48
- 95 个 `authorization_status=unknown`
- 95 个 `usable_for_training=false`
- 南京云锦可直接训练对象：0
- 未训练监督分类器，无 Accuracy、Precision、Recall、F1、Loss、confusion matrix 或模型权重

## 后续限制

- 文化知识库规模仍为 15 条知识、7 个来源；视觉关键词可能因模型措辞变化而无法通过严格门槛，此时系统宁可提示线索不足。
- 一次 Dots 成功调用不是正式数据集评测，仍需经许可样本、专家审阅和系统化测试。
- Digital Twin、Immersive Learning、Community Participation 均未实现，继续列为 Future Work。
