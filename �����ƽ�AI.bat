@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

call :say 5q2j5Zyo5ZCv5Yqo5LqR6ZSmIEFJ77yM6K+356iN5YCZLi4u

where python >nul 2>&1
if errorlevel 1 goto missing_python

python --version >nul 2>&1
if errorlevel 1 goto broken_python

python -m streamlit --version >nul 2>&1
if errorlevel 1 goto missing_streamlit

if not exist "app.py" goto missing_app

call :say 546v5aKD5qOA5p+l6YCa6L+H77yM5q2j5Zyo5omT5byA5rWP6KeI5Zmo5bm25ZCv5Yqo5bqU55SoLi4u
start "" "http://localhost:8501"
python -m streamlit run app.py

if errorlevel 1 goto launch_failed
exit /b 0

:missing_python
call :say W+mUmeivr10g5pyq5qOA5rWL5YiwIFB5dGhvbu+8jOaXoOazleWQr+WKqOS6kemUpiBBSeOAguivt+WFiOWuieijhSBQeXRob27vvIzlubblnKjlronoo4Xml7bli77pgInigJxBZGQgUHl0aG9uIHRvIFBBVEjigJ3jgILlronoo4XlrozmiJDlkI7vvIzor7fph43mlrDlj4zlh7vmnKzmlofku7bjgII
pause
exit /b 1

:broken_python
call :say W+mUmeivr10gUHl0aG9uIOW9k+WJjeS4jeWPr+eUqO+8jOivt+ajgOafpSBQeXRob24g5a6J6KOF5Y+KIFBBVEgg546v5aKD5Y+Y6YeP44CC5L+u5aSN5ZCO77yM6K+36YeN5paw5Y+M5Ye75pys5paH5Lu244CC
pause
exit /b 1

:missing_streamlit
call :say W+mUmeivr10g5pyq5qOA5rWL5YiwIFN0cmVhbWxpdO+8jOaXoOazleWQr+WKqOS6kemUpiBBSeOAguivt+aMieS4i+aWueWRveS7pOWuieijheS+nei1lu+8jOWujOaIkOWQjumHjeaWsOWPjOWHu+acrOaWh+S7tuOAgg
echo     python -m pip install -r requirements.txt
echo     python -m pip install streamlit
pause
exit /b 1

:missing_app
call :say W+mUmeivr10g5b2T5YmN6aG555uu55uu5b2V5Lit5pyq5om+5YiwIGFwcC5weeOAguivt+ehruiupOacrOWQr+WKqOaWh+S7tuS9jeS6juS6kemUpiBBSSDpobnnm67moLnnm67lvZXjgII
pause
exit /b 1

:launch_failed
call :say W+mUmeivr10g5LqR6ZSmIEFJIOWQr+WKqOWksei0pe+8jOivt+afpeeci+S4iuaWuemUmeivr+S/oeaBr+OAgg
pause
exit /b 1

:say
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -Command "$b='%~1'; while ($b.Length -band 3) {$b+='='}; [Console]::OutputEncoding=[Text.Encoding]::UTF8; [Console]::WriteLine([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($b)))"
exit /b
