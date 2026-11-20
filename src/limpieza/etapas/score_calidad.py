from __future__ import annotations

import numpy as np
import pandas as pd

from limpieza.etapas.nucleo import EtapaTabular, ResultadoEtapa


class EtapaScoreCalidad(EtapaTabular):
    nombre = "Score de calidad (0–100)"
    tema = "2.2.2"

    @classmethod
    def _parametros_por_defecto(cls) -> dict:
        return {
            "col_nitidez": "varianza_laplaciano",
            "col_brillo": "brillo_medio",
            "col_ruido": "ruido_estimado",
        }

    def aplicar(self, df: pd.DataFrame) -> ResultadoEtapa:
        df_antes = df.copy()
        cols = self.parametros
        faltan = [c for c in cols.values() if c not in df.columns]
        if faltan:
            return ResultadoEtapa(
                nombre=self.nombre, tema=self.tema, df=df, df_antes=df_antes,
                metricas={"filas_afectadas": 0},
                mensaje=f"Faltan columnas: {faltan}",
            )

        def _norm(s: pd.Series) -> pd.Series:
            lo, hi = s.min(), s.max()
            if pd.isna(lo) or hi == lo:
                return pd.Series(0.5, index=s.index)
            return (s - lo) / (hi - lo)

        nitidez = _norm(pd.to_numeric(df[cols["col_nitidez"]], errors="coerce"))
        brillo = pd.to_numeric(df[cols["col_brillo"]], errors="coerce")
        ruido = pd.to_numeric(df[cols["col_ruido"]], errors="coerce")

        brillo_score = 1 - (brillo - 128).abs() / 128
        brillo_score = brillo_score.clip(0, 1)

        r_min, r_max = ruido.min(), ruido.max()
        ruido_score = (
            pd.Series(0.5, index=ruido.index) if pd.isna(r_min) or r_min == r_max
            else 1 - (ruido - r_min) / (r_max - r_min)
        )

        score = (0.4 * nitidez + 0.3 * brillo_score + 0.3 * ruido_score) * 100
        df["score_calidad"] = score.round(2).fillna(0.0)

        return ResultadoEtapa(
            nombre=self.nombre, tema=self.tema, df=df, df_antes=df_antes,
            metricas={
                "filas_afectadas": len(df),
                "score_medio": round(float(df["score_calidad"].mean()), 2),
                "score_min": round(float(df["score_calidad"].min()), 2),
                "score_max": round(float(df["score_calidad"].max()), 2),
                "histograma": np.histogram(df["score_calidad"], bins=10)[0].tolist(),
            },
            mensaje=f"score medio: {float(df['score_calidad'].mean()):.1f}/100",
        )