import numpy as np

from .interfaz import Clasificador, Prediccion


class ClasificadorYOLO(Clasificador):
    """Usa Ultralytics YOLOv8-cls. Acepta el modelo .pt estándar.

    pip install ultralytics
    """

    def __init__(self, ruta_modelo, etiquetas: tuple[str, ...], tamano_entrada: int = 224):
        from ultralytics import YOLO
        self._modelo = YOLO(str(ruta_modelo))
        self._etiquetas = etiquetas
        self._tamano = tamano_entrada

    def predecir(self, frame_bgr) -> Prediccion | None:
        resultados = self._modelo.predict(
            source=frame_bgr,
            imgsz=self._tamano,
            verbose=False,
            device="cpu",
        )
        if not resultados:
            return None
        probs = resultados[0].probs
        if probs is None:
            return None
        valores = probs.data.cpu().numpy()
        idx = int(np.argmax(valores))
        scores = {c: float(v) for c, v in zip(self._etiquetas, valores)}
        return Prediccion(
            clase=self._etiquetas[idx],
            confianza=float(valores[idx]),
            scores=scores,
        )

    @property
    def clases(self) -> tuple[str, ...]:
        return self._etiquetas