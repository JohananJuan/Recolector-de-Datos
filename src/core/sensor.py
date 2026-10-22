from __future__ import annotations

import re
import threading
import time
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from typing import Optional

try:
    import serial  # pyserial
    from serial.tools import list_ports
except ImportError:
    serial = None
    list_ports = None


@dataclass(frozen=True)
class LecturaSensor:
    distancia_cm: Optional[float]
    estado: str
    timestamp: float

    @property
    def valida(self) -> bool:
        return self.distancia_cm is not None


class FuenteDistancia(ABC):

    @abstractmethod
    def iniciar(self) -> bool:
        """Arranca la fuente. Devuelve True si quedó lista."""

    @abstractmethod
    def detener(self) -> None:
        """Libera recursos."""

    @abstractmethod
    def ultima_lectura(self) -> Optional[LecturaSensor]:
        """Devuelve la última lectura disponible (thread-safe)."""

    @abstractmethod
    def esta_activa(self) -> bool:
        """True si la fuente está entregando datos."""


_RE_DIST = re.compile(r"Distancia:\s*(SIN LECTURA|[\d.]+)")
_RE_ESTADO = re.compile(r"ESTADO:\s*([A-Z! ]+)")


class LectorArduinoSerial(FuenteDistancia):

    def __init__(self, puerto: str, baudios: int = 115200,
                 ventana_media: int = 3, verbose: bool = True):
        self._puerto = puerto
        self._baudios = baudios
        self._ventana_media = max(1, ventana_media)
        self._verbose = verbose
        self._hilo: Optional[threading.Thread] = None
        self._parar = threading.Event()
        self._ultima: Optional[LecturaSensor] = None
        self._lock = threading.Lock()
        self._activa = False
        self._ventana: deque[float] = deque(maxlen=self._ventana_media)

    def _log(self, msg: str) -> None:
        if self._verbose:
            print(f"[SENSOR] {msg}")

    def iniciar(self) -> bool:
        self._log(f"iniciar() → puerto={self._puerto} baudios={self._baudios}")
        if serial is None:
            self._log("pyserial NO instalado (pip install pyserial)")
            return False
        self._parar.clear()
        self._ventana.clear()
        self._hilo = threading.Thread(
            target=self._loop, daemon=True, name="lector-arduino"
        )
        self._hilo.start()
        self._log("Esperando 2.5s a que la ESP32 termine de resetear...")
        time.sleep(2.5)
        self._log(f"Estado tras espera: _activa={self._activa}")
        return self._activa

    def detener(self) -> None:
        self._log("detener() → señalizando hilo...")
        self._parar.set()
        if self._hilo:
            self._hilo.join(timeout=3)
            self._log(f"detener() → hilo vivo={self._hilo.is_alive()}")
        self._activa = False
        self._hilo = None

    def ultima_lectura(self) -> Optional[LecturaSensor]:
        with self._lock:
            return self._ultima

    def esta_activa(self) -> bool:
        return self._activa

    def _loop(self) -> None:
        self._log(f"_loop() arrancando; abriendo {self._puerto}...")

        try:
            ser = serial.Serial(self._puerto, self._baudios, timeout=0.5)
        except serial.SerialException as e:
            self._log(f"SerialException al abrir: {e}")
            self._log("   (¿monitor serie del IDE abierto? ¿driver? ¿otro programa?)")
            return
        except Exception as e:
            self._log(f"Error inesperado al abrir: {e!r}")
            return

        try:
            is_open = getattr(ser, "is_open", True)
            self._log(f"Puerto abierto: is_open={is_open} puerto={ser.port}")
        except Exception:
            self._log(f"Puerto abierto en {self._puerto}")

        try:
            self._log("Esperando 2s a que la ESP32 termine de resetear...")
            time.sleep(2)
            try:
                ser.reset_input_buffer()
            except Exception as e:
                self._log(f"Aviso: reset_input_buffer falló: {e}")

            self._activa = True
            self._log("_activa=True, leyendo líneas...")

            n = 0
            while not self._parar.is_set():
                try:
                    raw = ser.readline()
                except Exception as e:
                    self._log(f"Error en readline: {e!r}")
                    break
                if not raw:
                    continue
                n += 1
                linea = raw.decode(errors="replace").strip()
                if not linea:
                    continue
                if n <= 5 or "Distancia" in linea:
                    self._log(f"RAW[{n:05d}] {linea!r}")
                self._procesar_linea(linea)
            self._log(f"_loop() terminando tras {n} líneas")
        finally:
            try:
                ser.close()
                self._log("Puerto cerrado")
            except Exception:
                pass
            self._activa = False

    def _procesar_linea(self, linea: str) -> None:
        m_dist = _RE_DIST.search(linea)
        m_estado = _RE_ESTADO.search(linea)
        if not m_dist and not m_estado:
            return

        distancia: Optional[float] = None
        if m_dist:
            raw = m_dist.group(1)
            if raw != "SIN LECTURA":
                try:
                    distancia = float(raw)
                except ValueError:
                    distancia = None

        if distancia is not None:
            self._ventana.append(distancia)
            distancia = sum(self._ventana) / len(self._ventana)

        estado = m_estado.group(1).strip() if m_estado else "SIN LECTURA"
        with self._lock:
            self._ultima = LecturaSensor(distancia, estado, time.time())


class FuenteNula(FuenteDistancia):

    def iniciar(self) -> bool:
        return True

    def detener(self) -> None:
        pass

    def ultima_lectura(self) -> Optional[LecturaSensor]:
        return None

    def esta_activa(self) -> bool:
        return False


def listar_puertos_seriales() -> list[str]:
    if list_ports is None:
        return []
    return [p.device for p in list_ports.comports()]


def autodetectar_puerto() -> Optional[str]:
    if list_ports is None:
        return None

    def es_bluetooth(p) -> bool:
        desc = (p.description or "").lower()
        hwid = (p.hwid or "").lower()
        return "bluetooth" in desc or "bth" in hwid or "bthenum" in hwid

    def es_usb_real(p) -> bool:
        desc = (p.description or "").lower()
        hwid = (p.hwid or "").lower()
        return any(k in desc or k in hwid for k in (
            "cp210", "ch340", "ch341", "ftdi", "usb serial", "usb-serial",
            "silicon labs", "uart", "acm",
        ))

    candidatos = [p for p in list_ports.comports() if not es_bluetooth(p)]
    if not candidatos:
        print("[SENSOR] autodetectar_puerto → no hay candidatos (sin Bluetooth)")
        return None

    for p in candidatos:
        if es_usb_real(p):
            print(f"[SENSOR] autodetectar_puerto → {p.device} ({p.description})")
            return p.device

    print(f"[SENSOR] autodetectar_puerto → {candidatos[0].device} (fallback)")
    return candidatos[0].device