import io
import contextlib
from pathlib import Path

from core.rutas import PROCESSED_DIR, CAPTURAS_DIR, METADATA_CAPTURAS
from metadata.repositorio import nuevo_repositorio
from limpieza.reglas import reglas_por_defecto
from limpieza.pipeline import PipelineValidacion
from servicios.validacion import ServicioValidacion


class ControladorValidacion:
    def __init__(self):
        self._repo = nuevo_repositorio()
        self._pipeline = PipelineValidacion(reglas_por_defecto())
        self._servicio = ServicioValidacion(self._pipeline, self._repo)

    def validar(self, directorio: Path, fuente: str) -> tuple[dict, str]:
        """Ejecuta la validación y captura stdout para mostrarlo en la consola UI."""
        salida = Path(directorio) / "metadata.csv"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            resumen = self._servicio.validar_directorio(directorio, salida, fuente)
        return resumen, buf.getvalue()

    def preset_publico(self) -> tuple[Path, str]:
        return PROCESSED_DIR, "dataset_publico"

    def preset_capturas(self) -> tuple[Path, str]:
        return CAPTURAS_DIR, "captura_controlada"