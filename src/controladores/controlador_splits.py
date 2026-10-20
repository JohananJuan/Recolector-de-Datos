import io
import contextlib
from pathlib import Path

from core.rutas import METADATA_PROCESSED, SPLITS_DIR
from division.exportar import exportar_splits


class ControladorSplits:
    def exportar(self, metadata_path: Path, salida: Path) -> tuple[dict, str]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            conteo = exportar_splits(metadata_path, salida)
        return conteo, buf.getvalue()

    @property
    def default_metadata(self) -> Path:
        return METADATA_PROCESSED

    @property
    def default_salida(self) -> Path:
        return SPLITS_DIR