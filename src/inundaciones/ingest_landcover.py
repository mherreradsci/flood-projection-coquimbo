"""Uso de suelo ESA WorldCover 10 m (AWS público) → mapa de Curve Number.

Se lee por ventana directamente desde S3 (vsicurl) para no descargar tiles
completos de 3°x3°, y se remuestrea a la grilla del DEM por moda.
"""

import math
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import Resampling, reproject

from .utils import cargar_config, guardar_raster, leer_raster, log, ruta_data

URL_TILE = (
    "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
    "ESA_WorldCover_10m_2021_v200_{lat}{lon}_Map.tif"
)


def _tiles_worldcover(bbox) -> list[str]:
    o, s, e, n = bbox
    urls = []
    for lat_sw in range(math.floor(s / 3) * 3, math.ceil(n / 3) * 3, 3):
        for lon_sw in range(math.floor(o / 3) * 3, math.ceil(e / 3) * 3, 3):
            lat = f"S{abs(lat_sw):02d}" if lat_sw < 0 else f"N{lat_sw:02d}"
            lon = f"W{abs(lon_sw):03d}" if lon_sw < 0 else f"E{lon_sw:03d}"
            urls.append(URL_TILE.format(lat=lat, lon=lon))
    return urls


def preparar_landcover(cfg: dict) -> Path:
    """WorldCover remuestreado (moda) a la grilla del DEM."""
    destino = ruta_data(cfg, "landcover", "worldcover.tif")
    if destino.exists():
        return destino

    dem, transform_dem, crs_dem = leer_raster(ruta_data(cfg, "dem", "dem.tif"))
    acumulado = np.zeros(dem.shape, dtype="uint8")
    for url in _tiles_worldcover(cfg["region"]["bbox"]):
        try:
            with rasterio.open(url) as src:
                parcial = np.zeros(dem.shape, dtype="uint8")
                reproject(
                    rasterio.band(src, 1), parcial,
                    dst_transform=transform_dem, dst_crs=crs_dem,
                    resampling=Resampling.mode,
                )
                acumulado = np.where(parcial > 0, parcial, acumulado)
                log.info("WorldCover leído: %s", url.rsplit("/", 1)[-1])
        except rasterio.errors.RasterioIOError as exc:
            log.info("Tile WorldCover no disponible (%s): %s", exc, url)

    if acumulado.sum() == 0:
        raise RuntimeError("No se pudo leer ningún tile de WorldCover")
    guardar_raster(destino, acumulado, transform_dem, nodata=0, dtype="uint8")
    return destino


def preparar_curve_number(cfg: dict) -> Path:
    """Mapa de Curve Number a partir de las clases WorldCover (config.yaml)."""
    destino = ruta_data(cfg, "landcover", "curve_number.tif")
    if destino.exists():
        return destino

    lc, transform, _ = leer_raster(preparar_landcover(cfg))
    tabla = {int(k): float(v) for k, v in cfg["modelo"]["cn_por_worldcover"].items()}
    cn = np.full(lc.shape, float(cfg["modelo"]["cn_defecto"]), dtype="float32")
    for clase, valor in tabla.items():
        cn[lc == clase] = valor
    guardar_raster(destino, cn, transform, nodata=-9999)
    log.info("Curve Number: media %.1f (min %.0f / max %.0f)",
             float(cn.mean()), float(cn.min()), float(cn.max()))
    return destino


if __name__ == "__main__":
    cfg = cargar_config()
    preparar_landcover(cfg)
    print(preparar_curve_number(cfg))
