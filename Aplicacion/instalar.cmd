@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"
call "%~dp0preparar.cmd"
if errorlevel 1 (
    echo.
    echo La preparacion no termino. Revisa el mensaje anterior.
    if /I "%~1"=="--verificar" exit /b 1
    pause
    exit /b 1
)
echo.
echo Listo. Abre iniciar.cmd para probar tus fotos.
if /I "%~1"=="--verificar" exit /b 0
pause
exit /b 0
