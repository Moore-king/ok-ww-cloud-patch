@echo off
chcp 65001 >nul
setlocal
set "TARGET=%~1"

if not "%TARGET%"=="" goto have_target
for %%D in ("D:\ok-ww" "%USERPROFILE%\ok-ww" "C:\ok-ww" "%USERPROFILE%\Desktop\ok-ww") do (
    if not defined TARGET if exist "%%~D\data\apps\ok-ww\python\Lib\site-packages" set "TARGET=%%~D"
)
:have_target
if "%TARGET%"=="" (
    echo 未自动找到 ok-ww 目录。
    set /p TARGET=请输入 ok-ww 根目录，例如 D:\ok-ww: 
)
if "%TARGET%"=="" (
    echo [取消] 未提供目录。
    pause
    exit /b 1
)

set "SP=%TARGET%\data\apps\ok-ww\python\Lib\site-packages"
if not exist "%SP%\okww_cloud.pth" (
    echo [提示] 未安装补丁，无需卸载。
    pause
    exit /b 0
)

del /q "%SP%\okww_cloud.pth" 2>nul
del /q "%SP%\okww_cloud_hook.py" 2>nul
echo [完成] 补丁已移除，ok-ww 恢复原版行为。
echo        重启 ok-ww 后生效。
pause
