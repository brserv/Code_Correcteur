"""PySide6 GUI for the transmission TP.

Provides a main window with tabs for transmission and reception.
"""
from PySide6.QtWidgets import (QMainWindow, QWidget, QLabel, QPushButton, QComboBox,
                               QLineEdit, QTextEdit, QCheckBox, QSpinBox, QGridLayout,
                               QHBoxLayout, QVBoxLayout, QTabWidget)
from PySide6.QtCore import QTimer
from src.serial_comm import list_serial_ports, build_frame, SerialLink
from src.codec import ChannelCodec
from src.utils import to_hex, inject_exact_bits, to_bin, to_text
import traceback


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('TP Transmission fiabilisée - RS232 loopback')
        self.codec = ChannelCodec(t=4, enabled=True)
        self.link: SerialLink | None = None
        self._build_ui()
        self._refresh_ports()
        self.port_timer = QTimer(self)
        self.port_timer.timeout.connect(self._refresh_ports)
        self.port_timer.start(2000)

    def _build_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Transmission tab
        transmit_widget = QWidget()
        self._build_transmit_ui(transmit_widget)
        self.tabs.addTab(transmit_widget, "Transmission")

        # Reception tab
        receive_widget = QWidget()
        self._build_receive_ui(receive_widget)
        self.tabs.addTab(receive_widget, "Réception")

    def _build_transmit_ui(self, widget):
        layout = QGridLayout()

        # Port selection
        layout.addWidget(QLabel('Port:'), 0, 0)
        self.port_combo = QComboBox()
        layout.addWidget(self.port_combo, 0, 1)
        layout.addWidget(QLabel('Baudrate:'), 0, 2)
        self.baud_combo = QComboBox()
        for b in [9600, 19200, 38400, 57600, 115200, 230400]:
            self.baud_combo.addItem(str(b))
        self.baud_combo.setCurrentText('115200')
        layout.addWidget(self.baud_combo, 0, 3)

        # Word input (variable size)
        layout.addWidget(QLabel('Mot (binaire ou hex ou texte, ex: 10101010 ou AA ou hello, taille variable):'), 1, 0, 1, 4)
        self.word_input = QLineEdit('00000000')
        layout.addWidget(self.word_input, 2, 0, 1, 4)

        # Options
        self.chk_disable_coding = QCheckBox('Inhiber codage canal (envoyer brut)')
        layout.addWidget(self.chk_disable_coding, 3, 0, 1, 4)

        # Encode / view
        self.btn_encode = QPushButton('Encoder et afficher mot codé (hex)')
        self.btn_encode.clicked.connect(self.on_encode)
        layout.addWidget(self.btn_encode, 4, 0, 1, 4)
        self.encoded_view = QLineEdit()
        self.encoded_view.setReadOnly(True)
        layout.addWidget(self.encoded_view, 5, 0, 1, 4)

        # Error injection
        layout.addWidget(QLabel('Nombre d\'erreurs à injecter (aléatoire):'), 6, 0, 1, 2)
        self.spin_errors = QSpinBox()
        self.spin_errors.setMinimum(0)
        self.spin_errors.setMaximum(256)  # arbitrary max
        layout.addWidget(self.spin_errors, 6, 2)
        self.btn_inject = QPushButton('Injecter erreurs')
        self.btn_inject.clicked.connect(self.on_inject)
        layout.addWidget(self.btn_inject, 6, 3)

        # Send
        self.btn_send = QPushButton('Envoyer sur RS232 (loopback)')
        self.btn_send.clicked.connect(self.on_send)
        layout.addWidget(self.btn_send, 7, 0, 1, 2)
        self.btn_test = QPushButton('Test liaison (ping TEST)')
        self.btn_test.clicked.connect(self.on_test)
        layout.addWidget(self.btn_test, 7, 2, 1, 2)

        widget.setLayout(layout)

    def _build_receive_ui(self, widget):
        layout = QVBoxLayout()

        layout.addWidget(QLabel('Trame reçue (payload brut hex):'))
        self.received_view = QLineEdit()
        self.received_view.setReadOnly(True)
        layout.addWidget(self.received_view)

        layout.addWidget(QLabel('Message décodé / statut:'))
        self.decoded_view = QTextEdit()  # Changed to QTextEdit for multi-line
        self.decoded_view.setReadOnly(True)
        layout.addWidget(self.decoded_view)

        widget.setLayout(layout)

    def _refresh_ports(self):
        current = self.port_combo.currentText()
        ports = list_serial_ports()
        self.port_combo.clear()
        self.port_combo.addItems(ports)
        if current in ports:
            self.port_combo.setCurrentText(current)

    def _read_word_input(self) -> bytes:
        s = self.word_input.text().strip()
        # accept binary (multiple of 8), hex (even length), or text
        try:
            if all(ch in '01' for ch in s):
                if len(s) % 8 != 0:
                    raise ValueError('Longueur binaire doit être multiple de 8')
                bytes_list = []
                for i in range(0, len(s), 8):
                    byte_str = s[i:i+8]
                    val = int(byte_str, 2)
                    bytes_list.append(val)
                return bytes(bytes_list)
            elif all(c in '0123456789abcdefABCDEF' for c in s):
                if len(s) % 2 != 0:
                    raise ValueError('Longueur hex doit être paire')
                return bytes.fromhex(s)
            else:
                # treat as text, encode to UTF-8
                return s.encode('utf-8')
        except Exception as e:
            QMessageBox.warning(self, 'Entrée invalide', f'Saisir binaire (multiple de 8), hex (paire), ou texte. Erreur: {e}')
            raise

    def on_encode(self):
        try:
            payload = self._read_word_input()
        except Exception:
            return
        self.codec.enabled = not self.chk_disable_coding.isChecked()
        coded = self.codec.encode(payload)
        self.current_payload = coded
        self.encoded_view.setText(to_hex(coded))

    def on_inject(self):
        # Toujours repartir du mot encodé pour éviter l'accumulation d'erreurs
        try:
            payload = self._read_word_input()
        except Exception:
            QMessageBox.warning(self, 'Aucun mot', 'Encoder un mot avant d\'injecter')
            return
        self.codec.enabled = not self.chk_disable_coding.isChecked()
        coded = self.codec.encode(payload)
        num_errors = self.spin_errors.value()
        after = inject_exact_bits(coded, num_errors)
        self.current_payload = after
        self.encoded_view.setText(to_hex(after))

    def on_send(self):
        try:
            # ensure current_payload
            if not hasattr(self, 'current_payload'):
                self.on_encode()
            payload = self.current_payload
            frame = build_frame(payload)
            port = self.port_combo.currentText()
            if not port:
                QMessageBox.warning(self, 'Port manquant', 'Sélectionner un port série')
                return
            baud = int(self.baud_combo.currentText())
            link = SerialLink(port, baud)
            try:
                payload_recv, leftover = link.send_and_receive(frame, read_timeout=1.0)
            finally:
                link.close()
            if payload_recv is None:
                self.received_view.setText('<Aucune trame>')
                self.decoded_view.setText('')

                return
            self.received_view.setText(to_hex(payload_recv))
            # decode
            self.codec.enabled = not self.chk_disable_coding.isChecked()
            decoded, status, ok, num_errors = self.codec.decode(payload_recv)
            if ok:
                hex_str = to_hex(decoded)
                bin_str = to_bin(decoded)
                text_str = to_text(decoded)
                self.decoded_view.setPlainText(f"Hex: {hex_str}\nBin: {bin_str}\nTexte: '{text_str}'\nStatut: {status} - Erreurs corrigées: {num_errors}")
            else:
                self.decoded_view.setPlainText("Détection impossible : trop d'erreurs détectées")
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, 'Erreur', str(e))

    def on_test(self):
        # send TEST message (raw) and expect loopback
        try:
            msg = b'TEST'
            payload = msg if self.chk_disable_coding.isChecked() else self.codec.encode(msg)
            frame = build_frame(payload)
            port = self.port_combo.currentText()
            if not port:
                QMessageBox.warning(self, 'Port manquant', 'Sélectionner un port série')
                return
            baud = int(self.baud_combo.currentText())
            link = SerialLink(port, baud)
            try:
                payload_recv, _ = link.send_and_receive(frame, read_timeout=1.0)
            finally:
                link.close()
            if payload_recv is None:
                QMessageBox.information(self, 'Test', 'Aucune réponse')
                return
            # try decode
            self.received_view.setText(to_hex(payload_recv))
            self.codec.enabled = not self.chk_disable_coding.isChecked()
            decoded, status, ok, num_errors = self.codec.decode(payload_recv)
            if ok:
                QMessageBox.information(self, 'Test', f'Reçu décodé:\nHex: {to_hex(decoded)}\nBin: {to_bin(decoded)}\nTexte: \'{to_text(decoded)}\'\nStatut: {status} - Erreurs: {num_errors}')
            else:
                QMessageBox.warning(self, 'Test', f'Décodage impossible: {status}')
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, 'Erreur', str(e))


