from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd
from openpyxl.chart import (
    BarChart, LineChart, PieChart, Reference, ScatterChart, Series,
)
from openpyxl.chart.label import DataLabelList
from openpyxl.worksheet.worksheet import Worksheet


@dataclass
class DefinicionGrafica:
    tipo: str                       # "bar" | "pie" | "line" | "scatter"
    titulo: str
    hoja_datos: str
    col_categorias: str
    cols_valores: list[str]
    posicion: str = "H2"
    ancho: int = 18
    alto: int = 10


def _indice_columna(df: pd.DataFrame, nombre: str) -> int:
    return list(df.columns).index(nombre) + 1


def _construir_bar(datos_df: pd.DataFrame, defn: DefinicionGrafica) -> BarChart:
    chart = BarChart()
    chart.type = "col"
    chart.style = 10
    chart.title = defn.titulo
    chart.y_axis.title = "Valor"
    chart.x_axis.title = defn.col_categorias
    chart._meta_refs = {
        "idx_cat": _indice_columna(datos_df, defn.col_categorias),
        "cols_valores": [_indice_columna(datos_df, c) for c in defn.cols_valores],
        "n_filas": len(datos_df),
    }
    return chart


def _construir_pie(datos_df: pd.DataFrame, defn: DefinicionGrafica) -> PieChart:
    chart = PieChart()
    chart.title = defn.titulo
    chart._meta_refs = {
        "idx_cat": _indice_columna(datos_df, defn.col_categorias),
        "cols_valores": [_indice_columna(datos_df, defn.cols_valores[:1])],
        "n_filas": len(datos_df),
    }
    return chart


def _construir_line(datos_df: pd.DataFrame, defn: DefinicionGrafica) -> LineChart:
    chart = LineChart()
    chart.title = defn.titulo
    chart.y_axis.title = "Valor"
    chart.x_axis.title = defn.col_categorias
    chart._meta_refs = {
        "idx_cat": _indice_columna(datos_df, defn.col_categorias),
        "cols_valores": [_indice_columna(datos_df, c) for c in defn.cols_valores],
        "n_filas": len(datos_df),
    }
    return chart


def _construir_scatter(datos_df: pd.DataFrame, defn: DefinicionGrafica) -> ScatterChart:
    chart = ScatterChart()
    chart.title = defn.titulo
    chart.style = 13
    chart.x_axis.title = defn.col_categorias
    chart.y_axis.title = defn.cols_valores[0] if defn.cols_valores else "Y"
    chart._meta_refs = {
        "idx_x": _indice_columna(datos_df, defn.col_categorias),
        "idx_y": _indice_columna(datos_df, defn.cols_valores[0]),
        "n_filas": len(datos_df),
    }
    return chart


_CONSTRUCTORES = {
    "bar": _construir_bar,
    "pie": _construir_pie,
    "line": _construir_line,
    "scatter": _construir_scatter,
}


def _vincular_refs(chart, hoja: Worksheet, datos_df: pd.DataFrame) -> None:
    refs = getattr(chart, "_meta_refs", None)
    if refs is None:
        return
    n = refs["n_filas"]
    filas = (2, n + 1)

    if isinstance(chart, PieChart):
        idx_cat = refs["idx_cat"]
        idx_val = refs["cols_valores"][0]
        cats = Reference(hoja, min_col=idx_cat, min_row=filas[0], max_row=filas[1])
        vals = Reference(hoja, min_col=idx_val, min_row=filas[0], max_row=filas[1])
        chart.add_data(vals, titles_from_data=False)
        chart.set_categories(cats)
        chart.dataLabels = DataLabelList()
        chart.dataLabels.showPercent = True

    elif isinstance(chart, (BarChart, LineChart)):
        idx_cat = refs["idx_cat"]
        cats = Reference(hoja, min_col=idx_cat, min_row=filas[0], max_row=filas[1])
        chart.set_categories(cats)
        for idx_val in refs["cols_valores"]:
            vals = Reference(
                hoja, min_col=idx_val, min_row=filas[0] - 1, max_row=filas[1],
            )
            chart.add_data(vals, titles_from_data=True)

    elif isinstance(chart, ScatterChart):
        idx_x = refs["idx_x"]
        idx_y = refs["idx_y"]
        xs = Reference(hoja, min_col=idx_x, min_row=filas[0], max_row=filas[1])
        ys = Reference(hoja, min_col=idx_y, min_row=filas[0], max_row=filas[1])
        series = Series(ys, xs, title=datos_df.columns[idx_y - 1])
        chart.series.append(series)

    try:
        del chart._meta_refs
    except AttributeError:
        pass


