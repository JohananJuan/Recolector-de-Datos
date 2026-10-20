from datetime import datetime

CAMPOS = [
    "archivo", "clase", "ruta", "fuente",
    "fecha_captura", "hora_captura",
    "camara", "sesion", "version_dataset",
    "ancho", "alto", "formato", "tamano_bytes",
    "hash", "phash", "valido", "motivo",
]

FUENTES_VALIDAS = {"dataset_publico", "captura_controlada", "prototipo"}


def ahora() -> tuple[str, str]:
    m = datetime.now()
    return m.strftime("%Y-%m-%d"), m.strftime("%H:%M:%S")


def crear_registro(**kw) -> dict:
    if kw.get("fuente") not in FUENTES_VALIDAS:
        raise ValueError(f"Fuente invalida: {kw.get('fuente')}")
    f, h = ahora()
    return {
        "archivo": kw.get("archivo", ""),
        "clase": kw.get("clase", ""),
        "ruta": kw.get("ruta", ""),
        "fuente": kw.get("fuente", ""),
        "fecha_captura": kw.get("fecha_captura") or f,
        "hora_captura": kw.get("hora_captura") or h,
        "camara": kw.get("camara", ""),
        "sesion": kw.get("sesion", ""),
        "version_dataset": kw.get("version_dataset", "1.0.0"),
        "ancho": kw.get("ancho", ""),
        "alto": kw.get("alto", ""),
        "formato": kw.get("formato", ""),
        "tamano_bytes": kw.get("tamano_bytes", ""),
        "hash": kw.get("hash", ""),
        "phash": kw.get("phash", ""),
        "valido": kw.get("valido", True),
        "motivo": kw.get("motivo", "OK"),
    }