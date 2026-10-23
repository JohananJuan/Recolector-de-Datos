from pathlib import Path
from typing import NamedTuple

from core.rutas import (
    METADATA_PROCESSED,
    METADATA_CAPTURAS,
    PROCESSED_DIR,
    CAPTURAS_DIR,
    SPLITS_DIR,
)


class Preset(NamedTuple):
    directorio: Path
    metadata: Path
    etiqueta: str


def preset_publico() -> Preset:
    return Preset(
        directorio=PROCESSED_DIR,
        metadata=METADATA_PROCESSED,
        etiqueta="Dataset público",
    )


def preset_capturas() -> Preset:
    return Preset(
        directorio=CAPTURAS_DIR,
        metadata=METADATA_CAPTURAS,
        etiqueta="Capturas propias",
    )


def preset_splits() -> Preset:
    return Preset(
        directorio=SPLITS_DIR,
        metadata=METADATA_PROCESSED,
        etiqueta="Splits",
    )