"""Reception window for the TP."""
from PySide6.QtWidgets import (QWidget, QLabel, QLineEdit, QTextEdit, QVBoxLayout, QGroupBox)
from PySide6.QtCore import Slot


class ReceiveWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Réception - TP RS232')
        self.setMinimumWidth(700)
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout()
        
        # === Trame reçue ===
        received_group = QGroupBox("Trame reçue (avant décodage)")
        received_layout = QVBoxLayout()
        
        received_layout.addWidget(QLabel('Données brutes (hexadécimal):'))
        self.received_view = QLineEdit()
        self.received_view.setReadOnly(True)
        self.received_view.setStyleSheet("background-color: #1e1e1e; font-family: 'Courier New'; color: #e6e6e6;")
        received_layout.addWidget(self.received_view)
        
        received_group.setLayout(received_layout)
        main_layout.addWidget(received_group)
        
        # === Message décodé ===
        decoded_group = QGroupBox("Message décodé et corrigé")
        decoded_layout = QVBoxLayout()
        
        self.decoded_view = QTextEdit()
        self.decoded_view.setReadOnly(True)
        self.decoded_view.setMinimumHeight(150)
        self.decoded_view.setStyleSheet("background-color: #1e1e1e; font-family: 'Courier New'; color: #e6e6e6;")
        decoded_layout.addWidget(self.decoded_view)
        
        decoded_group.setLayout(decoded_layout)
        main_layout.addWidget(decoded_group)
        
        main_layout.addStretch()
        self.setLayout(main_layout)

    @Slot(bytes, str)
    def on_data_received(self, received_payload, decoded_info):
        from src.utils import to_hex
        self.received_view.setText(to_hex(received_payload))
        self.decoded_view.setPlainText(decoded_info)