from __future__ import annotations

import pandas as pd

from limpieza.etapas.nucleo import EtapaTabular, ResultadoEtapa
from limpieza.faltantes import imputar
from limpieza.ruido import detectar_ruido_caracteristicas, winsorizar


class EtapaLimpieza(EtapaTabular):

    nombre = "Limpieza (ruido + imputación + winsor)"
    tema = "2.1"

    @classmethod
    def _parametros_por_defecto(cls) -> dict:
        return {"metodo_imputacion": "mediana"}

    def aplicar(self, df: pd.DataFrame) -> ResultadoEtapa:
        df_antes = df.copy()
        nulos_antes = int(df.isna().sum().sum())

        es_ruido = detectar_ruido_caracteristicas(df)
        limpio = df.loc[~es_ruido].copy()
        eliminadas_ruido = df.loc[es_ruido, ["ruta"]].copy() \
            if "ruta" in df.columns else df.loc[es_ruido].head(0)

        limpio = imputar(limpio, self.parametros["metodo_imputacion"])
        nulos_despues = int(limpio.isna().sum().sum())
        limpio = winsorizar(limpio)

        return ResultadoEtapa(
            nombre=self.nombre, tema=self.tema, df=limpio, df_antes=df_antes,
            metricas={
                "filas_afectadas": int(es_ruido.sum()) + (nulos_antes - nulos_despues),
                "filas_ruido_eliminadas": int(es_ruido.sum()),
                "celdas_nulas_imputadas": nulos_antes - nulos_despues,
                "nulos_por_columna": df.isna().sum().to_dict(),
                "filas_eliminadas": eliminadas_ruido.to_dict(orient="records"),
            },
            mensaje=(
                f"ruido eliminado: {int(es_ruido.sum())}; "
                f"nulos imputados: {nulos_antes - nulos_despues}"
            ),
        )