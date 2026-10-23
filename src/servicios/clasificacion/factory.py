from pathlib import Path

from core.rutas import BASE_DIR
from .interfaz import Clasificador
from .nulo import ClasificadorNulo


MODELO_DIR = BASE_DIR / "models"
ETIQUETAS = ("carton", "papel", "tela")


def crear_clasificador(preferido: str = "yolo") -> Clasificador:
    if preferido == "yolo":
        ruta = MODELO_DIR / "clasificador.pt"
        if ruta.exists():
            try:
                from .yolo import ClasificadorYOLO
                return ClasificadorYOLO(ruta, ETIQUETAS)
            except Exception as e:
                print(f"[clasificador] YOLO no disponible: {e}")

    if preferido == "mobilenet":
        ruta = MODELO_DIR / "mobilenet_v3.pth"
        if ruta.exists():
            try:
                from .mobilenet import ClasificadorMobileNet
                return ClasificadorMobileNet(ruta, ETIQUETAS)
            except Exception as e:
                print(f"[clasificador] MobileNet no disponible: {e}")

    return ClasificadorNulo()