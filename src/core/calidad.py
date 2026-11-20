from __future__ import annotations
import cv2
import numpy as np


def estimar_ruido(gray: np.ndarray) -> float:
    return float(np.std(cv2.Laplacian(gray, cv2.CV_64F)))


def brillo_medio(gray: np.ndarray) -> float:
    return float(np.mean(gray))


def contraste_rms(gray: np.ndarray) -> float:
    return float(np.std(gray))


def varianza_laplaciano(gray: np.ndarray) -> float:
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())