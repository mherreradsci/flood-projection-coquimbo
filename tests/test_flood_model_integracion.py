"""Tests de integración de modelar_inundacion: rasters sintéticos en tmp_path,
sin red ni datos reales de Coquimbo. A diferencia de tests/test_flood_model.py
(funciones puras), estos ejercitan la lectura/escritura real de GeoTIFF y el
cruce por id de subcuenca — la parte de "wiring" que un test de función pura
no puede atrapar (p. ej. una subcuenca inundando la máscara de otra).

rasterizar_subcuencas() cachea por existencia de archivo (ver CLAUDE.md): al
pre-crear subcuencas_id.tif, se evita por completo la descarga de HydroBASINS.
"""

import numpy as np
import pandas as pd
import pytest
from rasterio.transform import Affine

from inundaciones.flood_model import _umbral_para_volumen, modelar_inundacion
from inundaciones.utils import area_celda_m2, guardar_raster, leer_raster

TRANSFORM = Affine(0.001, 0.0, -71.0, 0.0, -0.001, -30.0)
LAT_MEDIA = -30.0


def _cfg(tmp_path):
    return {
        "rutas": {"data": str(tmp_path / "data"), "outputs": str(tmp_path / "outputs")},
        "terreno": {"hand_max_m": 10.0},
        "region": {"bbox": [-71.01, -30.02, -70.99, -29.98]},  # lat_media = -30.0
    }


def test_modelar_inundacion_asigna_profundidad_solo_a_la_subcuenca_con_volumen(tmp_path):
    # dos subcuencas de 8 celdas cada una: columnas 0-1 = subcuenca 1, 2-3 = subcuenca 2
    ids = np.array([
        [1, 1, 2, 2],
        [1, 1, 2, 2],
        [1, 1, 2, 2],
        [1, 1, 2, 2],
    ], dtype="int32")
    # mismo patrón de HAND en ambas subcuencas, para poder comparar directamente
    hand = np.array([
        [0.0, 1.0, 0.0, 1.0],
        [2.0, 3.0, 2.0, 3.0],
        [0.0, 1.0, 0.0, 1.0],
        [2.0, 3.0, 2.0, 3.0],
    ], dtype="float32")

    cfg = _cfg(tmp_path)
    guardar_raster(tmp_path / "data" / "dem" / "hand.tif", hand, TRANSFORM, nodata=-9999)
    guardar_raster(tmp_path / "data" / "vector" / "subcuencas_id.tif", ids, TRANSFORM,
                   nodata=0, dtype="int32")

    celda_m2 = area_celda_m2(TRANSFORM, LAT_MEDIA)
    hand_sub1 = np.sort(hand[ids == 1].astype("float64"))
    volumen_1 = 1.0 * celda_m2  # alcanza para inundar solo las celdas con hand=0, hasta h=0.5
    h_esperado_1 = _umbral_para_volumen(hand_sub1, volumen_1, celda_m2, hand_max=10.0)

    volumenes = pd.DataFrame({
        "HYBAS_ID": [100, 200],
        "id_raster": [1, 2],
        "volumen_m3": [volumen_1, 0.0],  # subcuenca 2 sin escorrentía
    })

    resultado = modelar_inundacion(cfg, volumenes, sufijo="test")

    assert resultado["umbrales"]["100"] == pytest.approx(h_esperado_1)
    assert resultado["umbrales"]["200"] == 0.0

    profundidad, _, _ = leer_raster(resultado["profundidad"])
    extension, _, _ = leer_raster(resultado["extension"])

    esperado_prof = np.where(ids == 1, np.maximum(h_esperado_1 - hand, 0), 0).astype("float32")
    assert profundidad == pytest.approx(esperado_prof, abs=1e-4)
    assert profundidad[ids == 2].sum() == 0.0  # la subcuenca sin volumen nunca se toca
    assert extension.sum() == int((esperado_prof >= 0.05).sum())
    assert resultado["area_km2"] == pytest.approx(float(extension.sum()) * celda_m2 / 1e6)


def test_modelar_inundacion_sin_volumenes_no_inunda_nada(tmp_path):
    ids = np.ones((3, 3), dtype="int32")
    hand = np.zeros((3, 3), dtype="float32")

    cfg = _cfg(tmp_path)
    guardar_raster(tmp_path / "data" / "dem" / "hand.tif", hand, TRANSFORM, nodata=-9999)
    guardar_raster(tmp_path / "data" / "vector" / "subcuencas_id.tif", ids, TRANSFORM,
                   nodata=0, dtype="int32")

    volumenes = pd.DataFrame({"HYBAS_ID": [], "id_raster": [], "volumen_m3": []})
    resultado = modelar_inundacion(cfg, volumenes, sufijo="test")

    assert resultado["umbrales"] == {}
    assert resultado["area_km2"] == 0.0
    extension, _, _ = leer_raster(resultado["extension"])
    assert extension.sum() == 0
