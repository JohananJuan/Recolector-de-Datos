from __future__ import annotations

import pandas as pd

from limpieza.etapas.nucleo import ResultadoEtapa
from limpieza.registro import registro_etapas, mapa_cumplimiento_temario


def tabla_cumplimiento(
    resultados: list[ResultadoEtapa] | None = None,
) -> pd.DataFrame:
    ejecutadas = {r.tema: r for r in (resultados or [])}
    filas = []
    for tema, etapas in mapa_cumplimiento_temario().items():
        for e in etapas:
            r = ejecutadas.get(tema)
            filas.append({
                "tema": tema,
                "etapa": e["nombre"],
                "clase": e["clase"],
                "implementada": "✓",
                "ultima_ejecucion": (
                    r.mensaje if r else "—"
                ),
                "filas_afectadas": r.filas_afectadas if r else 0,
                "estado": "✓" if r and r.ok else "pendiente",
            })
    return pd.DataFrame(filas)