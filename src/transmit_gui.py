"""Transmission window for the TP."""
from PySide6.QtWidgets import (QWidget, QLabel, QPushButton, QComboBox,
                               QLineEdit, QCheckBox, QSpinBox, QGridLayout, QMessageBox)
from PySide6.QtCore import Signal, QTimer
from src.serial_comm import list_serial_ports, build_frame, SerialLink
from src.codec import ChannelCodec
from src.utils import to_hex, inject_exact_bits
import traceback


class TransmitWindow(QWidget):
    data_sent = Signal(bytes, str)  # Signal to send received data to receive window: (received_payload, decoded_info_str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Transmission - TP RS232')
        self.codec = ChannelCodec(t=4, enabled=True)
        self.link: SerialLink | None = None
        self._build_ui()
        self._refresh_ports()
        self.port_timer = QTimer(self)
        self.port_timer.timeout.connect(self._refresh_ports)
        self.port_timer.start(2000)

    def _build_ui(self):
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
        layout.addWidget(QLabel('Mot (binaire multiple de 8 bits, hex paire, ou texte, taille variable):'), 1, 0, 1, 4)
        self.word_input = QLineEdit('00000000')
        layout.addWidget(self.word_input, 2, 0, 1, 4)

        # Format selection
        self.chk_binary = QCheckBox('Binaire')
        self.chk_hex = QCheckBox('Hexadécimal')
        self.chk_text = QCheckBox('Texte')
        self.chk_binary.setChecked(True)  # Default to binary
        self.chk_binary.stateChanged.connect(self._on_format_changed)
        self.chk_hex.stateChanged.connect(self._on_format_changed)
        self.chk_text.stateChanged.connect(self._on_format_changed)
        layout.addWidget(self.chk_binary, 3, 0)
        layout.addWidget(self.chk_hex, 3, 1)
        layout.addWidget(self.chk_text, 3, 2)

        # Options
        self.chk_disable_coding = QCheckBox('Inhiber codage canal (envoyer brut)')
        layout.addWidget(self.chk_disable_coding, 3, 3)

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
        self.spin_errors.setMaximum(256)
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

        self.setLayout(layout)

    def _on_format_changed(self):
        # Ensure only one checkbox is checked
        sender = self.sender()
        if sender.isChecked():
            if sender == self.chk_binary:
                self.chk_hex.setChecked(False)
                self.chk_text.setChecked(False)
            elif sender == self.chk_hex:
                self.chk_binary.setChecked(False)
                self.chk_text.setChecked(False)
            elif sender == self.chk_text:
                self.chk_binary.setChecked(False)
                self.chk_hex.setChecked(False)
        else:
            # If unchecked, check binary by default
            if not any([self.chk_binary.isChecked(), self.chk_hex.isChecked(), self.chk_text.isChecked()]):
                self.chk_binary.setChecked(True)

    def _refresh_ports(self):
        current = self.port_combo.currentText()
        ports = list_serial_ports()
        self.port_combo.clear()
        self.port_combo.addItems(ports)
        if current in ports:
            self.port_combo.setCurrentText(current)

    def _read_word_input(self) -> bytes:
        s = self.word_input.text().strip()
        try:
            if self.chk_binary.isChecked():
                if len(s) % 8 != 0:
                    raise ValueError('Longueur binaire doit être multiple de 8')
                bytes_list = []
                for i in range(0, len(s), 8):
                    byte_str = s[i:i+8]
                    val = int(byte_str, 2)
                    bytes_list.append(val)
                return bytes(bytes_list)
            elif self.chk_hex.isChecked():
                if len(s) % 2 != 0:
                    raise ValueError('Longueur hex doit être paire')
                return bytes.fromhex(s)
            elif self.chk_text.isChecked():
                return s.encode('utf-8')
            else:
                raise ValueError('Sélectionnez un format (Binaire, Hex, ou Texte)')
        except Exception as e:
            QMessageBox.warning(self, 'Entrée invalide', f'Erreur: {e}')
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
                self.data_sent.emit(b'', 'Détection impossible : aucune trame reçue')
                return
            self.data_sent.emit(payload_recv, self._decode_payload(payload_recv))
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, 'Erreur', str(e))

    def on_test(self):
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
            QMessageBox.information(self, 'Test', f'Reçu décodé: {payload_recv}')
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, 'Erreur', str(e))

    def _decode_payload(self, payload_recv):
        from src.utils import to_bin, to_text
        self.codec.enabled = not self.chk_disable_coding.isChecked()
        decoded, corrected_with_parity, status, ok, num_errors = self.codec.decode(payload_recv)
        if ok:
            hex_str = to_hex(decoded)
            bin_str = to_bin(decoded)
            text_str = to_text(decoded)
            # Count corrected bits
            corrected_bits = self._count_different_bits(payload_recv, corrected_with_parity)
            return f"Hex: {hex_str}\nBin: {bin_str}\nTexte: '{text_str}'\nStatut: {status} - Bits corrigés: {corrected_bits}"
        else:
            return "Détection impossible : trop d'erreurs détectées"

    def _count_different_bits(self, original: bytes, corrected: bytearray) -> int:
        count = 0
        for o, c in zip(original, corrected):
            diff = o ^ c
            count += bin(diff).count('1')
        return count