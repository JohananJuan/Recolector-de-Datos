from __future__ import annotations
from pathlib import Path
import pandas as pd

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from analisis.estadisticas_generales import EstadisticasGenerales


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
) -> Path:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(ruta, engine="openpyxl") as writer:
        pd.DataFrame([metricas]).to_excel(
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

    return ruta