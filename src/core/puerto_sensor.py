from __future__ import annotations

from typing import Optional

from core.sensor import (
    FuenteDistancia,
    FuenteNula,
    LectorArduinoSerial,
    autodetectar_puerto,
)


def crear_fuente_distancia(
    puerto_preferido: Optional[str] = None,
    baudios: int = 115200,
    permitir_nulo: bool = True,
) -> FuenteDistancia:

    if puerto_preferido:
        return LectorArduinoSerial(puerto_preferido, baudios)

    detectado = autodetectar_puerto()
    if detectado:
        return LectorArduinoSerial(detectado, baudios)

    if permitir_nulo:
        print("[SENSOR] No se detectó Arduino; usando modo sin sensor.")
        return FuenteNula()

    raise RuntimeError("No se encontró ningún puerto serial para el sensor")