import pytest
from rasterio.transform import Affine

from inundaciones.utils import area_celda_m2


def test_area_celda_en_el_ecuador():
    # celda cuadrada de 0.01° (~1113 m E-O en el ecuador, ~1105 m N-S)
    transform = Affine(0.01, 0.0, -70.0, 0.0, -0.01, -20.0)
    area = area_celda_m2(transform, lat_media=0.0)
    esperado = (0.01 * 111_320) * (0.01 * 110_540)
    assert area == pytest.approx(esperado, rel=1e-9)


def test_area_celda_decrece_con_la_latitud():
    transform = Affine(0.01, 0.0, -70.0, 0.0, -0.01, -20.0)
    area_ecuador = area_celda_m2(transform, lat_media=0.0)
    area_60 = area_celda_m2(transform, lat_media=60.0)
    # a 60° el ancho E-O de un grado de longitud se reduce a la mitad (cos 60° = 0.5)
    assert area_60 == pytest.approx(area_ecuador * 0.5, rel=1e-6)


def test_area_celda_ignora_el_signo_del_transform():
    # las filas de un raster north-up bajan en latitud: transform.e es negativo
    transform_norte = Affine(0.01, 0.0, -70.0, 0.0, -0.01, -20.0)
    transform_sur = Affine(0.01, 0.0, -70.0, 0.0, 0.01, -20.0)
    assert area_celda_m2(transform_norte, 10.0) == pytest.approx(
        area_celda_m2(transform_sur, 10.0)
    )


def test_area_celda_distingue_ancho_de_alto():
    # pixel no cuadrado: si la función confundiera a/e, este caso lo delataría
    transform = Affine(0.02, 0.0, -70.0, 0.0, -0.01, -20.0)
    area = area_celda_m2(transform, lat_media=0.0)
    esperado = (0.02 * 111_320) * (0.01 * 110_540)
    assert area == pytest.approx(esperado, rel=1e-9)
