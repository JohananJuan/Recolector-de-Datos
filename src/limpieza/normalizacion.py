from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd


@dataclass
class ResultadoNormalizacion:
    df: pd.DataFrame
    metodo: str
    columnas_afectadas: list[str]
    parametros: dict = field(default_factory=dict)


def _columnas_numericas(df: pd.DataFrame) -> list[str]:
    return list(df.select_dtypes(include="number").columns)


def normalizar_minmax(df: pd.DataFrame) -> ResultadoNormalizacion:
    salida = df.copy()
    cols = _columnas_numericas(df)
    parametros: dict[str, dict] = {}
    for c in cols:
        s = salida[c]
        if s.notna().sum() < 2:
            continue
        lo, hi = float(s.min()), float(s.max())
        parametros[c] = {"min": lo, "max": hi}
        rango = hi - lo
        salida[c] = 0.0 if rango == 0 else (s - lo) / rango
    return ResultadoNormalizacion(
        df=salida, metodo="minmax",
        columnas_afectadas=cols, parametros=parametros,
    )


def normalizar_zscore(df: pd.DataFrame) -> ResultadoNormalizacion:
    salida = df.copy()
    cols = _columnas_numericas(df)
    parametros: dict[str, dict] = {}
    for c in cols:
        s = salida[c]
        if s.notna().sum() < 2:
            continue
        mu, sigma = float(s.mean()), float(s.std(ddof=0))
        parametros[c] = {"media": mu, "std": sigma}
        salida[c] = 0.0 if sigma == 0 else (s - mu) / sigma
    return ResultadoNormalizacion(
        df=salida, metodo="zscore",
        columnas_afectadas=cols, parametros=parametros,
    )


def normalizar_robusto(df: pd.DataFrame) -> ResultadoNormalizacion:
    salida = df.copy()
    cols = _columnas_numericas(df)
    parametros: dict[str, dict] = {}
    for c in cols:
        s = salida[c]
        if s.notna().sum() < 2:
            continue
        mediana = float(s.median())
        q1, q3 = float(s.quantile(0.25)), float(s.quantile(0.75))
        iqr = q3 - q1
        parametros[c] = {"mediana": mediana, "iqr": iqr}
        salida[c] = 0.0 if iqr == 0 else (s - mediana) / iqr
    return ResultadoNormalizacion(
        df=salida, metodo="robusto",
        columnas_afectadas=cols, parametros=parametros,
    )


def normalizar_l2(df: pd.DataFrame) -> ResultadoNormalizacion:
    salida = df.copy()
    cols = _columnas_numericas(df)
    parametros: dict[str, dict] = {}
    for c in cols:
        s = salida[c]
        norma = float(np.sqrt((s ** 2).sum()))
        parametros[c] = {"norma_l2": norma}
        salida[c] = 0.0 if norma == 0 else s / norma
    return ResultadoNormalizacion(
        df=salida, metodo="l2",
        columnas_afectadas=cols, parametros=parametros,
    )


_METODOS: dict[str, Callable[[pd.DataFrame], ResultadoNormalizacion]] = {
    "minmax": normalizar_minmax,
    "zscore": normalizar_zscore,
    "robusto": normalizar_robusto,
    "l2": normalizar_l2,
}


def metodos_disponibles() -> list[str]:
    return list(_METODOS.keys())


def normalizar(df: pd.DataFrame, metodo: str = "zscore") -> ResultadoNormalizacion:
    if metodo not in _METODOS:
        raise ValueError(
            f"Método desconocido: {metodo}. "
            f"Disponibles: {metodos_disponibles()}"
        )
    return _METODOS[metodo](df)