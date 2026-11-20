from __future__ import annotations

import re
import unicodedata

import pandas as pd

from limpieza.etapas.nucleo import EtapaTabular, ResultadoEtapa

_STOPWORDS = {"de", "la", "el", "los", "las", "un", "una", "y", "o", "para"}


def _normalizar(s: str, quitar_stop: bool) -> tuple[str, list[str]]:
    s = str(s).lower()
    s = "".join(
        c for c in unicodedata.normalize("NFKD", s)
        if not unicodedata.combining(c)
    )
    s = re.sub(r"\s+", " ", s).strip()
    tokens = re.findall(r"\w+", s)
    if quitar_stop:
        tokens = [t for t in tokens if t not in _STOPWORDS]
    return " ".join(tokens), tokens


class EtapaTexto(EtapaTabular):
    nombre = "Normalización de texto"
    tema = "3.1.3"

    @classmethod
    def _parametros_por_defecto(cls) -> dict:
        return {"columna": "clase", "quitar_stopwords": False}

    def aplicar(self, df: pd.DataFrame) -> ResultadoEtapa:
        df_antes = df.copy()
        df = df.copy()
        col = self.parametros["columna"]
        if col not in df.columns:
            return ResultadoEtapa(
                nombre=self.nombre, tema=self.tema, df=df, df_antes=df_antes,
                metricas={"filas_afectadas": 0},
                mensaje=f"Columna '{col}' ausente",
            )

        qs = bool(self.parametros["quitar_stopwords"])
        nueva = f"{col}_norm"
        tokens_col = f"{col}_tokens"
        resultado = df[col].map(lambda x: _normalizar(x, qs))
        df[nueva] = resultado.map(lambda t: t[0])
        df[tokens_col] = resultado.map(lambda t: t[1])

        mapeo = (
            df[[col, nueva]].astype(str)
            .drop_duplicates()
            .set_index(col)[nueva].to_dict()
        )

        return ResultadoEtapa(
            nombre=self.nombre, tema=self.tema, df=df, df_antes=df_antes,
            metricas={
                "filas_afectadas": len(df),
                "mapeo": mapeo,
                "etiquetas_antes": int(df[col].astype(str).nunique()),
                "etiquetas_despues": int(df[nueva].nunique()),
            },
            mensaje=f"{df[col].nunique()} → {df[nueva].nunique()} etiquetas únicas",
        )