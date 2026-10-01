@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
  set "PY=py -3"
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo 未找到 Python。请先安装 Python 3.10+，并勾选 Add Python to PATH。
    pause
    exit /b 1
  )
  set "PY=python"
)

echo 正在安装/检查依赖...
%PY% -m pip install -r requirements.txt
if errorlevel 1 (
  echo 依赖安装失败。请检查网络、Python 和 pip。
  pause
  exit /b 1
)

echo 正在启动南京云锦 Streamlit 项目...
%PY% -m streamlit run app.py
pause
