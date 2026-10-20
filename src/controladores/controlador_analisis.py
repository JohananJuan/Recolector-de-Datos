from pathlib import Path
import pandas as pd

from core.rutas import METADATA_PROCESSED, LOGS_DIR
from metadata.repositorio import nuevo_repositorio
from limpieza.outliers import detectar_outliers


class ControladorAnalisis:
    def __init__(self):
        self._repo = nuevo_repositorio()

    def cargar_dataframe(self, metadata_path: Path = METADATA_PROCESSED) -> pd.DataFrame | None:
        registros = self._repo.leer(metadata_path)
        if not registros:
            return None
        return pd.DataFrame([r.a_dict() for r in registros])

    def resumen_numerico(self, df: pd.DataFrame, col: str) -> dict | None:
        if col not in df:
            return None
        s = pd.to_numeric(df[col], errors="coerce").dropna()
        if s.empty:
            return None
        out = detectar_outliers(s.tolist())
        return {
            "media": s.mean(), "mediana": s.median(),
            "moda": s.mode().iloc[0] if not s.mode().empty else None,
            "std": s.std(), "min": s.min(), "max": s.max(),
            "outliers_z": len(out.indices_zscore),
            "outliers_iqr": len(out.indices_iqr),
            "interseccion": len(out.indices_zscore & out.indices_iqr),
        }

    @property
    def logs_dir(self) -> Path:
        return LOGS_DIR