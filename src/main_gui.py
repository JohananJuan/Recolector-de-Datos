import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PyQt5.QtWidgets import QApplication
from ui.estilos import QSS
from ui.ventana_principal import VentanaPrincipal


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    win = VentanaPrincipal()
    win.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())