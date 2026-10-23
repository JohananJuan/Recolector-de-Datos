from __future__ import annotations
import pandas as pd

from analisis.estadisticas import resumen_estadistico
from limpieza.ruido import detectar_ruido_caracteristicas, winsorizar
from limpieza.faltantes import imputar


def pipeline_limpieza(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    nulos_antes = int(df.isna().sum().sum())
    es_ruido = detectar_ruido_caracteristicas(df)
    limpio = df.loc[~es_ruido].copy()

    limpio = imputar(limpio, "mediana")
    nulos_despues = int(limpio.isna().sum().sum())

    limpio = winsorizar(limpio)

    metricas = {
        "filas_originales": len(df),
        "filas_ruido_eliminadas": int(es_ruido.sum()),
        "filas_finales": len(limpio),
        "columnas": len(df.columns),
        "celdas_nulas_antes": nulos_antes,
        "celdas_nulas_imputadas": nulos_antes - nulos_despues,
    }
    return limpio, metricas


def tabla_comparativa(
    df_crudo: pd.DataFrame, df_limpio: pd.DataFrame
) -> pd.DataFrame:
    est_c = resumen_estadistico(df_crudo)
    est_l = resumen_estadistico(df_limpio)
    if est_c.empty or est_l.empty:
        return pd.DataFrame()

    met_analizar = ("media", "mediana", "std", "min", "max", "sesgo", "curtosis")
    filas = []
    for col in est_c.index.intersection(est_l.index):
        for met in met_analizar:
            crudo_v = est_c.loc[col, met]
            limpio_v = est_l.loc[col, met]
            if pd.isna(crudo_v) and pd.isna(limpio_v):
                continue
            delta = (limpio_v - crudo_v) / (abs(crudo_v) + 1e-9) * 100
            filas.append({
                "columna": col,
                "estadistico": met,
                "crudo": crudo_v,
                "limpio": limpio_v,
                "delta_%": delta,
            })
    return pd.DataFrame(filas)

# analisis/comparador.py  (añadir al final, SIN borrar lo existente)

def comparativa_pairwise(
    df_crudo: pd.DataFrame,
    df_limpio: pd.DataFrame,
    por_fila: bool = True,
) -> pd.DataFrame:
    """Compara fila a fila (por 'ruta') columna numérica a numérica.

    Devuelve un DataFrame long-format:
      ruta | columna | crudo | limpio | delta | delta_% | cambio
    """
    if "ruta" not in df_crudo.columns or "ruta" not in df_limpio.columns:
        return pd.DataFrame()

    cols_num = [
        c for c in df_crudo.select_dtypes(include="number").columns
        if c in df_limpio.columns
    ]
    if not cols_num:
        return pd.DataFrame()

    crudo_idx = df_crudo.set_index("ruta")
    limpio_idx = df_limpio.set_index("ruta")
    comunes = crudo_idx.index.intersection(limpio_idx.index)

    filas: list[dict] = []
    for ruta in comunes:
        for col in cols_num:
            v_c = crudo_idx.at[ruta, col]
            v_l = limpio_idx.at[ruta, col]
            if pd.isna(v_c) and pd.isna(v_l):
                continue
            delta = (v_l - v_c) if pd.notna(v_c) and pd.notna(v_l) else None
            delta_pct = (
                (delta / (abs(v_c) + 1e-9)) * 100
                if delta is not None else None
            )
            cambio = (
                "sin cambio" if delta == 0
                else "aumentó" if (delta or 0) > 0
                else "disminuyó"
            )
            filas.append({
                "ruta": ruta,
                "columna": col,
                "crudo": v_c,
                "limpio": v_l,
                "delta": delta,
                "delta_%": delta_pct,
                "cambio": cambio,
            })
    return pd.DataFrame(filas)


def comparativa_listwise(
    df_crudo: pd.DataFrame,
    df_limpio: pd.DataFrame,
    por_fila: bool = True,
) -> pd.DataFrame:
    if "ruta" not in df_crudo.columns or "ruta" not in df_limpio.columns:
        return pd.DataFrame()

    cols_num = [
        c for c in df_crudo.select_dtypes(include="number").columns
        if c in df_limpio.columns
    ]
    if not cols_num:
        return pd.DataFrame()

    crudo_idx = df_crudo.set_index("ruta")[cols_num]
    limpio_idx = df_limpio.set_index("ruta")[cols_num]

    todas = crudo_idx.index.union(limpio_idx.index)
    comunes = crudo_idx.index.intersection(limpio_idx.index)
    eliminadas = crudo_idx.index.difference(limpio_idx.index)

    filas: list[dict] = []
    for ruta in comunes:
        a = crudo_idx.loc[ruta].to_numpy(dtype=float)
        b = limpio_idx.loc[ruta].to_numpy(dtype=float)
        mascara = ~(pd.isna(a) | pd.isna(b))
        if not mascara.any():
            distancia = 0.0
        else:
            distancia = float(((a[mascara] - b[mascara]) ** 2).sum() ** 0.5)
        filas.append({
            "ruta": ruta,
            "distancia_l2": distancia,
            "similar": distancia < 1e-6,
            "eliminada": False,
        })
    for ruta in eliminadas:
        filas.append({
            "ruta": ruta,
            "distancia_l2": None,
            "similar": False,
            "eliminada": True,
        })
    return pd.DataFrame(filas)