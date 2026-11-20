from __future__ import annotations

from limpieza.etapas.nucleo import EtapaPreprocesamiento
from limpieza.etapas.legal import EtapaLegal
from limpieza.etapas.limpieza_datos import EtapaLimpieza
from limpieza.etapas.correlacion import EtapaCorrelacion
from limpieza.etapas.score_calidad import EtapaScoreCalidad
from limpieza.etapas.normalizacion_etapa import EtapaNormalizacion
from limpieza.etapas.discretizacion import EtapaDiscretizacion
from limpieza.etapas.redimensionado import EtapaRedimensionado
from limpieza.etapas.mejora import EtapaMejora
from limpieza.etapas.texto import EtapaTexto
from limpieza.etapas.caracteristicas import EtapaCaracteristicas

registro_etapas: dict[str, type[EtapaPreprocesamiento]] = {
    "legal": EtapaLegal,
    "limpieza": EtapaLimpieza,
    "correlacion": EtapaCorrelacion,
    "score_calidad": EtapaScoreCalidad,
    "normalizacion": EtapaNormalizacion,
    "discretizacion": EtapaDiscretizacion,
    "redimensionado": EtapaRedimensionado,
    "mejora": EtapaMejora,
    "texto": EtapaTexto,
    "caracteristicas": EtapaCaracteristicas,
}

ORDEN_TEMARIO = [
    "legal", "redimensionado", "mejora", "caracteristicas",
    "limpieza", "correlacion", "score_calidad",
    "discretizacion", "texto", "normalizacion",
]


def etapas_por_defecto():
    from limpieza.pipeline import ConfigEtapa
    return [ConfigEtapa(clave=k) for k in ORDEN_TEMARIO]


def listar_etapas() -> list[type[EtapaPreprocesamiento]]:
    return list(registro_etapas.values())


def mapa_cumplimiento_temario() -> dict[str, list[dict]]:
    mapa: dict[str, list[dict]] = {}
    for clave, cls in registro_etapas.items():
        mapa.setdefault(cls.tema, []).append({
            "clave": clave,
            "nombre": cls.nombre,
            "clase": cls.__name__,
        })
    return dict(sorted(mapa.items()))