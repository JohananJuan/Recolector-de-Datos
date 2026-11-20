from __future__ import annotations

import pandas as pd

from limpieza.etapas.nucleo import EtapaTabular, ResultadoEtapa
from limpieza.normalizacion import normalizar


class EtapaNormalizacion(EtapaTabular):
    nombre = "Normalización"
    tema = "2.3.1"

    @classmethod
    def _parametros_por_defecto(cls) -> dict:
        return {"metodo": "zscore"}  

    def aplicar(self, df: pd.DataFrame) -> ResultadoEtapa:
        df_antes = df.copy()
        res = normalizar(df, self.parametros["metodo"])

        return ResultadoEtapa(
            nombre=self.nombre, tema=self.tema, df=res.df, df_antes=df_antes,
            metricas={
                "filas_afectadas": len(df),
                "metodo": res.metodo,
                "columnas_afectadas": res.columnas_afectadas,
                "parametros": res.parametros,
            },
            mensaje=f"{len(res.columnas_afectadas)} col. con {res.metodo}",
        )