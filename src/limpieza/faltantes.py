from __future__ import annotations
import pandas as pd


def reporte_faltantes(df: pd.DataFrame) -> pd.DataFrame:
    rep = pd.DataFrame({
        "columna": df.columns,
        "faltantes": [df[c].isna().sum() for c in df.columns],
        "porcentaje": [df[c].isna().mean() * 100 for c in df.columns],
    })
    return rep.sort_values("faltantes", ascending=False)


def imputar(df: pd.DataFrame, estrategia: str = "mediana") -> pd.DataFrame:
    salida = df.copy()
    columnas_num = salida.select_dtypes(include="number").columns
    for c in columnas_num:
        if salida[c].isna().sum() == 0:
            continue
        if estrategia == "media":
            salida[c] = salida[c].fillna(salida[c].mean())
        elif estrategia == "moda":
            m = salida[c].mode()
            if not m.empty:
                salida[c] = salida[c].fillna(m.iloc[0])
            salida[c] = salida[c].fillna(salida[c].median())
    return salida


def eliminar_columnas_vacias(df: pd.DataFrame, umbral: float = 0.5) -> pd.DataFrame:
    conservar = [c for c in df.columns if df[c].isna().mean() <= umbral]
    return df[conservar]