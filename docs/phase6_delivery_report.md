# Phase 6 交付报告：南京云锦织造教学型数字孪生原型

交付日期：2026-09-07。

当前实现的是**知识驱动、状态驱动的南京云锦织造教学型数字孪生原型**。
当前数字状态由用户交互驱动，而不是由实体织机传感器驱动；
物理实体—数字模型的实时双向同步属于后续工作。

## 1. 唯一代码基线与独立目录

- 原 ZIP：`yunjin_ai_mvp_phase5_round3_core_20260907.zip`。
- 原 ZIP SHA-256：`4866434272C083C24F65EEDDEBA26F1D1147F084ED9A349CECAC0058DA76AAE6`。
- 从该 ZIP 建立独立目录 `work/yunjin_ai_mvp_phase6_20260907`，没有从更早版本重新开发。
- ZIP 内305个文件直接提取并建立逐文件SHA-256清单；原ZIP未修改。
- 历史报告继续原样保留，历史待验收表述不覆盖用户随后已完成的Windows网页、Dots Base64和知识问答人工验证。

## 2. 实际修改与新增文件

旧文件只修改2个：

| 文件 | 变化 |
| --- | --- |
| `app.py` | 新增数字织机导航及页面调用；更新首页、数据与可信AI的阶段说明 |
| `README.md` | 新增Phase 6定位、体验、运行、验证及边界说明；保留历史说明 |

新增16个文件：

| 文件 | 用途 |
| --- | --- |
| `data/digital_twin/twin_states.json` | 六个教学状态、逐事实引用、来源、追问和证据缺口 |
| `src/yunjin_ai/digital_twin.py` | 状态数据校验、不可变TwinState、事件转换、可见快照 |
| `src/yunjin_ai/digital_twin_svg.py` | 读取运行时教学值生成自绘HTML/SVG |
| `src/yunjin_ai/digital_twin_page.py` | 原生控件、图形、状态面板、证据说明及助手入口 |
| `tests/test_phase6_digital_twin.py` | 状态、证据、转换及SVG行为测试 |
| `tests/test_phase6_streamlit.py` | 页面交互、六个AI跳转入口、iframe输出、图片隔离测试 |
| `tests/test_phase6_protection.py` | 基线文件、治理、训练门禁和宣传边界测试 |
| `scripts/phase6_health_check.py` | 只读健康检查；支持原ZIP核验及保护结果输出 |
| `docs/phase6_baseline_manifest.json` | 原ZIP305个文件的字节哈希和大小 |
| `docs/phase6_protection_result.json` | 基线全部文件的预期／实际哈希和保护结果 |
| `docs/phase6_health_check_result.json` | Phase 6实际健康检查结果 |
| `docs/phase6_legacy_health_results.json` | 原四项健康检查的本轮结果，原历史报告未覆盖 |
| `docs/phase6_test_results.txt` | 最终测试结果、命令、运行环境 |
| `docs/phase6_test_results.xml` | 最终JUnit机器可读结果 |
| `docs/phase6_browser_acceptance.md` | 实际浏览器验收及发现问题的修复记录 |
| `docs/phase6_delivery_report.md` | 本报告 |

依赖安装目录、临时脚本、缓存和测试过程文件不作为交付代码打包。`requirements.txt`与原ZIP一致。

## 3. 实际产品功能

主导航为：首页｜AI探锦｜数字织机｜AI文化助手｜数据与可信AI。

数字织机提供SVG教学视图、当前步骤与操作者说明、工艺事实、进度、上一步、执行当前步骤、下一步、
自由探索、按顺序体验、重新开始、减少动态效果、当前知识来源、证据范围、资料缺口及AI文化助手入口。

“数字孪生状态”区域持续可见，展示当前阶段、模式、当前步骤是否已执行、已执行状态、重播次数、
与当前步骤对应的教学值和最近变化；可展开查看完整运行时对象。

页面明确显示：**交互示意｜非织机机械结构精确仿真**。
六个状态是教学抽取，不代表百余道工序的完整流程，也不是正式工艺编号或完整操作规程。

## 4. 六状态及真实运行时Twin State

事件链为：原生控件回调 → `transition()`验证并返回新TwinState → 更新会话对象 → 由SVG读取新状态渲染。
阶段索引仅用于教学顺序和位置显示；图形内容由运行时教学值决定。

