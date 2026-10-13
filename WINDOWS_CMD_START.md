# Windows CMD 启动说明

本 ZIP 是 3D Human-Loom Collaborative Digital Twin Prototype 的 V20 Exhibition 展示优先版，原稳定版没有被覆盖。

## 方法一：双击启动

解压 ZIP 后，双击项目根目录中的：

```text
START_WINDOWS_CMD.bat
```

它会进入项目目录、安装/检查依赖，然后执行：

```cmd
python -m streamlit run app.py
```

如果电脑没有把 Python 加入 PATH，请先安装 Python 3.10+，安装时勾选 `Add Python to PATH`。

## 方法二：手动用 CMD 启动

在项目目录地址栏输入 `cmd` 回车，然后运行：

```cmd
py -3 -m pip install -r requirements.txt
py -3 -m streamlit run app.py
```

如果 `py -3` 不可用，改用：

```cmd
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## 关于 Dots

本次修复没有更改 Dots 路径或配置。未配置 `DOTS_API_KEY` 时，AI探锦会按原逻辑明确回退到 `local_cv`；AI文化助手仍只使用本地知识库证据回答。

## 看 3D 人—织机协同

网页打开后进入：

```text
数字织机 → Exhibition Mode / 展示模式
```

此页面以沉浸式南京云锦大花楼织机展示为主角。V20 Exhibition 使用嵌入 Streamlit iframe 的 Three.js WebGL 渲染层，Python/Streamlit 仍负责六阶段数字孪生状态机和仿真数据。可以直接在 3D 场景上：

```text
鼠标拖动 = 旋转视角
鼠标滚轮 = 缩放场景
```

展示模式默认使用深色展陈舞台、暖色聚光、低角度镜头和更大的动作幅度；空间标签和教学说明被弱化，数据、曲线和运行状态收进折叠面板。第 4 阶段会自动靠近上层拉提区，第 5 阶段看向下层织口，第 6 阶段看向织口和卷取区，但过渡更偏连续运镜，不再把每一步当成课堂卡片切换。
V20 保留 V19 的五层织机结构：机身框架层、上层花楼/操作层、经线/开口过程层、下层织造/梭子/筘框层、卷布/成品层。经线主要用半透明层面表示密度，只保留少数高亮线表示正在运动的部分。上层拽花、开口、引纬、打纬和卷取被放进同一个连续协作循环。
教学页面仍保留在：

```text
数字织机 → Teaching Mode / 教学模式
```

更多实时数据页面仍保留在：

```text
数字织机 → Live Simulation Mode / 实时仿真模式
```

所有数值仍标注为 `Simulation-driven / Simulated Data`，不代表真实织机传感器或真实机械精度。

## 关于 3D 资产和纹样

V15 捆绑一个授权清楚的 CC0 rigged human GLB 人体基础模型：`assets/models/human-base-rigged.cc0.glb`。织机、梭子、经线、可见梭口、脚踏提示、打纬筘框、卷取提示、工匠衣袖/围裙/头巾、动作轨迹、连续时间轴、交叉渐变过渡、红金提花控制面、密集线帘、红色布床、机制高亮提示、纪录片式镜头和连续织物仍由 Three.js 程序化生成；连续布面的纹样是明确标注的教学视觉示意，不是历史实物云锦纹样复原。详细说明见：

```text
ASSET_LICENSES_V14.md
```
