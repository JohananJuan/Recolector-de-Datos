from dataclasses import dataclass
from typing import Iterable
import numpy as np


@dataclass
class ResultadoOutliers:
    indices_zscore: set[int]
    indices_iqr: set[int]
    umbral_z: float
    q1: float
    q3: float
    mediana: float
    media: float
    moda: float | None


def detectar_outliers(valores: Iterable[float], umbral_z: float = 3.0) -> ResultadoOutliers:
    arr = np.array([v for v in valores if v is not None and not np.isnan(v)], dtype=float)
    n = len(arr)
    if n < 5:
        return ResultadoOutliers(set(), set(), umbral_z, 0, 0, 0, 0, None)

    media = float(arr.mean())
    std = float(arr.std(ddof=0))
    mediana = float(np.median(arr))
    q1 = float(np.percentile(arr, 25))
    q3 = float(np.percentile(arr, 75))
    iqr = q3 - q1

    if std > 0:
        z = np.abs((arr - media) / std)
        idx_z = set(np.where(z > umbral_z)[0].tolist())
    else:
        idx_z = set()

    if iqr > 0:
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        idx_iqr = set(np.where((arr < lo) | (arr > hi))[0].tolist())
    else:
        idx_iqr = set()

    vals, counts = np.unique(arr, return_counts=True)
    moda = float(vals[counts.argmax()]) if len(vals) else None

    return ResultadoOutliers(idx_z, idx_iqr, umbral_z, q1, q3, mediana, media, moda)