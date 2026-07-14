"""Descarga y mosaico del DEM Copernicus GLO-30 (AWS Open Data, sin credenciales)."""

import math
from pathlib import Path

import numpy as np
import rasterio
import requests
from rasterio.merge import merge
from rasterio.warp import Resampling, aligned_target, reproject

from .utils import cargar_config, log, ruta_data

URL_TILE = (
    "https://copernicus-dem-30m.s3.amazonaws.com/"
    "Copernicus_DSM_COG_10_{lat}_00_{lon}_00_DEM/"
    "Copernicus_DSM_COG_10_{lat}_00_{lon}_00_DEM.tif"
)


def _nombre_celda(lat_sw: int, lon_sw: int) -> dict:
    lat = f"S{abs(lat_sw):02d}" if lat_sw < 0 else f"N{lat_sw:02d}"
    lon = f"W{abs(lon_sw):03d}" if lon_sw < 0 else f"E{lon_sw:03d}"
    return {"lat": lat, "lon": lon}


def descargar_tiles(cfg: dict) -> list[Path]:
    """Descarga los tiles GLO-30 de 1°x1° que cubren el bbox regional."""
    o, s, e, n = cfg["region"]["bbox"]
    rutas = []
    for lat_sw in range(math.floor(s), math.ceil(n)):
        for lon_sw in range(math.floor(o), math.ceil(e)):
            partes = _nombre_celda(lat_sw, lon_sw)
            destino = ruta_data(cfg, "dem", f"glo30_{partes['lat']}_{partes['lon']}.tif")
            if destino.exists():
                rutas.append(destino)
                continue
            url = URL_TILE.format(**partes)
            r = requests.get(url, timeout=300)
            if r.status_code == 404:
                # tile oceánico inexistente
                log.info("Tile no existe (océano): %s%s", partes["lat"], partes["lon"])
                continue
            r.raise_for_status()
            destino.write_bytes(r.content)
            log.info("DEM tile descargado: %s (%.1f MB)", destino.name, len(r.content) / 1e6)
            rutas.append(destino)
    return rutas


def preparar_dem(cfg: dict) -> Path:
    """Mosaico, recorte al bbox y remuestreo a la resolución de trabajo."""
    destino = ruta_data(cfg, "dem", "dem.tif")
    if destino.exists():
        return destino

    tiles = descargar_tiles(cfg)
    if not tiles:
        raise RuntimeError("No se descargó ningún tile de DEM")

    o, s, e, n = cfg["region"]["bbox"]
    fuentes = [rasterio.open(t) for t in tiles]
    mosaico, transform = merge(fuentes, bounds=(o, s, e, n))
    perfil = fuentes[0].profile
    for f in fuentes:
        f.close()
    datos = mosaico[0].astype("float32")

    # remuestreo a la resolución de trabajo (grados equivalentes en el ecuador)
    res_m = cfg["dem"]["resolucion_m"]
    res_deg = res_m / 111_320
    transform_dst, ancho, alto = aligned_target(transform, datos.shape[1], datos.shape[0], res_deg)
    salida = np.empty((alto, ancho), dtype="float32")
    reproject(
        datos, salida,
        src_transform=transform, src_crs="EPSG:4326",
        dst_transform=transform_dst, dst_crs="EPSG:4326",
        resampling=Resampling.average, src_nodata=perfil.get("nodata"), dst_nodata=-9999,
    )

    from .utils import guardar_raster
    guardar_raster(destino, salida, transform_dst, nodata=-9999)
    log.info("DEM listo: %s (%d x %d @ %d m)", destino, alto, ancho, res_m)
    return destino


if __name__ == "__main__":
    cfg = cargar_config()
    print(preparar_dem(cfg))
