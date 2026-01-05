"""Application entrypoint: launches PySide6 GUI."""
import sys
from PySide6.QtWidgets import QApplication
from src.gui import MainWindow


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
