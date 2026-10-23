from __future__ import annotations
from pathlib import Path
import pandas as pd

from analisis.estadisticas import resumen_estadistico
from core.rutas import METADATA_PROCESSED
from limpieza.outliers import detectar_outliers
from metadata.repositorio import RepositorioMetadata, nuevo_repositorio


class AnalisisLectura:
    def __init__(self, repo: RepositorioMetadata | None = None):
        self._repo = repo or nuevo_repositorio()

    def cargar_dataframe(
        self, metadata_path: Path = METADATA_PROCESSED
    ) -> pd.DataFrame | None:
        registros = self._repo.leer(metadata_path)
        if not registros:
            return None
        return pd.DataFrame([r.a_dict() for r in registros])

    def resumen_numerico(self, df: pd.DataFrame, col: str) -> dict | None:
        if col not in df:
            return None
        est = resumen_estadistico(df)
        if est.empty or col not in est.index:
            return None
        out = detectar_outliers(
            pd.to_numeric(df[col], errors="coerce").dropna().tolist()
        )
        return {
            "media": est.loc[col, "media"],
            "mediana": est.loc[col, "mediana"],
            "moda": est.loc[col, "moda"],
            "std": est.loc[col, "std"],
            "min": est.loc[col, "min"],
            "max": est.loc[col, "max"],
            "outliers_z": len(out.indices_zscore),
            "outliers_iqr": len(out.indices_iqr),
            "interseccion": len(out.indices_zscore & out.indices_iqr),
        }