import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime
import cv2

from core.rutas import CAPTURAS_DIR, BASE_DIR, CLASES_VALIDAS, VERSION_DATASET
from core.hashing import sha256_archivo
from metadata.repositorio import RepositorioMetadata
from metadata.dominio import RegistroMetadata, ruta_relativa


EXTENSION = ".jpg"
CALIDAD_JPEG = 95
FUENTE = "captura_controlada"


class ServicioCaptura:
    def __init__(self, repo: RepositorioMetadata, metadata_path: Path,
                 camara: str = "webcam_0"):
        self._repo = repo
        self._metadata_path = Path(metadata_path)
        self._camara = camara
        # microsegundos para evitar colisión si reabres en el mismo segundo
        self._sesion = datetime.now().strftime("sesion_%Y%m%d_%H%M%S_%f")

    def _siguiente_numero(self, clase: str) -> int:
        carpeta = CAPTURAS_DIR / clase
        carpeta.mkdir(parents=True, exist_ok=True)
        prefijo = f"{clase}_cap_"
        numeros = []
        for f in carpeta.iterdir():
            if f.is_file() and f.suffix.lower() == EXTENSION and f.stem.startswith(prefijo):
                resto = f.stem[len(prefijo):]
                if resto.isdigit():
                    numeros.append(int(resto))
        return max(numeros) + 1 if numeros else 1

    def guardar(self, frame, clase: str) -> Path | None:
        if clase not in CLASES_VALIDAS:
            print(f"[ERROR] Clase invalida: {clase}")
            return None

        carpeta = CAPTURAS_DIR / clase
        carpeta.mkdir(parents=True, exist_ok=True)

        numero = self._siguiente_numero(clase)
        nombre = f"{clase}_cap_{numero:05d}{EXTENSION}"
        destino = carpeta / nombre

        ok = cv2.imwrite(str(destino), frame, [cv2.IMWRITE_JPEG_QUALITY, CALIDAD_JPEG])
        if not ok:
            print(f"[ERROR] No se pudo guardar {destino}")
            return None

        alto, ancho = frame.shape[:2]
        reg = RegistroMetadata(
            archivo=nombre,
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
        return destino

    def contar_por_clase(self) -> dict[str, int]:
        conteo = {}
        for clase in CLASES_VALIDAS:
            carpeta = CAPTURAS_DIR / clase
            if not carpeta.exists():
                conteo[clase] = 0
                continue
            prefijo = f"{clase}_cap_"
            conteo[clase] = sum(
                1 for f in carpeta.iterdir()
                if f.is_file() and f.suffix.lower() == EXTENSION
                and f.stem.startswith(prefijo)
            )
        return conteo
    
    @property
    def sesion(self) -> str:
        return self._sesion