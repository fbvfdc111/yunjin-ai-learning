# Phase 6.5 Human-Loom Collaboration Delivery

本版本基于 `yunjin_ai_mvp_3d_digital_twin_20261006.zip` 解压后复制开发，原始稳定版保存在 Work 的 `stable_original` 目录中，未覆盖原版。

## 本轮目标

将原有 `3D Process Digital Twin / 3D织造过程数字孪生` 升级为：

```text
3D Human-Loom Collaborative Digital Twin Prototype
三维人—织机协同数字孪生原型
```

重点不重做底层逻辑，只升级 3D 表现层，让评委能直接看出南京云锦大花楼织机中“上层拽花工 + 下层织手”的协同关系。

## 主要修改

- 保留原有六阶段状态机、模拟张力、模拟提经位移、协同状态、实时曲线、教学模式、2D SVG 教学仿真、Dots、CLIP、AI探锦和 AI文化助手。
- 将 3D 场景改为上下结构：上层提花工作区、提经绳、较高木质框架、密集经线、下层织造区、梭子/纬线和织物成纹区域。
- 加入两位可理解的人形角色：拽花工位于上层，织手位于下层织造位置。
- 第 4 阶段：拽花工 `ACTIVE`，织手 `WAITING`，经线按 `lift_mm` 提升。
- 第 5 阶段：拽花工 `HOLDING` 保持提经，织手 `ACTIVE`，梭子/纬线横向穿过织物区域。
- 第 6 阶段：经线复位，织物区域增加纹样段，表现一次协同循环完成。
- 移除页面顶部旋转/俯视/缩放滑杆，改为在 3D 场景中直接鼠标拖动旋转、滚轮缩放。
- 将 3D 场景扩大为页面主视觉，张力、位移、双人状态、协同状态和曲线改为辅助信息。
- 保留 `正在发生什么？ / What's happening?` 中英双语说明，并随六阶段变化。

## 边界说明

本版本仍是 `Simulation-driven / Simulated Data` 教学仿真原型：

- 不连接真实南京云锦织机。
- 不使用真实传感器。
- 不声称真实机械参数。
- 不声称一比一机械复原。
- 不声称已经经过云锦工匠验证。

## 已做验证

- `compileall src tests` 语法检查通过。
- 核心 3D 协同逻辑断言通过：第 4 阶段提经、第 5 阶段保持提经与梭子穿纬、第 6 阶段成纹循环、鼠标交互提示、Simulation-driven 边界声明。

当前 Codex 内置 Python 环境未安装 `pytest` 和 `streamlit`，因此未在此环境执行完整 Streamlit 浏览器级测试。项目 ZIP 保留 `requirements.txt` 和 `START_WINDOWS_CMD.bat`，用户 Windows 电脑可按启动说明自动安装依赖并运行。
