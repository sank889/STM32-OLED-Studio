@echo off
chcp 65001 >nul
echo 正在安装依赖...
py -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo 若 py 不可用，请尝试: D:\anaconda3\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)
echo.
echo 安装完成！运行 run.bat 启动程序。
pause
