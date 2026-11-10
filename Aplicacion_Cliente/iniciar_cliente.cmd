@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
set "PYTHONUTF8=1"
cd /d "%~dp0\.."

echo ==============================================================
echo   Walmart Vision - Operaciones de Tienda (Version Cliente)
echo   Puerto por defecto: http://127.0.0.1:8098
echo ==============================================================

if exist ".venv-modelo\Scripts\python.exe" (
    echo [GPU] Iniciando con entorno .venv-modelo...
    set "VISION_CLIENT_PYTHON=%~dp0..\.venv-modelo\Scripts\python.exe"
    goto iniciar
) else (
    call "%~dp0..\Aplicacion\preparar.cmd"
)
if errorlevel 1 goto error
set "VISION_CLIENT_PYTHON=%~dp0..\Aplicacion\.entorno-py312\Scripts\python.exe"
:iniciar
if /I "%~1"=="--verificar" goto verificar
"%VISION_CLIENT_PYTHON%" "%~dp0app_cliente.py" --port 8098 --open %*
if errorlevel 1 goto error
exit /b 0
:verificar
"%VISION_CLIENT_PYTHON%" "%~dp0app_cliente.py" --check
exit /b %errorlevel%
:error
echo No se pudo iniciar la aplicacion cliente. Revisa el detalle anterior.
if /I "%~1"=="--verificar" exit /b 1
pause
exit /b 1
