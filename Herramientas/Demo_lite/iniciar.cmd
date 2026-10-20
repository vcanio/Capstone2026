@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
set "PYTHONUTF8=1"
cd /d "%~dp0"
echo Walmart Lite
echo.
call "%~dp0preparar.cmd"
if errorlevel 1 goto error
if /I "%~1"=="--verificar" (
    echo Preparacion verificada correctamente.
    exit /b 0
)
".entorno-py312\Scripts\python.exe" -u app.py --open %*
if errorlevel 1 goto error
exit /b 0
:error
echo.
echo No se pudo iniciar Walmart Lite. El detalle aparece arriba.
echo Si existe, revisa .runtime\instalacion.log dentro de esta carpeta.
if /I "%~1"=="--verificar" exit /b 1
pause
exit /b 1
