from __future__ import annotations

import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)


class TablaDatos(QTableWidget):

    COLOR_ENTEROS = QColor("#a6e3a1")   # verde
    COLOR_FLOTANTES = QColor("#89b4fa") # azul
    COLOR_TEXTO = QColor("#cdd6f4")     # texto base
    COLOR_NULO = QColor("#6c7086")      # gris para NaN

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self.horizontalHeader().setStretchLastSection(True)
        self.setWordWrap(False)

    def cargar(self, df: pd.DataFrame | None, max_filas: int = 500) -> None:
        self.clear()
        if df is None or df.empty:
            self.setRowCount(0)
            self.setColumnCount(0)
            return

        recorte = df.head(max_filas)
        self.setRowCount(len(recorte))
        self.setColumnCount(len(recorte.columns))
        self.setHorizontalHeaderLabels([str(c) for c in recorte.columns])

        for i, (_, fila) in enumerate(recorte.iterrows()):
            for j, valor in enumerate(fila):
                item = self._crear_item(valor)
                self.setItem(i, j, item)

    def _crear_item(self, valor) -> QTableWidgetItem:
        item = QTableWidgetItem(self._formatear(valor))

        if isinstance(valor, (int, float)) and not isinstance(valor, bool):
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        else:
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        if pd.isna(valor):
            item.setForeground(self.COLOR_NULO)
        elif isinstance(valor, bool):
            item.setForeground(self.COLOR_TEXTO)
        elif isinstance(valor, int):
            item.setForeground(self.COLOR_ENTEROS)
        elif isinstance(valor, float):
            item.setForeground(self.COLOR_FLOTANTES)
        else:
            item.setForeground(self.COLOR_TEXTO)

        return item

    @staticmethod
    def _formatear(valor) -> str:
        if pd.isna(valor):
            return "—"
        if isinstance(valor, bool):
            return "sí" if valor else "no"
        if isinstance(valor, float):
            if abs(valor) >= 1e4 or (0 < abs(valor) < 1e-3):
                return f"{valor:.3e}"
            return f"{valor:.4f}"
        return str(valor)