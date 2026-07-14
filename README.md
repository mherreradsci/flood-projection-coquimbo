# Proyección de anegamientos — Región de Coquimbo

Sistema en Python para estimar **dónde se producirán anegamientos** ante un
evento de precipitación extrema (río atmosférico de julio 2026) y detectar los
**puntos nuevos** sin registro histórico de inundación. 100% herramientas de
código abierto y datos públicos.

## Método

Modelo semi-hidrológico **HAND calibrado**:

1. **Terreno**: DEM Copernicus GLO-30 → direcciones de flujo, acumulación, red
   de drenaje y HAND (Height Above Nearest Drainage) con `pysheds`.
2. **Lluvia efectiva**: precipitación GFS 0.25° (o escenario sintético)
   filtrada por la **isoterma 0** — solo el área bajo la cota de nieve aporta
   escorrentía líquida, el mecanismo dominante en crecidas chilenas.
3. **Escorrentía**: SCS Curve Number (CN desde ESA WorldCover) por subcuenca
   HydroBASINS.
4. **Extensión**: el volumen de escorrentía se distribuye en el espacio HAND
   de cada subcuenca (estilo FwDET) → raster de profundidad.
5. **Calibración**: factores de volumen por subcuenca ajustados contra huellas
   de inundación observadas (Global Flood Database, MODIS 250 m).
6. **Zonas nuevas**: extensión proyectada − huellas históricas.

## Uso

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/01_descargar_datos.py    # insumos + GFS vigente
.venv/bin/python scripts/02_preparar_terreno.py   # HAND (lento, se cachea)
.venv/bin/python scripts/03_calibrar.py           # contra eventos históricos
.venv/bin/python scripts/04_proyectar.py --fuente gfs
.venv/bin/python scripts/04_proyectar.py --fuente escenario --escenario extremo_200mm
```

Resultado principal: `outputs/mapa_anegamientos.html` (folium, capas
conmutables) más GeoTIFF/GeoJSON en `outputs/`.

## Datos usados (todos públicos)

| Insumo | Fuente |
|---|---|
| DEM 30 m | Copernicus GLO-30 (AWS Open Data) |
| Pronóstico | GFS 0.25° vía `herbie-data` (NOAA) |
| Huellas históricas | Global Flood Database v1.4 (GCS `gfd_v1_4`) |
| Uso de suelo | ESA WorldCover 10 m (AWS) |
| Subcuencas | HydroSHEDS HydroBASINS nivel 8 |
| Límite regional | OpenStreetMap (Nominatim) |
| Exposición | OpenStreetMap (Overpass vía `osmnx`) |

## Limitaciones

- GFS 25 km es grueso para quebradas costeras; usar el modo escenario para
  forzar acumulados locales.
- La calibración usa el **único** evento con huella MODIS sobre Coquimbo en el
  Global Flood Database (tormenta del 24-29 de agosto de 2002, DFO 2042); los
  aluviones de 2015 y 2017 no fueron procesados por GFD v1.4. MODIS (250 m)
  solo detecta cuerpos de agua grandes, por lo que el modelo se calibra al
  corredor que captura el 80% de la observación (POD≈0.8) y **tiende a
  sobrepredecir extensión** — es un producto de susceptibilidad, no un mapa de
  certeza.
- El modelo representa anegamiento fluvial/de quebradas, no fallas de
  colectores urbanos.
- **Esto no reemplaza los avisos oficiales de la DMC ni de SENAPRED.**
