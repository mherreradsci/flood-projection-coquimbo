import numpy as np
import pytest

from inundaciones.ingest_forecast import _isoterma0_desde_perfil


def test_interpola_linealmente_entre_dos_niveles():
    z = np.array([0.0, 1000.0])
    t = np.array([275.15, 269.15])  # 2 °C en superficie, -4 °C a 1000 m
    assert _isoterma0_desde_perfil(t, z, defecto_m=3000.0) == pytest.approx(333.33, abs=0.1)


def test_ordena_el_perfil_antes_de_interpolar():
    # mismos niveles que el caso anterior, pero desordenados (z decreciente)
    z = np.array([1000.0, 0.0])
    t = np.array([269.15, 275.15])
    assert _isoterma0_desde_perfil(t, z, defecto_m=3000.0) == pytest.approx(333.33, abs=0.1)


def test_sin_cruce_devuelve_el_defecto():
    z = np.array([0.0, 500.0, 1000.0])
    t = np.array([300.15, 295.15, 290.15])  # siempre sobre 0 °C
    assert _isoterma0_desde_perfil(t, z, defecto_m=2500.0) == 2500.0


def test_con_inversion_termica_toma_el_cruce_mas_alto():
    # superficie fría, capa cálida intermedia (inversión), fría de nuevo en altura:
    # cruza 0 °C dos veces; debe quedarse con el más alto de los dos.
    z = np.array([0.0, 500.0, 1000.0, 1500.0])
    t = np.array([271.15, 276.15, 274.15, 270.15])  # -2, +3, +1, -3 °C
    assert _isoterma0_desde_perfil(t, z, defecto_m=3000.0) == pytest.approx(1125.0, abs=0.1)
