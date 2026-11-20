from __future__ import annotations

import pandas as pd

from analisis.estadisticas import resumen_estadistico


def tabla_comparativa(
    df_crudo: pd.DataFrame, df_limpio: pd.DataFrame,
) -> pd.DataFrame:
    est_c = resumen_estadistico(df_crudo)
    est_l = resumen_estadistico(df_limpio)
    if est_c.empty or est_l.empty:
        return pd.DataFrame()

    met = ("media", "mediana", "std", "min", "max", "sesgo", "curtosis")
    filas = []
    for col in est_c.index.intersection(est_l.index):
        for m in met:
            a, b = est_c.loc[col, m], est_l.loc[col, m]
            if pd.isna(a) and pd.isna(b):
                continue
            delta = (b - a) / (abs(a) + 1e-9) * 100
            filas.append({
                "columna": col, "estadistico": m,
                "crudo": a, "limpio": b, "delta_%": delta,
            })
    return pd.DataFrame(filas)


def _indexar(df_crudo: pd.DataFrame, df_limpio: pd.DataFrame):
    k = "ruta_original" if "ruta_original" in df_limpio.columns else "ruta"
    return (df_crudo.drop_duplicates("ruta").set_index("ruta"),
            df_limpio.drop_duplicates(k).set_index(k))


def comparativa_pairwise(
    df_crudo: pd.DataFrame, df_limpio: pd.DataFrame,
) -> pd.DataFrame:
    if "ruta" not in df_crudo.columns or "ruta" not in df_limpio.columns:
        return pd.DataFrame()

    cols_num = [
        c for c in df_crudo.select_dtypes(include="number").columns
        if c in df_limpio.columns
    ]
    if not cols_num:
        return pd.DataFrame()

    crudo_idx, limpio_idx = _indexar(df_crudo, df_limpio)
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
            if delta is None:
                cambio = "sin dato"
            elif delta == 0:
                cambio = "sin cambio"
            else:
                cambio = "aumentó" if delta > 0 else "disminuyó"
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
    df_crudo: pd.DataFrame, df_limpio: pd.DataFrame,
) -> pd.DataFrame:
    if "ruta" not in df_crudo.columns or "ruta" not in df_limpio.columns:
        return pd.DataFrame()

    cols_num = [
        c for c in df_crudo.select_dtypes(include="number").columns
        if c in df_limpio.columns
    ]
    if not cols_num:
        return pd.DataFrame()

    crudo_idx, limpio_idx = _indexar(df_crudo, df_limpio)
    crudo_idx, limpio_idx = crudo_idx[cols_num], limpio_idx[cols_num]

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