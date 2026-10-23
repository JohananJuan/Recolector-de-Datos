from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd


@dataclass
class SeccionEstadisticas:
    titulo: str
    tabla: pd.DataFrame


@dataclass
class EstadisticasGenerales:
    secciones: list[SeccionEstadisticas]

    def como_dict(self) -> dict[str, pd.DataFrame]:
        return {s.titulo: s.tabla for s in self.secciones}


def _tabla_resumen_dimensiones(
    crudo: pd.DataFrame, limpio: pd.DataFrame,
    metricas: dict,
) -> pd.DataFrame:
    filas = [
        ("filas_crudas", len(crudo)),
        ("filas_limpias", len(limpio)),
        ("filas_eliminadas", len(crudo) - len(limpio)),
        ("columnas_crudas", len(crudo.columns)),
        ("columnas_limpias", len(limpio.columns)),
        ("celdas_totales_crudas", int(crudo.size)),
        ("celdas_totales_limpias", int(limpio.size)),
        ("nulos_crudos", int(crudo.isna().sum().sum())),
        ("nulos_limpios", int(limpio.isna().sum().sum())),
        ("%_filas_eliminadas",
         round((len(crudo) - len(limpio)) / max(len(crudo), 1) * 100, 2)),
        ("metodo_normalizacion", metricas.get("metodo_normalizacion", "—")),
    ]
    return pd.DataFrame(filas, columns=["métrica", "valor"])


def _tabla_distribucion_clase(df: pd.DataFrame) -> pd.DataFrame:
    if "clase" not in df.columns or df.empty:
        return pd.DataFrame(columns=["clase", "conteo", "porcentaje"])
    vc = df["clase"].value_counts()
    total = int(vc.sum())
    return pd.DataFrame({
        "clase": vc.index,
        "conteo": vc.values,
        "porcentaje": (vc.values / total * 100).round(2),
    })


def _tabla_resumen_numerico(
    df: pd.DataFrame, top_n: int = 8,
) -> pd.DataFrame:
    candidatas = [
        c for c in (
            "brillo_medio", "contraste_rms", "varianza_laplaciano",
            "ruido_estimado", "colorido", "hist_entropia",
            "saturacion_media", "tamano_bytes",
        )
        if c in df.columns and pd.api.types.is_numeric_dtype(df[c])
    ]

    filas: list[dict] = []
    for col in candidatas:
        s = pd.to_numeric(df[col], errors="coerce").dropna()
        if s.empty:
            continue
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        n_out_iqr = int(((s < lo) | (s > hi)).sum())

        mu = s.mean()
        sigma = s.std(ddof=0)
        n_out_z = 0
        if sigma > 0:
            n_out_z = int((((s - mu) / sigma).abs() > 3).sum())

        filas.append({
            "columna": col,
            "n": int(s.size),
            "media": round(float(mu), 4),
            "mediana": round(float(s.median()), 4),
            "std": round(float(sigma), 4),
            "min": round(float(s.min()), 4),
            "p25": round(float(q1), 4),
            "p75": round(float(q3), 4),
            "max": round(float(s.max()), 4),
            "sesgo": round(float(s.skew()), 4),
            "curtosis": round(float(s.kurt()), 4),
            "outliers_iqr": n_out_iqr,
            "outliers_z": n_out_z,
        })
    return pd.DataFrame(filas)


def _tabla_top_bottom(
    df: pd.DataFrame, col: str, etiqueta: str, n: int = 5,
) -> pd.DataFrame:
    """Top n y bottom n de una columna, con su ruta."""
    if col not in df.columns or df.empty:
        return pd.DataFrame()
    columnas = [c for c in ("ruta", "clase", col) if c in df.columns]
    s = pd.to_numeric(df[col], errors="coerce")
    validos = df.loc[s.notna(), columnas].copy()
    if validos.empty:
        return pd.DataFrame()

    top = validos.nlargest(n, col).assign(ranking=[f"top_{i+1}" for i in range(min(n, len(validos)))])
    bottom = validos.nsmallest(n, col).assign(ranking=[f"bottom_{i+1}" for i in range(min(n, len(validos)))])
    resultado = pd.concat([top, bottom], ignore_index=True)
    resultado.insert(0, "métrica", etiqueta)
    return resultado


def _tabla_normalizacion(
    meta_norm: Optional[dict],
) -> pd.DataFrame:
    if not meta_norm:
        return pd.DataFrame([{"parámetro": "sin normalización", "valor": "—"}])

    metodo = meta_norm.get("metodo", "?")
    filas: list[dict] = [
        {"parámetro": "método", "columna": "—", "valor": metodo},
        {"parámetro": "columnas_afectadas", "columna": "—",
         "valor": len(meta_norm.get("columnas_afectadas", []))},
    ]
    for col, params in meta_norm.get("parametros", {}).items():
        for k, v in params.items():
            filas.append({
                "parámetro": k,
                "columna": col,
                "valor": round(float(v), 6) if isinstance(v, (int, float)) else v,
            })
    return pd.DataFrame(filas)


