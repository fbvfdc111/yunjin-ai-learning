# Phase 6.6 3D Scene V2 交付说明

本轮基于用户提供的 `yunjin_ai_mvp_3d_human_loom_collab_20261006.zip` 建立新的工作副本，原 ZIP 与原稳定目录未覆盖。

## 修改重点

- 保留原有六阶段状态机、simulation signals、Human Coordination、Dots、AI探锦、AI文化助手、教学模式和知识测验逻辑。
- 重构 `src/yunjin_ai/digital_twin_3d.py` 的 3D 主场景。
- 织机视觉升级为更高大的多层木构教学重建，包含顶部花楼木架、上层工作平台、拽花/提花控制区、密集经线与梭口区、下层织造与卷布区、经轴/卷布轴、横梁、立柱、斜撑、综线/控制线等构件。
- 两位工匠升级为低多边形 3D 人形，包含头、躯干、上臂、前臂、大腿、小腿；拽花工位于明显更高的上层工作区，织手位于下层织造区。
- 第 4 阶段表现拽花工拉提控制线、经线提升、织手等待。
- 第 5 阶段表现拽花工保持提经、织手伸臂操作、梭子/纬线横穿。
- 第 6 阶段表现经线复位、织物区域增加纹样段，完成一次协同循环。
- 保留鼠标拖动旋转、滚轮缩放，默认视角优先展示“高大的多层织机 + 上层拽花工 + 下层织手”。
- 强化边界说明：`Visual teaching reconstruction inspired by traditional Nanjing Yunjin drawloom structure; not a dimensionally accurate mechanical reconstruction.` 并继续标注 `Simulation-driven / Simulated Data`。

## 验证结果

当前 Codex 环境缺少项目运行所需的 `streamlit` 与 `pytest` 包，因此未能在本环境执行完整 Streamlit 页面测试。

已完成以下可运行检查：

```cmd
python -m py_compile src\yunjin_ai\digital_twin_3d.py
python -m compileall src tests -q
python tests\test_phase66_3d_scene_v2.py
```

结果：新增 3D Scene V2 断言通过，源码编译通过。

新增测试：

```text
tests/test_phase66_3d_scene_v2.py
```

该测试检查多层织机结构、低多边形双人角色、上下高度差、阶段 4/5/6 动作映射、仿真数据边界声明。

## 启动方式

解压 ZIP 后进入项目目录，双击：

```text
START_WINDOWS_CMD.bat
```

或在项目目录地址栏输入 `cmd` 回车，手动执行：

```cmd
py -3 -m pip install -r requirements.txt
py -3 -m streamlit run app.py
```

如果 `py -3` 不可用，改用：

```cmd
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

打开网页后进入：

```text
数字织机 -> Live Simulation Mode / 实时仿真模式
```
