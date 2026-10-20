from pathlib import Path
from dataclasses import dataclass
from PIL import Image

EXTENSIONES_VALIDAS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


@dataclass
class InfoImagen:
    valida: bool
    motivo: str
    ancho: int | None = None
    alto: int | None = None
    formato: str | None = None
    modo: str | None = None


def inspeccionar_imagen(archivo: Path) -> InfoImagen:
    try:
        with Image.open(archivo) as img:
            img.verify()
        with Image.open(archivo) as img:
            ancho, alto = img.size
            formato = img.format
            modo = img.mode
        if ancho <= 0 or alto <= 0:
            return InfoImagen(False, "Dimensiones invalidas")
        return InfoImagen(True, "OK", ancho, alto, formato, modo)
    except Exception as e:
        return InfoImagen(False, f"Corrupta: {e}")