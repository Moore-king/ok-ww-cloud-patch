@echo off
chcp 65001 >nul
setlocal
set "SRC=%~dp0files"
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
if not exist "%SP%\" (
    echo [错误] 这个目录不存在：
    echo        %SP%
    echo 请确认 %TARGET% 是 ok-ww 的解压根目录（里面应有 data\apps\ok-ww）。
    pause
    exit /b 1
)

copy /y "%SRC%\okww_cloud.pth" "%SP%\" >nul
copy /y "%SRC%\okww_cloud_hook.py" "%SP%\" >nul
if errorlevel 1 (
    echo [错误] 复制失败，请用管理员身份运行本脚本。
    pause
    exit /b 1
)

echo [完成] 已安装到：
echo        %SP%
echo.
echo 正在验证...
pushd "%TARGET%\data\apps\ok-ww\working"
"..\python\python.exe" -c "import ok.util.window as w, config; print('  WGC 可用 :', bool(w.windows_graphics_available())); print('  云窗口尺寸:', config.config['browser']['resolution'])"
popd
echo.
echo 请重启 ok-ww，然后在左上角设备下拉中选择「云游戏 (Cloud)」。
echo 日志：%TARGET%\data\apps\ok-ww\cloud\hook.log
pause
