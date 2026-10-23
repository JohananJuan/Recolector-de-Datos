from __future__ import annotations
import numpy as np
import pandas as pd


def detectar_ruido_caracteristicas(df: pd.DataFrame, k: float = 3.0) -> pd.Series:
    num = df.select_dtypes(include="number").dropna()
    if len(num) < 5:
        return pd.Series(False, index=df.index)

    X = num.to_numpy(dtype=float)
    mu = X.mean(axis=0)
    cov = np.cov(X, rowvar=False) + np.eye(X.shape[1]) * 1e-6
    try:
        inv = np.linalg.inv(cov)
    except np.linalg.LinAlgError:
        return pd.Series(False, index=df.index)

    diff = X - mu
    md = np.sqrt(np.einsum("ij,jk,ik->i", diff, inv, diff))
    umbral = md.mean() + k * md.std()
    es_ruido = pd.Series(False, index=df.index)
    es_ruido.loc[num.index] = md > umbral
    return es_ruido


def suavizar_serie(s: pd.Series, ventana: int = 5) -> pd.Series:
    return s.rolling(window=ventana, center=True, min_periods=1).mean()


def winsorizar(
    df: pd.DataFrame, limites: tuple[float, float] = (0.01, 0.99)
) -> pd.DataFrame:
    salida = df.copy()
    for col in salida.select_dtypes(include="number").columns:
        serie = salida[col]
        if serie.notna().sum() < 2:
            continue
        lo, hi = serie.quantile(limites)
        if lo == hi:
            continue
        salida[col] = serie.clip(lo, hi)
    return salida