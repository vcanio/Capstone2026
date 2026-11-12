@echo off
setlocal
cd /d "%~dp0..\.."
set "PY_GPU=.\.venv-modelo\Scripts\python.exe"
set "PY_CPU=.\Aplicacion\.entorno-py312\Scripts\python.exe"
if exist "%PY_GPU%" (
  "%PY_GPU%" .\Laboratorio\Ocupacion\visor_linea_a.py --port 8097 --open
) else (
  "%PY_CPU%" .\Laboratorio\Ocupacion\visor_linea_a.py --port 8097 --open
)
endlocal
