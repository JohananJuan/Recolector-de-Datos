from datetime import datetime

CAMPOS = [
    "archivo", "clase", "ruta", "fuente",
    "fecha_captura", "hora_captura",
    "camara", "sesion", "version_dataset",
    "ancho", "alto", "formato", "tamano_bytes",
    "hash", "phash", "valido", "motivo",
    "licencia", "origen", "consentimiento", "anonimizado",
    "sensor", "puerto", "resolucion", "modo_captura",
]

FUENTES_VALIDAS = {"dataset_publico", "captura_controlada", "prototipo"}


def ahora() -> tuple[str, str]:
    m = datetime.now()
    return m.strftime("%Y-%m-%d"), m.strftime("%H:%M:%S")