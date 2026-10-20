@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
if not exist "herramientas\uv.exe" (
    echo Falta una parte del paquete. Extrae todo el ZIP antes de abrir iniciar.cmd.
    exit /b 1
)
set "UV_PYTHON_INSTALL_DIR=%CD%\.runtime\python"
set "UV_PYTHON_BIN_DIR=%CD%\.runtime\bin"
set "UV_CACHE_DIR=%CD%\.runtime\cache"
set "UV_PYTHON_INSTALL_BIN=false"
set "UV_PYTHON_INSTALL_REGISTRY=false"
set "UV_PYTHON_NO_REGISTRY=true"
set "UV_PYTHON_PREFERENCE="
set "UV_LINK_MODE=copy"
set "PYTHONHOME="
set "PYTHONPATH="
set "PYTHONUTF8=1"
if not exist ".entorno-py312\Scripts\python.exe" goto python
".entorno-py312\Scripts\python.exe" -c "import sys; sys.exit(sys.version_info[:2] != (3,12))" >nul 2>&1
if not errorlevel 1 goto dependencias
:python
echo Preparando Python compatible dentro de esta carpeta...
echo La primera vez necesita Internet y puede tardar unos minutos.
"herramientas\uv.exe" --no-config venv --managed-python --python 3.12 --allow-existing ".entorno-py312"
if errorlevel 1 (
    echo No se pudo preparar Python. Comprueba la conexion y los permisos de esta carpeta.
    exit /b 1
)
:dependencias
".entorno-py312\Scripts\python.exe" preparar.py
exit /b %errorlevel%
