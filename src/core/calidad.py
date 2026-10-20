from pathlib import Path
from dataclasses import dataclass
import numpy as np
from PIL import Image


@dataclass
class MetricasCalidad:
    luminancia_media: float     # media de Y (luma) 0-255
    luminancia_mediana: float   # mediana de Y (robusta a reflejos)
    luminancia_std: float       # desviación estándar de Y
    laplaciano_var: float       # varianza del Laplaciano = nitidez
    pct_muy_oscuro: float       # % píxeles con Y < 15
    pct_muy_claro: float        # % píxeles con Y > 240
    entropia_hist: float        # entropía del histograma de Y
    imagen_vacia: bool          # casi uniforme
    borrosa: bool               # heurística, no sentencia


def calcular_metricas(archivo: Path) -> MetricasCalidad | None:
    try:
        with Image.open(archivo) as img:
            gris = np.asarray(img.convert("L"), dtype=np.float32)
    except Exception:
        return None

    if gris.size == 0:
        return None

    media = float(gris.mean())
    mediana = float(np.median(gris))
    std = float(gris.std())

    lap = (
        -4 * gris[1:-1, 1:-1]
        + gris[:-2, 1:-1] + gris[2:, 1:-1]
        + gris[1:-1, :-2] + gris[1:-1, 2:]
    )
    lap_var = float(lap.var()) if lap.size else 0.0

    pct_oscuro = float((gris < 15).mean() * 100)
    pct_claro = float((gris > 240).mean() * 100)

    hist, _ = np.histogram(gris, bins=256, range=(0, 255))
    p = hist / hist.sum()
    p = p[p > 0]
    entropia = float(-(p * np.log2(p)).sum())

    imagen_vacia = bool(std < 8.0 and entropia < 3.0)
    borrosa = bool(lap_var < 80.0)  

    return MetricasCalidad(
        luminancia_media=media,
        luminancia_mediana=mediana,
        luminancia_std=std,
        laplaciano_var=lap_var,
        pct_muy_oscuro=pct_oscuro,
        pct_muy_claro=pct_claro,
        entropia_hist=entropia,
        imagen_vacia=imagen_vacia,
        borrosa=borrosa,
    )