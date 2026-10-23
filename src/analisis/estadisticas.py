from __future__ import annotations
import pandas as pd


def _moda_por_columna(num: pd.DataFrame) -> pd.Series:
    resultado: dict[str, float | None] = {}
    for col in num.columns:
        m = num[col].mode(dropna=True)
        resultado[col] = m.iloc[0] if not m.empty else None
    return pd.Series(resultado, dtype="object")


def resumen_estadistico(df: pd.DataFrame) -> pd.DataFrame:
    num = df.select_dtypes(include="number")
    if num.empty:
        return pd.DataFrame()

    media = num.mean()
    std = num.std()
    return pd.DataFrame({
        "media": media,
        "mediana": num.median(),
        "moda": _moda_por_columna(num),
        "std": std,
        "varianza": num.var(),
        "min": num.min(),
        "p25": num.quantile(0.25),
        "p75": num.quantile(0.75),
        "max": num.max(),
        "sesgo": num.skew(),
        "curtosis": num.kurt(),
        "cv": std / (media.abs() + 1e-9),
    })