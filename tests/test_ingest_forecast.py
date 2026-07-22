from datetime import datetime, timezone

import numpy as np
import pytest

from inundaciones.ingest_forecast import _estado_ciclo, _isoterma0_desde_perfil, _ultimo_ciclo_gfs


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


def test_ciclo_completo_cuando_llega_al_horizonte_pedido():
    def existe(fxx):
        return fxx == 24

    assert _estado_ciclo(existe, horas=24) == {"completo": True, "ultima_fxx": 24}


def test_ciclo_no_publicado_da_ultima_fxx_none():
    def existe(fxx):
        return False

    assert _estado_ciclo(existe, horas=24) == {"completo": False, "ultima_fxx": None}


def test_ciclo_parcial_ubica_el_ultimo_paso_disponible():
    def existe(fxx):
        # publicado hasta f012 nomás: f000 y f012 existen, f018 y f024 no
        return fxx in (0, 12)

    assert _estado_ciclo(existe, horas=24) == {"completo": False, "ultima_fxx": 12}


def test_ciclo_parcial_sin_ningun_paso_intermedio_disponible():
    def existe(fxx):
        # solo f000 existe: el escaneo hacia atrás no encuentra nada
        return fxx == 0

    assert _estado_ciclo(existe, horas=24) == {"completo": False, "ultima_fxx": 0}


def test_ultimo_ciclo_gfs_resta_el_rezago_y_redondea_a_6_horas():
    ahora = datetime(2026, 7, 22, 3, 30, tzinfo=timezone.utc)  # -5h -> 21 jul 22:30
    assert _ultimo_ciclo_gfs(ahora) == datetime(2026, 7, 21, 18, 0, tzinfo=timezone.utc)


def test_ultimo_ciclo_gfs_en_un_limite_exacto():
    ahora = datetime(2026, 7, 22, 5, 0, tzinfo=timezone.utc)  # -5h -> 22 jul 00:00
    assert _ultimo_ciclo_gfs(ahora) == datetime(2026, 7, 22, 0, 0, tzinfo=timezone.utc)
