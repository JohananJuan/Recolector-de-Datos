from __future__ import annotations

from datetime import datetime
from pathlib import Path

import cv2

from core.hashing import sha256_archivo
from core.rutas import BASE_DIR, CAPTURAS_DIR, CLASES_VALIDAS, VERSION_DATASET
from metadata.dominio import RegistroMetadata, ruta_relativa
from metadata.repositorio import RepositorioMetadata


EXTENSION = ".jpg"
CALIDAD_JPEG = 95
FUENTE = "captura_controlada"


class ServicioCaptura:
    def __init__(
        self,
        repo: RepositorioMetadata,
        metadata_path: Path,
        camara: str = "webcam_0",
    ):
        self._repo = repo
        self._metadata_path = Path(metadata_path)
        self._camara = camara
        self._sesion = datetime.now().strftime("sesion_%Y%m%d_%H%M%S_%f")

    def _siguiente_numero(self, clase: str) -> int:
        carpeta = CAPTURAS_DIR / clase
        carpeta.mkdir(parents=True, exist_ok=True)
        prefijo = f"{clase}_cap_"
        numeros = []
        for f in carpeta.iterdir():
            if (
                f.is_file()
                and f.suffix.lower() == EXTENSION
                and f.stem.startswith(prefijo)
            ):
                resto = f.stem[len(prefijo):]
                if resto.isdigit():
                    numeros.append(int(resto))
        return max(numeros) + 1 if numeros else 1

    def _persistir_frame(self, frame, clase: str) -> Path | None:
        carpeta = CAPTURAS_DIR / clase
        carpeta.mkdir(parents=True, exist_ok=True)

        numero = self._siguiente_numero(clase)
        nombre = f"{clase}_cap_{numero:05d}{EXTENSION}"
        destino = carpeta / nombre

        ok = cv2.imwrite(
            str(destino), frame,
            [cv2.IMWRITE_JPEG_QUALITY, CALIDAD_JPEG],
        )
        if not ok:
            print(f"[ERROR] No se pudo guardar {destino}")
            return None
        return destino

    def _registrar_metadata(self, destino: Path, frame, clase: str) -> None:
        alto, ancho = frame.shape[:2]
        reg = RegistroMetadata(
            archivo=destino.name,
            clase=clase,
            ruta=ruta_relativa(destino, BASE_DIR),
            fuente=FUENTE,
            camara=self._camara,
            sesion=self._sesion,
            version_dataset=VERSION_DATASET,
            ancho=ancho,
            alto=alto,
            formato="JPEG",
            tamano_bytes=destino.stat().st_size,
            hash=sha256_archivo(destino),
            valido=True,
            motivo="OK",
        )
        self._repo.agregar(reg, self._metadata_path)

    def guardar(self, frame, clase: str) -> Path | None:
        if clase not in CLASES_VALIDAS:
            print(f"[ERROR] Clase invalida: {clase}")
            return None

        destino = self._persistir_frame(frame, clase)
        if destino is None:
            return None

        self._registrar_metadata(destino, frame, clase)
        return destino

    def contar_por_clase(self) -> dict[str, int]:
        conteo: dict[str, int] = {}
        for clase in CLASES_VALIDAS:
            carpeta = CAPTURAS_DIR / clase
            if not carpeta.exists():
                conteo[clase] = 0
                continue
            prefijo = f"{clase}_cap_"
            conteo[clase] = sum(
                1 for f in carpeta.iterdir()
                if f.is_file()
                and f.suffix.lower() == EXTENSION
                and f.stem.startswith(prefijo)
            )
        return conteo

    @property
    def sesion(self) -> str:
        return self._sesion