def insertar_grafica(
    writer,
    definicion: DefinicionGrafica,
    datos_df: pd.DataFrame,
) -> None:
    if definicion.tipo not in _CONSTRUCTORES:
        raise ValueError(f"tipo de gráfica desconocido: {definicion.tipo}")

    hoja = writer.sheets.get(definicion.hoja_datos)
    if hoja is None or datos_df is None or datos_df.empty:
        return
    if definicion.col_categorias not in datos_df.columns:
        return
    if not all(c in datos_df.columns for c in definicion.cols_valores):
        return

    chart = _CONSTRUCTORES[definicion.tipo](datos_df, definicion)
    _vincular_refs(chart, hoja, datos_df)
    chart.width = definicion.ancho
    chart.height = definicion.alto
    hoja.add_chart(chart, definicion.posicion)


def insertar_graficas_extra(
    writer,
    *,
    nombre_hoja_por_titulo: dict[str, str],
    resumen_numerico: pd.DataFrame,
    top_bottom: dict[str, pd.DataFrame],
    comparativa_resumen: pd.DataFrame,
    distribucion_clases: pd.DataFrame | None = None,
) -> None:
    if distribucion_clases is not None and not distribucion_clases.empty:
        hoja = nombre_hoja_por_titulo.get("Distribucion_Clases")
        if hoja:
            insertar_grafica(
                writer,
                DefinicionGrafica(
                    tipo="pie",
                    titulo="Distribución por clase",
                    hoja_datos=hoja,
                    col_categorias="clase",
                    cols_valores=["conteo"],
                    posicion="F2",
                    ancho=14,
                    alto=10,
                ),
                distribucion_clases,
            )

    if comparativa_resumen is not None and not comparativa_resumen.empty:
        hoja = nombre_hoja_por_titulo.get("Comparativa_Resumen")
        if hoja:
            insertar_grafica(
                writer,
                DefinicionGrafica(
                    tipo="bar",
                    titulo="Δ% medio absoluto por columna",
                    hoja_datos=hoja,
                    col_categorias="columna",
                    cols_valores=["delta_medio_abs"],
                    posicion="F2",
                    ancho=20,
                    alto=12,
                ),
                comparativa_resumen.head(20),
            )

    for etiqueta, df in top_bottom.items():
        titulo_seccion = f"TopBottom_{etiqueta}"
        hoja = nombre_hoja_por_titulo.get(titulo_seccion)
        if not hoja or df is None or df.empty:
            continue
        col_valor = next(
            (c for c in df.columns
             if c not in ("métrica", "ruta", "clase", "ranking")),
            None,
        )
        if col_valor is None:
            continue
        insertar_grafica(
            writer,
            DefinicionGrafica(
                tipo="bar",
                titulo=f"Top/Bottom — {col_valor}",
                hoja_datos=hoja,
                col_categorias="ranking",
                cols_valores=[col_valor],
                posicion="H2",
                ancho=18,
                alto=10,
            ),
            df,
        )

    if not resumen_numerico.empty:
        hoja = nombre_hoja_por_titulo.get("Resumen_Numerico")
        if hoja:
            df_aux = resumen_numerico[["columna", "outliers_iqr"]].copy()
            insertar_grafica(
                writer,
                DefinicionGrafica(
                    tipo="bar",
                    titulo="Outliers IQR por columna",
                    hoja_datos=hoja,
                    col_categorias="columna",
                    cols_valores=["outliers_iqr"],
                    posicion="L2",
                    ancho=20,
                    alto=10,
                ),
                df_aux,
            )

    if not resumen_numerico.empty:
        hoja = nombre_hoja_por_titulo.get("Resumen_Numerico")
        if hoja:
            df_aux = resumen_numerico[["columna", "media"]].copy()
            insertar_grafica(
                writer,
                DefinicionGrafica(
                    tipo="bar",
                    titulo="Media por columna",
                    hoja_datos=hoja,
                    col_categorias="columna",
                    cols_valores=["media"],
                    posicion="L26",
                    ancho=20,
                    alto=10,
                ),
                df_aux,
            )