"""Exposición: infraestructura OSM dentro de la extensión proyectada.

Cuantifica km de vías, número de edificios y servicios críticos afectados.
Tolerante a fallas de red/Overpass: devuelve lo que logre obtener.
"""

import json
from pathlib import Path

import geopandas as gpd

from .utils import cargar_config, log, ruta_outputs


def evaluar_exposicion(cfg: dict, sufijo: str = "proyectada") -> Path:
    import osmnx as ox

    zonas = gpd.read_file(ruta_outputs(cfg, f"zonas_nuevas_{sufijo}.geojson"))
    recurrentes = gpd.read_file(ruta_outputs(cfg, f"zonas_recurrentes_{sufijo}.geojson"))
    todas = gpd.GeoDataFrame(geometry=list(zonas.geometry) + list(recurrentes.geometry),
                             crs="EPSG:4326")
    resumen = {"vias_km": 0.0, "edificios": 0, "servicios": []}
    destino = ruta_outputs(cfg, f"exposicion_{sufijo}.json")
    if todas.empty:
        destino.write_text(json.dumps(resumen, indent=2))
        return destino

    poligono = todas.union_all().buffer(0.001)  # ~100 m de tolerancia

    try:
        vias = ox.features_from_polygon(poligono, {"highway": cfg["exposicion"]["vias"]})
        vias = vias[vias.geometry.geom_type.isin(["LineString", "MultiLineString"])]
        if not vias.empty:
            resumen["vias_km"] = round(float(
                vias.to_crs(32719).geometry.length.sum() / 1000), 1)
            vias[["geometry"]].to_file(
                ruta_outputs(cfg, f"vias_expuestas_{sufijo}.geojson"), driver="GeoJSON")
    except Exception as exc:
        log.warning("OSM vías no disponible: %s", exc)

    try:
        edif = ox.features_from_polygon(poligono, {"building": True})
        resumen["edificios"] = int(len(edif))
    except Exception as exc:
        log.warning("OSM edificios no disponible: %s", exc)

    try:
        serv = ox.features_from_polygon(
            poligono, {"amenity": cfg["exposicion"]["servicios"]})
        for _, fila in serv.iterrows():
            punto = fila.geometry.centroid
            resumen["servicios"].append({
                "tipo": fila.get("amenity"), "nombre": fila.get("name", "s/n"),
                "lon": punto.x, "lat": punto.y})
    except Exception as exc:
        log.warning("OSM servicios no disponible: %s", exc)

    destino.write_text(json.dumps(resumen, indent=2, ensure_ascii=False))
    log.info("Exposición: %.1f km de vías, %d edificios, %d servicios críticos",
             resumen["vias_km"], resumen["edificios"], len(resumen["servicios"]))
    return destino


if __name__ == "__main__":
    cfg = cargar_config()
    print(evaluar_exposicion(cfg))
