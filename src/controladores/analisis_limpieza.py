from __future__ import annotations
from pathlib import Path
import pandas as pd

from servicios.extraccion_caracteristicas import ServicioExtraccionCaracteristicas
from analisis.comparador import pipeline_limpieza, tabla_comparativa
from analisis.exportador_excel import exportar_excel


class AnalisisLimpieza:
    def __init__(
        self,
        servicio_extraccion: ServicioExtraccionCaracteristicas | None = None,
    ):
        self._extraccion = (
            servicio_extraccion or ServicioExtraccionCaracteristicas()
        )

    def extraer_y_limpiar(
        self, raiz: Path
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
        df_crudo = self._extraccion.extraer_directorio(raiz)
        df_limpio, metricas = pipeline_limpieza(df_crudo)
        comparativa = tabla_comparativa(df_crudo, df_limpio)
        return df_crudo, df_limpio, comparativa, metricas

    def exportar(
        self,
        df_crudo: pd.DataFrame,
        df_limpio: pd.DataFrame,
        comparativa: pd.DataFrame,
        metricas: dict,
        ruta: Path,
    ) -> Path:
        return exportar_excel(df_crudo, df_limpio, comparativa, metricas, ruta)