import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import shutil
from PIL import Image

from core.rutas import ARCHIVE_DIR, PROCESSED_DIR, BASE_DIR, VERSION_DATASET
from core.imagen import EXTENSIONES_VALIDAS
from core.hashing import sha256_archivo
from metadata.repositorio import RepositorioMetadata
from metadata.dominio import RegistroMetadata, ruta_relativa


CLASES_ORIGEN = {
    "1-Cardboard": "carton",
    "6-Paper": "papel",
    "8-Textile Trash": "tela",
}

FUENTE = "dataset_publico"


class ServicioRecoleccion:
    def __init__(self, repo: RepositorioMetadata, metadata_path: Path):
        self._repo = repo
        self._metadata_path = Path(metadata_path)

    def recolectar(self) -> dict:
        if not ARCHIVE_DIR.exists():
            raise FileNotFoundError(f"No existe: {ARCHIVE_DIR}")

        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        registros: list[RegistroMetadata] = []
        resumen: dict[str, int] = {}

        for carpeta_original, clase in CLASES_ORIGEN.items():
            origen = ARCHIVE_DIR / carpeta_original
            destino_dir = PROCESSED_DIR / clase
            if not origen.exists():
                print(f"[ADVERTENCIA] No existe: {origen}")
                continue
            destino_dir.mkdir(parents=True, exist_ok=True)

            archivos = sorted(
                f for f in origen.iterdir()
                if f.is_file() and f.suffix.lower() in EXTENSIONES_VALIDAS
            )
            print(f"\nClase: {clase}  |  encontradas: {len(archivos)}")

            for numero, archivo in enumerate(archivos, start=1):
                nuevo_nombre = f"{clase}_{numero:05d}{archivo.suffix.lower()}"
                destino = destino_dir / nuevo_nombre
                shutil.copy2(archivo, destino)

                try:
                    with Image.open(destino) as img:
                        ancho, alto = img.size
                        formato = img.format
                except Exception:
                    ancho = alto = ""
                    formato = ""

                reg = RegistroMetadata(
                    archivo=nuevo_nombre,
                    clase=clase,
                    ruta=ruta_relativa(destino, BASE_DIR),
                    fuente=FUENTE,
                    version_dataset=VERSION_DATASET,
                    ancho=ancho,
                    alto=alto,
                    formato=formato or "",
                    tamano_bytes=destino.stat().st_size,
                    hash=sha256_archivo(destino),
                    valido=True,
                    motivo="OK",
                )
                registros.append(reg)

            resumen[clase] = len(archivos)

        self._repo.escribir(registros, self._metadata_path)
        total = sum(resumen.values())
        print(f"\nTOTAL RECOLECTADO: {total}")
        print(f"Metadata en: {self._metadata_path}")
        return resumen