from __future__ import annotations

import pandas as pd

from limpieza.etapas.nucleo import EtapaTabular, ResultadoEtapa


class EtapaCorrelacion(EtapaTabular):
    nombre = "Redundancia y correlación"
    tema = "2.2.1"

    @classmethod
    def _parametros_por_defecto(cls) -> dict:
        return {"umbral": 0.9, "eliminar": False}

    def aplicar(self, df: pd.DataFrame) -> ResultadoEtapa:
        df_antes = df.copy()
        num = df.select_dtypes("number")
        if num.shape[1] < 2:
            return ResultadoEtapa(
                nombre=self.nombre, tema=self.tema, df=df, df_antes=df_antes,
                metricas={"filas_afectadas": 0},
                mensaje="Sin columnas numéricas suficientes",
            )

        corr = num.corr().abs()
        umbral = float(self.parametros["umbral"])
        pares = [
            {"a": c1, "b": c2, "r": round(float(corr.loc[c1, c2]), 4)}
            for i, c1 in enumerate(corr.columns)
            for c2 in corr.columns[i + 1:]
            if corr.loc[c1, c2] >= umbral
        ]

        eliminadas: list[str] = []
        if self.parametros.get("eliminar"):
            a_eliminar: set[str] = set()
            for par in pares:
                if par["a"] not in a_eliminar:
                    a_eliminar.add(par["b"])
            eliminadas = sorted(a_eliminar)
            df = df.drop(columns=eliminadas, errors="ignore")

        return ResultadoEtapa(
            nombre=self.nombre, tema=self.tema, df=df, df_antes=df_antes,
            metricas={
                "filas_afectadas": len(eliminadas),
                "pares_correlacionados": pares,
                "columnas_eliminadas": eliminadas,
                "matriz_correlacion": corr.round(3).to_dict(),
            },
            mensaje=f"{len(pares)} pares |r|≥{umbral}; {len(eliminadas)} col. eliminadas",
        )
        