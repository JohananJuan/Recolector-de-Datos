from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import cv2
import numpy as np


@dataclass
class CaracteristicasImagen:
    ancho: int
    alto: int
    canales: int
    tamano_bytes: int
    formato: str
    # --- Color (RGB + HSV + LAB) ---
    r_media: float; g_media: float; b_media: float
    r_std: float;   g_std: float;   b_std: float
    h_media: float; s_media: float; v_media: float
    l_media: float; a_media: float; b_lab_media: float
    # --- Iluminación ---
    brillo_medio: float
    brillo_std: float
    contraste_rms: float        
    rango_dinamico: float         
    # --- Nitidez / ruido ---
    varianza_laplaciano: float    
    ruido_estimado: float         
    # --- Histograma ---
    hist_entropia: float
    hist_uniformidad: float
    hist_sesgo: float
    hist_curtosis: float
    # --- Bordes / textura ---
    densidad_bordes: float        
    gradiente_medio: float
    # --- Balance de blancos ---
    wb_ratio_rg: float
    wb_ratio_bg: float
    # --- Colorido 
    colorido: float
    # --- Dominancia cromática ---
    color_dominante_hex: str
    saturacion_media: float

    def a_dict(self) -> dict[str, Any]:
        return asdict(self)


def _entropia(hist: np.ndarray) -> float:
    p = hist.astype(np.float64) / (hist.sum() + 1e-12)
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def _colorido(img_bgr: np.ndarray) -> float:
    # Hasler & Süsstrunk (2003)
    b, g, r = cv2.split(img_bgr.astype(np.float32))
    rg = r - g
    yb = 0.5 * (r + g) - b
    std_root = np.sqrt(rg.std() ** 2 + yb.std() ** 2)
    mean_root = np.sqrt(rg.mean() ** 2 + yb.mean() ** 2)
    return float(std_root + 0.3 * mean_root)


def extraer_caracteristicas(ruta: Path) -> CaracteristicasImagen | None:
    img = cv2.imread(str(ruta))
    if img is None:
        return None
    alto, ancho, canales = img.shape
    b, g, r = cv2.split(img)

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, bb = cv2.split(lab)

    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Nitidez
    var_lap = float(cv2.Laplacian(gris, cv2.CV_64F).var())

    # Ruido estimado: diferencia con desenfoque gaussiano
    desenfoque = cv2.GaussianBlur(gris, (5, 5), 0)
    ruido = float(np.std(gris.astype(np.float32) - desenfoque.astype(np.float32)))

    # Histograma de luminancia
    hist = cv2.calcHist([gris], [0], None, [256], [0, 256]).flatten()
    p = hist / (hist.sum() + 1e-12)
    valores = np.arange(256)
    media_h = float((p * valores).sum())
    std_h = float(np.sqrt((p * (valores - media_h) ** 2).sum()))
    sesgo_h = float((p * (valores - media_h) ** 3).sum() / (std_h ** 3 + 1e-12))
    curtosis_h = float((p * (valores - media_h) ** 4).sum() / (std_h ** 4 + 1e-12))

    # Bordes
    canny = cv2.Canny(gris, 100, 200)
    densidad_bordes = float((canny > 0).mean())
    sobel_x = cv2.Sobel(gris, cv2.CV_64F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(gris, cv2.CV_64F, 0, 1, ksize=3)
    grad_medio = float(np.sqrt(sobel_x**2 + sobel_y**2).mean())

    # Brillo / contraste
    brillo = float(gris.mean())
    contraste = float(gris.std())
    p5, p95 = np.percentile(gris, [5, 95])
    rango_din = float(p95 - p5)

    # Balance de blancos
    r_mean = float(r.mean()) + 1e-9
    g_mean = float(g.mean()) + 1e-9
    b_mean = float(b.mean()) + 1e-9
    wb_rg = r_mean / g_mean
    wb_bg = b_mean / g_mean

    # Color dominante 
    pequena = cv2.resize(img, (64, 64), interpolation=cv2.INTER_AREA)
    cuant = (pequena // 32).reshape(-1, 3)
    codigos = cuant[:, 0] * 64 + cuant[:, 1] * 8 + cuant[:, 2]
    idx = np.bincount(codigos).argmax()
    cb, cg, cr = (idx // 64, (idx // 8) % 8, idx % 8)
    dom_hex = f"#{cr*32:02x}{cg*32:02x}{cb*32:02x}"

    return CaracteristicasImagen(
        ancho=ancho, alto=alto, canales=canales,
        tamano_bytes=ruta.stat().st_size,
        formato=ruta.suffix.lower().lstrip("."),
        r_media=float(r.mean()), g_media=g_mean, b_media=b_mean,
        r_std=float(r.std()), g_std=float(g.std()), b_std=float(b.std()),
        h_media=float(h.mean()), s_media=float(s.mean()), v_media=float(v.mean()),
        l_media=float(l.mean()), a_media=float(a.mean()), b_lab_media=float(bb.mean()),
        brillo_medio=brillo, brillo_std=contraste,
        contraste_rms=contraste, rango_dinamico=rango_din,
        varianza_laplaciano=var_lap, ruido_estimado=ruido,
        hist_entropia=_entropia(hist),
        hist_uniformidad=float((p ** 2).sum()),
        hist_sesgo=sesgo_h, hist_curtosis=curtosis_h,
        densidad_bordes=densidad_bordes, gradiente_medio=grad_medio,
        wb_ratio_rg=wb_rg, wb_ratio_bg=wb_bg,
        colorido=_colorido(img),
        color_dominante_hex=dom_hex,
        saturacion_media=float(s.mean()),
    )