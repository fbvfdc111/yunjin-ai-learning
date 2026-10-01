# Windows CMD 启动说明

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