至少维护：`current_stage`、`executed_stages`、`mode`、`current_stage_executed`、`replay_count`。
另有 `teaching`、`revision`、`last_action`、`last_changes`，不包含传感器或物理测量值。

| 状态 | 运行时变化 | 直接复用知识 |
| --- | --- | --- |
| 图案设计 | `sketch_visible`由False变True，显示原创几何草图 | KB003，事实1、2 |
| 挑花结本 | `carrier_visible`由False变True，显示规则化线结符号 | KB019，事实1、2 |
| 织造准备 | `preparation_ready`由False变True，点亮教学准备标记 | KB003事实1、KB004事实2 |
| 拽花工提经 | `warp_emphasis`由rest变a，重播时a/b切换 | KB004，事实1、2 |
| 织手织造 | `weft_direction`由rest变right，重播时left/right切换 | KB004，事实1、2 |
| 织造成纹 | `pattern_bands`从0逐次变1、2、3，三段全显示后完成 | KB003事实1、KB004事实1、2 |

A/B是界面强调组；left/right是提示方向；三段是界面分段。它们不对应真实经线编号、提经顺序、
穿纬规定、织造次数、工序数量或产量。SVG坐标和过渡时长为界面设计值，不是机械参数。

自由探索不会执行前置步骤，也不会补造中间状态。返回顺序模式会定位到最早未完成步骤。
重复执行已完成步骤增加重播次数，不增加已执行步骤数量；状态被保存在当前会话中。
不同会话使用不同对象，未设置数据库或永久学习记录。

## 5. 知识复用、角色与AI联动

原25条知识、12个来源及其逐事实证据范围保持字节不变。每个教学状态的`claim_refs`指向原知识事实，
`source_ids`与引用事实的来源集合严格匹配。文化事实直接读取原文；教学操作、图形比喻和证据缺口单独展示。
S10继续保留B级及其原有核验状态，不被升级为技术标准。

图案设计、挑花结本、织造准备均不创造统一岗位名称。拽花工与织手的分工说明来自KB004。
织造成纹是结果展示，不新增“成纹工”等岗位。

追问沿用`open_cultural_guide()`和`apply_guide_handoff()`，切到原助手并预填问题，清除上一次答案显示，
保留原会话历史。用户提交后仍由`answer_from_knowledge()`返回证据约束回答。
没有另建聊天系统，不把教学状态当作文化事实输入，也不自动发起视觉API调用。

六个预设追问的实际命中结果见健康报告。图案设计追问作为延伸学习命中KB010；
双人协作问题沿用原检索规则命中KB001和KB004，保留现有知识回答行为。

## 6. 自动测试与健康检查

最终自动测试：**93 passed，另有29 subtests passed**，退出码0，用时13.57秒。
其中原Round 3测试49项保持不变；新增Phase 6测试44项（含参数化场景）。
测试数字是软件验收结果，不是识别准确率或模型性能指标。

最终环境：Windows 11、Python 3.12.14、Streamlit 1.63.0、pytest 9.1.1、OpenAI SDK 2.54.0、
Pillow 12.3.0、PyYAML 6.0.3。使用任务内独立运行依赖；没有修改系统Python或原基线依赖声明。

最终命令：

```text
python -m pytest tests -q -p no:cacheprovider --junitxml=docs/phase6_test_results.xml
```

验收过程中有一次原页面测试触发AppTest的15秒超时，其余92项和29个子场景通过。
停止浏览器验收服务后，在不改原测试、不延长其超时阈值的情况下完整复跑，得到上述93项全部通过结果。
本报告不把该次超时解释为已证明的产品功能缺陷，也不隐藏它。

| 健康检查 | 实际结果 |
| --- | --- |
| `phase4_health_check.py` | 退出码0，通过 |
| `phase5_health_check.py` | 退出码0，通过 |
| `phase5_round2_health_check.py` | 退出码0，通过 |
| `phase5_round3_health_check.py` | 退出码0，通过 |
| `phase6_health_check.py --baseline-zip …` | 退出码0，ok=true |
| `phase6_health_check.py --baseline-zip … --protection-only` | 退出码0，ok=true |

旧四项结果单独保存于`phase6_legacy_health_results.json`，没有覆盖旧阶段的报告。
Dots保护测试继续覆盖请求形状、JPG/PNG Base64字节、内存压缩及失败回退；OpenAI/local_cv代码和既有测试保留。
本轮没有调用真实Dots/OpenAI API；用户此前已完成的真实Dots Base64成功验证只作为历史已验收事实记录。

