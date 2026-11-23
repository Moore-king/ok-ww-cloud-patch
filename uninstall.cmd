@echo off
setlocal
set "TARGET=%~1"

if not "%TARGET%"=="" goto have_target
for %%D in ("D:/ok-ww" "%USERPROFILE%\ok-ww" "C:/ok-ww" "%USERPROFILE%\Desktop\ok-ww") do (
    if not defined TARGET if exist "%%~D\data\apps\ok-ww\python\Lib\site-packages" set "TARGET=%%~D"
)
:have_target
if "%TARGET%"=="" (
    echo ok-ww folder not found automatically.
    set /p TARGET=Enter ok-ww root folder ^(e.g. D:/ok-ww^): 
)
if "%TARGET%"=="" (
    echo [CANCELLED] no folder given.
    pause
    exit /b 1
)

set "SP=%TARGET%\data\apps\ok-ww\python\Lib\site-packages"
if not exist "%SP%\okww_cloud.pth" (
    echo [INFO] patch is not installed, nothing to do.
    pause
    exit /b 0
)

del /q "%SP%\okww_cloud.pth" 2>nul
del /q "%SP%\okww_cloud_hook.py" 2>nul
echo [OK] patch removed. Restart ok-ww to get stock behaviour.
pause
