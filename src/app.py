"""Application entrypoint: launches PySide6 GUI."""
import sys
from PySide6.QtWidgets import QApplication
from src.transmit_gui import TransmitWindow
from src.receive_gui import ReceiveWindow


def main():
    app = QApplication(sys.argv)
    transmit_win = TransmitWindow()
    receive_win = ReceiveWindow()
    transmit_win.data_sent.connect(receive_win.on_data_received)
    transmit_win.show()
    receive_win.show()
    sys.exit(app.exec())
