from __future__ import annotations
from pathlib import Path
import json

import pandas as pd

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from analisis.estadisticas_generales import EstadisticasGenerales


def _celda(v):
    if isinstance(v, (dict, list, tuple, set)):
        s = json.dumps(v, default=str, ensure_ascii=False)
        return s if len(s) <= 32000 else s[:32000] + "…"
    return v


def _plano(df):
    if df is None:
        return None
    df = df.copy()
    for c in df.columns:
        if df[c].dtype == object and df[c].map(
            lambda x: isinstance(x, (list, tuple, set, dict))
        ).any():
            df[c] = df[c].map(
                lambda x: ", ".join(map(str, x))
                if isinstance(x, (list, tuple, set)) else _celda(x)
            )
    return df


def _resumen_metricas(m: dict) -> pd.DataFrame:
    filas = []
    for k, v in m.items():
        if isinstance(v, dict):
            filas += [{"etapa": k, "métrica": kk, "valor": _celda(vv)}
                      for kk, vv in v.items()]
        else:
            filas.append({"etapa": "global", "métrica": k, "valor": _celda(v)})
    return pd.DataFrame(filas)


def exportar_excel(
    df_crudo: pd.DataFrame,
    df_limpio: pd.DataFrame,
    tabla_comparativa: pd.DataFrame,
    metricas: dict,
    ruta: Path,
    *,
    df_normalizado: pd.DataFrame | None = None,
    normalizacion: dict | None = None,
    pairwise: pd.DataFrame | None = None,
    listwise: pd.DataFrame | None = None,
    estandar: dict | None = None,
    df_aprobadas: pd.DataFrame | None = None,
    df_rechazadas: pd.DataFrame | None = None,
    estadisticas: "EstadisticasGenerales | None" = None,
    cumplimiento_temario: "pd.DataFrame | None" = None,
    legal_resumen: "pd.DataFrame | None" = None,
    trazabilidad_etapas: "list[dict] | None" = None,
) -> Path:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    df_crudo, df_limpio = _plano(df_crudo), _plano(df_limpio)
    df_normalizado = _plano(df_normalizado)
    df_aprobadas, df_rechazadas = _plano(df_aprobadas), _plano(df_rechazadas)

    with pd.ExcelWriter(ruta, engine="openpyxl") as writer:
        _resumen_metricas(metricas).to_excel(
            writer, sheet_name="00_Resumen", index=False
        )
        df_crudo.to_excel(writer, sheet_name="01_Crudo", index=False)
        df_limpio.to_excel(writer, sheet_name="02_Limpio", index=False)
        tabla_comparativa.to_excel(
            writer, sheet_name="03_Comparativa", index=False
        )
        df_crudo.describe(include="all").T.to_excel(
            writer, sheet_name="04_Describe_Crudo"
        )
        df_limpio.describe(include="all").T.to_excel(
            writer, sheet_name="05_Describe_Limpio"
        )

        if df_normalizado is not None:
            df_normalizado.to_excel(
                writer, sheet_name="06_Normalizado", index=False
            )

        if normalizacion:
            filas_norm = []
            metodo = normalizacion.get("metodo", "?")
            for col, params in normalizacion.get("parametros", {}).items():
                for k, v in params.items():
                    filas_norm.append({
                        "columna": col, "metodo": metodo,
                        "parametro": k, "valor": v,
                    })
            if filas_norm:
                pd.DataFrame(filas_norm).to_excel(
                    writer, sheet_name="07_Param_Normalizacion", index=False
                )

        if pairwise is not None and not pairwise.empty:
            pairwise.to_excel(writer, sheet_name="08_Pairwise", index=False)

        if listwise is not None and not listwise.empty:
            listwise.to_excel(writer, sheet_name="09_Listwise", index=False)

        if estandar:
            filas_est = [{"campo": "estandar",
                          "valor": estandar.get("estandar", "")}]
            for k in ("total_filas", "aprobadas", "rechazadas",
                      "porcentaje_aprobacion"):
                filas_est.append({"campo": k, "valor": estandar.get(k, "")})
            pd.DataFrame(filas_est).to_excel(
                writer, sheet_name="10_Estandar_Resumen", index=False
            )
            reglas = estandar.get("reglas", [])
            if reglas:
                pd.DataFrame(reglas).to_excel(
                    writer, sheet_name="11_Estandar_Reglas", index=False
                )

        if df_aprobadas is not None:
            df_aprobadas.to_excel(
                writer, sheet_name="12_Aprobadas", index=False
            )
        if df_rechazadas is not None:
            df_rechazadas.to_excel(
                writer, sheet_name="13_Rechazadas", index=False
            )

        nombre_hoja_por_titulo: dict[str, str] = {}
        secciones_dict: dict[str, pd.DataFrame] = {}
        if estadisticas is not None:
            offset = 14
            for i, seccion in enumerate(estadisticas.secciones):
                nombre = f"{offset + i:02d}_{seccion.titulo}"[:31]
                seccion.tabla.to_excel(
                    writer, sheet_name=nombre, index=False
                )
                nombre_hoja_por_titulo[seccion.titulo] = nombre
                secciones_dict[seccion.titulo] = seccion.tabla

        if estadisticas is not None:
            from analisis.graficas_excel import insertar_graficas_extra

            top_bottom = {
                k.split("_", 1)[1]: v
                for k, v in secciones_dict.items()
                if k.startswith("TopBottom_")
            }
            insertar_graficas_extra(
                writer,
                nombre_hoja_por_titulo=nombre_hoja_por_titulo,
                resumen_numerico=secciones_dict.get(
                    "Resumen_Numerico", pd.DataFrame()
                ),
                top_bottom=top_bottom,
                comparativa_resumen=secciones_dict.get(
                    "Comparativa_Resumen", pd.DataFrame()
                ),
                distribucion_clases=secciones_dict.get(
                    "Distribucion_Clases", pd.DataFrame()
                ),
            )

        if cumplimiento_temario is not None and not cumplimiento_temario.empty:
            cumplimiento_temario.to_excel(
                writer, sheet_name="Cumplimiento_Temario", index=False
            )
        if legal_resumen is not None and not legal_resumen.empty:
            legal_resumen.to_excel(writer, sheet_name="Legal", index=False)
        if trazabilidad_etapas:
            df_traz = pd.DataFrame(trazabilidad_etapas)
            df_traz = df_traz.map(_celda) if hasattr(df_traz, "map") \
                else df_traz.applymap(_celda)
            df_traz.to_excel(writer, sheet_name="Trazabilidad_Etapas", index=False)

    return ruta