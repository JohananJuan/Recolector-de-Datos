from __future__ import annotations

import pandas as pd

from limpieza.etapas.nucleo import EtapaTabular, ResultadoEtapa


class EtapaLegal(EtapaTabular):
    nombre = "Cumplimiento legal"
    tema = "1.4"

    @classmethod
    def _parametros_por_defecto(cls) -> dict:
        return {"requeridas": ["licencia", "consentimiento", "origen"]}

    def aplicar(self, df: pd.DataFrame) -> ResultadoEtapa:
        df_antes = df.copy()
        requeridas = [c for c in self.parametros["requeridas"] if c in df.columns]

        if not requeridas:
            return ResultadoEtapa(
                nombre=self.nombre, tema=self.tema, df=df, df_antes=df_antes,
                metricas={"filas_afectadas": 0, "cumplen": 0, "semaforo": "rojo"},
                mensaje="Sin campos legales en el esquema",
            )

        mask = pd.Series(True, index=df.index)
        for c in requeridas:
            mask &= df[c].notna() & (df[c].astype(str).str.strip() != "")

        cumplen = int(mask.sum())
        total = len(df)
        semaforo = (
            "verde" if cumplen == total
            else "amarillo" if cumplen > 0 else "rojo"
        )

        return ResultadoEtapa(
            nombre=self.nombre, tema=self.tema, df=df, df_antes=df_antes,
            metricas={
                "filas_afectadas": total - cumplen,
                "cumplen": cumplen, "total": total, "semaforo": semaforo,
                "por_columna": {
                    c: int(df[c].notna().sum()) for c in requeridas
                },
            },
            mensaje=f"{cumplen}/{total} cumplen · {semaforo.upper()}",
        )