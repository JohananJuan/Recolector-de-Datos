from .interfaz import Clasificador, Prediccion


class ClasificadorNulo(Clasificador):
    def predecir(self, frame_bgr) -> Prediccion | None:
        return None

    @property
    def clases(self) -> tuple[str, ...]:
        return ("carton", "papel", "tela")