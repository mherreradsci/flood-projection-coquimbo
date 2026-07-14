#!/usr/bin/env python
"""Calcula los derivados hidrológicos del DEM: flujo, red de drenaje y HAND."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from inundaciones.terrain import preparar_terreno
from inundaciones.utils import cargar_config

if __name__ == "__main__":
    print(preparar_terreno(cargar_config()))
