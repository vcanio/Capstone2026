"""Pruebas del panel; ejecutar unittest discover desde Laboratorio/Modelos."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
for directory in (HERE.parent, HERE):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
