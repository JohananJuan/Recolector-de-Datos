QSS = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}
QTabWidget::pane {
    border: 1px solid #313244;
    border-radius: 8px;
    background: #181825;
}
QTabBar::tab {
    background: #313244;
    color: #cdd6f4;
    padding: 10px 22px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    min-width: 100px;
}
QTabBar::tab:selected {
    background: #89b4fa;
    color: #1e1e2e;
    font-weight: bold;
}
QTabBar::tab:hover:!selected { background: #45475a; }

QPushButton {
    background-color: #89b4fa;
    color: #1e1e2e;
    border: none;
    border-radius: 6px;
    padding: 9px 16px;
    font-weight: bold;
    min-height: 20px;
}
QPushButton:hover  { background-color: #b4befe; }
QPushButton:pressed{ background-color: #74c7ec; }
QPushButton:disabled {
    background-color: #45475a;
    color: #6c7086;
}
QPushButton#peligro  { background-color: #f38ba8; color: #1e1e2e; }
QPushButton#exito    { background-color: #a6e3a1; color: #1e1e2e; }

QLineEdit, QComboBox, QSpinBox {
    background: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 7px 10px;
    color: #cdd6f4;
    min-height: 20px;
}
QLineEdit:focus, QComboBox:focus { border: 1px solid #89b4fa; }

QPlainTextEdit, QTextEdit {
    background: #11111b;
    border: 1px solid #313244;
    border-radius: 6px;
    padding: 8px;
    color: #a6e3a1;
    font-family: 'Consolas', monospace;
    font-size: 12px;
}

QGroupBox {
    border: 1px solid #313244;
    border-radius: 8px;
    margin-top: 16px;
    padding: 14px 10px 10px 10px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #89b4fa;
}

QLabel#titulo {
    font-size: 22px;
    font-weight: bold;
    color: #89b4fa;
}
QLabel#subtitulo {
    font-size: 12px;
    color: #a6adc8;
}
QLabel#valor {
    font-size: 26px;
    font-weight: bold;
    color: #a6e3a1;
}
QLabel#clase_actual {
    font-size: 18px;
    font-weight: bold;
    color: #f9e2af;
}

QScrollArea { border: none; background: transparent; }

QScrollBar:vertical {
    background: #181825;
    width: 10px;
    border-radius: 5px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #45475a;
    border-radius: 5px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover { background: #89b4fa; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal {
    background: #181825;
    height: 10px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal {
    background: #45475a;
    border-radius: 5px;
    min-width: 24px;
}
QScrollBar::handle:horizontal:hover { background: #89b4fa; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
"""