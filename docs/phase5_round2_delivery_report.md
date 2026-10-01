# Phase 5 Round 2 真实验收修复交付报告

日期：2026-09-06

## 基线与范围

本轮唯一基线为 `yunjin_ai_mvp_phase5_round1_productized_20260906.zip`，SHA-256：
`8AB32E360CAEDBB06251E0DD9D4028A4665C7E4337E2E77BB83997E423889AFF`。

本轮没有重新开发架构、训练分类器或扩充文化事实。Dots prompt、Base64 data URL、
Dots provider、OpenAI provider 与 local_cv fallback 没有修改。

## 三个验收问题与修复

### 1. 视觉结果误返回 KB015

Round 1 的视觉匹配同时允许正向和反向子串；“标签”可反向匹配“候选标签”。一个匹配计
6 分，而最低门槛也是 6 分，因此 KB015 会进入文化结果。

Round 2 为每条知识新增：

- `knowledge_use`：`cultural_content`、`process/history`、`governance/methodology`；
- `answer_terms`：该条证据能够直接回答的问题词组。

视觉检索只使用文化内容与工艺/历史条目，不使用治理/方法条目填充 Top-K；自动视觉匹配
删除反向子串规则，并将标签、编号、边框、背景、工笔画、花鸟画等场景/载体词纳入清洗。
飞鸟、燕子、柳枝等当前没有知识证据时返回空结果，不新增其文化寓意。

### 2. AI文化助手答非所问

`answer_from_knowledge()` 现在先执行 answerability gate。只有问题满足知识条目显式声明的
`answer_terms`，该条目才可进入检索；图片上下文只能帮助排序，不能建立可回答性。来源 ID
缺失时同样拒答。

四个支持问题分别返回：

- 妆花是什么？→ KB008；
- 南京云锦有哪些主要品种？→ KB007；
- 云锦为什么需要手工织造？→ KB004；
- 八宝纹有什么文化寓意？→ KB013。

“视觉线索与文化知识之间为什么不能等同于鉴定结论？”当前没有足够直接证据，返回“证据
不足”，不再输出 KB015。正文移除显眼的 KB 编号，来源和证据等级保留在折叠区。

### 3. Streamlit removeChild

在 Streamlit 1.63.0、Python 3.12.14、无扩展 Chromium/Edge 环境中，对 Round 1 执行了上传、
local_cv fallback、无匹配、跳转、回答及三轮切换，未复现 `removeChild`。因此不能把用户环境
中的一次异常确定归因于单一应用代码缺陷；浏览器翻译/扩展等外部 DOM 修改仍是可能条件。

Round 1 的应用侧风险窗口是：受控 `st.tabs(on_change="rerun")`、所有隐藏标签内容仍同时生成，
以及提交后动态插入大段回答组件树。Round 2 使用稳定的原生 `st.segmented_control` 导航，只生成
当前页面；问答用 `st.form` 提交、固定 `guide_answer_slot` 容器和原生 `st.chat_message`，没有加入
JavaScript、错误隐藏或 DOM hack。

## 产品体验调整

- 推荐问题只来自已检索文化主题；无匹配时提供知识库真实支持的通用文化问题，不再推荐治理问题。
- AI文化助手改为用户/助手消息布局，直接回答优先，来源与证据等级随后展开。
- 首页保留主标题与三项核心能力，将原始 KB 卡片改为“探索云锦文化”主题入口。
- 95/47/48/0 数据放入第二层折叠区，治理事实未隐藏。
- AI识锦第一屏只保留上传价值说明；Dots、API、provider、Base64、endpoint、transport 和 fallback
  均放入 Technical Details。
- 使用 Streamlit 原生主题形成克制的绛红、织金与暖白配色；未使用学校 Logo、外部背景图或来源不明素材。

## 自动化验证

`python -m unittest discover -s tests -v`：36/36 通过。

覆盖 Round 1 的 27 项测试及 Round 2 新增回归：飞鸟/柳枝/标签无 KB015、治理知识隔离、三类用途、
无匹配推荐、四个可回答问题、鉴定边界拒答、页面联动、多次页面切换与回答、无自定义 DOM、Dots
Base64、压缩、HTTP fallback、local_cv、OpenAI 保留和 95 对象治理不变量。自动化测试没有调用真实 API。

`scripts/phase5_health_check.py` 与 `scripts/phase5_round2_health_check.py` 均通过。

## 实际浏览器验收

通过 Playwright 驱动本机无扩展 Chromium 内核，实际连接运行中的 Streamlit 1.63.0：

- 场景 A：上传本地测试图片 → local_cv 可控 fallback → AI视觉观察 → 正确显示文化知识不足；
- 场景 B：AI文化助手询问“妆花是什么？”→ 返回 KB008 对应直接答案 → 可展开真实来源与 A 级证据；
- 场景 C：AI识锦无匹配推荐 → AI文化助手 → 获取回答，并继续三轮页面切换和不同问题回答。

结果：三个场景均通过；`pageerror=[]`、`consoleErrors=[]`、`removeChild/NotFoundError/React DOM=[]`。

## 数据治理核验

- Official Evidence Database：95；
- 南京云锦：47；其他织锦：48；
- 95 个 `authorization_status=unknown`；
- 95 个 `usable_for_training=false`；
- 南京云锦可直接训练对象：0；
- 知识事实仍为 15 条、来源仍为 7 个；
- 未训练监督分类器；没有 Accuracy、Precision、Recall、F1、Loss、confusion matrix 或模型权重。

## 当前限制

- 知识库仍只有 15 条知识、7 个来源；燕子、柳枝等没有直接证据时只能诚实返回不足。
- answerability 范围由显式元数据维护，新增知识时必须同步审阅问题词组。
- 无扩展浏览器验收不能证明所有浏览器翻译或扩展组合均无 DOM 冲突。
- Dots 的一次真实调用记录只证明链路可运行，不代表准确率或性能评测。
- Digital Twin、Immersive Learning、Community Participation 仍为 Future Work。
