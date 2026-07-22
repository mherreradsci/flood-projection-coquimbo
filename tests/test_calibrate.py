import numpy as np

from inundaciones.calibrate import _metricas


def test_metricas_caso_conocido():
    modelo = np.array([True, True, False, False])
    observado = np.array([True, False, True, False])
    # tp=1 (idx0), fp=1 (idx1), fn=1 (idx2)
    m = _metricas(modelo, observado)
    assert m["CSI"] == 1 / 3
    assert m["POD"] == 1 / 2
    assert m["FAR"] == 1 / 2


def test_metricas_prediccion_perfecta():
    modelo = np.array([True, True, False, False])
    observado = modelo.copy()
    m = _metricas(modelo, observado)
    assert m["CSI"] == 1.0
    assert m["POD"] == 1.0
    assert m["FAR"] == 0.0


def test_metricas_sin_deteccion_ni_observacion_da_nan():
    modelo = np.array([False, False])
    observado = np.array([False, False])
    m = _metricas(modelo, observado)
    assert np.isnan(m["CSI"])
    assert np.isnan(m["POD"])
    assert np.isnan(m["FAR"])


def test_metricas_sin_positivos_modelados_da_far_nan():
    modelo = np.array([False, False])
    observado = np.array([True, False])
    m = _metricas(modelo, observado)
    assert np.isnan(m["FAR"])  # tp+fp == 0
    assert m["POD"] == 0.0
