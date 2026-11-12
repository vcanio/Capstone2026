@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0..\.."

set "PY=Aplicacion\.entorno-py312\Scripts\python.exe"
if not exist "%PY%" set "PY=.venv-modelo\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

echo Iniciando etiquetador rapido de disponibilidad V3...
"%PY%" "Laboratorio\Ocupacion\etiquetador_ocupacion.py" --port 8096 --open
endlocal
