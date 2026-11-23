@echo off
setlocal
set "SRC=%~dp0files"
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
if not exist "%SP%\" (
    echo [ERROR] folder not found: %SP%
    echo Make sure %TARGET% is the ok-ww root ^(it should contain data\apps\ok-ww^).
    pause
    exit /b 1
)

copy /y "%SRC%\okww_cloud.pth" "%SP%\" >nul
copy /y "%SRC%\okww_cloud_hook.py" "%SP%\" >nul
if errorlevel 1 (
    echo [ERROR] copy failed. Run this script as administrator.
    pause
    exit /b 1
)

echo [OK] installed to:
echo      %SP%
echo.
echo Verifying...
pushd "%TARGET%\data\apps\ok-ww\working"
"..\python\python.exe" -c "import ok.util.window as w, config; print('  WGC available :', bool(w.windows_graphics_available())); print('  cloud viewport:', config.config['browser']['resolution'])"
popd
echo.
echo Restart ok-ww, then pick "Cloud" in the device dropdown.
echo Log: %TARGET%\data\apps\ok-ww\cloud\hook.log
pause
