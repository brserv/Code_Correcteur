"""Application entrypoint: launches PySide6 GUI."""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor, QPalette
from PySide6.QtCore import Qt
from src.transmit_gui import TransmitWindow
from src.receive_gui import ReceiveWindow


def apply_dark_theme(app: QApplication) -> None:
    """Force a dark theme so UI looks consistent across machines."""
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(18, 18, 18))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(30, 30, 30))
    palette.setColor(QPalette.AlternateBase, QColor(45, 45, 45))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(35, 35, 35))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)


def main():
    app = QApplication(sys.argv)
    apply_dark_theme(app)
    transmit_win = TransmitWindow()
    receive_win = ReceiveWindow()
    transmit_win.data_sent.connect(receive_win.on_data_received)
    transmit_win.show()
    receive_win.show()
    sys.exit(app.exec())
