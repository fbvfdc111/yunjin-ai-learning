# Phase 6.4 3D Process Digital Twin Delivery Report

## 基线

- 基于 `yunjin_ai_mvp_digital_twin_sim_20261006.zip` 复制开发。
- 未覆盖用户原始 2D 稳定版 ZIP。
- `original_stable_backup_20261002.zip` 仅作为稳定备份，不参与改写。

## 新增内容

- 新增 `src/yunjin_ai/digital_twin_3d.py`。
- `Live Simulation Mode / 实时仿真模式` 改为 3D 主视图：
  - 简化云锦织机框架。
  - 经线。
  - 纬线/梭子。
  - 织物区域。
  - 拽花工与织手位置。
  - 旋转、俯视角、缩放控制。
- 3D 视图直接读取现有 `SimulationSample`：
  - 第 4 阶段读取 `lift_mm`，驱动经线升起。
  - 第 5 阶段驱动梭子/纬线横向穿过。
  - 第 6 阶段显示经线复位和织物纹样段形成。
- 新增“正在发生什么？/ What's happening?”中英双语解释。
- 原有模拟张力、模拟位移、拽花工/织手状态、协同状态和实时曲线保留为辅助信息。

## 未改变内容

- 未删除或重写 AI探锦。
- 未破坏 Dots / local_cv provider 路径。
- 未删除 AI文化助手。
- 未删除 Teaching Mode / 教学模式。
- 未删除原 2D SVG 教学数字织机。
- 未引入真实硬件、真实传感器或真实机械精度声明。

## 可信边界

页面继续标注：

- `Simulation-driven`
- `Simulated Data / 仿真数据`
- `hardware_connected=False`
- `real_sensor_data=False`
- `sensor_input=None`

本版本是教学和比赛展示原型，不代表真实南京云锦织机测量值、真实传感器数据、真实机械结构复原或专家级机械精度。

## 已执行检查

当前 Codex 运行环境缺少 `pytest` 和 `streamlit`，因此未能在本环境完成 Streamlit 浏览器级测试。

已完成：

```text
python -m compileall app.py src tests
```

结果：通过。

已完成 3D 核心渲染检查：

```text
3D core render check passed
```

## 建议在用户电脑项目环境中执行

```cmd
py -3 -m pip install -r requirements.txt
py -3 -m pip install pytest
py -3 -m pytest tests -q
py -3 -m streamlit run app.py
```

进入：

```text
数字织机 → Live Simulation Mode / 实时仿真模式
```
