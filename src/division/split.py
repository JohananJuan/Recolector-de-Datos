from collections import defaultdict
import random


def _es_valido(r: dict) -> bool:
    v = r.get("valido", "")
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("true", "1", "yes", "si", "sí")


def split_por_grupo(registros: list[dict], campo_grupo: str = "sesion",
                    ratios: tuple[float, float, float] = (0.7, 0.15, 0.15),
                    semilla: int = 42) -> dict[str, list[dict]]:
    """
    Agrupa por `campo_grupo` y asigna grupos completos a train/val/test.
    Si un registro no tiene grupo, cae a un grupo sintético por clase
    para evitar que todo termine en `test` (caso típico: dataset público
    sin `sesion`).
    """
    grupos: dict[str, list[dict]] = defaultdict(list)

    for r in registros:
        if not _es_valido(r):
            continue
        g = (r.get(campo_grupo) or "").strip()
        if not g:
            g = f"__clase_{r.get('clase', 'desconocida')}__"
        grupos[g].append(r)

    claves = list(grupos.keys())
    random.Random(semilla).shuffle(claves)

    n = len(claves)
    if n == 0:
        return {"train": [], "val": [], "test": []}

    n_train = int(n * ratios[0])
    n_val = int(n * ratios[1])

    # Garantizar al menos 1 grupo por split si hay suficientes
    if n >= 3:
        n_train = max(n_train, 1)
        n_val = max(n_val, 1)
        if n_train + n_val >= n:
            n_train = n - 2
            n_val = 1

    train, val, test = [], [], []
    for i, g in enumerate(claves):
        if i < n_train:
            train.extend(grupos[g])
        elif i < n_train + n_val:
            val.extend(grupos[g])
        else:
            test.extend(grupos[g])

    return {"train": train, "val": val, "test": test}