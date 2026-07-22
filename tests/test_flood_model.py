import numpy as np
import pytest

from inundaciones.flood_model import _umbral_para_volumen, _volumen_bajo_umbral


def _volumen_en(hand_orden: np.ndarray, h: float, celda_m2: float) -> float:
    """Reimplementación directa (no vectorizada por prefijos) para verificar
    que el umbral devuelto por _umbral_para_volumen realmente contiene el
    volumen pedido."""
    return float(np.sum(np.maximum(h - hand_orden, 0)) * celda_m2)


def test_volumen_cero_no_inunda():
    hand = np.array([0.0, 1.0, 2.0, 3.0])
    assert _umbral_para_volumen(hand, 0.0, celda_m2=1.0, hand_max=10.0) == 0.0


def test_subcuenca_sin_celdas_validas():
    assert _umbral_para_volumen(np.array([]), 100.0, celda_m2=1.0, hand_max=10.0) == 0.0


@pytest.mark.parametrize("volumen_m3", [0.5, 3.0, 7.5, 15.0])
def test_umbral_contiene_el_volumen_pedido(volumen_m3):
    hand = np.array([0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0])
    celda_m2 = 2.0
    h = _umbral_para_volumen(hand, volumen_m3, celda_m2, hand_max=10.0)
    assert _volumen_en(hand, h, celda_m2) == pytest.approx(volumen_m3, rel=1e-6)


def test_volumen_que_excede_capacidad_satura_en_hand_max():
    hand = np.array([0.0, 1.0, 2.0])
    hand_max = 5.0
    # capacidad máxima bajo hand_max: sum(hand_max - hand_i) * celda_m2
    capacidad = float(np.sum(hand_max - hand)) * 1.0
    h = _umbral_para_volumen(hand, capacidad + 1000.0, celda_m2=1.0, hand_max=hand_max)
    assert h == hand_max


def test_umbral_es_monotono_creciente_con_el_volumen():
    hand = np.sort(np.random.default_rng(0).uniform(0, 8, size=50))
    celda_m2 = 3.0
    h_bajo = _umbral_para_volumen(hand, 20.0, celda_m2, hand_max=10.0)
    h_alto = _umbral_para_volumen(hand, 80.0, celda_m2, hand_max=10.0)
    assert h_alto >= h_bajo


@pytest.mark.parametrize("h", [0.2, 1.2, 3.5, 10.0])
def test_volumen_bajo_umbral_coincide_con_la_definicion_directa(h):
    hand = np.array([0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0])
    celda_m2 = 2.0
    assert _volumen_bajo_umbral(hand, h, celda_m2) == pytest.approx(
        _volumen_en(hand, h, celda_m2), rel=1e-9)


def test_volumen_bajo_umbral_arreglo_vacio_da_cero():
    assert _volumen_bajo_umbral(np.array([]), 5.0, celda_m2=1.0) == 0.0


def test_volumen_bajo_umbral_bajo_el_minimo_da_cero():
    hand = np.array([1.0, 2.0, 3.0])
    assert _volumen_bajo_umbral(hand, 0.5, celda_m2=1.0) == 0.0


def test_volumen_bajo_umbral_es_inversa_de_umbral_para_volumen():
    # calibrate.py usa _volumen_bajo_umbral y flood_model usa
    # _umbral_para_volumen sobre el mismo corredor HAND; deben ser
    # consistentes entre sí o el factor de calibración queda sesgado.
    hand = np.sort(np.random.default_rng(1).uniform(0, 8, size=30))
    celda_m2 = 4.0
    h = float((hand[14] + hand[15]) / 2)  # entre dos valores, sin ambigüedad de empate
    v = _volumen_bajo_umbral(hand, h, celda_m2)
    assert v > 0
    h_recuperado = _umbral_para_volumen(hand, v, celda_m2, hand_max=100.0)
    assert h_recuperado == pytest.approx(h, rel=1e-6)