## 7. Round 3保护与数据治理

305个基线文件中，303个逐字节不变；只有允许修改的`app.py`、`README.md`发生变化。
未发现缺失文件或非预期修改。`data/official`下145个文件逐文件SHA-256差异为0。
通过对原ZIP与现代码的AST比对，`app.py`原有函数及AI探锦、AI文化助手业务分支保持一致。

| 关键保护文件 | SHA-256（与Round 3相同） |
| --- | --- |
| `src/yunjin_ai/vision.py` | `F1CCDB58311E63588466431B440235417D6F5595D31E4917C55B55DEC2FDEA09` |
| `tests/test_phase4_dots.py` | `B18DCE6BA889B5D3B064111A7A1D4A27BBF0F2552FDC5126AF66DC1F1ABDDCF7` |
| `data/metadata/official_metadata.csv` | `915F8C4C9605D912DA7ED8B8307957B4D000DEAED679BA250D4670BD49788823` |
| `data/metadata/official_level2_candidate_labels.csv` | `F326EC87F79CEF1E0B474D3515B8954B1460F7C0735A7C2E6750B15A93790C9B` |
| `docs/phase2_audit_results.json` | `8FDADF9470E85DA063883A55B39F398FDB9D6EF82609647508C94FAAA8052C39` |

完整清单覆盖知识库、来源、47件对象知识关系、训练门禁、其他原测试与配置。

| 治理不变量 | 核验值 |
| --- | --- |
| 官网对象总数 | 95 |
| 南京云锦对象 | 47 |
| 其他织锦对象 | 48 |
| 可训练官网对象 | 0 |
| `authorization_status=unknown` | 95 |
| `usable_for_training=false` | 95 |
| 南京云锦关系记录 | 47；19件有关系，共35条显式关系 |

两个训练门禁仍拒绝当前数据。未执行训练，未生成Accuracy、Precision、Recall、F1、Loss、混淆矩阵或模型权重。
SVG不读取官网图片；页面交互测试将图片读取和视觉分析设为失败哨兵，六状态运行仍通过。

## 8. 浏览器验收与实现调整

实际浏览器走通六状态，验证成纹1/3→2/3→3/3、自由探索重播、现有AI助手完整回答链、返回后状态保留，
并观察390×844窄屏的图形和说明纵向布局。详见`phase6_browser_acceptance.md`。

原计划优先使用`st.html`；实际发现Streamlit 1.63.0清理内联SVG，因此改为原生`st.iframe`显示受控HTML/SVG。
新增测试检查真实发送到iframe的文档与当前TwinState完全对应。没有引入Unity、Three.js或复杂3D模型。

## 9. 未实现能力与已知限制

- 未接入实体传感器或实体织机实时数据。
- 未实现物理实体与数字模型的实时双向同步。
- 未建立物理参数仿真，包括经线精确位置、提经高度、运动速度、机械传动参数。
- 未完成专家级机械结构验证，SVG不是织机结构复原。
- 不掌握真实花本编码；没有完整百余道工序、装造步骤或正式岗位标准。
- 无永久学习记录；当前会话状态不是现场织造记录、学习成绩或熟练度证明。
- 几何图案是原创教学符号，不是馆藏图像、真实云锦作品复原或织物生成算法。
- 浏览器已验收桌面及窄屏布局；尚无跨浏览器全面兼容性、真实手机和屏幕阅读器专项验收。
- 快速连续操作需等待上一轮界面重绘完成；不提供实时性或工业控制保证。
- 本轮未重新进行真实Dots/OpenAI调用；自动化外部调用测试使用mock。

## 10. 最终归档

最终ZIP：`yunjin_ai_mvp_phase6_teaching_twin_20260907.zip`。
ZIP在最终自动测试、五项健康检查及Round 3保护核验通过后生成。
ZIP包含321个文件（305个基线文件加16个新增文件），不包含运行依赖、临时脚本、缓存或真实凭据。

归档SHA-256在ZIP生成后计算，保存于同目录`yunjin_ai_mvp_phase6_teaching_twin_20260907.sha256`。
为避免归档自引用哈希，本报告在ZIP内不写入包含自身的ZIP哈希。
打包后的逐文件一致性结果另见外部`phase6_package_verification.json`。

外部交付报告路径：`outputs/phase6_delivery_report.md`；ZIP内报告路径：`docs/phase6_delivery_report.md`。
