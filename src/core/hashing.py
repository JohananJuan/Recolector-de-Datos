import hashlib
from pathlib import Path
from PIL import Image

try:
    import imagehash
    _TIENE_IMAGEHASH = True
except ImportError:
    _TIENE_IMAGEHASH = False


def sha256_archivo(archivo: Path) -> str:
    h = hashlib.sha256()
    with open(archivo, "rb") as f:
        for bloque in iter(lambda: f.read(8192), b""):
            h.update(bloque)
    return h.hexdigest()


def phash_imagen(archivo: Path, hash_size: int = 8):
    if not _TIENE_IMAGEHASH:
        return None
    try:
        with Image.open(archivo) as img:
            return imagehash.phash(img, hash_size=hash_size)
    except Exception:
        return None


def distancia_hamming(h1, h2) -> int:
    if h1 is None or h2 is None:
        return 999
    return h1 - h2