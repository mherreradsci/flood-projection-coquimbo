#!/usr/bin/env python
"""Calibra el modelo contra las huellas históricas y guarda data/calibracion.json."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from inundaciones.calibrate import calibrar
from inundaciones.utils import cargar_config

if __name__ == "__main__":
    print(calibrar(cargar_config()))
