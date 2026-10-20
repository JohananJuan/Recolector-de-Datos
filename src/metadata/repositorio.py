from pathlib import Path
from typing import Protocol, runtime_checkable, Iterable
import csv

from .esquema import CAMPOS
from .dominio import RegistroMetadata


@runtime_checkable
class LectorMetadata(Protocol):
    """ISP: consumidores que solo leen no dependen de la escritura."""
    def leer(self, origen: Path) -> list[RegistroMetadata]: ...
    def listar_por_clase(self, origen: Path, clase: str) -> list[RegistroMetadata]: ...
    def existe_hash(self, origen: Path, sha: str) -> RegistroMetadata | None: ...


@runtime_checkable
class EscritorMetadata(Protocol):
    def escribir(self, registros: Iterable[RegistroMetadata], destino: Path) -> Path: ...
    def agregar(self, registro: RegistroMetadata, destino: Path) -> Path: ...


@runtime_checkable
class RepositorioMetadata(LectorMetadata, EscritorMetadata, Protocol):
    """Contrato completo del patrón Repositorio."""
    ...


class RepositorioCSV:
    """Implementación concreta sobre CSV. Cumple RepositorioMetadata."""

    def leer(self, origen: Path) -> list[RegistroMetadata]:
        origen = Path(origen)
        if not origen.exists():
            return []
        with open(origen, newline="", encoding="utf-8") as f:
            filas = list(csv.DictReader(f))
        return [RegistroMetadata.desde_dict(fila) for fila in filas]

    def escribir(self, registros: Iterable[RegistroMetadata], destino: Path) -> Path:
        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        with open(destino, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CAMPOS, extrasaction="ignore")
            w.writeheader()
            for r in registros:
                w.writerow(r.a_dict())
        return destino

    def agregar(self, registro: RegistroMetadata, destino: Path) -> Path:
        registros = self.leer(destino)
        registros.append(registro)
        return self.escribir(registros, destino)

    def listar_por_clase(self, origen: Path, clase: str) -> list[RegistroMetadata]:
        return [r for r in self.leer(origen) if r.clase == clase]

    def existe_hash(self, origen: Path, sha: str) -> RegistroMetadata | None:
        if not sha:
            return None
        for r in self.leer(origen):
            if r.hash == sha and r.es_valido():
                return r
        return None


def nuevo_repositorio() -> RepositorioMetadata:
    return RepositorioCSV()