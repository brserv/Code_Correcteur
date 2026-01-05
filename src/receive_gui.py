"""Reception window for the TP."""
from PySide6.QtWidgets import (QWidget, QLabel, QLineEdit, QTextEdit, QVBoxLayout)
from PySide6.QtCore import Slot


class ReceiveWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Réception - TP RS232')
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel('Trame reçue (payload brut hex):'))
        self.received_view = QLineEdit()
        self.received_view.setReadOnly(True)
        layout.addWidget(self.received_view)

        layout.addWidget(QLabel('Message décodé / statut:'))
        self.decoded_view = QTextEdit()
        self.decoded_view.setReadOnly(True)
        layout.addWidget(self.decoded_view)

        self.setLayout(layout)

    @Slot(bytes, str)
    def on_data_received(self, received_payload, decoded_info):
        from src.utils import to_hex
        self.received_view.setText(to_hex(received_payload))
        self.decoded_view.setPlainText(decoded_info)