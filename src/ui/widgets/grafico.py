from __future__ import annotations

from typing import Mapping

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QSizePolicy, QVBoxLayout, QWidget


class GraficoBarras(QWidget):
    FONDO = "#181825"
    EJE = "#45475a"
    TEXTO = "#cdd6f4"
    BARRA = "#89b4fa"

    def __init__(self):
        super().__init__()
        self._figura = Figure(figsize=(5, 2.6), dpi=100, facecolor=self.FONDO)
        self._canvas = FigureCanvasQTAgg(self._figura)
        self._canvas.setStyleSheet(f"background:{self.FONDO};")
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._canvas)

    def mostrar(self, conteos: Mapping[str, int], titulo: str) -> None:
        self._figura.clear()
        ax = self._figura.add_subplot(111)
        ax.set_facecolor(self.FONDO)

        etiquetas = list(conteos.keys())
        valores = list(conteos.values())
        barras = ax.bar(etiquetas, valores, color=self.BARRA)

        ax.set_title(titulo, color=self.TEXTO, fontsize=11, pad=8)
        ax.tick_params(colors=self.TEXTO, labelsize=9)
        for spine in ax.spines.values():
            spine.set_color(self.EJE)
        ax.grid(axis="y", color=self.EJE, linestyle="--", alpha=0.4)
        ax.set_axisbelow(True)

        for barra, valor in zip(barras, valores):
            ax.text(
                barra.get_x() + barra.get_width() / 2,
                barra.get_height(),
                str(valor),
                ha="center",
                va="bottom",
                color=self.TEXTO,
                fontsize=9,
            )

        self._figura.tight_layout()
        self._canvas.draw_idle()