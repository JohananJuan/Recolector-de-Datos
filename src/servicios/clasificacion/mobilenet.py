import numpy as np
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image

from .interfaz import Clasificador, Prediccion


class ClasificadorMobileNet(Clasificador):
    """MobileNetV3 con pesos fine-tuneados a 3 clases.

    pip install torch torchvision
    """

    def __init__(self, ruta_pesos, etiquetas: tuple[str, ...]):
        self._etiquetas = etiquetas
        self._device = torch.device("cpu")

        modelo = models.mobilenet_v3_small(weights=None)
        modelo.classifier[-1] = nn.Linear(modelo.classifier[-1].in_features, len(etiquetas))
        estado = torch.load(str(ruta_pesos), map_location=self._device)
        modelo.load_state_dict(estado)
        modelo.eval()
        self._modelo = modelo.to(self._device)

        self._prep = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225]),
        ])

    def predecir(self, frame_bgr) -> Prediccion | None:
        img = Image.fromarray(frame_bgr[:, :, ::-1])
        tensor = self._prep(img).unsqueeze(0).to(self._device)
        with torch.no_grad():
            logits = self._modelo(tensor)
            probs = torch.softmax(logits, dim=1)[0].cpu().numpy()
        idx = int(np.argmax(probs))
        scores = {c: float(p) for c, p in zip(self._etiquetas, probs)}
        return Prediccion(clase=self._etiquetas[idx],
                          confianza=float(probs[idx]),
                          scores=scores)

    @property
    def clases(self) -> tuple[str, ...]:
        return self._etiquetas