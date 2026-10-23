import io
import contextlib
from pathlib import Path

from division.exportar import exportar_splits


class ControladorSplits:
    def exportar(self, metadata_path: Path, salida: Path) -> tuple[dict, str]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            conteo = exportar_splits(metadata_path, salida)
        return conteo, buf.getvalue()