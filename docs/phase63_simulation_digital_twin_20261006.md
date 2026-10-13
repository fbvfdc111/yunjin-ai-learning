# Phase 6.3 Simulation-driven Digital Twin Prototype

本版本基于 `yunjin_ai_mvp_phase62_dots_stability_fix_20261002.zip` 复制开发，原稳定 ZIP 未被修改。

## 本次新增

- 在“数字织机”页面新增 `Teaching Mode / 教学模式` 与 `Live Simulation Mode / 实时仿真模式` 切换。
- 保留原六阶段教学模式、知识测验、AI文化助手跳转、Dots/CLIP/AI探锦相关代码路径。
- 新增无硬件实时仿真核心：六阶段自动状态机、模拟经纱张力、模拟提经位移。
- 新增拽花工与织手状态：`ACTIVE`、`WAITING`、`READY`、`MONITORING`。
- 新增协同状态：`SYNCHRONIZED`、`WAITING`。
- 新增张力-时间与位移-时间实时曲线。
- 中英同页展示关键模式名、指标名、状态名和数据源。

## 真实性边界

页面明确标注：

- `Simulated Data / 仿真数据`
- `hardware_connected=False`
- `real_sensor_data=False`
- `sensor_input=None`

本版本不连接真实织机、真实传感器、摄像头或实验采集数据；所有动态数值仅用于教学展示和比赛原型演示，不代表真实南京云锦织机测量值。

## 修改文件

- `src/yunjin_ai/digital_twin_simulation.py`
- `src/yunjin_ai/digital_twin_page.py`
- `tests/test_phase63_live_simulation.py`
- `requirements.txt`

## 本地核验

已通过：

```text
python -m compileall -q src tests app.py
simulation core checks passed
```

未完整运行 `pytest tests -q`，原因是当前 Codex 运行环境的 Python 缺少 `pytest` 与 `streamlit` 包。项目自身仍保留原有 Windows 启动脚本，用户电脑首次启动时会按 `requirements.txt` 安装运行依赖。

## Windows CMD 启动

最简单方式：

1. 解压本项目 ZIP。
2. 双击项目里的 `START_WINDOWS_CMD.bat`。
3. 浏览器自动打开后，进入“数字织机”。
4. 在页面里选择 `Live Simulation Mode / 实时仿真模式`。

手动 CMD 方式：

```cmd
cd /d 解压后的项目文件夹
py -3 -m pip install -r requirements.txt
py -3 -m streamlit run app.py
```

如果 `py -3` 不可用，改用：

```cmd
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