def _tabla_estandar(resumen: Optional[dict]) -> pd.DataFrame:
    if not resumen:
        return pd.DataFrame([{"campo": "estándar", "valor": "no aplicado"}])
    filas = [
        ("estandar", resumen.get("estandar", "")),
        ("total_filas", resumen.get("total_filas", 0)),
        ("aprobadas", resumen.get("aprobadas", 0)),
        ("rechazadas", resumen.get("rechazadas", 0)),
        ("porcentaje_aprobacion", resumen.get("porcentaje_aprobacion", 0.0)),
    ]
    return pd.DataFrame(filas, columns=["campo", "valor"])


def _tabla_estandar_reglas(resumen: Optional[dict]) -> pd.DataFrame:
    if not resumen or not resumen.get("reglas"):
        return pd.DataFrame()
    return pd.DataFrame(resumen["reglas"])


def _tabla_comparativa_resumen(
    comparativa: pd.DataFrame,
) -> pd.DataFrame:
    """Cuántas columnas cambiaron y magnitud media del delta."""
    if comparativa is None or comparativa.empty:
        return pd.DataFrame()
    agrup = comparativa.groupby("columna").agg(
        cambios=("delta_%", lambda x: int((x.abs() > 1e-6).sum())),
        delta_medio_abs=("delta_%", lambda x: round(float(x.abs().mean()), 4)),
        delta_max_abs=("delta_%", lambda x: round(float(x.abs().max()), 4)),
    ).reset_index()
    return agrup.sort_values("delta_medio_abs", ascending=False)


def generar_estadisticas_generales(
    crudo: pd.DataFrame,
    limpio: pd.DataFrame,
    metricas: dict,
    *,
    comparativa: pd.DataFrame | None = None,
    pairwise: pd.DataFrame | None = None,
    listwise: pd.DataFrame | None = None,
    meta_normalizacion: dict | None = None,
    estandar_resumen: dict | None = None,
) -> EstadisticasGenerales:
    secciones: list[SeccionEstadisticas] = []

    # 1) Dimensiones
    secciones.append(SeccionEstadisticas(
        "Dimensiones", _tabla_resumen_dimensiones(crudo, limpio, metricas),
    ))

    # 2) Distribución por clase
    dist = _tabla_distribucion_clase(limpio)
    if not dist.empty:
        secciones.append(SeccionEstadisticas(
            "Distribucion_Clases", dist,
        ))

    # 3) Resumen numérico de columnas clave
    resumen_num = _tabla_resumen_numerico(limpio)
    if not resumen_num.empty:
        secciones.append(SeccionEstadisticas(
            "Resumen_Numerico", resumen_num,
        ))

    # 4) Top/bottom por métricas clave
    for col, etiqueta in (
        ("brillo_medio", "Brillo (top/bottom)"),
        ("varianza_laplaciano", "Nitidez (top/bottom)"),
        ("ruido_estimado", "Ruido (top/bottom)"),
        ("colorido", "Colorido (top/bottom)"),
    ):
        tabla = _tabla_top_bottom(limpio, col, etiqueta)
        if not tabla.empty:
            secciones.append(SeccionEstadisticas(
                f"TopBottom_{etiqueta.split(' ')[0]}", tabla,
            ))

    # 5) Normalización
    secciones.append(SeccionEstadisticas(
        "Normalizacion", _tabla_normalizacion(meta_normalizacion),
    ))

    # 6) Estándar
    secciones.append(SeccionEstadisticas(
        "Estandar_Resumen", _tabla_estandar(estandar_resumen),
    ))
    tabla_reglas = _tabla_estandar_reglas(estandar_resumen)
    if not tabla_reglas.empty:
        secciones.append(SeccionEstadisticas(
            "Estandar_Reglas", tabla_reglas,
        ))

    # 7) Comparativa resumen
    if comparativa is not None and not comparativa.empty:
        tabla_comp = _tabla_comparativa_resumen(comparativa)
        if not tabla_comp.empty:
            secciones.append(SeccionEstadisticas(
                "Comparativa_Resumen", tabla_comp,
            ))

    # 8) Pairwise / Listwise 
    if pairwise is not None and not pairwise.empty:
        tabla_p = pd.DataFrame([{
            "total_comparaciones": len(pairwise),
            "columnas_comparadas": pairwise["columna"].nunique(),
            "rutas_comparadas": pairwise["ruta"].nunique(),
            "cambio_medio_abs": round(
                float(pairwise["delta"].abs().mean()), 6
            ),
        }])
        secciones.append(SeccionEstadisticas(
            "Pairwise_Resumen", tabla_p,
        ))

    if listwise is not None and not listwise.empty:
        tabla_l = pd.DataFrame([{
            "total_filas": len(listwise),
            "eliminadas": int(listwise["eliminada"].sum()),
            "similares": int(listwise["similar"].sum()),
            "distancia_media": round(
                float(listwise["distancia_l2"].dropna().mean()), 6
            ),
            "distancia_max": round(
                float(listwise["distancia_l2"].dropna().max()), 6
            ),
        }])
        secciones.append(SeccionEstadisticas(
            "Listwise_Resumen", tabla_l,
        ))

    return EstadisticasGenerales(secciones)