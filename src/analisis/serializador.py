from __future__ import annotations
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def _a_json(obj: Any) -> Any:
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return None if np.isnan(obj) else float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, pd.Series):
        return obj.to_dict()
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, set):
        return list(obj)
    if pd.isna(obj):
        return None
    raise TypeError(f"No serializable: {type(obj)} → {obj!r}")


def serializar_analisis(
    ruta: Path,
    metricas: dict,
    tabla_comparativa: pd.DataFrame,
    pairwise: pd.DataFrame | None = None,
    listwise: pd.DataFrame | None = None,
    normalizacion: dict | None = None,
    estandar: dict | None = None,
    resumen_estadistico: pd.DataFrame | None = None,
) -> Path:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    payload: dict[str, Any] = {
        "metricas": metricas,
        "normalizacion": normalizacion or {},
        "estandar": estandar or {},
        "tabla_comparativa": (
            tabla_comparativa.to_dict(orient="records")
            if not tabla_comparativa.empty else []
        ),
        "pairwise": (
            pairwise.to_dict(orient="records") if pairwise is not None
            else []
        ),
        "listwise": (
            listwise.to_dict(orient="records") if listwise is not None
            else []
        ),
        "resumen_estadistico": (
            resumen_estadistico.to_dict()
            if resumen_estadistico is not None else {}
        ),
    }

    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=_a_json)
    return ruta


def serializar_csv_plano(
    ruta: Path,
    pairwise: pd.DataFrame | None = None,
    listwise: pd.DataFrame | None = None,
) -> Path:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    if pairwise is not None and not pairwise.empty:
        pairwise.to_csv(ruta.with_name(ruta.stem + "_pairwise.csv"), index=False)
    if listwise is not None and not listwise.empty:
        listwise.to_csv(ruta.with_name(ruta.stem + "_listwise.csv"), index=False)
    return ruta