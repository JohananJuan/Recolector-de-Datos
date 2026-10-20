from pathlib import Path

from core.rutas import CAPTURAS_DIR, METADATA_CAPTURAS, CLASES_VALIDAS
from metadata.repositorio import nuevo_repositorio
from servicios.captura import ServicioCaptura
from servicios.clasificacion.factory import crear_clasificador
from servicios.clasificacion.servicio import ServicioClasificacion, EstadoClasificacion


class ControladorCaptura:
    def __init__(self, modelo_preferido: str = "yolo"):
        self._repo = nuevo_repositorio()
        self._captura = ServicioCaptura(self._repo, METADATA_CAPTURAS, camara="webcam_0")
        self._clasificacion = ServicioClasificacion(crear_clasificador(modelo_preferido))

    def guardar(self, frame, clase: str) -> Path | None:
        return self._captura.guardar(frame, clase)

    def contar_por_clase(self) -> dict[str, int]:
        return self._captura.contar_por_clase()

    def sesion_actual(self) -> str:
        return self._captura.sesion

    def clasificar(self, frame) -> EstadoClasificacion:
        return self._clasificacion.procesar(frame)

    def reiniciar_clasificacion(self) -> None:
        self._clasificacion.reset()

    def tiene_modelo(self) -> bool:
        return self._clasificacion.tiene_modelo

    @property
    def clases(self) -> tuple[str, ...]:
        return CLASES_VALIDAS

    @property
    def directorio(self) -> Path:
        return CAPTURAS_DIR